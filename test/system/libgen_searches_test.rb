require "application_system_test_case"

class LibgenSearchesTest < ApplicationSystemTestCase
  test "searching libgen" do
    results = [
      LibgenSearch::Result.new(author: "Nia Calder", series: "Maps of the Quiet Sea",
        title: "The Cartographer's Lantern", format: "EPUB", size: "2.1 MB", score: 88,
        mirrors: [ "https://libgen.li/ads/one" ])
    ]
    LibgenSearch.stub(:call, results) do
      visit root_path

      click_on "Search Libgen"

      assert_selector "h1", text: "Search Libgen"
      assert_selector "table", count: 0

      fill_in "Author", with: "Nia Calder"
      click_on "Search"

      assert_selector "h1", text: "Search Libgen"
      assert_text "1 result found"
      assert_selector "tbody tr", count: 1
      assert_text "The Cartographer's Lantern"
    end
  end
end
