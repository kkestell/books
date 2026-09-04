require "test_helper"

class LibgenSearchesControllerTest < ActionDispatch::IntegrationTest
  test "show renders the empty search form" do
    get libgen_search_path
    assert_response :success
    assert_select "h1", text: "Search Libgen"
    assert_select "form[action='#{libgen_search_path}'][method='get']"
    assert_select "input[name='author']"
    assert_select "input[name='title']"
    assert_select "select[name='format'] option", count: LibgenSearch::SEARCH_FORMATS.size + 1
    assert_select "table", count: 0
  end

  test "show runs the search and lists results sorted by score" do
    results = [
      LibgenSearch::Result.new(author: "Nia Calder", series: "Maps of the Quiet Sea",
        title: "The Cartographer's Lantern", format: "EPUB", size: "2.1 MB", score: 88,
        mirrors: [ "https://libgen.li/ads/one" ]),
      LibgenSearch::Result.new(author: "Tamsin Rowe", series: "",
        title: "Small Gods of the Service Corridor", format: "AZW3", size: "N/A", score: 95,
        mirrors: [ "https://libgen.li/ads/two" ])
    ]
    LibgenSearch.stub(:call, ->(author:, title:, format:) {
      assert_equal "Nia Calder", author
      assert_equal "lantern", title
      assert_equal "EPUB", format
      results
    }) do
      get libgen_search_path, params: { author: "  Nia Calder  ", title: "lantern", format: "EPUB" }
    end

    assert_response :success
    assert_select "p", text: "2 results found"
    assert_select "tbody tr", count: 2
    assert_select "tbody tr:first-child td", text: /Small Gods of the Service Corridor/
    assert_select "tbody tr[data-mirrors='https://libgen.li/ads/two']"
  end

  test "show reports search failures" do
    LibgenSearch.stub(:call, ->(author:, title:, format:) {
      raise LibgenSearch::Error, "Search timed out - the server took too long to respond"
    }) do
      get libgen_search_path, params: { author: "Nia Calder" }
    end

    assert_response :success
    assert_select "div.alert-danger", text: "Search timed out - the server took too long to respond"
    assert_select "tbody tr", count: 0
  end

  test "show asks for a query when both fields are blank" do
    get libgen_search_path, params: { author: "", title: "" }

    assert_response :success
    assert_select "div.alert-danger", text: "Enter an author or a title to search for."
  end
end
