class BookImport < ApplicationRecord
  belongs_to :library

  has_many_attached :files

  enum :status, {
    pending: "pending",
    importing: "importing",
    completed: "completed",
    cancelled: "cancelled",
    failed: "failed"
  }, validate: true

  serialize :error_messages, coder: JSON, type: Array

  validates :total_files, :processed_files, :imported_files, :failed_files, :ignored_files,
    numericality: { only_integer: true, greater_than_or_equal_to: 0 }

  def progress_percentage
    return 0 if total_files.zero?

    (processed_files * 100.0 / total_files).round
  end

  def cancellable?
    pending? || importing?
  end

  def request_cancellation!
    with_lock do
      return unless cancellable?

      self.cancel_requested = true
      self.status = :cancelled if pending?
      self.finished_at = Time.current if cancelled?
      save!
    end
  end
end
