require "test_helper"

class HomeControllerTest < ActionDispatch::IntegrationTest
  test "should get index" do
    get root_url

    assert_response :success
    assert_select "a[href=?]", libraries_path, text: "Browse libraries"
  end
end
