class BooksController < ApplicationController
  before_action :set_library
  before_action :set_book, only: [ :edit, :update, :download ]

  def edit
  end

  def update
    if @book.update(book_params)
      redirect_to library_path(@library), notice: "Book updated."
    else
      render :edit, status: :unprocessable_entity
    end
  end

  def download
    return head :not_found unless @book.file.attached?

    @book.file.open do |source|
      converted = EbookConversion.convert(io: source, filename: @book.file.filename.to_s)
      send_data converted.file.read, filename: converted.filename,
        type: converted.content_type, disposition: "attachment"
      converted.file.close!
    end
  rescue EbookConversion::Error => error
    Rails.logger.error("Book #{@book.id} could not be converted: #{error.message}")
    head :unprocessable_entity
  end

  private

  def set_library
    @library = Library.find_by!(slug: params[:library_slug])
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
