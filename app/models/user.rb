class User < ApplicationRecord
  has_one :library

  validates :username, presence: true, uniqueness: true
end
