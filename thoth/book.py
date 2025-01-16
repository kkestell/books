import os
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime

from dateutil import parser
from settings import Settings

from log import Log
from utils import run, clean_text


@dataclass
class Book:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    author: str = ''
    series: str | None = None
    series_number: int | None = None
    title: str = ''
    published: str | None = None
    type: str | None = None
    description: str | None = None
    added: str = ''
    path: str = ''
    format: str = ''

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', str(uuid.uuid4()))
        self.author = kwargs.get('author', '')
        self.series = kwargs.get('series')
        self.series_number = kwargs.get('series_number')
        self.title = kwargs.get('title', '')
        self.published = kwargs.get('published')
        self.type = kwargs.get('type')
        self.description = kwargs.get('description')
        self.added = kwargs.get('added', '')
        self.path = kwargs.get('path', '')
        self.format = kwargs.get('format', '')
        if not self.format and self.path:
            extension = os.path.splitext(self.path)[1].lower()
            self.format = extension.strip('.').upper()

    def load_metadata(self):
        settings = Settings.load()
        args = []

        if settings.python_path:
            args.append(settings.python_path)
        args.append(settings.ebook_meta_path)
        args.append(self.path)

        Log.info(f"Getting metadata: {args}")

        try:
            result = run(args)
        except subprocess.CalledProcessError as e:
            Log.info(f"Failed to get metadata: {e.stderr}")
            return None, None

        output = result.stdout
        Log.info(f"Metadata:\n{output}")
        lines = output.split('\n')

        title = None
        authors = None
        published = None
        series_name = None
        series_number = None
        description = None

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
                    series_name, series_number = series.rsplit('#', 1)
                    series_name = series_name.strip()
                    series_number = series_number.strip()
            elif line.startswith("Comments"):
                description = line.split(':', 1)[1].strip()
                description = clean_text(description)

        if authors:
            self.author = authors
        if title:
            self.title = title
        if published:
            self.published = published
        if series_name:
            self.series = series_name
            self.series_number = series_number
        if description:
            self.description = description

    def save_metadata(self):
        settings = Settings.load()
        args = []

        if settings.python_path:
            args.append(settings.python_path)
        args.append(settings.ebook_meta_path)

        args.extend(['-a', self.author, '-t', self.title])
        if self.series:
            args.extend(['-s', self.series, '-i', str(self.series_number)])
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
        return self.title == other.title

    def __lt__(self, other):
        return self.title < other.title


def create_book_from_file(path: str):
    book = Book(
        author="Unknown Author",
        title="Unknown Title",
        added=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        path=path
    )
    book.load_metadata()
    return book
