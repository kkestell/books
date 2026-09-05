class BookDownloadJob < ApplicationJob
  queue_as :default

  def perform(book_download)
    return unless start(book_download)

    downloaded = Libgen::Downloader.download(
      mirrors: result(book_download).mirrors,
      fallback_filename: fallback_filename(book_download)
    )

    begin
      create_book(book_download, downloaded)
    ensure
      downloaded.file.close!
    end

    finish(book_download)
  rescue StandardError => error
    fail_download(book_download, error)
  end

  private

  def result(book_download)
    book_download.libgen_search_result
  end

  def fallback_filename(book_download)
    result = result(book_download)
    [ result.title, result.format.downcase.presence ].compact_blank.join(".")
  end

  def create_book(book_download, downloaded)
    book = book_download.library.books.create!(book_attributes(book_download).merge(metadata(downloaded)))
    book.file.attach(io: downloaded.file, filename: downloaded.filename,
      content_type: downloaded.content_type)
  end

  def book_attributes(book_download)
    result = result(book_download)
    { author: result.author, title: result.title, series: result.series, format: result.format }
  end

  # The download already succeeded, so a metadata failure never fails the
  # download - the book keeps the author and title from the search result.
  def metadata(downloaded)
    EbookMetadata.extract(io: downloaded.file, filename: downloaded.filename)
  rescue EbookMetadata::Error => error
    Rails.logger.warn("Could not extract ebook metadata: #{error.message}")
    {}
  end

  def start(book_download)
    started = false

    book_download.with_lock do
      if book_download.pending?
        book_download.update!(status: :running, started_at: Time.current)
        started = true
      end
    end

    broadcast(book_download) if started
    started
  end

  def finish(book_download)
    book_download.update!(status: :completed, finished_at: Time.current)
    broadcast(book_download)
  end

  def fail_download(book_download, error)
    Rails.logger.error("Book download #{book_download.id} failed: #{error.full_message}")
    book_download.reload
    book_download.update!(status: :failed, finished_at: Time.current, error: error.message)
    broadcast(book_download)
  rescue StandardError => reporting_error
    Rails.logger.error("Could not record book download failure: #{reporting_error.full_message}")
  end

  def broadcast(book_download)
    libgen_search = result(book_download).libgen_search
    libgen_search_result = result(book_download)
    libgen_search.broadcast_replace_to(
      libgen_search,
      target: ActionView::RecordIdentifier.dom_id(libgen_search_result),
      partial: "libgen_searches/result",
      locals: { result: libgen_search_result, libgen_search: }
    )
  end
end
