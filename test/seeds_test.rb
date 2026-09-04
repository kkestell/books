require "test_helper"

class SeedsTest < ActiveSupport::TestCase
  test "creates the two libraries without books and can be run repeatedly" do
    Book.destroy_all
    Library.destroy_all

    2.times { capture_io { load Rails.root.join("db/seeds.rb") } }

    assert_equal [ [ "Kyle", "kyle" ], [ "Liz", "liz" ] ], Library.order(:slug).pluck(:name, :slug)
    assert_empty Book.all
  end

  test "creates downloadable demo books only in development and can be run repeatedly" do
    Book.destroy_all
    Library.destroy_all
    development = ActiveSupport::EnvironmentInquirer.new("development")

    Rails.stub(:env, development) do
      2.times { capture_io { load Rails.root.join("db/seeds.rb") } }
    end

    assert_equal 12, Library.find_by!(slug: "kyle").books.count
    assert Library.find_by!(slug: "kyle").books.all? { |book| book.file.attached? }
  end
end
