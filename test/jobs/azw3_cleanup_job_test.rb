require "test_helper"

class Azw3CleanupJobTest < ActiveJob::TestCase
  test "purges an azw3 file that was never downloaded" do
    book = create_ready_book
    book.azw3_file.blob.update!(created_at: 2.days.ago)

    Azw3CleanupJob.perform_now

    book.reload
    assert_nil book.azw3_status
    assert_not book.azw3_file.attached?
  end

  test "keeps a fresh azw3 file" do
    book = create_ready_book

    Azw3CleanupJob.perform_now

    book.reload
    assert book.azw3_ready?
    assert book.azw3_file.attached?
  end

  private

  def create_ready_book
    book = books(:dune)
    book.file.attach(io: file_fixture("dune.epub").open, filename: "dune.epub",
      content_type: "application/epub+zip")
    book.azw3_file.attach(io: StringIO.new("azw3 bytes"), filename: "dune.azw3",
      content_type: EbookConversion::CONTENT_TYPE)
    book.update!(azw3_status: :ready, azw3_source_blob_id: book.file.blob.id)
    book
  end
end
