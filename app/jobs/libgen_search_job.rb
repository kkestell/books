class LibgenSearchJob < ApplicationJob
  queue_as :default

  def perform(libgen_search)
    return unless start(libgen_search)

    scraper = Libgen::Scraper.new(author: libgen_search.author, title: libgen_search.title, format: libgen_search.format)
    scraper.each_page do |page_results|
      page_results.each { |result| libgen_search.results.create!(**result.to_h) }
      libgen_search.update!(result_count: libgen_search.results.count)
      broadcast(libgen_search)
    end

    finish(libgen_search)
  rescue StandardError => error
    fail_search(libgen_search, error)
  end

  private

  def start(libgen_search)
    started = false

    libgen_search.with_lock do
      if libgen_search.pending?
        libgen_search.update!(status: :running, started_at: Time.current)
        started = true
      end
    end

    broadcast(libgen_search) if started
    started
  end

  def finish(libgen_search)
    libgen_search.update!(status: :completed, finished_at: Time.current)
    broadcast(libgen_search)
  end

  def fail_search(libgen_search, error)
    Rails.logger.error("Libgen search #{libgen_search.id} failed: #{error.full_message}")
    libgen_search.reload
    libgen_search.update!(status: :failed, finished_at: Time.current, error: error.message)
    broadcast(libgen_search)
  rescue StandardError => reporting_error
    Rails.logger.error("Could not record libgen search failure: #{reporting_error.full_message}")
  end

  def broadcast(libgen_search)
    libgen_search.broadcast_replace_to(
      libgen_search,
      target: ActionView::RecordIdentifier.dom_id(libgen_search),
      partial: "libgen_searches/search",
      locals: { libgen_search: }
    )
  end
end
