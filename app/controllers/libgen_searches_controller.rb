class LibgenSearchesController < ApplicationController
  def show
    @author = params[:author].to_s.strip
    @title = params[:title].to_s.strip
    @format = LibgenSearch::SEARCH_FORMATS.include?(params[:format]) ? params[:format] : ""
    @results = nil
    @error = nil
    return unless searched?

    if @author.empty? && @title.empty?
      @error = "Enter an author or a title to search for."
      return
    end

    @results = LibgenSearch.call(author: @author, title: @title, format: @format)
      .sort_by { |result| -result.score }
  rescue LibgenSearch::Error => error
    @error = error.message
    @results = []
  end

  private

  def searched?
    params.key?(:author) || params.key?(:title)
  end
end
