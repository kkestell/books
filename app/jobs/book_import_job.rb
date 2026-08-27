class BookImportJob < ApplicationJob
  queue_as :default

  def perform(book_import)
    unless start(book_import)
      book_import.files_attachments.find_each(&:purge) if book_import.cancelled?
      return
    end

    book_import.files_attachments.order(:id).to_a.each do |attachment|
      book_import.reload
      break if book_import.cancel_requested?

      import_attachment(book_import, attachment)
      broadcast(book_import)
    end

    finish(book_import)
  rescue StandardError => error
    fail_import(book_import, error)
  end

  private

  def start(book_import)
    started = false

    book_import.with_lock do
      if book_import.pending? && !book_import.cancel_requested?
        book_import.update!(status: :importing, started_at: Time.current)
        started = true
      end
    end

    broadcast(book_import) if started
    started
  end

  def import_attachment(book_import, attachment)
    attachment.blob.open do |file|
      metadata = EbookMetadata.extract(io: file, filename: attachment.filename.to_s)
      book = book_import.library.books.build({
        author: "Unknown Author",
        title: "Unknown Title",
        format: attachment.filename.extension&.upcase
      }.merge(metadata))
      book.file.attach(attachment.blob)
      book.save!
    end

    attachment.delete
    record_result(book_import, imported: true)
  rescue EbookMetadata::Error, ActiveRecord::RecordInvalid, ActiveStorage::FileNotFoundError => error
    attachment.purge
    record_result(book_import, imported: false, error: "#{attachment.filename}: #{error.message}")
  end

  def record_result(book_import, imported:, error: nil)
    book_import.with_lock do
      book_import.processed_files += 1
      imported ? book_import.imported_files += 1 : book_import.failed_files += 1
      book_import.error_messages = book_import.error_messages + [ error ] if error
      book_import.save!
    end
  end

  def finish(book_import)
    book_import.reload

    if book_import.cancel_requested?
      book_import.files_attachments.find_each(&:purge)
      book_import.update!(status: :cancelled, finished_at: Time.current)
    else
      book_import.update!(status: :completed, finished_at: Time.current)
    end

    broadcast(book_import)
  end

  def fail_import(book_import, error)
    Rails.logger.error("Book import #{book_import.id} failed: #{error.full_message}")
    book_import.reload
    book_import.update!(
      status: :failed,
      finished_at: Time.current,
      error_messages: book_import.error_messages + [ "Import stopped: #{error.message}" ]
    )
    broadcast(book_import)
  rescue StandardError => reporting_error
    Rails.logger.error("Could not record book import failure: #{reporting_error.full_message}")
  end

  def broadcast(book_import)
    book_import.broadcast_replace_to(
      book_import,
      target: ActionView::RecordIdentifier.dom_id(book_import),
      partial: "book_imports/book_import",
      locals: { book_import: }
    )
  end
end
