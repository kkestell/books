require "test_helper"

class BooksControllerTest < ActionDispatch::IntegrationTest
  setup do
    @library = libraries(:kyle)
    @book = books(:dune)
  end

  test "edit renders the form" do
    get edit_library_book_path(@library, @book)

    assert_response :ok
    assert_select "form"
    assert_select "input[name='book[title]']" do |input|
      assert_equal "Dune", input.first["value"]
    end
  end

  test "update saves the book and redirects to the library" do
    patch library_book_path(@library, @book), params: { book: {
      title: "Dune Messiah", series: "Dune", series_number: "2", published: "1969-01-01"
    } }

    assert_redirected_to library_path(@library)
    @book.reload
    assert_equal "Dune Messiah", @book.title
    assert_equal 2, @book.series_number
    assert_equal Date.new(1969, 1, 1), @book.published
  end

  test "update clears a series that has no number" do
    patch library_book_path(@library, @book), params: { book: { series: "Dune", series_number: "" } }

    assert_redirected_to library_path(@library)
    @book.reload
    assert_nil @book.series
    assert_nil @book.series_number
  end

  test "update rejects a blank title" do
    patch library_book_path(@library, @book), params: { book: { title: "" } }

    assert_response :unprocessable_entity
    assert_equal "Dune", @book.reload.title
  end

  test "update does not expose another library's book" do
    patch library_book_path(libraries(:liz), @book), params: { book: { title: "Stolen" } }

    assert_response :not_found
  end

  test "download converts the book to azw3" do
    @book.file.attach(io: file_fixture("dune.epub").open, filename: "dune.epub",
      content_type: "application/epub+zip")
    converted = Tempfile.new("converted", binmode: true)
    converted.write("azw3 bytes")
    converted.rewind
    result = EbookConversion::Result.new(file: converted, filename: "dune.azw3",
      content_type: EbookConversion::CONTENT_TYPE)

    EbookConversion.stub(:convert, result) do
      get download_library_book_path(@library, @book)
    end

    assert_response :ok
    assert_equal "application/x-mobi8-ebook", response.media_type
    assert_match "dune.azw3", response.headers["Content-Disposition"]
    assert_equal "azw3 bytes", response.body
    converted.close!
  end

  test "download rejects a book without a file" do
    get download_library_book_path(@library, @book)

    assert_response :not_found
  end

  test "download does not expose another library's book" do
    get download_library_book_path(libraries(:liz), @book)

    assert_response :not_found
  end
end
