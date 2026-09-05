require "cgi"
require "net/http"
require "uri"

module Libgen
  # Port of the desktop Books app's libgen.li search. Pages through the
  # result table and yields each page's parsed results so callers can
  # persist and broadcast them as they arrive.
  class Scraper
    class Error < StandardError; end
    class TimeoutError < Error; end
    class ConnectionFailed < Error; end

    Result = Struct.new(:author, :series, :title, :format, :size, :score, :mirrors, keyword_init: true)

    SEARCH_FORMATS = %w[EPUB MOBI AZW AZW3 FB2 PDF RTF TXT].freeze
    BASE_URL = "https://libgen.li"
    MAX_PAGES = 10

    class HttpTransport
      TIMEOUT_SECONDS = 30

      def get(url)
        uri = URI(url)
        Net::HTTP.start(uri.host, uri.port, use_ssl: uri.scheme == "https",
          open_timeout: TIMEOUT_SECONDS, read_timeout: TIMEOUT_SECONDS) do |http|
          response = http.request(Net::HTTP::Get.new(uri))
          raise Error, "HTTP Error #{response.code}" unless response.is_a?(Net::HTTPSuccess)

          response.body
        end
      rescue Net::OpenTimeout, Net::ReadTimeout, Errno::ETIMEDOUT
        raise TimeoutError, "Search timed out - the server took too long to respond"
      rescue SocketError, Errno::ECONNREFUSED, Errno::EHOSTUNREACH, Errno::ENETUNREACH,
        Errno::ECONNRESET, OpenSSL::SSL::SSLError, IOError
        raise ConnectionFailed, "Connection failed - unable to reach the server"
      end
    end

    def self.each_page(author:, title:, format: "", transport: HttpTransport.new, &block)
      new(author:, title:, format:, transport:).each_page(&block)
    end

    def initialize(author:, title:, format:, transport: HttpTransport.new)
      @author = author.to_s
      @title = title.to_s
      @format = format.to_s.upcase
      @transport = transport
    end

    def each_page
      page = 1
      while page < MAX_PAGES
        document = Nokogiri::HTML(@transport.get(search_url(page)))
        table = document.at_css("table#tablelibgen tbody")
        break unless table

        results = []
        table.css("tr").each do |row|
          result = parse_row(row)
          results << result if result
        end
        yield results
        page += 1
      end
    rescue StandardError => error
      raise Error, error.message
    end

    def self.fix_author(author)
      parts = author.split(",")
      return author if parts.length < 2

      "#{parts[1].strip} #{parts[0].strip}"
    end

    private

    def search_url(page)
      uri = URI("#{BASE_URL}/index.php")
      uri.query = URI.encode_www_form(req: query, res: 100, page: page)
      uri.to_s
    end

    def query
      [ @author, @title ].reject(&:empty?).join(" ")
    end

    def parse_row(row)
      columns = row.css("td")
      title_link = columns[0]&.at_css("a[data-toggle='tooltip']")
      return nil unless title_link
      title_attribute = title_link["title"]
      return nil unless title_attribute

      fragments = CGI.unescapeHTML(title_attribute).split("<br>")
      title = fragments[1] || fragments[0]

      author_names = columns[1]&.text.to_s.strip.split(";")
        .map { |name| self.class.fix_author(name) }.join(", ")
      author_names = "#{author_names[0, 40]}..." if author_names.length > 40

      series_node = columns[0]&.at_css("b")
      series = series_node ? series_node.text.strip : ""

      language = columns[4]&.text.to_s.strip
      return nil unless language.casecmp("english").zero?

      file_info = columns[6]&.at_css("nobr a")&.text&.strip
      size = file_info ? file_info.upcase : "N/A"

      extension = columns[7]&.text.to_s.strip.upcase
      return nil if @format.present? && extension != @format

      Result.new(
        author: author_names,
        series:,
        title:,
        format: extension,
        size:,
        score: score(author_names, title),
        mirrors: mirrors(columns[8])
      )
    end

    def score(author_names, title)
      if @author.present? && @title.present?
        (Fuzzy.token_sort_ratio(@author, author_names) + Fuzzy.token_sort_ratio(@title, title)) / 2
      elsif @author.present?
        Fuzzy.token_sort_ratio(@author, author_names)
      else
        Fuzzy.token_sort_ratio(@title, title)
      end
    end

    def mirrors(cell)
      links = []
      cell&.css("a[data-toggle='tooltip']")&.each do |link|
        href = link["href"]
        next unless href

        links << if href.start_with?("http://", "https://")
          href
        else
          "#{BASE_URL}#{href}"
        end
      end
      links
    end
  end
end
