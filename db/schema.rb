# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# This file is the source Rails uses to define your schema when running `bin/rails
# db:schema:load`. When creating a new database, `bin/rails db:schema:load` tends to
# be faster and is potentially less error prone than running all of your
# migrations from scratch. Old migrations may fail to apply correctly if those
# migrations use external dependencies or application code.
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema[8.1].define(version: 2026_09_05_120000) do
  create_table "active_storage_attachments", force: :cascade do |t|
    t.bigint "blob_id", null: false
    t.datetime "created_at", null: false
    t.string "name", null: false
    t.bigint "record_id", null: false
    t.string "record_type", null: false
    t.index ["blob_id"], name: "index_active_storage_attachments_on_blob_id"
    t.index ["record_type", "record_id", "name", "blob_id"], name: "index_active_storage_attachments_uniqueness", unique: true
  end

  create_table "active_storage_blobs", force: :cascade do |t|
    t.bigint "byte_size", null: false
    t.string "checksum"
    t.string "content_type"
    t.datetime "created_at", null: false
    t.string "filename", null: false
    t.string "key", null: false
    t.text "metadata"
    t.string "service_name", null: false
    t.index ["key"], name: "index_active_storage_blobs_on_key", unique: true
  end

  create_table "active_storage_variant_records", force: :cascade do |t|
    t.bigint "blob_id", null: false
    t.string "variation_digest", null: false
    t.index ["blob_id", "variation_digest"], name: "index_active_storage_variant_records_uniqueness", unique: true
  end

  create_table "book_downloads", force: :cascade do |t|
    t.datetime "created_at", null: false
    t.string "error"
    t.datetime "finished_at"
    t.integer "libgen_search_result_id", null: false
    t.integer "library_id", null: false
    t.datetime "started_at"
    t.string "status", default: "pending", null: false
    t.datetime "updated_at", null: false
    t.index ["libgen_search_result_id"], name: "index_book_downloads_on_libgen_search_result_id"
    t.index ["library_id"], name: "index_book_downloads_on_library_id"
  end

  create_table "book_imports", force: :cascade do |t|
    t.boolean "cancel_requested", default: false, null: false
    t.datetime "created_at", null: false
    t.text "error_messages"
    t.integer "failed_files", default: 0, null: false
    t.datetime "finished_at"
    t.integer "ignored_files", default: 0, null: false
    t.integer "imported_files", default: 0, null: false
    t.integer "library_id", null: false
    t.integer "processed_files", default: 0, null: false
    t.datetime "started_at"
    t.string "status", default: "pending", null: false
    t.integer "total_files", default: 0, null: false
    t.datetime "updated_at", null: false
    t.index ["library_id"], name: "index_book_imports_on_library_id"
  end

  create_table "books", force: :cascade do |t|
    t.string "author", null: false
    t.string "book_type"
    t.datetime "created_at", null: false
    t.text "description"
    t.string "format"
    t.string "google_books_id"
    t.integer "library_id", null: false
    t.string "open_library_key"
    t.date "published"
    t.string "series"
    t.integer "series_number"
    t.string "title", null: false
    t.datetime "updated_at", null: false
    t.index ["library_id"], name: "index_books_on_library_id"
  end

  create_table "libgen_search_results", force: :cascade do |t|
    t.string "author", default: "", null: false
    t.datetime "created_at", null: false
    t.string "format", default: "", null: false
    t.integer "libgen_search_id", null: false
    t.text "mirrors"
    t.integer "score", default: 0, null: false
    t.string "series", default: "", null: false
    t.string "size", default: "", null: false
    t.string "title", null: false
    t.datetime "updated_at", null: false
    t.index ["libgen_search_id"], name: "index_libgen_search_results_on_libgen_search_id"
  end

  create_table "libgen_searches", force: :cascade do |t|
    t.string "author", default: "", null: false
    t.datetime "created_at", null: false
    t.string "error"
    t.datetime "finished_at"
    t.string "format", default: "", null: false
    t.integer "library_id", null: false
    t.integer "result_count", default: 0, null: false
    t.datetime "started_at"
    t.string "status", default: "pending", null: false
    t.string "title", default: "", null: false
    t.datetime "updated_at", null: false
    t.index ["library_id"], name: "index_libgen_searches_on_library_id"
  end

  create_table "libraries", force: :cascade do |t|
    t.datetime "created_at", null: false
    t.string "name", null: false
    t.string "slug", null: false
    t.datetime "updated_at", null: false
    t.integer "user_id", null: false
    t.index ["slug"], name: "index_libraries_on_slug", unique: true
    t.index ["user_id"], name: "index_libraries_on_user_id", unique: true
  end

  create_table "users", force: :cascade do |t|
    t.datetime "created_at", null: false
    t.datetime "updated_at", null: false
    t.string "username", null: false
    t.index ["username"], name: "index_users_on_username", unique: true
  end

  add_foreign_key "active_storage_attachments", "active_storage_blobs", column: "blob_id"
  add_foreign_key "active_storage_variant_records", "active_storage_blobs", column: "blob_id"
  add_foreign_key "book_downloads", "libgen_search_results"
  add_foreign_key "book_downloads", "libraries"
  add_foreign_key "book_imports", "libraries"
  add_foreign_key "books", "libraries"
  add_foreign_key "libgen_search_results", "libgen_searches"
  add_foreign_key "libgen_searches", "libraries"
  add_foreign_key "libraries", "users"
end
