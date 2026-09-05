class BookDownloadsController < ApplicationController
  def download
    @library = Library.find_by!(slug: params[:library_slug])
    libgen_search = @library.libgen_searches.find(params[:id])
    libgen_search_result = libgen_search.results.find(params[:result_id])

    unless libgen_search_result.book_downloads.where(status: %w[pending running]).exists?
      book_download = libgen_search_result.book_downloads.create!(library: @library)
      BookDownloadJob.perform_later(book_download)
    end

    redirect_to library_libgen_search_path(@library, libgen_search)
  end
end
