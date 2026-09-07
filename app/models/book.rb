class Book < ApplicationRecord
  TYPES = [
    "Novel", "Novella", "Short Story", "Anthology", "Collection", "Omnibus",
    "Graphic Novel", "Comic", "Non-Fiction", "Cookbook", "Poetry", "Other"
  ].freeze

  belongs_to :library

  has_one_attached :file
  has_one_attached :azw3_file

  # The azw3 copy is produced on demand for a download and is not a cache:
  # it is purged once delivered, and swept if the download never happens.
  enum :azw3_status, {
    pending: "pending",
    running: "running",
    ready: "ready",
    failed: "failed"
  }, prefix: :azw3

  validates :author, presence: true
  validates :title, presence: true

  def reset_azw3
    azw3_file.purge if azw3_file.attached?
    update!(azw3_status: nil, azw3_source_blob_id: nil, azw3_error: nil)
  end
end
