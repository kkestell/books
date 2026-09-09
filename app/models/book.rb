class Book < ApplicationRecord
  TYPES = [
    "Novel", "Novella", "Short Story", "Anthology", "Collection", "Omnibus",
    "Graphic Novel", "Comic", "Non-Fiction", "Cookbook", "Poetry", "Other"
  ].freeze

  belongs_to :library

  has_one_attached :file

  validates :author, presence: true
  validates :title, presence: true
end
