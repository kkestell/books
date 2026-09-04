require "test_helper"

class LibgenSearchTest < ActiveSupport::TestCase
  test "scores strings exactly like fuzzywuzzy's token_sort_ratio" do
    cases = [
      [ 100, "fuzzy wuzzy was a bear", "wuzzy fuzzy was a bear" ],
      [ 100, "Nia Calder", "Calder, Nia" ],
      [ 100, "Hello   World", "hello world" ],
      [ 100, "Star Wars: Episode IV", "Episode IV - Star Wars" ],
      [ 100, "", "" ],
      [ 100, "", "ü" ],
      [ 95, "Nia Calder", "Nia Caldr" ],
      [ 80, "aaa", "aa" ],
      [ 19, "Nia Calder", "Tamsin Rowe" ],
      [ 0, "a", "b" ],
      [ 0, "", "abc" ],
      [ 0, "abc", "" ],
      [ 0, nil, "abc" ],
      [ 0, "abc", nil ]
    ]

    cases.each do |expected, first, second|
      assert_equal expected, LibgenSearch::Fuzzy.token_sort_ratio(first, second),
        "token_sort_ratio(#{first.inspect}, #{second.inspect})"
    end
  end

  test "reorders 'Last, First' author names" do
    assert_equal "Annemarie Vandermeer", LibgenSearch.fix_author("Vandermeer, Annemarie")
    assert_equal "Tamsin Rowe", LibgenSearch.fix_author("Tamsin Rowe")
    assert_equal "Middle A", LibgenSearch.fix_author("A, Middle, B")
  end

  test "parses results, filters by language and format, and stops when pages run out" do
    transport = FakeTransport.new([ results_page, "<html></html>" ])

    results = LibgenSearch.call(author: "Nia Calder", title: "", format: "EPUB", transport:)

    assert_equal [
      "https://libgen.li/index.php?req=Nia+Calder&res=100&page=1",
      "https://libgen.li/index.php?req=Nia+Calder&res=100&page=2"
    ], transport.requested_urls

    assert_equal 3, results.size

    cartographer = results.first
    assert_equal "Nia Calder", cartographer.author
    assert_equal "Maps of the Quiet Sea", cartographer.series
    assert_equal "The Cartographer's Lantern", cartographer.title
    assert_equal "EPUB", cartographer.format
    assert_equal "2.1 MB", cartographer.size
    assert_equal 100, cartographer.score
    assert_equal [ "https://libgen.li/ads/first", "http://mirror.example.org/file" ], cartographer.mirrors

    memory = results.second
    assert_equal "Winifred Featherstone-Haugh, Annemarie V...", memory.author
    assert_equal "A Memory Built from Snow", memory.title
    assert_equal "", memory.series
    assert_equal 24, memory.score

    plain = results.third
    assert_equal "Just A Plain Title", plain.title
    assert_equal "Tamsin Rowe", plain.author
    assert_equal 19, plain.score
    assert_equal [ "https://mirror.example.org/direct" ], plain.mirrors
  end

  test "searches by title alone when no author is given" do
    transport = FakeTransport.new([ results_page, "<html></html>" ])

    results = LibgenSearch.call(author: "", title: "The Cartographer's Lantern", format: "", transport:)

    assert_equal [
      "https://libgen.li/index.php?req=The+Cartographer%27s+Lantern&res=100&page=1",
      "https://libgen.li/index.php?req=The+Cartographer%27s+Lantern&res=100&page=2"
    ], transport.requested_urls
    assert_equal 4, results.size

    cartographer = results.first
    assert_equal 100, cartographer.score
  end

  test "wraps transport and parse failures in LibgenSearch::Error" do
    transport = FakeTransport.new([])

    error = assert_raises(LibgenSearch::Error) do
      LibgenSearch.call(author: "Nia Calder", title: "", format: "", transport:)
    end
    assert_equal "No more responses", error.message
  end

  private

  def results_page
    file_fixture("libgen_search_results.html").read
  end

  class FakeTransport
    attr_reader :requested_urls

    def initialize(responses)
      @responses = responses
      @requested_urls = []
    end

    def get(url)
      @requested_urls << url
      raise "No more responses" if @responses.empty?

      @responses.shift
    end
  end
end
