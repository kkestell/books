require "test_helper"

class LibrariesControllerTest < ActionDispatch::IntegrationTest
  setup do
    log_in_as(users(:kyle))
  end

  test "the root shows the current user's library" do
    books(:dune).file.attach(
      io: file_fixture("dune.epub").open,
      filename: "dune.epub",
      content_type: "application/epub+zip"
    )

    get root_path
    assert_response :success
    assert_select "h1", text: "Kyle"
    assert_select "main table"
    assert_select "th", text: "File", count: 0
    assert_select "td a", text: "Dune", href: edit_book_path(books(:dune))
    assert_select "td a", text: "azw3", href: download_book_path(books(:dune))
    assert_select "td", text: "Dune"
  end

  test "the root links a pdf book to its original file" do
    pdf = libraries(:kyle).books.create!(author: "Frank Herbert", title: "Dune Script", format: "PDF")
    pdf.file.attach(io: file_fixture("dune.epub").open, filename: "dune.pdf",
      content_type: "application/pdf")

    get root_path

    assert_select "td a", text: "pdf",
      href: rails_blob_path(pdf.file, disposition: "attachment")
  end

  test "new book import displays directory and file pickers" do
    get new_book_import_path

    assert_response :success
    assert_select "h1", text: "Import ebooks into Kyle"
    assert_select "input#ebook-directory[type=file][multiple][webkitdirectory]"
    assert_select "input#ebook-directory[name='files[]'][data-direct-upload-url]"
    assert_select "input#ebook-files[type=file][multiple]"
    assert_select "input[type=submit][value='Start import'][disabled]"
  end

  test "book import stores uploads and enqueues background processing" do
    upload = fixture_file_upload("dune.epub", "application/epub+zip")

    assert_difference([ "BookImport.count", "ActiveStorage::Attachment.count" ], 1) do
      assert_no_difference "Book.count" do
        assert_enqueued_with(job: BookImportJob) do
          post book_imports_path, params: { files: [ upload ] }
        end
      end
    end

    book_import = BookImport.order(:created_at).last
    assert_redirected_to book_import_path(book_import)
    assert_equal libraries(:kyle), book_import.library
    assert_equal 1, book_import.total_files
    assert_equal "dune.epub", book_import.files.first.filename.to_s
  end

  test "book import requires files" do
    assert_no_difference "BookImport.count" do
      post book_imports_path
    end

    assert_response :unprocessable_entity
    assert_select "[role=alert]", text: "Choose an ebook directory or one or more ebook files."
  end

  test "book import accepts direct-upload blob ids" do
    blob = file_fixture("dune.epub").open do |file|
      ActiveStorage::Blob.create_and_upload!(
        io: file,
        filename: "dune.epub",
        content_type: "application/epub+zip"
      )
    end

    assert_difference "BookImport.count", 1 do
      post book_imports_path, params: { files: [ blob.signed_id ] }
    end

    assert_redirected_to book_import_path(BookImport.order(:created_at).last)
  end

  test "book import rejects selections without supported ebooks" do
    upload = Rack::Test::UploadedFile.new(
      file_fixture("dune.epub"),
      "image/jpeg",
      false,
      original_filename: "cover.jpg"
    )

    assert_no_difference "BookImport.count" do
      post book_imports_path, params: { files: [ upload ] }
    end

    assert_response :unprocessable_entity
    assert_select "[role=alert]", text: "No supported ebooks were selected."
  end

  test "book import purges unsupported direct uploads" do
    blob = file_fixture("dune.epub").open do |file|
      ActiveStorage::Blob.create_and_upload!(io: file, filename: "cover.jpg", content_type: "image/jpeg")
    end

    post book_imports_path, params: { files: [ blob.signed_id ] }

    assert_response :unprocessable_entity
    assert_not ActiveStorage::Blob.exists?(blob.id)
  end

  test "book import status shows progress and can be cancelled" do
    book_import = libraries(:kyle).book_imports.create!(total_files: 2, processed_files: 1, imported_files: 1)

    get book_import_path(book_import)

    assert_response :success
    assert_select "progress[max='2'][value='1']"
    assert_select "form[action=?]", cancel_book_import_path(book_import)

    patch cancel_book_import_path(book_import)

    assert_redirected_to book_import_path(book_import)
    assert book_import.reload.cancelled?
    assert book_import.cancel_requested?
  end
end
