require "test_helper"

class SeedsTest < ActiveSupport::TestCase
  test "creates the two libraries without books and can be run repeatedly" do
    Book.destroy_all
    Library.destroy_all

    2.times { capture_io { load Rails.root.join("db/seeds.rb") } }

    assert_equal [ [ "Kyle", "kyle" ], [ "Liz", "liz" ] ], Library.order(:slug).pluck(:name, :slug)
    assert_empty Book.all
  end
end
