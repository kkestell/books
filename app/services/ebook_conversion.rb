require "open3"
require "tempfile"

# Converts a book to Amazon's azw3 format for a Kindle Paperwhite using
# Calibre's ebook-convert command.
class EbookConversion
  class Error < StandardError; end

  OUTPUT_PROFILE = "kindle_pw3"
  CONTENT_TYPE = "application/x-mobi8-ebook"

  # file is an open, rewound Tempfile the caller must close.
  Result = Struct.new(:file, :filename, :content_type, keyword_init: true)

  def self.convert(io:, filename:, command: ENV.fetch("EBOOK_CONVERT_PATH", "ebook-convert"))
    new(io:, filename:, command:).convert
  end

  def initialize(io:, filename:, command:)
    @io = io
    @filename = filename
    @command = command
  end

  def convert
    Tempfile.create([ "ebook", extension ], binmode: true) do |source|
      @io.rewind
      IO.copy_stream(@io, source)
      source.flush

      Tempfile.create([ "ebook", ".azw3" ], binmode: true) do |target|
        stdout, stderr, status = Open3.capture3(@command, source.path, target.path,
          "--output-profile", OUTPUT_PROFILE)

        unless status.success? && File.file?(target.path) && target.size.positive?
          detail = [ stderr, stdout ].map { |output| output.to_s.strip }.find(&:present?)
          raise Error, [ "Could not convert that ebook to azw3.", detail ].compact.join(" ")
        end

        converted = Tempfile.new("ebook-download", binmode: true)
        IO.copy_stream(target, converted)
        converted.rewind
        Result.new(file: converted, filename: converted_filename, content_type: CONTENT_TYPE)
      end
    end
  rescue Errno::ENOENT
    raise Error, "ebook-convert is not available."
  ensure
    @io.rewind if @io.respond_to?(:rewind)
  end

  private

  def extension
    suffix = File.extname(@filename.to_s)
    suffix.match?(/\A\.[a-z0-9]{1,10}\z/i) ? suffix : ""
  end

  def converted_filename
    "#{File.basename(@filename.to_s, ".*")}.azw3"
  end
end
