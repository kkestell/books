module LibrariesHelper
  def series_label(book)
    [ book.series.presence, ("##{book.series_number}" if book.series_number) ].compact.join(" ")
  end
end
