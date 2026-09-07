class BooksController < ApplicationController
  before_action :set_library
  before_action :set_book, only: [ :edit, :update, :convert, :download ]

  def edit
  end

  def update
    if @book.update(book_params)
      redirect_to root_path, notice: "Book updated."
    else
      render :edit, status: :unprocessable_entity
    end
  end

  # Starts the azw3 conversion in the background; the converted file is
  # delivered by #download once the job reports it ready.
  def convert
    return head :not_found unless @book.file.attached?

    unless @book.azw3_pending? || @book.azw3_running?
      @book.update!(azw3_status: :pending, azw3_error: nil)
      BookConversionJob.perform_later(@book)
    end

    redirect_to root_path
  end

  def download
    return head :not_found unless @book.file.attached?

    unless @book.azw3_ready? && @book.azw3_file.attached?
      redirect_to root_path, alert: "That azw3 file is not ready. Convert the book first."
      return
    end

    if @book.azw3_source_blob_id != @book.file.blob.id
      @book.reset_azw3
      redirect_to root_path, alert: "The book's file changed since that azw3 was made. Convert it again."
      return
    end

    file = @book.azw3_file
    data = file.download
    filename = file.filename.to_s
    content_type = file.content_type
    @book.reset_azw3

    send_data data, filename: filename, type: content_type, disposition: "attachment"
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
