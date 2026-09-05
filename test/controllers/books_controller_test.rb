require "test_helper"

class BooksControllerTest < ActionDispatch::IntegrationTest
  setup do
    log_in_as(users(:kyle))
    @book = books(:dune)
  end

  test "edit renders the form" do
    get edit_book_path(@book)

    assert_response :ok
    assert_select "form"
    assert_select "input[name='book[title]']" do |input|
      assert_equal "Dune", input.first["value"]
    end
  end

  test "update saves the book and redirects to the library" do
    patch book_path(@book), params: { book: {
      title: "Dune Messiah", series: "Dune", series_number: "2", published: "1969-01-01"
    } }

    assert_redirected_to root_path
    @book.reload
    assert_equal "Dune Messiah", @book.title
    assert_equal 2, @book.series_number
    assert_equal Date.new(1969, 1, 1), @book.published
  end

  test "update clears a series that has no number" do
    patch book_path(@book), params: { book: { series: "Dune", series_number: "" } }

    assert_redirected_to root_path
    @book.reload
    assert_nil @book.series
    assert_nil @book.series_number
  end

  test "update rejects a blank title" do
    patch book_path(@book), params: { book: { title: "" } }

    assert_response :unprocessable_entity
    assert_equal "Dune", @book.reload.title
  end

  test "update does not expose another user's book" do
    log_in_as(users(:liz))

    patch book_path(@book), params: { book: { title: "Stolen" } }

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
      get download_book_path(@book)
    end

    assert_response :ok
    assert_equal "application/x-mobi8-ebook", response.media_type
    assert_match "dune.azw3", response.headers["Content-Disposition"]
    assert_equal "azw3 bytes", response.body
    converted.close!
  end

  test "download reports a failed conversion" do
    @book.file.attach(io: file_fixture("dune.epub").open, filename: "dune.epub",
      content_type: "application/epub+zip")
    error = EbookConversion::Error.new("ebook-convert is not available.")

    EbookConversion.stub(:convert, lambda { |_| raise error }) do
      get download_book_path(@book)
    end

    assert_redirected_to root_path
    assert_equal "ebook-convert is not available.", flash[:alert]
  end

  test "download rejects a book without a file" do
    get download_book_path(@book)

    assert_response :not_found
  end

  test "download does not expose another user's book" do
    log_in_as(users(:liz))

    get download_book_path(@book)

    assert_response :not_found
  end
end
