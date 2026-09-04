require "application_system_test_case"

class LibrariesTest < ApplicationSystemTestCase
  test "browsing a library" do
    books(:dune).file.attach(
      io: file_fixture("dune.epub").open,
      filename: "dune.epub",
      content_type: "application/epub+zip"
    )

    visit root_path

    click_on "Browse libraries"
    click_on "Kyle"

    assert_selector "h1", text: "Kyle"
    assert_selector "main.container-fluid"
    assert_selector ".table-responsive.w-100"
    assert_selector "table.table.w-100.library-books"
    assert_text "Dune"

    author_cell = find("tbody td", text: "Frank Herbert")
    assert_equal "14px", page.evaluate_script("getComputedStyle(arguments[0]).fontSize", author_cell.native)
    assert_equal "nowrap", page.evaluate_script("getComputedStyle(arguments[0]).whiteSpace", author_cell.native)
    assert_equal "ellipsis", page.evaluate_script("getComputedStyle(arguments[0]).textOverflow", author_cell.native)

    find("tbody tr", text: "Dune").right_click
    assert_selector ".context-menu:not([hidden])"
    assert_link "Download", href: %r{/rails/active_storage/blobs/}
  end
end
