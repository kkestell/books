class BookDownload < ApplicationRecord
  belongs_to :library
  belongs_to :libgen_search_result

  enum :status, {
    pending: "pending",
    running: "running",
    completed: "completed",
    failed: "failed"
  }, validate: true
end
