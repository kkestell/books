require "stringio"

{
  "kyle" => "Kyle",
  "liz" => "Liz"
}.each do |username, name|
  user = User.find_or_create_by!(username: username)
  library = Library.find_or_initialize_by(user: user)
  library.update!(name: name, slug: username)
end

if Rails.env.development?
  library = Library.find_by!(slug: "kyle")
  demo_books = [
    { author: "Nia Calder", title: "The Cartographer's Lantern", series: "Maps of the Quiet Sea", series_number: 1, published: "2024-07-24", book_type: "Novel", format: "EPUB" },
    { author: "Nia Calder", title: "A Compass for Vanishing Islands", series: "Maps of the Quiet Sea", series_number: 2, published: "2025-02-23", book_type: "Novel", format: "EPUB" },
    { author: "Oren Vale", title: "The Extremely Long and Inconvenient Title of a Very Short Journey", published: "2022-10-15", book_type: "Novella", format: "EPUB" },
    { author: "Priya Sen", title: "Signal at Aphelion", series: "The Far Relay", series_number: 1, published: "2019-10-15", book_type: "Novel", format: "EPUB" },
    { author: "Priya Sen", title: "Where the Relay Ends", series: "The Far Relay", series_number: 2, published: "2021-11-16", book_type: "Novel", format: "AZW3" },
    { author: "Rafael North", title: "Lake of Darkness", published: "2024-03-30", format: "EPUB" },
    { author: "Rafael North", title: "Saturation Point", published: "2023-04-26", book_type: "Novel", format: "EPUB" },
    { author: "S. L. Ibarra", title: "A Memory Built from Snow", series: "Archive Weather", series_number: 3, published: "2018-05-03", book_type: "Novel", format: "EPUB" },
    { author: "Tamsin Rowe", title: "Small Gods of the Service Corridor", published: "2020-08-11", book_type: "Novel", format: "EPUB" },
    { author: "Tamsin Rowe", title: "The Final Architecture of Ordinary Things", series: "Maintenance Cycle", series_number: 12, published: "2026-01-09", book_type: "Novel", format: "EPUB" },
    { author: "Wei Mercer", title: "Elder Race", published: "2021-11-16", book_type: "Novella", format: "AZW3" },
    { author: "Yara Okafor", title: "Children of the Long Afternoon", series: "A Season in Glass", series_number: 1, published: "2015-10-15", book_type: "Novel", format: "EPUB" }
  ]

  demo_books.each do |attributes|
    book = library.books.find_or_initialize_by(author: attributes[:author], title: attributes[:title])
    book.assign_attributes(attributes.except(:author, :title))
    book.save!

    next if book.file.attached?

    extension = book.format.downcase
    content_type = extension == "epub" ? "application/epub+zip" : "application/vnd.amazon.ebook"
    book.file.attach(
      io: StringIO.new("Dummy #{book.format} file for local development: #{book.title}\n"),
      filename: "#{book.author} - #{book.title}.#{extension}",
      content_type: content_type
    )
  end

  puts "Ensured 12 downloadable demo books exist in Kyle's library."
else
  puts "Ensured the Kyle and Liz libraries exist."
end
