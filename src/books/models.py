import json
import os.path
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional

from PySide6.QtCore import Signal, QObject
from dateutil import parser

from config import Config
from log import Log
from utils import run


def createBookFromFile(path: str):
    """
    Create a Book object from a file path by initializing it with default values and loading its metadata.

    :param path: The file path to create the book from.
    :type path: str
    :return: A book object initialized from the file's metadata.
    :rtype: Book
    """
    book = Book(
        "Unknown Author",
        None,
        None,
        "Unknown Title",
        None,
        None,
        None,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        path
    )
    book.loadMetadata()
    return book


@dataclass
class Book:
    """
    Represents a book in the library with metadata and file information.
    """
    author: str
    series: str | None
    seriesNumber: int | None
    title: str
    published: str | None
    type: str | None
    description: str | None
    added: str
    path: str = ""
    format: str = ""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __init__(self, author: str, series: str | None, seriesNumber: int | None, title: str,
                 published: str | None, type: str | None, description: str | None, added: str,
                 path: str, format: str = None, id: str = None):
        """
        Initialize a Book object with metadata and file path.

        :param author: The author of the book.
        :type author: str
        :param series: The series name, if any.
        :type series: str | None
        :param seriesNumber: The number in the series, if any.
        :type seriesNumber: int | None
        :param title: The title of the book.
        :type title: str
        :param published: The published date, if any.
        :type published: str | None
        :param type: The type of the book.
        :type type: str | None
        :param description: The description of the book.
        :type description: str | None
        :param added: The date the book was added.
        :type added: str
        :param path: The file path to the book.
        :type path: str
        :param format: The file format of the book.
        :type format: str | None
        :param id: The unique identifier for the book.
        :type id: str | None
        """
        self.author = author
        self.series = series
        self.seriesNumber = seriesNumber
        self.title = title
        self.published = published
        self.type = type
        self.description = description

        if format:
            self.format = format
        else:
            # Extract format from file extension
            extension = os.path.splitext(path)[1].lower()
            self.format = extension.strip('.').upper()

        self.added = added
        self.path = path

        if id:
            self.id = id
        else:
            self.id = str(uuid.uuid4())

    def loadMetadata(self):
        """
        Load metadata for the book using an external metadata extraction tool.
        """
        config = Config.load()
        args = []

        if config.pythonPath:
            args.append(config.pythonPath)
        args.append(config.ebookMetaPath)
        args.append(self.path)

        Log.info(f"Getting metadata: {args}")

        # Run the external metadata extraction tool
        try:
            result = run(args)
        except subprocess.CalledProcessError as e:
            Log.info(f"Failed to get metadata: {e.stderr}")
            return None, None

        output = result.stdout
        Log.info(f"Metadata:\n{output}")
        lines = output.split('\n')

        # Initialize metadata variables
        title = None
        authors = None
        published = None
        seriesName = None
        seriesNumber = None

        # Parse the output line by line
        for line in lines:
            if line.startswith('Title'):
                title = line.split(':', 1)[1].strip()
            elif line.startswith('Author(s)'):
                authors = line.split(':', 1)[1].strip()
                if '[' in authors:
                    authors = authors.split('[')[0].strip()
            elif line.startswith('Published'):
                published = line.split(':', 1)[1].strip()
                try:
                    published = parser.parse(published).strftime('%Y-%m-%d')
                except ValueError:
                    pass
            elif line.startswith('Series'):
                series = line.split(':', 1)[1].strip()
                if '#' in series:
                    seriesName, seriesNumber = series.rsplit('#', 1)
                    seriesName = seriesName.strip()
                    seriesNumber = seriesNumber.strip()

        # Update the Book object with the parsed metadata
        if authors:
            self.author = authors
        if title:
            self.title = title
        if published:
            self.published = published
        if seriesName:
            self.series = seriesName
            self.seriesNumber = seriesNumber

    def saveMetadata(self):
        """
        Save metadata for the book to the file using an external tool.
        """
        config = Config.load()
        args = []

        if config.pythonPath:
            args.append(config.pythonPath)
        args.append(config.ebookMetaPath)

        # Add metadata arguments
        args.extend(['-a', self.author, '-t', self.title])
        if self.series:
            args.extend(['-s', self.series, '-i', str(self.seriesNumber)])
        if self.description:
            args.extend(['-c', self.description])

        args.append(self.path)

        Log.info(f"Updating metadata: {args}")

        try:
            result = run(args)
        except subprocess.CalledProcessError as e:
            Log.info(f"Failed to update metadata: {e.stderr}")

        Log.info(f"Metadata updated:\n{result.stdout}")

    def __eq__(self, other):
        """
        Check equality based on the book title.

        :param other: The book object to compare.
        :type other: Book
        :return: True if titles match, False otherwise.
        :rtype: bool
        """
        return self.title == other.title

    def __lt__(self, other):
        """
        Define less than based on the book title for sorting.

        :param other: The book object to compare.
        :type other: Book
        :return: True if this book's title is less than the other's title.
        :rtype: bool
        """
        return self.title < other.title


