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

    assert_link "Dune", href: edit_library_book_path(libraries(:kyle), books(:dune))
    assert_link "azw3", href: download_library_book_path(libraries(:kyle), books(:dune))
  end

  test "editing a book" do
    visit library_path(libraries(:kyle))

    click_on "Dune"

    assert_selector "h1", text: "Edit Dune"
    fill_in "Author", with: "Frank P. Herbert"
    click_on "Save"

    assert_text "Book updated."
    assert_text "Frank P. Herbert"
  end
end
