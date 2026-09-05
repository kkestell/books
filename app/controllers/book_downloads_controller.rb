class BookDownloadsController < ApplicationController
  def download
    libgen_search = current_user.library.libgen_searches.find(params[:id])
    libgen_search_result = libgen_search.results.find(params[:result_id])

    unless libgen_search_result.book_downloads.where(status: %w[pending running]).exists?
      book_download = libgen_search_result.book_downloads.create!(library: libgen_search.library)
      BookDownloadJob.perform_later(book_download)
    end

    redirect_to libgen_search_path(libgen_search)
  end
end
