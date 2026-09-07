require "application_system_test_case"

class LibrariesTest < ApplicationSystemTestCase
  test "browsing the library" do
    books(:dune).file.attach(
      io: file_fixture("dune.epub").open,
      filename: "dune.epub",
      content_type: "application/epub+zip"
    )

    visit root_path
    click_on "Log in as Kyle"

    assert_selector "h1", text: "Kyle"
    assert_selector "main table"
    assert_text "Dune"
    assert_text "Dune #1"

    assert_link "Dune", href: edit_book_path(books(:dune))
    assert_button "azw3"
  end

  test "converting a book for download" do
    books(:dune).file.attach(
      io: file_fixture("dune.epub").open,
      filename: "dune.epub",
      content_type: "application/epub+zip"
    )

    visit root_path
    click_on "Log in as Kyle"

    click_button "azw3"

    assert_text "Converting…"
    assert books(:dune).reload.azw3_pending?
  end

  test "filtering the library table" do
    visit root_path
    click_on "Log in as Kyle"

    assert_selector "datalist#library-filter-author option[value='Frank Herbert']", visible: :all
    assert_selector "datalist#library-filter-series option[value='Dune']", visible: :all
    assert_no_selector "datalist#library-filter-series option[value='Dune #1']", visible: :all

    fill_in "Title", with: "Dun"
    assert_text "Frank Herbert"

    fill_in "Title", with: "Circe"
    assert_no_text "Frank Herbert"

    fill_in "Title", with: ""
    fill_in "Author", with: "Madeline"
    assert_no_text "Dune"

    fill_in "Author", with: "Herbert"
    assert_text "Dune #1"

    fill_in "Series", with: "#2"
    assert_no_text "Dune #1"

    fill_in "Series", with: "Dune"
    assert_text "Dune #1"
  end

  test "editing a book" do
    visit root_path
    click_on "Log in as Kyle"

    click_on "Dune"

    assert_selector "h1", text: "Edit Dune"
    fill_in "Author", with: "Frank P. Herbert"
    click_on "Save"

    assert_text "Book updated."
    assert_text "Frank P. Herbert"
  end
end
