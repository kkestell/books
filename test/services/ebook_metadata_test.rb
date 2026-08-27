require "test_helper"

class EbookMetadataTest < ActiveSupport::TestCase
  test "extracts book and Calibre series metadata from ebook-meta OPF output" do
    epub_opf = <<~XML
      <?xml version="1.0" encoding="UTF-8"?>
      <package xmlns="http://www.idpf.org/2007/opf" xmlns:dc="http://purl.org/dc/elements/1.1/">
        <metadata>
          <dc:title>A Wizard of Earthsea</dc:title>
          <dc:creator>Ursula K. Le Guin</dc:creator>
          <dc:type>Novel</dc:type>
        </metadata>
      </package>
    XML
    io = Zip::OutputStream.write_buffer do |epub|
      epub.put_next_entry("OEBPS/content.opf")
      epub.write(epub_opf)
    end
    io.rewind
    status = Object.new.tap { |object| object.define_singleton_method(:success?) { true } }
    opf = <<~XML
      <?xml version="1.0" encoding="UTF-8"?>
      <package xmlns="http://www.idpf.org/2007/opf" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">
        <metadata>
          <dc:title>A Wizard of Earthsea</dc:title>
          <dc:creator>Ursula K. Le Guin</dc:creator>
          <dc:date>1968-01-01T00:00:00+00:00</dc:date>
          <dc:description>Ged begins his training as a wizard.</dc:description>
          <dc:identifier opf:scheme="GOOGLE">google-id</dc:identifier>
          <meta name="calibre:series" content="Earthsea Cycle" />
          <meta name="calibre:series_index" content="1.0" />
        </metadata>
      </package>
    XML
    command = lambda do |*arguments|
      assert_equal "ebook-meta", arguments.first
      assert_equal ".epub", File.extname(arguments.second)
      assert_equal "--to-opf", arguments.third
      File.write(arguments.fourth, opf)
      [ "", "", status ]
    end

    metadata = Open3.stub(:capture3, command) do
      EbookMetadata.extract(io:, filename: "dune.epub")
    end

    assert_equal "Ursula K. Le Guin", metadata[:author]
    assert_equal "A Wizard of Earthsea", metadata[:title]
    assert_equal "Earthsea Cycle", metadata[:series]
    assert_equal 1, metadata[:series_number]
    assert_equal Date.new(1968, 1, 1), metadata[:published]
    assert_equal "Novel", metadata[:book_type]
    assert_equal "Ged begins his training as a wizard.", metadata[:description]
    assert_equal "google-id", metadata[:google_books_id]
  end

  test "raises a useful error when ebook-meta fails" do
    io = StringIO.new("not a real ebook")
    status = Object.new.tap { |object| object.define_singleton_method(:success?) { false } }

    error = Open3.stub(:capture3, [ "", "unsupported format", status ]) do
      assert_raises(EbookMetadata::Error) do
        EbookMetadata.extract(io:, filename: "notes.txt")
      end
    end

    assert_match "Could not extract metadata", error.message
    assert_match "unsupported format", error.message
  end
end
