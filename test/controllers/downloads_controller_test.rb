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

  test "index lists every download across libraries" do
    other_library = libraries(:liz)
    other_result = other_library.libgen_searches.create!(author: "", title: "Other", format: "PDF",
      status: :completed, result_count: 1).results.create!(title: "Other", format: "PDF")
    other_result.book_downloads.create!(library: other_library, status: :failed, error: "cut short")

    get downloads_path

    assert_response :success
    assert_select "tbody tr", count: 2
    assert_select "td", text: "The Cartographer's Lantern"
    assert_select "td", text: "2.1 MB"
    assert_select "td", text: "Completed"
    assert_select "td[title='cut short']", text: "Failed"
    assert_select "td a", text: "Kyle", href: library_path(@library)
    assert_select "td a", text: "Liz", href: library_path(other_library)
  end

  test "index lists the newest download first" do
    @result.book_downloads.create!(library: @library, status: :pending, created_at: 1.minute.from_now)

    get downloads_path

    assert_select "tbody tr:first-child td", text: "Pending"
  end
end
