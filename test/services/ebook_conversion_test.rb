require "test_helper"

class EbookConversionTest < ActiveSupport::TestCase
  test "converts an ebook to azw3 for a paperwhite" do
    status = Object.new.tap { |object| object.define_singleton_method(:success?) { true } }
    command = lambda do |*arguments|
      assert_equal "ebook-convert", arguments.first
      assert_equal ".epub", File.extname(arguments.second)
      assert_equal ".azw3", File.extname(arguments.third)
      assert_equal "--output-profile", arguments.fourth
      assert_equal "kindle_pw3", arguments.fifth
      File.write(arguments.third, "azw3 bytes")
      [ "", "", status ]
    end

    result = Open3.stub(:capture3, command) do
      EbookConversion.convert(io: StringIO.new("epub bytes"), filename: "dune.epub")
    end

    assert_equal "dune.azw3", result.filename
    assert_equal "application/x-mobi8-ebook", result.content_type
    assert_equal "azw3 bytes", result.file.read
  ensure
    result&.file&.close!
  end

  test "replaces a missing extension with azw3" do
    status = Object.new.tap { |object| object.define_singleton_method(:success?) { true } }
    command = lambda do |*arguments|
      File.write(arguments.third, "azw3 bytes")
      [ "", "", status ]
    end

    result = Open3.stub(:capture3, command) do
      EbookConversion.convert(io: StringIO.new("epub bytes"), filename: "dune")
    end

    assert_equal "dune.azw3", result.filename
  ensure
    result&.file&.close!
  end

  test "raises a useful error when ebook-convert fails" do
    status = Object.new.tap { |object| object.define_singleton_method(:success?) { false } }

    error = Open3.stub(:capture3, [ "", "no listener detected", status ]) do
      assert_raises(EbookConversion::Error) do
        EbookConversion.convert(io: StringIO.new("garbage"), filename: "dune.epub")
      end
    end

    assert_match "Could not convert that ebook to azw3.", error.message
    assert_match "no listener detected", error.message
  end
end
