import os
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from dateutil import parser

from src.books.core.config import Config
from src.books.core.log import Log
from src.books.core.utils import run, cleanText


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
        description = None

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
            elif line.startswith("Comments"):
                description = line.split(':', 1)[1].strip()
                description = cleanText(description)

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
        if description:
            self.description = description

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
            Log.info(f"Metadata updated:\n{result.stdout}")
        except subprocess.CalledProcessError as e:
            Log.info(f"Failed to update metadata: {e.stderr}")


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


def createBookFromFile(path: str):
    """
    Create a Book object from a file path by initializing it with default values and loading its metadata.

    :param path: The file path to create the book from.
    :type path: str
    :return: A book object initialized from the file's metadata.
    :rtype: src.books.models.book.Book
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
