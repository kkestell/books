require "date"
require "nokogiri"
require "open3"
require "tempfile"
require "tmpdir"
require "zip"

class EbookMetadata
  class Error < StandardError; end

  SUPPORTED_EXTENSIONS = %w[
    .azw .azw3 .azw4 .cb7 .cbc .cbr .cbz .chm .djv .djvu .docx .epub .fb2
    .fbz .htm .html .htmlz .kepub .lit .lrf .mobi .odt .pdf .pdb .pml .prc
    .rb .rtf .snb .tcr .txt .txtz
  ].freeze

  def self.supported_filename?(filename)
    SUPPORTED_EXTENSIONS.include?(File.extname(filename.to_s).downcase)
  end

  def self.accept_attribute
    SUPPORTED_EXTENSIONS.join(",")
  end

  def self.extract(io:, filename:, command: ENV.fetch("EBOOK_META_PATH", "ebook-meta"))
    new(io:, filename:, command:).extract
  end

  def initialize(io:, filename:, command:)
    @io = io
    @filename = filename
    @command = command
  end

  def extract
    Tempfile.create([ "ebook", extension ], binmode: true) do |ebook|
      @io.rewind
      IO.copy_stream(@io, ebook)
      ebook.flush

      Dir.mktmpdir("ebook-metadata") do |directory|
        opf_path = File.join(directory, "metadata.opf")
        stdout, stderr, status = Open3.capture3(@command, ebook.path, "--to-opf", opf_path)

        unless status.success? && File.file?(opf_path)
          detail = [ stderr, stdout ].map { |output| output.to_s.strip }.find(&:present?)
          raise Error, [ "Could not extract metadata from that ebook.", detail ].compact.join(" ")
        end

        metadata = parse(File.read(opf_path))
        epub_metadata(ebook.path).merge(metadata)
      end
    end
  rescue Errno::ENOENT
    raise Error, "ebook-meta is not available."
  rescue Nokogiri::XML::SyntaxError
    raise Error, "ebook-meta returned invalid metadata."
  ensure
    @io.rewind if @io.respond_to?(:rewind)
  end

  private

  def extension
    suffix = File.extname(@filename.to_s)
    suffix.match?(/\A\.[a-z0-9]{1,10}\z/i) ? suffix : ""
  end

  def parse(xml)
    document = Nokogiri::XML(xml) { |config| config.strict.nonet }
    @metadata = document.at_xpath("//*[local-name()='metadata']")
    raise Error, "ebook-meta returned no metadata." unless @metadata

    series, series_number = series_metadata

    {
      author: authors,
      title: text_value("title"),
      series:,
      series_number:,
      published: published_date,
      book_type: text_value("type"),
      description: text_value("description"),
      google_books_id:
    }.compact
  end

  def epub_metadata(path)
    return {} unless extension.casecmp?(".epub")

    Zip::File.open(path) do |epub|
      opf = epub.find { |entry| entry.name.downcase.end_with?(".opf") }
      return {} unless opf && opf.size <= 5.megabytes

      parse(opf.get_input_stream.read)
    end
  rescue Error, Nokogiri::XML::SyntaxError, Zip::Error
    {}
  end

  def authors
    values = @metadata.xpath("./*[local-name()='creator']").filter_map { |node| clean(node.text) }
    values.join(" & ").presence
  end

  def published_date
    value = text_value("date")
    date = value&.match(/\A\d{4}-\d{2}-\d{2}/)&.to_s
    Date.iso8601(date) if date
  rescue Date::Error
    nil
  end

  def series_metadata
    name = calibre_meta("calibre:series")
    number = integer(calibre_meta("calibre:series_index"))
    return [ name, number ] if name

    collection = @metadata.xpath("./*[local-name()='meta']").find do |node|
      node["property"] == "belongs-to-collection" && collection_type(node) == "series"
    end
    return [ nil, nil ] unless collection

    position = refinement(collection, "group-position")
    [ clean(collection.text), integer(clean(position&.text)) ]
  end

  def collection_type(collection)
    type = refinement(collection, "collection-type")
    clean(type&.text) || "series"
  end

  def refinement(collection, property)
    id = collection["id"]
    return unless id

    @metadata.xpath("./*[local-name()='meta']").find do |node|
      node["refines"] == "##{id}" && node["property"] == property
    end
  end

  def calibre_meta(name)
    node = @metadata.xpath("./*[local-name()='meta']").find { |meta| meta["name"] == name }
    clean(node&.[]("content") || node&.text)
  end

  def google_books_id
    @metadata.xpath("./*[local-name()='identifier']").each do |identifier|
      value = clean(identifier.text)
      scheme = identifier.attribute_nodes.find { |attribute| attribute.name == "scheme" }&.value
      return value if scheme&.casecmp?("google")
      return value.sub(/\Agoogle:/i, "") if value&.match?(/\Agoogle:/i)
    end

    nil
  end

  def text_value(name)
    clean(@metadata.at_xpath("./*[local-name()='#{name}']")&.text)
  end

  def clean(value)
    value.to_s.strip.presence
  end

  def integer(value)
    number = Float(value, exception: false)
    number.to_i if number&.finite? && number == number.to_i
  end
end
