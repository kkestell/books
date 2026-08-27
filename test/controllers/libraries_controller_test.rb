require "test_helper"

class LibrariesControllerTest < ActionDispatch::IntegrationTest
  test "index lists libraries" do
    get libraries_path
    assert_response :success
    assert_select "li", minimum: 2
    assert_select "a", text: "Kyle"
    assert_select "a", text: "Liz"
  end

  test "show lists a library's books by slug" do
    get library_path("kyle")
    assert_response :success
    assert_select "h1", text: "Kyle"
    assert_select "td", text: "Dune"
  end

  test "show 404s for an unknown slug" do
    get library_path("nobody")
    assert_response :not_found
  end

  test "new book import displays an upload form" do
    get new_library_book_import_path("kyle")

    assert_response :success
    assert_select "h1", text: "Import a book into Kyle"
    assert_select "input[type=file][name=file]"
    assert_select "input[type=submit][value='Import book']"
  end

  test "book import extracts metadata and attaches the ebook" do
    upload = fixture_file_upload("dune.epub", "application/epub+zip")
    metadata = {
      author: "Ursula K. Le Guin",
      title: "A Wizard of Earthsea",
      series: "Earthsea Cycle",
      series_number: 1,
      published: Date.new(1968, 1, 1),
      book_type: "Novel"
    }

    assert_difference([ "Book.count", "ActiveStorage::Attachment.count" ], 1) do
      EbookMetadata.stub(:extract, metadata) do
        post library_book_import_path("kyle"), params: { file: upload }
      end
    end

    book = Book.order(:created_at).last
    assert_redirected_to library_path("kyle")
    assert_equal libraries(:kyle), book.library
    assert_equal "Ursula K. Le Guin", book.author
    assert_equal "A Wizard of Earthsea", book.title
    assert_equal "Earthsea Cycle", book.series
    assert_equal 1, book.series_number
    assert_equal "EPUB", book.format
    assert book.file.attached?
    assert_equal "dune.epub", book.file.filename.to_s
  end

  test "book import requires a file" do
    assert_no_difference "Book.count" do
      post library_book_import_path("kyle")
    end

    assert_response :unprocessable_entity
    assert_select "[role=alert]", text: "Choose an ebook file to import."
  end

  test "book import displays metadata extraction errors" do
    upload = fixture_file_upload("dune.epub", "application/epub+zip")

    assert_no_difference "Book.count" do
      EbookMetadata.stub(:extract, ->(**) { raise EbookMetadata::Error, "Metadata extraction failed." }) do
        post library_book_import_path("kyle"), params: { file: upload }
      end
    end

    assert_response :unprocessable_entity
    assert_select "[role=alert]", text: "Metadata extraction failed."
  end
end
