require "test_helper"

class ApplicationSystemTestCase < ActionDispatch::SystemTestCase
  driven_by :selenium, using: :headless_chrome, screen_size: [ 1400, 1400 ]

  private

  def log_in_as(user)
    visit root_path
    click_on "Log in as #{user.username.capitalize}"
  end
end
