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

  test "convert enqueues a background conversion" do
    attach_dune_epub

    assert_enqueued_with(job: BookConversionJob) do
      post convert_book_path(@book)
    end

    assert_redirected_to root_path
    assert @book.reload.azw3_pending?
  end

  test "convert does not enqueue twice while a conversion is in flight" do
    attach_dune_epub
    @book.update!(azw3_status: :running)

    assert_no_enqueued_jobs only: BookConversionJob do
      post convert_book_path(@book)
    end

    assert_redirected_to root_path
    assert @book.reload.azw3_running?
  end

  test "convert rejects a book without a file" do
    post convert_book_path(@book)

    assert_response :not_found
  end

  test "download serves the converted file once and clears its state" do
    attach_dune_epub
    @book.azw3_file.attach(io: StringIO.new("azw3 bytes"), filename: "dune.azw3",
      content_type: EbookConversion::CONTENT_TYPE)
    @book.update!(azw3_status: :ready, azw3_source_blob_id: @book.file.blob.id)

    get download_book_path(@book)

    assert_response :ok
    assert_equal "application/x-mobi8-ebook", response.media_type
    assert_match "dune.azw3", response.headers["Content-Disposition"]
    assert_equal "azw3 bytes", response.body
    @book.reload
    assert_nil @book.azw3_status
    assert_not @book.azw3_file.attached?
  end

  test "download rejects a conversion made from an older file" do
    attach_dune_epub
    @book.azw3_file.attach(io: StringIO.new("stale azw3 bytes"), filename: "dune.azw3",
      content_type: EbookConversion::CONTENT_TYPE)
    @book.update!(azw3_status: :ready, azw3_source_blob_id: @book.file.blob.id + 1)

    get download_book_path(@book)

    assert_redirected_to root_path
    assert_equal "The book's file changed since that azw3 was made. Convert it again.", flash[:alert]
    @book.reload
    assert_nil @book.azw3_status
    assert_not @book.azw3_file.attached?
  end

  test "download redirects when no conversion is ready" do
    attach_dune_epub

    get download_book_path(@book)

    assert_redirected_to root_path
    assert_equal "That azw3 file is not ready. Convert the book first.", flash[:alert]
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

  private

  def attach_dune_epub
    @book.file.attach(io: file_fixture("dune.epub").open, filename: "dune.epub",
      content_type: "application/epub+zip")
  end
end
