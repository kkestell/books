# Development seed data: two libraries with a handful of books each.
# Each book gets a small placeholder EPUB attached via Active Storage.

Book.destroy_all
Library.destroy_all

def add_book(library, author:, title:, series: nil, series_number: nil, published: nil, book_type: "Novel", description: nil)
  book = library.books.create!(
    author: author,
    title: title,
    series: series,
    series_number: series_number,
    published: published,
    book_type: book_type,
    format: "EPUB",
    description: description
  )
  book.file.attach(
    io: StringIO.new("Placeholder for #{author} - #{title}"),
    filename: "#{author} - #{title}.epub",
    content_type: "application/epub+zip"
  )
  book
end

kyle = Library.create!(name: "Kyle", slug: "kyle")
liz = Library.create!(name: "Liz", slug: "liz")

add_book(kyle, author: "Frank Herbert", title: "Dune", series: "Dune", series_number: 1,
  published: Date.new(1965, 8, 1), description: "Paul Atreides and the desert planet Arrakis.")
add_book(kyle, author: "Frank Herbert", title: "Dune Messiah", series: "Dune", series_number: 2,
  published: Date.new(1969, 10, 15))
add_book(kyle, author: "Neal Stephenson", title: "Snow Crash",
  published: Date.new(1992, 6, 1), description: "Hiro Protagonist delivers pizza for the Mafia.")
add_book(kyle, author: "Ursula K. Le Guin", title: "The Dispossessed", series: "Hainish Cycle", series_number: 6,
  published: Date.new(1974, 5, 1))
add_book(kyle, author: "William Gibson", title: "Neuromancer", series: "Sprawl", series_number: 1,
  published: Date.new(1984, 7, 1))

add_book(liz, author: "Jane Austen", title: "Pride and Prejudice",
  published: Date.new(1813, 1, 28), description: "It is a truth universally acknowledged...")
add_book(liz, author: "Donna Tartt", title: "The Secret History",
  published: Date.new(1992, 9, 1))
add_book(liz, author: "Madeline Miller", title: "Circe",
  published: Date.new(2018, 4, 10))
add_book(liz, author: "Emily St. John Mandel", title: "Station Eleven",
  published: Date.new(2014, 9, 9), description: "A traveling symphony after the collapse.")

puts "Seeded #{Library.count} libraries and #{Book.count} books."
