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
    assert_selector "main table"
    assert_text "Dune"

    find("tbody tr", text: "Dune").right_click
    assert_selector ".context-menu:not([hidden])"
    assert_link "Download", href: %r{/rails/active_storage/blobs/}
    assert_link "Edit", href: edit_library_book_path(libraries(:kyle), books(:dune))
  end

  test "editing a book" do
    visit library_path(libraries(:kyle))

    find("tbody tr", text: "Dune").right_click
    click_on "Edit"

    assert_selector "h1", text: "Edit Dune"
    fill_in "Author", with: "Frank P. Herbert"
    click_on "Save"

    assert_text "Book updated."
    assert_text "Frank P. Herbert"
  end
end
