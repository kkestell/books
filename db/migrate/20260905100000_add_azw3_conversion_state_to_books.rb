class AddAzw3ConversionStateToBooks < ActiveRecord::Migration[8.1]
  def change
    add_column :books, :azw3_status, :string
    add_column :books, :azw3_source_blob_id, :integer
    add_column :books, :azw3_error, :string
  end
end
