require "application_system_test_case"

class LibgenSearchesTest < ApplicationSystemTestCase
  test "starting a search shows the pending status page" do
    visit root_path

    click_on "Browse libraries"
    click_on "Kyle"
    click_on "Search Libgen"

    assert_selector "h1", text: "Search Libgen in Kyle"
    assert_selector "table", count: 0

    fill_in "Author", with: "Nia Calder"
    fill_in "Title", with: "Cartographer"
    select "EPUB", from: "Format"
    click_on "Search"

    assert_selector "h1", text: "Search Libgen in Kyle"
    assert_text "Waiting for the background searcher…"
  end

  test "a completed search shows its results" do
    search = completed_search_with_result

    visit library_libgen_search_path(libraries(:kyle), search)

    assert_selector "h1", text: "Search Libgen in Kyle"
    assert_text "Search complete. 1 result found."
    assert_selector "tbody tr", count: 1
    assert_text "The Cartographer's Lantern"
  end

  test "a search result without a download shows a download button" do
    search = completed_search_with_result

    visit library_libgen_search_path(libraries(:kyle), search)

    assert_button "Download"
    assert_no_text "Downloading…"
  end

  test "a running download shows its progress in place of the button" do
    search = completed_search_with_result
    search.results.first.book_downloads.create!(library: libraries(:kyle), status: :running)

    visit library_libgen_search_path(libraries(:kyle), search)

    assert_text "Downloading…"
    assert_no_button "Download"
  end

  test "a completed download links into the library" do
    search = completed_search_with_result
    search.results.first.book_downloads.create!(library: libraries(:kyle), status: :completed)

    visit library_libgen_search_path(libraries(:kyle), search)

    assert_link "In library", href: library_path(libraries(:kyle))
  end

  test "a failed download offers a retry with the error" do
    search = completed_search_with_result
    search.results.first.book_downloads.create!(library: libraries(:kyle), status: :failed,
      error: "The Libgen server did not return the requested file.")

    visit library_libgen_search_path(libraries(:kyle), search)

    assert_button "Retry download"
    assert_selector "button[title='The Libgen server did not return the requested file.']"
  end

  private

  def completed_search_with_result
    search = libraries(:kyle).libgen_searches.create!(author: "Nia Calder", title: "", format: "EPUB",
      status: :completed, result_count: 1)
    search.results.create!(author: "Nia Calder", series: "Maps of the Quiet Sea",
      title: "The Cartographer's Lantern", format: "EPUB", size: "2.1 MB", score: 100,
      mirrors: [ "https://libgen.li/ads/one" ])
    search
  end
end
