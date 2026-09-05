class LibgenSearchResult < ApplicationRecord
  belongs_to :libgen_search

  serialize :mirrors, coder: JSON, type: Array

  scope :best_first, -> { order(score: :desc, id: :asc) }
end
