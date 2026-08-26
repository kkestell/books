class LibrariesController < ApplicationController
  def index
    @libraries = Library.order(:name)
  end

  def show
    @library = Library.find_by!(slug: params[:slug])
    @books = @library.books.order(:author, :title)
  end
end
