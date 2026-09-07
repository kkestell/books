require "test_helper"

class BookConversionJobTest < ActiveJob::TestCase
  test "converts the book and marks it ready for download" do
    book = create_book
    converted = converted_result

    EbookConversion.stub(:convert, ->(io:, filename:, **) {
      assert_equal "dune.epub", filename
      converted
    }) do
      BookConversionJob.perform_now(book)
    end

    book.reload
    assert book.azw3_ready?
    assert book.azw3_file.attached?
    assert_equal "dune.azw3", book.azw3_file.filename.to_s
    assert_equal EbookConversion::CONTENT_TYPE, book.azw3_file.content_type
    assert_equal book.file.blob.id, book.azw3_source_blob_id
    assert_nil book.azw3_error
  end

  test "records a failure when the conversion fails" do
    book = create_book

    EbookConversion.stub(:convert,
      ->(**) { raise EbookConversion::Error, "ebook-convert is not available." }) do
      BookConversionJob.perform_now(book)
    end

    book.reload
    assert book.azw3_failed?
    assert_equal "ebook-convert is not available.", book.azw3_error
    assert_not book.azw3_file.attached?
  end

  test "does not rerun a conversion that already started" do
    book = create_book(status: :running)

    EbookConversion.stub(:convert, ->(**) { raise "Conversion should not be called" }) do
      BookConversionJob.perform_now(book)
    end

    assert book.reload.azw3_running?
  end

  private

  def create_book(status: :pending)
    book = books(:dune)
    book.file.attach(io: file_fixture("dune.epub").open, filename: "dune.epub",
      content_type: "application/epub+zip")
    book.update!(azw3_status: status)
    book
  end

  def converted_result
    file = Tempfile.new("converted", binmode: true)
    file.write("azw3 bytes")
    file.rewind
    EbookConversion::Result.new(file:, filename: "dune.azw3",
      content_type: EbookConversion::CONTENT_TYPE)
  end
end
