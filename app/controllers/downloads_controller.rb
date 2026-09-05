class DownloadsController < ApplicationController
  def index
    @downloads = current_user.library.book_downloads.order(created_at: :desc)
      .includes(:libgen_search_result)
  end
end
