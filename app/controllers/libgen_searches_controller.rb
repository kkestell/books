class LibgenSearchesController < ApplicationController
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

    libgen_search = LibgenSearch.create!(author:, title:, format:)
    LibgenSearchJob.perform_later(libgen_search)

    redirect_to libgen_search_path(libgen_search)
  end

  def show
    @libgen_search = LibgenSearch.find(params[:id])
  end
end
