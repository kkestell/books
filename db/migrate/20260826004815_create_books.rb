class CreateBooks < ActiveRecord::Migration[8.1]
  def change
    create_table :books do |t|
      t.references :library, null: false, foreign_key: true
      t.string :author, null: false
      t.string :title, null: false
      t.string :series
      t.integer :series_number
      t.date :published
      t.string :book_type
      t.string :format
      t.text :description
      t.string :google_books_id
      t.string :open_library_key

      t.timestamps
    end
  end
end
