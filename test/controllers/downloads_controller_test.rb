require "test_helper"

class DownloadsControllerTest < ActionDispatch::IntegrationTest
  setup do
    @library = libraries(:kyle)
    @search = @library.libgen_searches.create!(author: "Nia Calder", title: "", format: "EPUB",
      status: :completed, result_count: 1)
    @result = @search.results.create!(author: "Nia Calder", series: "Maps of the Quiet Sea",
      title: "The Cartographer's Lantern", format: "EPUB", size: "2.1 MB", score: 100,
      mirrors: [ "https://libgen.li/ads.php?md5=abc" ])
    @download = @result.book_downloads.create!(library: @library, status: :completed,
      started_at: Time.current, finished_at: Time.current)
  end

  test "index lists only the current user's downloads" do
    other_library = libraries(:liz)
    other_result = other_library.libgen_searches.create!(author: "", title: "Other", format: "PDF",
      status: :completed, result_count: 1).results.create!(title: "Other", format: "PDF")
    other_result.book_downloads.create!(library: other_library, status: :failed, error: "cut short")

    log_in_as(users(:kyle))
    get downloads_path

    assert_response :success
    assert_select "tbody tr", count: 1
    assert_select "td", text: "The Cartographer's Lantern"
    assert_select "td", text: "2.1 MB"
    assert_select "td", text: "Completed"
    assert_select "td", text: "Failed", count: 0
  end

  test "index lists the newest download first" do
    @result.book_downloads.create!(library: @library, status: :pending, created_at: 1.minute.from_now)

    log_in_as(users(:kyle))
    get downloads_path

    assert_select "tbody tr:first-child td", text: "Pending"
  end
end
