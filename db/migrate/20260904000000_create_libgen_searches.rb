class CreateLibgenSearches < ActiveRecord::Migration[8.1]
  def change
    create_table :libgen_searches do |t|
      t.string :author, null: false, default: ""
      t.string :title, null: false, default: ""
      t.string :format, null: false, default: ""
      t.string :status, null: false, default: "pending"
      t.integer :result_count, null: false, default: 0
      t.string :error
      t.datetime :started_at
      t.datetime :finished_at

      t.timestamps
    end

    create_table :libgen_search_results do |t|
      t.references :libgen_search, null: false, foreign_key: true
      t.string :author, null: false, default: ""
      t.string :series, null: false, default: ""
      t.string :title, null: false
      t.string :format, null: false, default: ""
      t.string :size, null: false, default: ""
      t.integer :score, null: false, default: 0
      t.text :mirrors

      t.timestamps
    end
  end
end
