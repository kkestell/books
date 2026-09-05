require "test_helper"

class LibgenSearchJobTest < ActiveJob::TestCase
  test "stores each page of results and completes the search" do
    search = LibgenSearch.create!(author: "Nia Calder", title: "", format: "EPUB")
    pages = [
      [
        Libgen::Scraper::Result.new(author: "Nia Calder", series: "Maps of the Quiet Sea",
          title: "The Cartographer's Lantern", format: "EPUB", size: "2.1 MB", score: 100,
          mirrors: [ "https://libgen.li/ads/one" ])
      ],
      [
        Libgen::Scraper::Result.new(author: "Tamsin Rowe", series: "",
          title: "Small Gods of the Service Corridor", format: "EPUB", size: "N/A", score: 19,
          mirrors: [ "https://libgen.li/ads/two" ])
      ]
    ]

    stub_scraper(pages) do
      LibgenSearchJob.perform_now(search)
    end

    search.reload
    assert search.completed?
    assert_equal 2, search.result_count
    assert_equal 2, search.results.count

    best = search.results.best_first.first
    assert_equal "The Cartographer's Lantern", best.title
    assert_equal "Maps of the Quiet Sea", best.series
    assert_equal [ "https://libgen.li/ads/one" ], best.mirrors
  end

  test "records a failure and keeps earlier results" do
    search = LibgenSearch.create!(author: "Nia Calder", title: "", format: "EPUB")
    failing_scraper = Class.new do
      def each_page
        yield [
          Libgen::Scraper::Result.new(author: "Nia Calder", series: "", title: "Earthsea",
            format: "EPUB", size: "1.0 MB", score: 50, mirrors: [])
        ]
        raise Libgen::Scraper::Error, "HTTP Error 403"
      end
    end

    Libgen::Scraper.stub(:new, ->(**) { failing_scraper.new }) do
      LibgenSearchJob.perform_now(search)
    end

    search.reload
    assert search.failed?
    assert_equal "HTTP Error 403", search.error
    assert_equal 1, search.result_count
    assert_not_nil search.finished_at
  end

  test "does not rerun a search that already started" do
    search = LibgenSearch.create!(author: "Nia Calder", title: "", format: "EPUB", status: :running)

    Libgen::Scraper.stub(:new, ->(**) { raise "Scraper should not be constructed" }) do
      LibgenSearchJob.perform_now(search)
    end

    assert search.reload.running?
    assert_empty search.results
  end

  private

  def stub_scraper(pages)
    scraper = Class.new do
      def initialize(pages)
        @pages = pages
      end

      def each_page
        @pages.each { |page| yield page }
      end
    end

    Libgen::Scraper.stub(:new, ->(**) { scraper.new(pages) }) do
      yield
    end
  end
end
