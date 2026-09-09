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
end
