class ScopeLibgenSearchesAndCreateBookDownloads < ActiveRecord::Migration[8.1]
  def change
    # Searches are ephemeral scratch data and are now scoped to a library,
    # which existing rows cannot satisfy.
    execute "DELETE FROM libgen_search_results"
    execute "DELETE FROM libgen_searches"

    add_reference :libgen_searches, :library, null: false, foreign_key: true

    create_table :book_downloads do |t|
      t.references :library, null: false, foreign_key: true
      t.references :libgen_search_result, null: false, foreign_key: true
      t.string :status, null: false, default: "pending"
      t.string :error
      t.datetime :started_at
      t.datetime :finished_at

      t.timestamps
    end
  end
end
