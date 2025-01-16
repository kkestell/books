import os
import shutil
import sqlite3
import threading
from pathlib import Path
from dataclasses import asdict
from datetime import datetime

from PySide6.QtCore import Signal, QObject
from PySide6.QtCore import QStandardPaths
from log import Log
from book import Book
from job import Job


class Library(QObject):
    book_removed = Signal(Book)

    def __init__(self):
        super().__init__()

        home_location = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation))
        self._library_path = home_location / "Thoth"
        self._library_path.mkdir(parents=True, exist_ok=True)

        data_location = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))
        data_location.mkdir(parents=True, exist_ok=True)
        self.db_path = data_location / "library.db"

        # if the database file exists
        # if os.path.exists(self.db_path):
        #     os.remove(self.db_path)

        self._local = threading.local()
        self._initialize_database()

        self.num_books = self._get_num_books()

    def _get_connection(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn"):
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _initialize_database(self) -> None:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id TEXT PRIMARY KEY,
                    author TEXT,
                    series TEXT,
                    series_number INTEGER,
                    title TEXT,
                    published TEXT,
                    type TEXT,
                    description TEXT,
                    added TEXT,
                    path TEXT,
                    format TEXT
                )
            """)
            conn.commit()

    def _get_num_books(self) -> int:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM books")
            return cursor.fetchone()[0]

    @staticmethod
    def _sanitize_for_path(name: str) -> str:
        invalid_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        sanitized = name
        for invalidChar in invalid_chars:
            sanitized = sanitized.replace(invalidChar, '')

        if len(sanitized) > 64:
            sanitized = sanitized[:64]

        sanitized = sanitized.strip('.')
        sanitized = sanitized.strip()

        return sanitized

    def _book_directory(self, book: Book) -> str:
        author = self._sanitize_for_path(book.author)
        if not author:
            author = "Unknown Author"

        title = self._sanitize_for_path(book.title)
        if not title:
            title = "Unknown Title"

        return os.path.join(self._library_path, author, title)

    def _book_file(self, book: Book) -> str:
        extension = os.path.splitext(book.path)[1].lower()
        book_directory = self._book_directory(book)

        author = self._sanitize_for_path(book.author)
        if not author:
            author = "Unknown Author"

        title = self._sanitize_for_path(book.title)
        if not title:
            title = "Unknown Title"

        if book.series:
            series = self._sanitize_for_path(book.series)
            if not series:
                series = "Unknown Series"

            if book.series_number:
                series_number = book.series_number
                if not series_number:
                    series_number = 1

                return os.path.join(
                    book_directory,
                    f"{author} - {series} #{series_number} - {title}{extension}"
                )

            return os.path.join(book_directory, f"{author} - {series} - {title}{extension}")

        return os.path.join(book_directory, f"{author} - {title}{extension}")

    def add_book(self, file_path: str, job: Job = None) -> Book:
        Log.info(f"Adding book from {file_path}")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        book = Book(
            author="Unknown Author",
            title="Unknown Title",
            added=now,
            path=file_path
        )

        try:
            book.load_metadata()
        except Exception as e:
            print("Failed to extract metadata:", e)
            if job:
                book.author = job.author
                book.series = job.series
                book.title = job.title
            else:
                filename = os.path.basename(book.path)
                if '-' in filename:
                    parts = filename.split('-')
                    book.author = parts[0].strip()
                    book.title = parts[1].strip()
                else:
                    book.author = "Unknown Author"
                    filename_without_extension = os.path.splitext(filename)[0]
                    book.title = filename_without_extension

        book_directory = self._book_directory(book)
        if not os.path.exists(book_directory):
            os.makedirs(book_directory)

        book_file = self._book_file(book)
        shutil.copy(file_path, book_file)
        book.path = str(book_file)

        if len(book.author) > 64:
            book.author = book.author[:64]

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO books (id, author, series, series_number, title, published, type, description, added, path, format)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                book.id, book.author, book.series, book.series_number, book.title, book.published,
                book.type, book.description, book.added, book.path, book.format
            ))
            conn.commit()

        self.num_books = self._get_num_books()
        Log.info(f"Added book: {book}")
        return book

    def update_book(self, book: Book):
        book.save_metadata()

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM books WHERE id = ?", (book.id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Book with ID {book.id} not found")
            old_book = Book(**row)

        old_path = old_book.path
        new_path = self._book_file(book)

        if old_path != new_path:
            old_book_dir = os.path.dirname(old_path)
            old_author_dir = os.path.dirname(old_book_dir)

            new_dir = os.path.dirname(new_path)
            if not os.path.exists(new_dir):
                os.makedirs(new_dir)

            os.rename(old_path, new_path)
            book.path = new_path

            if os.path.exists(old_book_dir) and not os.listdir(old_book_dir):
                os.rmdir(old_book_dir)
            if os.path.exists(old_author_dir) and not os.listdir(old_author_dir):
                os.rmdir(old_author_dir)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE books
                SET author = ?, series = ?, series_number = ?, title = ?, published = ?, type = ?, description = ?, added = ?, path = ?, format = ?
                WHERE id = ?
            """, (
                book.author, book.series, book.series_number, book.title, book.published,
                book.type, book.description, book.added, book.path, book.format, book.id
            ))
            conn.commit()

    def remove_book(self, book: Book):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM books WHERE id = ?", (book.id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Book with ID {book.id} not found")
            book = Book(**row)

        try:
            os.remove(book.path)
        except FileNotFoundError:
            Log.info(f"Error deleting {book.path}. The file does not exist.")

        book_dir = os.path.dirname(book.path)
        if os.path.exists(book_dir) and not os.listdir(book_dir):
            os.rmdir(book_dir)

        author_dir = os.path.dirname(book_dir)
        if os.path.exists(author_dir) and not os.listdir(author_dir):
            os.rmdir(author_dir)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM books WHERE id = ?", (book.id,))
            conn.commit()

        self.num_books = self._get_num_books()

        self.book_removed.emit(book)

    def get_book_by_id(self, book_id: str) -> Book:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM books WHERE id = ?", (book_id,))
            row = cursor.fetchone()
            if row:
                return Book(**row)
        raise ValueError(f"Book with ID {book_id} not found")

    def author_path(self, author_name: str) -> str:
        return os.path.join(self._library_path, author_name)

    def reset(self):
        shutil.rmtree(self._library_path)
        self._library_path.mkdir(parents=True, exist_ok=True)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM books")
            conn.commit()

        self.num_books = 0

    def get_all_books(self) -> list[Book]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM books")
            rows = cursor.fetchall()
            return [Book(**row) for row in rows]
