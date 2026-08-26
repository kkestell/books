class Book < ApplicationRecord
  belongs_to :library

  has_one_attached :file

  validates :author, presence: true
  validates :title, presence: true
end
