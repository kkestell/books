class Azw3CleanupJob < ApplicationJob
  queue_as :default

  KEEP_FOR = 24.hours

  def perform
    Book.where(azw3_status: :ready).find_each do |book|
      next unless book.azw3_file.attached?
      next unless book.azw3_file.blob.created_at.before?(KEEP_FOR.ago)

      book.reset_azw3
    end
  end
end
