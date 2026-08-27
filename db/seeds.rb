{
  "kyle" => "Kyle",
  "liz" => "Liz"
}.each do |slug, name|
  library = Library.find_or_initialize_by(slug: slug)
  library.update!(name: name)
end

puts "Ensured the Kyle and Liz libraries exist."
