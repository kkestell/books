require "test_helper"

class LibgenSearchesControllerTest < ActionDispatch::IntegrationTest
  test "new renders the search form" do
    get new_libgen_search_path
    assert_response :success
    assert_select "h1", text: "Search Libgen"
    assert_select "form[action='#{libgen_searches_path}'][method='post']"
    assert_select "input[name='author']"
    assert_select "input[name='title']"
    assert_select "select[name='format'] option", count: Libgen::Scraper::SEARCH_FORMATS.size + 1
    assert_select "table", count: 0
  end

  test "create rejects a search without author or title" do
    assert_no_difference "LibgenSearch.count" do
      post libgen_searches_path, params: { author: " ", title: "" }
    end

    assert_response :unprocessable_entity
    assert_select "div.alert-danger", text: "Enter an author or a title to search for."
  end

  test "create stores the search, enqueues the job, and redirects" do
    assert_enqueued_with(job: LibgenSearchJob) do
      post libgen_searches_path, params: { author: " Nia Calder ", title: "lantern", format: "EPUB" }
    end

    search = LibgenSearch.last
    assert_equal "Nia Calder", search.author
    assert_equal "lantern", search.title
    assert_equal "EPUB", search.format
    assert search.pending?
    assert_redirected_to libgen_search_path(search)
  end

  test "create ignores an unknown format" do
    post libgen_searches_path, params: { author: "Nia Calder", format: "DOCX" }

    assert_equal "", LibgenSearch.last.format
  end

  test "show renders search progress and results" do
    search = LibgenSearch.create!(author: "Nia Calder", title: "", format: "EPUB",
      status: :completed, result_count: 1)
    search.results.create!(author: "Nia Calder", series: "Maps of the Quiet Sea",
      title: "The Cartographer's Lantern", format: "EPUB", size: "2.1 MB", score: 100,
      mirrors: [ "https://libgen.li/ads/one" ])

    get libgen_search_path(search)

    assert_response :success
    assert_select "p.libgen-search__status", text: "Search complete. 1 result found."
    assert_select "tbody tr", count: 1
    assert_select "tr[data-mirrors='https://libgen.li/ads/one']"
  end

  test "show renders a failed search" do
    search = LibgenSearch.create!(author: "Nia Calder", title: "", format: "",
      status: :failed, error: "HTTP Error 403")

    get libgen_search_path(search)

    assert_response :success
    assert_select "p.libgen-search__status", text: "Search failed: HTTP Error 403"
  end
end
