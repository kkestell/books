require "test_helper"

class SessionsControllerTest < ActionDispatch::IntegrationTest
  test "the login page links each user" do
    get login_path

    assert_response :success
    assert_select "a", text: "Log in as Kyle"
    assert_select "a", text: "Log in as Liz"
  end

  test "unauthenticated requests redirect to the login page" do
    get root_path

    assert_redirected_to login_path
  end

  test "logging in as kyle shows his library" do
    get login_user_path(users(:kyle).username)

    assert_redirected_to root_path
    follow_redirect!
    assert_select "h1", text: "Kyle"
  end

  test "logging in as liz shows her library" do
    get login_user_path(users(:liz).username)

    assert_redirected_to root_path
    follow_redirect!
    assert_select "h1", text: "Liz"
  end

  test "an unknown username returns to the login page" do
    get login_user_path("nobody")

    assert_redirected_to login_path
  end

  test "logging out ends the session" do
    log_in_as(users(:kyle))

    delete logout_path

    assert_redirected_to login_path
    get root_path
    assert_redirected_to login_path
  end
end
