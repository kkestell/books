class BookImportsController < ApplicationController
  before_action :set_library

  def new
  end

  def create
    upload = params[:file]

    unless upload.respond_to?(:tempfile)
      @error = "Choose an ebook file to import."
      return render :new, status: :unprocessable_entity
    end

    metadata = EbookMetadata.extract(io: upload.tempfile, filename: upload.original_filename)
    @book = @library.books.build({
      author: "Unknown Author",
      title: "Unknown Title",
      format: File.extname(upload.original_filename).delete_prefix(".").upcase.presence
    }.merge(metadata))
    @book.file.attach(upload)

    if @book.save
      redirect_to library_path(@library), notice: "#{@book.title} imported."
    else
      @error = @book.errors.full_messages.to_sentence
      render :new, status: :unprocessable_entity
    end
  rescue EbookMetadata::Error => error
    @error = error.message
    render :new, status: :unprocessable_entity
  end

  private

  def set_library
    @library = Library.find_by!(slug: params[:slug])
  end
end
