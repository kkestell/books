class BooksController < ApplicationController
  before_action :set_library
  before_action :set_book, only: [ :edit, :update ]

  def edit
  end

  def update
    if @book.update(book_params)
      redirect_to root_path, notice: "Book updated."
    else
      render :edit, status: :unprocessable_entity
    end
  end

  private

  def set_library
    @library = current_user.library
  end

  def set_book
    @book = @library.books.find(params[:id])
  end

  def book_params
    permitted = params.require(:book).permit(
      :author, :title, :series, :series_number, :published, :book_type, :description
    )

    # A series is only meaningful together with its position in it, matching
    # the desktop app's edit dialog.
    if permitted[:series].blank? || permitted[:series_number].blank?
      permitted[:series] = nil
      permitted[:series_number] = nil
    end

    permitted
  end
end
