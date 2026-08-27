class CreateBookImports < ActiveRecord::Migration[8.1]
  def change
    create_table :book_imports do |t|
      t.references :library, null: false, foreign_key: true
      t.string :status, null: false, default: "pending"
      t.integer :total_files, null: false, default: 0
      t.integer :processed_files, null: false, default: 0
      t.integer :imported_files, null: false, default: 0
      t.integer :failed_files, null: false, default: 0
      t.integer :ignored_files, null: false, default: 0
      t.boolean :cancel_requested, null: false, default: false
      t.text :error_messages
      t.datetime :started_at
      t.datetime :finished_at

      t.timestamps
    end
  end
end
