require "test_helper"

class BookDownloadsControllerTest < ActionDispatch::IntegrationTest
  setup do
    @library = libraries(:kyle)
    @search = @library.libgen_searches.create!(author: "Nia Calder", title: "", format: "EPUB",
      status: :completed, result_count: 1)
    @result = @search.results.create!(author: "Nia Calder", series: "Maps of the Quiet Sea",
      title: "The Cartographer's Lantern", format: "EPUB", size: "2.1 MB", score: 100,
      mirrors: [ "https://libgen.li/ads.php?md5=abc" ])
  end

  test "create enqueues a download and redirects to the search" do
    assert_enqueued_with(job: BookDownloadJob) do
      post download_library_libgen_search_path(@library, @search),
        params: { result_id: @result.id }
    end

    download = BookDownload.last
    assert_equal @library.id, download.library_id
    assert_equal @result.id, download.libgen_search_result_id
    assert download.pending?
    assert_redirected_to library_libgen_search_path(@library, @search)
  end

  test "create does not enqueue a second download while one is running" do
    @result.book_downloads.create!(library: @library, status: :running)

    assert_no_enqueued_jobs do
      post download_library_libgen_search_path(@library, @search), params: { result_id: @result.id }
    end

    assert_redirected_to library_libgen_search_path(@library, @search)
  end

  test "a completed download can be started again" do
    @result.book_downloads.create!(library: @library, status: :completed)

    assert_difference "BookDownload.count" do
      post download_library_libgen_search_path(@library, @search), params: { result_id: @result.id }
    end
  end

  test "create does not expose another library's search result" do
    post download_library_libgen_search_path(libraries(:liz), @search), params: { result_id: @result.id }

    assert_response :not_found
  end

  test "create rejects an unknown result" do
    assert_no_difference "BookDownload.count" do
      post download_library_libgen_search_path(@library, @search), params: { result_id: 0 }
    end

    assert_response :not_found
  end
end
