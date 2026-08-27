require "test_helper"

class BookImportJobTest < ActiveJob::TestCase
  test "imports every attached ebook and records progress" do
    book_import = create_import("earthsea.epub", "tehanu.mobi")
    metadata = { author: "Ursula K. Le Guin", title: "Earthsea" }

    assert_difference "Book.count", 2 do
      EbookMetadata.stub(:extract, metadata) do
        BookImportJob.perform_now(book_import)
      end
    end

    book_import.reload
    assert book_import.completed?
    assert_equal 2, book_import.processed_files
    assert_equal 2, book_import.imported_files
    assert_equal 0, book_import.failed_files
    assert_equal 100, book_import.progress_percentage
    assert_empty book_import.files
    assert Book.order(:created_at).last.file.attached?
  end

  test "continues after a metadata error" do
    book_import = create_import("broken.epub", "good.epub")
    extract = lambda do |filename:, **|
      raise EbookMetadata::Error, "Unreadable metadata." if filename == "broken.epub"

      { author: "Octavia Butler", title: "Kindred" }
    end

    assert_difference "Book.count", 1 do
      EbookMetadata.stub(:extract, extract) do
        BookImportJob.perform_now(book_import)
      end
    end

    book_import.reload
    assert book_import.completed?
    assert_equal 2, book_import.processed_files
    assert_equal 1, book_import.imported_files
    assert_equal 1, book_import.failed_files
    assert_match(/broken\.epub: Unreadable metadata/, book_import.error_messages.first)
  end

  test "stops between ebooks after cancellation is requested" do
    book_import = create_import("first.epub", "second.epub")
    extract = lambda do |**|
      book_import.request_cancellation!
      { author: "N. K. Jemisin", title: "The Fifth Season" }
    end

    assert_difference "Book.count", 1 do
      EbookMetadata.stub(:extract, extract) do
        BookImportJob.perform_now(book_import)
      end
    end

    book_import.reload
    assert book_import.cancelled?
    assert_equal 1, book_import.processed_files
    assert_equal 1, book_import.imported_files
    assert_empty book_import.files
  end

  test "cleans up files when a pending import was cancelled" do
    book_import = create_import("first.epub", "second.epub")
    book_import.request_cancellation!

    assert_no_difference "Book.count" do
      BookImportJob.perform_now(book_import)
    end

    assert book_import.reload.cancelled?
    assert_empty book_import.files
  end

  private

  def create_import(*filenames)
    book_import = libraries(:kyle).book_imports.create!(total_files: filenames.size)

    filenames.each do |filename|
      file_fixture("dune.epub").open do |file|
        book_import.files.attach(io: file, filename:, content_type: "application/octet-stream")
      end
    end

    book_import
  end
end
