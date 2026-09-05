class DownloadsController < ApplicationController
  def index
    @downloads = BookDownload.order(created_at: :desc).includes(:library, :libgen_search_result)
  end
end
