require "test_helper"

class LibgenDownloaderTest < ActiveSupport::TestCase
  setup do
    @mirrors = [
      "https://libgen.li/ads.php?md5=a13be9e40a4a79151a5584cc3c4b0e0f",
      "https://en.annas-archive.gl/md5/a13be9e40a4a79151a5584cc3c4b0e0f?r=Ax2w6jC"
    ]
    @transport = FakeHttpTransport.new
    @delays = [ 15, 30, 60 ]
    @sleeps = []
  end

  test "fetches the download page, follows the keyed get.php link, and streams the file" do
    @transport.respond_with(
      page_response,
      redirect_response("https://cdn.example.org/get.php?md5=a13be9e40a4a79151a5584cc3c4b0e0f&key=KEY"),
      file_response("epub bytes", content_type: "application/epub+zip",
        disposition: 'attachment; filename="The Cartographer\'s Lantern.epub"')
    )

    result = download

    assert_equal [
      "https://libgen.li/ads.php?md5=a13be9e40a4a79151a5584cc3c4b0e0f",
      "https://libgen.li/get.php?md5=a13be9e40a4a79151a5584cc3c4b0e0f&key=50W75TKWYW5VZPNV",
      "https://cdn.example.org/get.php?md5=a13be9e40a4a79151a5584cc3c4b0e0f&key=KEY"
    ], @transport.requested_urls
    assert_equal "The Cartographer's Lantern.epub", result.filename
    assert_equal "application/epub+zip", result.content_type
    assert_equal "epub bytes", result.file.read
    assert_empty @sleeps
  end

  test "keeps the fallback filename when the response has no content disposition" do
    @transport.respond_with(
      page_response,
      file_response("epub bytes", content_type: "application/epub+zip")
    )

    result = download

    assert_equal "cartographer.epub", result.filename
  end

  test "retries 503 responses and recovers" do
    @transport.respond_with(
      page_response,
      file_response("", content_type: "text/html", code: "503"),
      page_response,
      file_response("epub bytes", content_type: "application/epub+zip")
    )

    result = download

    assert_equal "epub bytes", result.file.read
    assert_equal [ 15 ], @sleeps
  end

  test "gives up after the final attempt and reports the failure" do
    4.times { @transport.respond_with(page_response, file_response("", content_type: "text/html", code: "503")) }

    error = assert_raises(Libgen::Downloader::Error) { download }

    assert_equal "The Libgen server did not return the requested file.", error.message
    assert_equal [ 15, 30, 60 ], @sleeps
    assert_equal 8, @transport.requested_urls.size
  end

  test "retries when the download page offers no get.php link" do
    @transport.respond_with(
      response("200", "<html><body>overloaded</body></html>", "text/html"),
      page_response,
      file_response("epub bytes", content_type: "application/epub+zip")
    )

    assert_equal "epub bytes", download.file.read
    assert_equal [ 15 ], @sleeps
  end

  test "retries when the server answers an HTML page instead of the file" do
    @transport.respond_with(
      page_response,
      response("200", "<html>home page</html>", "text/html"),
      page_response,
      file_response("epub bytes", content_type: "application/epub+zip")
    )

    assert_equal "epub bytes", download.file.read
  end

  test "resumes a download that was cut short" do
    @transport.respond_with(
      page_response,
      file_response("epub bytes cut", content_type: "application/epub+zip", write_bytes: 8),
      page_response,
      file_response("es cut", content_type: "application/epub+zip", code: "206")
    )

    result = download

    assert_equal "epub bytes cut", result.file.read
    assert_equal [ 15 ], @sleeps
    assert_equal [ "bytes=8-" ], @transport.ranges_requested
  end

  test "restarts from scratch when the server ignores the resume range" do
    @transport.respond_with(
      page_response,
      file_response("epub bytes cut", content_type: "application/epub+zip", write_bytes: 8),
      page_response,
      file_response("epub bytes cut", content_type: "application/epub+zip"),
      page_response,
      file_response("epub bytes cut", content_type: "application/epub+zip")
    )

    result = download

    assert_equal "epub bytes cut", result.file.read
    assert_equal [ 15, 30 ], @sleeps
  end

  test "raises when no mirror points at libgen.li" do
    error = assert_raises(Libgen::Downloader::Error) do
      Libgen::Downloader.download(mirrors: [ "https://mirror.example.org/direct" ],
        fallback_filename: "book.epub", transport: @transport, delays: @delays,
        sleep_seconds: sleep_recorder)
    end

    assert_equal "That search result has no Libgen download link.", error.message
  end

  private

  def download
    Libgen::Downloader.download(mirrors: @mirrors, fallback_filename: "cartographer.epub",
      transport: @transport, delays: @delays, sleep_seconds: sleep_recorder)
  end

  def sleep_recorder
    @sleep_recorder ||= ->(seconds) { @sleeps << seconds }
  end

  def page_response
    response("200", file_fixture("libgen_download_page.html").read, "text/html")
  end

  def file_response(body, content_type:, code: "200", disposition: nil, write_bytes: nil)
    response(code, body, content_type, disposition, write_bytes:)
  end

  def redirect_response(location)
    response("307", "", "text/html", nil, location:)
  end

  def response(code, body = "", content_type = nil, disposition = nil, write_bytes: nil, location: nil)
    headers = {
      "content-type" => content_type,
      "content-disposition" => disposition,
      "location" => location,
      "content-length" => body.length.to_s
    }.compact
    response_class = code.start_with?("2") ? Net::HTTPSuccess : Net::HTTPRedirection
    response = response_class.new("1.1", code, "test")
    response.initialize_http_header(headers.transform_values(&:to_s))
    response.instance_variable_set(:@read, true)
    response.body = body
    write_bytes ? [ response, write_bytes ] : response
  end

  class FakeHttpTransport
    attr_reader :requested_urls, :ranges_requested

    def initialize
      @entries = []
      @requested_urls = []
      @ranges_requested = []
    end

    # An entry is a response, or a [response, write_bytes] pair that makes
    # stream deliver only part of the body, as the real servers do when they
    # cut a transfer short.
    def respond_with(*entries)
      @entries.concat(entries)
    end

    def get(url, referer: nil)
      loop do
        @requested_urls << url
        response, = shift
        location = response["location"] if response.is_a?(Net::HTTPRedirection)
        return response unless location

        url = URI.join(url, location).to_s
      end
    end

    def stream(url, io:, offset:, referer: nil)
      loop do
        @requested_urls << url
        @ranges_requested << "bytes=#{offset}-" if offset.positive?

        response, write_bytes = shift
        if response.is_a?(Net::HTTPSuccess) && (offset.zero? || response.code == "206")
          io.write(response.body.byteslice(0, write_bytes || response.body.length))
        end

        location = response["location"] if response.is_a?(Net::HTTPRedirection)
        return response unless location

        url = URI.join(url, location).to_s
      end
    end

    private

    def shift
      raise "No more responses" if @entries.empty?

      entry = @entries.shift
      entry.is_a?(Array) ? entry : [ entry, nil ]
    end
  end
end
