require "test_helper"

class HomeControllerTest < ActionDispatch::IntegrationTest
  test "should get index" do
    get root_url

    assert_response :success
    assert_select "link[href*='bootstrap@5.3.8/dist/css/bootstrap.min.css']"
    assert_select "script[src*='bootstrap@5.3.8/dist/js/bootstrap.bundle.min.js']"
    assert_select "a[href=?]", libraries_path, text: "Browse libraries"
  end
end
