class BookConversionJob < ApplicationJob
  queue_as :default

  def perform(book)
    return unless start(book)

    converted = convert(book)
    begin
      book.azw3_file.attach(io: converted.file, filename: converted.filename,
        content_type: converted.content_type)
    ensure
      converted.file.close!
    end

    book.update!(azw3_status: :ready, azw3_source_blob_id: book.file.blob.id, azw3_error: nil)
    broadcast(book)
  rescue StandardError => error
    fail_conversion(book, error)
  end

  private

  def start(book)
    started = false

    book.with_lock do
      if book.azw3_pending?
        book.update!(azw3_status: :running)
        started = true
      end
    end

    broadcast(book) if started
    started
  end

  def convert(book)
    book.file.open do |source|
      EbookConversion.convert(io: source, filename: book.file.filename.to_s)
    end
  end

  def fail_conversion(book, error)
    Rails.logger.error("Book #{book.id} could not be converted: #{error.full_message}")
    book.reload
    book.update!(azw3_status: :failed, azw3_error: error.message)
    broadcast(book)
  rescue StandardError => reporting_error
    Rails.logger.error("Could not record conversion failure: #{reporting_error.full_message}")
  end

  def broadcast(book)
    book.broadcast_replace_to(
      book.library,
      target: ActionView::RecordIdentifier.dom_id(book),
      partial: "books/book",
      locals: { book: }
    )
  end
end
