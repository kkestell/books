class CreateUsers < ActiveRecord::Migration[8.1]
  def change
    create_table :users do |t|
      t.string :username, null: false

      t.timestamps
    end
    add_index :users, :username, unique: true

    %w[kyle liz].each do |username|
      User.create_or_find_by!(username: username)
    end

    add_reference :libraries, :user, index: { unique: true }
    Library.find_each do |library|
      # Attach every existing library to the user it was named after rather
      # than dropping anything that predates authentication.
      library.update_columns(user_id: User.find_by!(username: library.slug).id)
    end
    change_column_null :libraries, :user_id, false
    add_foreign_key :libraries, :users
  end
end
