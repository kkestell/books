class Library < ApplicationRecord
  has_many :books, dependent: :destroy
  has_many :book_imports, dependent: :destroy
  has_many :libgen_searches, dependent: :destroy

  validates :name, presence: true
  validates :slug, presence: true, uniqueness: true, format: { with: /\A[a-z0-9-]+\z/ }

  def to_param
    slug
  end
end
