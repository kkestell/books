class CreateLibraries < ActiveRecord::Migration[8.1]
  def change
    create_table :libraries do |t|
      t.string :name, null: false
      t.string :slug, null: false

      t.timestamps
    end
    add_index :libraries, :slug, unique: true
  end
end
