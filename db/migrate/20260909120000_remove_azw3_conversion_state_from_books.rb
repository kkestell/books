class RemoveAzw3ConversionStateFromBooks < ActiveRecord::Migration[8.1]
  def change
    remove_column :books, :azw3_status, :string
    remove_column :books, :azw3_source_blob_id, :integer
    remove_column :books, :azw3_error, :string
  end
end
