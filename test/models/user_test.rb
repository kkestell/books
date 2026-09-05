require "test_helper"

class UserTest < ActiveSupport::TestCase
  test "each user owns one library" do
    assert_equal libraries(:kyle), users(:kyle).library
    assert_equal libraries(:liz), users(:liz).library
  end

  test "usernames are unique" do
    assert_no_difference "User.count" do
      User.new(username: "kyle").save
    end
  end
end
