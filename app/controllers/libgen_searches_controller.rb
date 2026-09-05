class LibgenSearchesController < ApplicationController
  before_action :set_library

  def new
  end

  def create
    author = params[:author].to_s.strip
    title = params[:title].to_s.strip
    format = Libgen::Scraper::SEARCH_FORMATS.include?(params[:format]) ? params[:format] : ""

    if author.blank? && title.blank?
      @error = "Enter an author or a title to search for."
      return render :new, status: :unprocessable_entity
    end

    libgen_search = @library.libgen_searches.create!(author:, title:, format:)
    LibgenSearchJob.perform_later(libgen_search)

    redirect_to libgen_search_path(libgen_search)
  end

  def show
    @libgen_search = @library.libgen_searches.find(params[:id])
  end

  private

  def set_library
    @library = current_user.library
  end
end
