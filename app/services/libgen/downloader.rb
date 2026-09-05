require "cgi"
require "net/http"
require "tempfile"
require "uri"

module Libgen
  # Downloads a Libgen search result. Follows the site's own flow: fetch the
  # result's ads.php download page, extract the keyed get.php link it embeds,
  # then stream the file from the host that link redirects to. The site
  # rate-limits with 503s, intermittently answers 500s, and its storage
  # servers cut transfers short, so every step is retried with a backoff and
  # a cut download resumes where it stopped.
  class Downloader
    class Error < StandardError; end
    class TimeoutError < Error; end
    class ConnectionFailed < Error; end

    # file is an open, rewound Tempfile the caller must close.
    Result = Struct.new(:file, :filename, :content_type, keyword_init: true)

    ATTEMPT_DELAYS = [ 15, 30, 60 ].freeze
    BASE_URL = Libgen::Scraper::BASE_URL

    class HttpTransport
      TIMEOUT_SECONDS = 30
      MAX_REDIRECTS = 5
      USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36" \
        " (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
      # The download endpoint refuses requests that do not carry this cookie.
      # Any value works.
      LIBRARY_COOKIE = "lid=1"

      # Returns the full response, following redirects. Non-2xx responses are
      # returned, not raised, so callers can treat them as retryable.
      def get(url, referer: nil)
        redirects = 0
        loop do
          response = request(url, referer:, offset: 0) do |http, request|
            http.request(request)
          end

          location = redirect_location(response)
          return response unless location
          raise Error, "Too many redirects." if (redirects += 1) > MAX_REDIRECTS

          url = URI.join(url, location).to_s
        end
      end

      # Streams the response body into io, following redirects. When offset is
      # positive the request carries a Range header and only a 206 response's
      # body is read; a 200 means the server ignored the range and the caller
      # must restart. The response is returned without its body for any other
      # non-success.
      def stream(url, io:, offset: 0, referer: nil)
        redirects = 0
        loop do
          response = request(url, referer:, offset:) do |http, request|
            http.request(request) do |res|
              res.read_body { |chunk| io.write(chunk) } if read_body?(res, offset)
              res
            end
          end

          location = redirect_location(response)
          return response unless location
          raise Error, "Too many redirects." if (redirects += 1) > MAX_REDIRECTS

          url = URI.join(url, location).to_s
        end
      end

      private

      def read_body?(response, offset)
        return false unless response.is_a?(Net::HTTPSuccess)

        offset.zero? || response.code == "206"
      end

      def redirect_location(response)
        response["location"] if response.is_a?(Net::HTTPRedirection)
      end

      def request(url, referer:, offset:)
        uri = URI(url)
        headers = { "User-Agent" => USER_AGENT, "Cookie" => LIBRARY_COOKIE }
        headers["Referer"] = referer if referer
        headers["Range"] = "bytes=#{offset}-" if offset.positive?

        Net::HTTP.start(uri.host, uri.port, use_ssl: uri.scheme == "https",
          open_timeout: TIMEOUT_SECONDS, read_timeout: TIMEOUT_SECONDS) do |http|
          yield http, Net::HTTP::Get.new(uri, headers)
        end
      rescue Net::OpenTimeout, Net::ReadTimeout, Errno::ETIMEDOUT
        raise TimeoutError, "Download timed out - the server took too long to respond"
      rescue SocketError, Errno::ECONNREFUSED, Errno::EHOSTUNREACH, Errno::ENETUNREACH,
        Errno::ECONNRESET, OpenSSL::SSL::SSLError, IOError
        raise ConnectionFailed, "Connection failed - unable to reach the server"
      end
    end

    def self.download(mirrors:, fallback_filename:, transport: HttpTransport.new,
        delays: ATTEMPT_DELAYS, sleep_seconds: ->(seconds) { sleep(seconds) })
      new(mirrors:, fallback_filename:, transport:, delays:, sleep_seconds:).download
    end

    def initialize(mirrors:, fallback_filename:, transport:, delays:, sleep_seconds:)
      @mirrors = Array(mirrors)
      @fallback_filename = fallback_filename
      @transport = transport
      @delays = delays
      @sleep_seconds = sleep_seconds
    end

    def download
      @md5 = result_md5 or raise Error, "That search result has no Libgen download link."

      file = Tempfile.new("libgen-download", binmode: true)
      begin
        with_retries { attempt(file) }
      rescue StandardError
        file.close!
        raise
      end

      file.rewind
      Result.new(file:, filename: @filename, content_type: @content_type)
    end

    private

    def download_page_url
      "#{BASE_URL}/ads.php?md5=#{@md5}"
    end

    # One attempt fetches a fresh download key and streams the file, asking
    # to resume from the bytes previous attempts already downloaded.
    def attempt(file)
      offset = file.size
      page = @transport.get(download_page_url, referer: BASE_URL)
      link = download_link(page.body)
      response = @transport.stream(link, io: file, offset:, referer: download_page_url)

      if offset.positive? && response.code == "200"
        # The server ignored the Range header and sent no body, so the only
        # way forward is a full restart.
        file.truncate(0)
        file.seek(0)
        raise Error, "The server ignored the resume request."
      end
      unless file_response?(response)
        # Any HTML the server sent in place of the file is garbage to discard.
        file.truncate(offset)
        file.seek(offset)
        raise Error, "The Libgen server did not return the requested file."
      end

      @filename = file_name(response)
      @content_type = response["content-type"]
      verify_complete!(response, file, offset)
    end

    def download_link(page)
      document = Nokogiri::HTML(page)
      link = document.at_css("a[href*='get.php'][href*='md5=']")
      raise Error, "The Libgen download page did not offer a download link." unless link

      href = link["href"]
      href.start_with?("http://", "https://") ? href : "#{BASE_URL}/#{href}"
    end

    # Serving an HTML page instead of the file is the site's way of refusing
    # a stale or unaccepted download key, so it is treated as retryable.
    def file_response?(response)
      response.is_a?(Net::HTTPSuccess) && !response["content-type"].to_s.start_with?("text/html")
    end

    def verify_complete!(response, file, offset)
      expected = offset + response["content-length"].to_i
      return if expected <= offset

      return if file.size >= expected

      raise Error, "The download was cut short (#{file.size} of #{expected} bytes received)."
    end

    def file_name(response)
      disposition = response["content-disposition"].to_s
      disposition.match(/filename\*=UTF-8''([^;]+)/i) do |match|
        return CGI.unescape(match[1])
      end
      disposition.match(/filename="?([^";]+)"?/i) do |match|
        return CGI.unescapeHTML(match[1])
      end

      @fallback_filename.presence || "libgen-#{@md5}"
    end

    def result_md5
      @mirrors.each do |mirror|
        uri = begin
          URI(mirror)
        rescue URI::Error
          next
        end
        next unless uri.host.to_s.end_with?("libgen.li")

        md5 = URI.decode_www_form(uri.query.to_s).to_h["md5"]
        return md5 if md5&.match?(/\A[0-9a-f]{32}\z/i)
      end

      nil
    end

    def with_retries
      tries = @delays.length + 1
      tries.times do |try|
        begin
          return yield
        rescue Error, TimeoutError, ConnectionFailed
          raise if try == tries - 1

          @sleep_seconds.call(@delays[try])
        end
      end
    end
  end
end
