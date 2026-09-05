require "application_system_test_case"

class LibgenSearchesTest < ApplicationSystemTestCase
  test "starting a search shows the pending status page" do
    visit root_path

    click_on "Search Libgen"

    assert_selector "h1", text: "Search Libgen"
    assert_selector "table", count: 0

    fill_in "Author", with: "Nia Calder"
    fill_in "Title", with: "Cartographer"
    select "EPUB", from: "Format"
    click_on "Search"

    assert_selector "h1", text: "Search Libgen"
    assert_text "Waiting for the background searcher…"
  end

  test "a completed search shows its results" do
    search = LibgenSearch.create!(author: "Nia Calder", title: "", format: "EPUB",
      status: :completed, result_count: 1)
    search.results.create!(author: "Nia Calder", series: "Maps of the Quiet Sea",
      title: "The Cartographer's Lantern", format: "EPUB", size: "2.1 MB", score: 100,
      mirrors: [ "https://libgen.li/ads/one" ])

    visit libgen_search_path(search)

    assert_selector "h1", text: "Search Libgen"
    assert_text "Search complete. 1 result found."
    assert_selector "tbody tr", count: 1
    assert_text "The Cartographer's Lantern"
  end
end
