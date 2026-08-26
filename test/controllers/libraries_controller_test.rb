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
end
