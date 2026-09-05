class LibgenSearch < ApplicationRecord
  has_many :results, class_name: "LibgenSearchResult", dependent: :delete_all

  enum :status, {
    pending: "pending",
    running: "running",
    completed: "completed",
    failed: "failed"
  }, validate: true
end
