require "application_system_test_case"

class LibrariesTest < ApplicationSystemTestCase
  test "browsing a library" do
    visit root_path

    click_on "Browse libraries"
    click_on "Kyle"

    assert_selector "h1", text: "Kyle"
    assert_selector "main.container-fluid"
    assert_selector ".table-responsive.w-100"
    assert_selector "table.table.w-100"
    assert_text "Dune"
  end
end
