class LibrariesController < ApplicationController
  def show
    @library = current_user.library
    @books = @library.books.order(:author, :title)
  end
end
