import json
import os.path
import shutil
import subprocess
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime

from PySide6.QtCore import Signal, QObject
from dateutil import parser

from config import Config
from ebook import loadEpub
from log import Log


def createBookFromFile(path):
    book = Book("Unknown Author", None, None, "Unknown Title", None, None, None, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), path)
    book.loadMetadata()
    return book


@dataclass
class Book:
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

    def __init__(self, author, series, seriesNumber, title, published, type, description, added, path, format=None, id=None):
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
            extension = os.path.splitext(path)[1].lower()
            self.format = extension.strip('.').upper()
        self.added = added
        self.path = path
        if id:
            self.id = id
        else:
            self.id = str(uuid.uuid4())

    def loadMetadata(self):
        config = Config.load()
        args = []
        if config.pythonPath:
            args.append(config.pythonPath)
        args.append(config.ebookMetaPath)
        args.append(self.path)
        Log.info(f"Getting metadata: {args}")
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode != 0:
            Log.info(f"Failed to get metadata: {result.stderr}")
            return None, None
        output = result.stdout
        Log.info(f"Metadata:\n{output}")
        lines = output.split('\n')
        title = None
        authors = None
        published = None
        seriesName = None
        seriesNumber = None
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
                    published = parser.parse(published)
                    published = published.strftime('%Y-%m-%d')
                except ValueError:
                    pass
            elif line.startswith('Series'):
                series = line.split(':', 1)[1].strip()
                if '#' in series:
                    seriesName, seriesNumber = series.rsplit('#', 1)
                    seriesName = seriesName.strip()
                    seriesNumber = seriesNumber.strip()
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
        config = Config.load()
        args = []
        if config.pythonPath:
            args.append(config.pythonPath)
        args.append(config.ebookMetaPath)
        args.extend(['-a', self.author, '-t', self.title])
        if self.series:
            args.extend(['-s', self.series, '-i', str(self.seriesNumber)])
        if self.description:
            args.extend(['-c', self.description])
        args.append(self.path)
        Log.info(f"Updating metadata: {args}")
        result = subprocess.run(args, capture_output=True, text=True)
        if result.returncode != 0:
            Log.info(f"Failed to update metadata: {result.stderr}")
        output = result.stdout
        Log.info(f"Metadata updated:\n{output}")

    def __eq__(self, other):
        return self.title == other.title

    def __lt__(self, other):
        return self.title < other.title


@dataclass
class SearchResult:
    author: str
    series: str
    title: str
    format: str
    size: str
    mirrors: list


@dataclass
class Job:
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
    job: Job
    filePath: str


class Library(QObject):
    bookRemoved = Signal(Book)

    def __init__(self):
        super().__init__()
        config = Config.load()
        self.rootPath = config.libraryPath
        self.jsonPath = os.path.join(self.rootPath, 'books.json')
        self.books = []
        self.numBooks = 0
        self.load()

    def load(self):
        if os.path.exists(self.jsonPath):
            with open(self.jsonPath, 'r') as file:
                data = json.load(file)
                self.books = [Book(**item) for item in data]
        else:
            self.books = []
        self.numBooks = len(self.books)
        Log.info(f"Loaded {self.numBooks} books from {self.jsonPath}")

    def save(self):
        configDir = os.path.dirname(self.jsonPath)
        if not os.path.exists(configDir):
            os.makedirs(configDir)
        with open(self.jsonPath, 'w') as file:
            json.dump([asdict(book) for book in self.books], file, indent=4)
        Log.info(f"Saved {self.numBooks} books to {self.jsonPath}")

    def sanitizeForPath(self, name):
        if not name:
            return None
        invalidChars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        sanitized = name
        for invalidChar in invalidChars:
            sanitized = sanitized.replace(invalidChar, '')
        if len(sanitized) > 64:
            sanitized = sanitized[:64]
        sanitized = sanitized.strip('.')
        sanitized = sanitized.strip()
        return sanitized

    def bookDirectory(self, book):
        author = self.sanitizeForPath(book.author)
        if not author:
            author = "Unknown Author"
        title = self.sanitizeForPath(book.title)
        if not title:
            title = "Unknown Title"
        return os.path.join(self.rootPath, author, title)

    def bookFile(self, book):
        extension = os.path.splitext(book.path)[1].lower()
        bookDirectory = self.bookDirectory(book)
        author = self.sanitizeForPath(book.author)
        if not author:
            author = "Unknown Author"
        title = self.sanitizeForPath(book.title)
        if not title:
            title = "Unknown Title"
        return os.path.join(bookDirectory, f"{author} - {title}{extension}")

    def addBook(self, filePath, job=None):
        Log.info(f"Adding book from {filePath}")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        book = Book("Unknown Author", None, None, "Unknown Title", None, None, None, now, filePath)
        try:
            book.loadMetadata()
            extension = os.path.splitext(filePath)[1].lower()
            if extension == '.epub':
                epub = loadEpub(filePath)
                book.type = epub.type
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
                    filenameWithoutExtension = os.path.splitext(filename)[0]
                    book.title = filenameWithoutExtension
        bookDirectory = self.bookDirectory(book)
        if not os.path.exists(bookDirectory):
            os.makedirs(bookDirectory)
        bookFile = self.bookFile(book)
        shutil.copy(filePath, bookFile)
        book.path = bookFile
        if len(book.author) > 64:
            book.author = book.author[:64]
        self.books.append(book)
        self.save()
        self.numBooks = len(self.books)
        Log.info(f"Added book: {asdict(book)}")
        return book

    def updateBook(self, book):
        book.saveMetadata()
        index = next((i for i, b in enumerate(self.books) if b.id == book.id), None)
        oldBook = self.books[index]
        oldPath = oldBook.path
        newPath = self.bookFile(book)
        if oldPath != newPath:
            oldBookDir = os.path.dirname(oldPath)
            oldAuthorDir = os.path.dirname(oldBookDir)
            newDir = os.path.dirname(newPath)
            if not os.path.exists(newDir):
                os.makedirs(newDir)
            os.rename(oldPath, newPath)
            book.path = newPath
            if not os.listdir(oldBookDir):
                os.rmdir(oldBookDir)
            if not os.listdir(oldAuthorDir):
                os.rmdir(oldAuthorDir)
        self.books[index] = book
        self.save()

    def removeBook(self, book):
        index = next((i for i, b in enumerate(self.books) if b.id == book.id), None)
        if index is None:
            raise ValueError(f"Book with ID {book.id} not found")
        book = self.books.pop(index)
        os.remove(book.path)
        bookDir = os.path.dirname(book.path)
        if not os.listdir(bookDir):
            os.rmdir(bookDir)
        authorDir = os.path.dirname(bookDir)
        if not os.listdir(authorDir):
            os.rmdir(authorDir)
        self.save()
        self.numBooks = len(self.books)
        self.bookRemoved.emit(book)

    def getBookById(self, bookId):
        index = next((i for i, b in enumerate(self.books) if b.id == bookId), None)
        if index is not None:
            return self.books[index]
        raise ValueError(f"Book with ID {bookId} not found")

    def authorPath(self, authorName):
        return os.path.join(self.rootPath, authorName)

    def bookPath(self, authorName, title):
        return os.path.join(self.authorPath(authorName), title)

    def reset(self):
        shutil.rmtree(self.rootPath)
        os.makedirs(self.rootPath)
        self.books = []
        self.numBooks = 0
        self.save()
        self.load()
