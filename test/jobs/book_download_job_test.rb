require "test_helper"

class BookDownloadJobTest < ActiveJob::TestCase
  test "downloads the ebook and adds it to the library" do
    book_download = create_download
    metadata = { author: "Ursula K. Le Guin", title: "A Wizard of Earthsea",
      series: "Earthsea Cycle", series_number: 1 }
    downloaded = downloaded_result

    Libgen::Downloader.stub(:download, ->(mirrors:, fallback_filename:, **) {
      assert_equal [ "https://libgen.li/ads.php?md5=first" ], mirrors
      assert_equal "The Cartographer's Lantern.epub", fallback_filename
      downloaded
    }) do
      EbookMetadata.stub(:extract, metadata) do
        assert_difference "Book.count" do
          BookDownloadJob.perform_now(book_download)
        end
      end
    end

    book_download.reload
    assert book_download.completed?
    assert_not_nil book_download.finished_at

    book = book_download.library.books.order(:created_at).last
    assert_equal "Ursula K. Le Guin", book.author
    assert_equal "A Wizard of Earthsea", book.title
    assert_equal "Earthsea Cycle", book.series
    assert_equal 1, book.series_number
    assert book.file.attached?
    assert_equal "the-cartographer.epub", book.file.filename.to_s
  end

  test "keeps the search result's author and title when metadata extraction fails" do
    book_download = create_download
    downloaded = downloaded_result

    Libgen::Downloader.stub(:download, downloaded) do
      EbookMetadata.stub(:extract, ->(**) { raise EbookMetadata::Error, "Unreadable." }) do
        assert_difference "Book.count" do
          BookDownloadJob.perform_now(book_download)
        end
      end
    end

    book_download.reload
    assert book_download.completed?

    book = book_download.library.books.order(:created_at).last
    assert_equal "Nia Calder", book.author
    assert_equal "The Cartographer's Lantern", book.title
    assert_equal "Maps of the Quiet Sea", book.series
    assert_equal "EPUB", book.format
    assert book.file.attached?
  end

  test "records a failure when the download cannot be fetched" do
    book_download = create_download

    assert_no_difference "Book.count" do
      Libgen::Downloader.stub(:download,
        ->(**) { raise Libgen::Downloader::Error, "The Libgen server did not return the requested file." }) do
        BookDownloadJob.perform_now(book_download)
      end
    end

    book_download.reload
    assert book_download.failed?
    assert_equal "The Libgen server did not return the requested file.", book_download.error
    assert_not_nil book_download.finished_at
  end

  test "does not rerun a download that already started" do
    book_download = create_download(status: :running)

    assert_no_difference "Book.count" do
      Libgen::Downloader.stub(:download, ->(**) { raise "Downloader should not be called" }) do
        BookDownloadJob.perform_now(book_download)
      end
    end

    assert book_download.reload.running?
  end

  private

  def create_download(status: :pending)
    search = libraries(:kyle).libgen_searches.create!(author: "Nia Calder", title: "", format: "EPUB")
    result = search.results.create!(author: "Nia Calder", series: "Maps of the Quiet Sea",
      title: "The Cartographer's Lantern", format: "EPUB", size: "2.1 MB", score: 100,
      mirrors: [ "https://libgen.li/ads.php?md5=first" ])

    result.book_downloads.create!(library: libraries(:kyle), status:)
  end

  def downloaded_result
    file = Tempfile.new("downloaded", binmode: true)
    file.write("epub bytes")
    file.rewind
    Libgen::Downloader::Result.new(file:, filename: "the-cartographer.epub",
      content_type: "application/epub+zip")
  end
end
