require "application_system_test_case"

class SessionsTest < ApplicationSystemTestCase
  test "logging in and out" do
    visit root_path

    assert_selector "h1", text: "Books"
    click_on "Log in as Kyle"

    assert_selector "h1", text: "Kyle"

    click_on "Log out"

    assert_selector "a", text: "Log in as Liz"
  end
end
