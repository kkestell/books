require "test_helper"

class BookImportTest < ActiveSupport::TestCase
  test "reports progress as a percentage" do
    book_import = BookImport.new(total_files: 4, processed_files: 3)

    assert_equal 75, book_import.progress_percentage
  end

  test "pending import can be cancelled immediately" do
    book_import = libraries(:kyle).book_imports.create!(total_files: 2)

    book_import.request_cancellation!

    assert book_import.cancelled?
    assert book_import.cancel_requested?
    assert_not_nil book_import.finished_at
  end
end
