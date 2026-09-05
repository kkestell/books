class BookImportsController < ApplicationController
  before_action :set_library
  before_action :set_book_import, only: [ :show, :cancel ]

  def new
  end

  def create
    uploads = Array(params[:files]).compact_blank
    supported, ignored = uploads.partition { |upload| supported_upload?(upload) }
    purge_unattached_direct_uploads(ignored)

    if supported.empty?
      @error = uploads.empty? ? "Choose an ebook directory or one or more ebook files." : "No supported ebooks were selected."
      return render :new, status: :unprocessable_entity
    end

    @book_import = @library.book_imports.create!(
      total_files: supported.size,
      ignored_files: ignored.size
    )
    @book_import.files.attach(supported)
    BookImportJob.perform_later(@book_import)

    redirect_to book_import_path(@book_import)
  rescue ActiveSupport::MessageVerifier::InvalidSignature, ActiveRecord::RecordNotFound
    @error = "One or more uploads could not be found. Choose the directory again."
    render :new, status: :unprocessable_entity
  end

  def show
  end

  def cancel
    @book_import.request_cancellation!
    @book_import.broadcast_replace_to(
      @book_import,
      target: ActionView::RecordIdentifier.dom_id(@book_import),
      partial: "book_imports/book_import",
      locals: { book_import: @book_import }
    )

    redirect_to book_import_path(@book_import), notice: "Cancellation requested."
  end

  private

  def set_library
    @library = current_user.library
  end

  def set_book_import
    @book_import = @library.book_imports.find(params[:id])
  end

  def supported_upload?(upload)
    EbookMetadata.supported_filename?(upload_filename(upload))
  end

  def upload_filename(upload)
    return upload.original_filename if upload.respond_to?(:original_filename)

    ActiveStorage::Blob.find_signed!(upload).filename.to_s
  end

  def purge_unattached_direct_uploads(uploads)
    uploads.reject { |upload| upload.respond_to?(:original_filename) }.each do |signed_id|
      blob = ActiveStorage::Blob.find_signed!(signed_id)
      blob.purge unless blob.attachments.exists?
    end
  end
end
