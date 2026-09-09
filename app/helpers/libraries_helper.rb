module LibrariesHelper
  def series_label(book)
    [ book.series.presence, ("##{book.series_number}" if book.series_number) ].compact.join(" ")
  end

  # The download link is labelled with the file's own format.
  def download_label(book)
    book.file.filename.extension.presence&.downcase || "download"
  end
end