@dataclass
class SearchResult:
    """
    Represents a search result from an external source.
    """
    author: str
    series: str
    title: str
    format: str
    size: str
    score: int
    mirrors: list


@dataclass
class Job:
    """
    Represents a download job in the queue.
    """
    author: str
    series: str
    title: str
    format: str
    size: str
    mirrors: list
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "Queued"


@dataclass
class DownloadResult:
    """
    Represents the result of a download job.
    """
    job: Job
    filePath: str


class Library(QObject):
    """
    Represents the library of books, managing adding, removing, and updating books.

    :signal bookRemoved: Emitted when a book is removed from the library.
    """
    bookRemoved = Signal(Book)

    def __init__(self):
        """
        Initialize the Library by loading the books from the JSON file.
        """
        super().__init__()

        config = Config.load()
        self.rootPath = config.libraryPath
        self.jsonPath = os.path.join(self.rootPath, 'books.json')

        self.books = []
        self.numBooks = 0

        self.load()

    def load(self):
        """
        Load the books from the JSON file into the library.
        """
        if os.path.exists(self.jsonPath):
            with open(self.jsonPath, 'r') as file:
                data = json.load(file)
                self.books = [Book(**item) for item in data]
        else:
            self.books = []

        self.numBooks = len(self.books)
        Log.info(f"Loaded {self.numBooks} books from {self.jsonPath}")

    def save(self):
        """
        Save the current list of books to the JSON file.
        """
        configDir = os.path.dirname(self.jsonPath)
        if not os.path.exists(configDir):
            os.makedirs(configDir)

        with open(self.jsonPath, 'w') as file:
            json.dump([asdict(book) for book in self.books], file, indent=4)

        Log.info(f"Saved {self.numBooks} books to {self.jsonPath}")

    @staticmethod
    def sanitizeForPath(name: str) -> str:
        """
        Sanitize a string to make it safe for use in a file path.

        :param name: The string to sanitize.
        :type name: str
        :return: The sanitized string.
        :rtype: Optional[str]
        """
        invalidChars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        sanitized = name
        for invalidChar in invalidChars:
            sanitized = sanitized.replace(invalidChar, '')

        if len(sanitized) > 64:
            sanitized = sanitized[:64]

        sanitized = sanitized.strip('.')
        sanitized = sanitized.strip()

        return sanitized

    def bookDirectory(self, book: Book) -> str:
        """
        Get the directory path for a book based on its author and title.

        :param book: The book object.
        :type book: Book
        :return: The directory path for the book.
        :rtype: str
        """
        author = self.sanitizeForPath(book.author)
        if not author:
            author = "Unknown Author"

        title = self.sanitizeForPath(book.title)
        if not title:
            title = "Unknown Title"

        return os.path.join(self.rootPath, author, title)

    def bookFile(self, book: Book) -> str:
        """
        Construct the file path for a book based on its metadata.

        :param book: The book object.
        :type book: Book
        :return: The file path for the book.
        :rtype: str
        """
        extension = os.path.splitext(book.path)[1].lower()
        bookDirectory = self.bookDirectory(book)

        author = self.sanitizeForPath(book.author)
        if not author:
            author = "Unknown Author"

        title = self.sanitizeForPath(book.title)
        if not title:
            title = "Unknown Title"

        if book.series:
            series = self.sanitizeForPath(book.series)
            if not series:
                series = "Unknown Series"

            if book.seriesNumber:
                seriesNumber = book.seriesNumber
                if not seriesNumber:
                    seriesNumber = 1

                return os.path.join(
                    bookDirectory,
                    f"{author} - {series} #{seriesNumber} - {title}{extension}"
                )

            return os.path.join(bookDirectory, f"{author} - {series} - {title}{extension}")

        return os.path.join(bookDirectory, f"{author} - {title}{extension}")

    def addBook(self, filePath: str, job: Job = None) -> Book:
        """
        Add a new book to the library from a file path.

        :param filePath: The file path to the book file.
        :type filePath: str
        :param job: The job associated with the book download.
        :type job: Job | None
        :return: The added book object.
        :rtype: Book
        """
        Log.info(f"Adding book from {filePath}")

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Initialize the Book object with default metadata
        book = Book("Unknown Author", None, None, "Unknown Title", None, None, None, now, filePath)

        try:
            # Attempt to load metadata from the book file
            book.loadMetadata()
        except Exception as e:
            print("Failed to extract metadata:", e)
            if job:
                # Use metadata from the job if available
                book.author = job.author
                book.series = job.series
                book.title = job.title
            else:
                # Fallback to parsing filename
                filename = os.path.basename(book.path)
                if '-' in filename:
                    parts = filename.split('-')
                    book.author = parts[0].strip()
                    book.title = parts[1].strip()
                else:
                    book.author = "Unknown Author"
                    filenameWithoutExtension = os.path.splitext(filename)[0]
                    book.title = filenameWithoutExtension

        # Create the directory for the book
        bookDirectory = self.bookDirectory(book)
        if not os.path.exists(bookDirectory):
            os.makedirs(bookDirectory)

        # Copy the book file to the library
        bookFile = self.bookFile(book)
        shutil.copy(filePath, bookFile)
        book.path = bookFile

        # Truncate author name if it's too long
        if len(book.author) > 64:
            book.author = book.author[:64]

        # Add the book to the library
        self.books.append(book)
        self.save()
        self.numBooks = len(self.books)

        Log.info(f"Added book: {asdict(book)}")
        return book

    def updateBook(self, book: Book):
        """
        Update the metadata of a book and move the file if necessary.

        :param book: The book object with updated metadata.
        :type book: Book
        """
        # Save updated metadata to the book file
        book.saveMetadata()

        # Find the book in the library
        index = next((i for i, b in enumerate(self.books) if b.id == book.id), None)
        oldBook = self.books[index]

        oldPath = oldBook.path
        newPath = self.bookFile(book)

        # Move the book file if the path has changed
        if oldPath != newPath:
            oldBookDir = os.path.dirname(oldPath)
            oldAuthorDir = os.path.dirname(oldBookDir)

            newDir = os.path.dirname(newPath)
            if not os.path.exists(newDir):
                os.makedirs(newDir)

            os.rename(oldPath, newPath)
            book.path = newPath

            # Remove old directories if they are empty
            if not os.listdir(oldBookDir):
                os.rmdir(oldBookDir)
            if not os.listdir(oldAuthorDir):
                os.rmdir(oldAuthorDir)

        # Update the book in the library
        self.books[index] = book
        self.save()

    def removeBook(self, book: Book):
        """
        Remove a book from the library and delete its file.

        :param book: The book object to remove.
        :type book: Book
        """
        # Find the book in the library
        index = next((i for i, b in enumerate(self.books) if b.id == book.id), None)
        if index is None:
            raise ValueError(f"Book with ID {book.id} not found")

        # Remove the book from the list
        book = self.books.pop(index)

        # Delete the book file
        try:
            os.remove(book.path)
        except FileNotFoundError:
            Log.info(f"Error deleting {book.path}. The file does not exist.")

        # Remove empty directories
        bookDir = os.path.dirname(book.path)
        # if the directory doesn't exist, don't try to remove it
        if os.path.exists(bookDir) and not os.listdir(bookDir):
            os.rmdir(bookDir)

        authorDir = os.path.dirname(bookDir)
        if os.path.exists(authorDir) and not os.listdir(authorDir):
            os.rmdir(authorDir)

        self.save()
        self.numBooks = len(self.books)

        # Emit signal that the book was removed
        self.bookRemoved.emit(book)

    def getBookById(self, bookId: str) -> Book:
        """
        Retrieve a book from the library by its ID.

        :param bookId: The unique identifier of the book.
        :type bookId: str
        :return: The book object.
        :rtype: Book
        :raises ValueError: If the book is not found.
        """
        index = next((i for i, b in enumerate(self.books) if b.id == bookId), None)
        if index is not None:
            return self.books[index]
        raise ValueError(f"Book with ID {bookId} not found")

    def authorPath(self, authorName: str) -> str:
        """
        Get the file system path for an author's directory.

        :param authorName: The author's name.
        :type authorName: str
        :return: The path to the author's directory.
        :rtype: str
        """
        return os.path.join(self.rootPath, authorName)

    def bookPath(self, authorName: str, title: str) -> str:
        """
        Get the file system path for a book's directory.

        :param authorName: The author's name.
        :type authorName: str
        :param title: The book's title.
        :type title: str
        :return: The path to the book's directory.
        :rtype: str
        """
        return os.path.join(self.authorPath(authorName), title)

    def reset(self):
        """
        Reset the library by deleting all books and directories.
        """
        shutil.rmtree(self.rootPath)
        os.makedirs(self.rootPath)
        self.books = []
        self.numBooks = 0
        self.save()
        self.load()
