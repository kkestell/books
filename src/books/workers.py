import html
import tempfile
from queue import Empty, Queue
from typing import Optional

import requests
from PySide6.QtCore import QThread, Signal
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

from log import Log
from models import SearchResult, Job, DownloadResult, Book, Library


class ConversionWorker(QThread):
    """
    Worker thread to handle the conversion of books for the Kindle device.

    :signal conversionStarted: Emitted when the conversion process starts.
    :signal conversionSuccess: Emitted when a book is successfully converted.
    :signal conversionError: Emitted when a book fails to convert.
    :signal conversionFinished: Emitted when all books are processed.
    """
    conversionStarted = Signal()
    conversionSuccess = Signal(Book)
    conversionError = Signal(Book)
    conversionFinished = Signal()

    def __init__(self, kindle, books):
        """
        Initialize the ConversionWorker.

        :param kindle: The Kindle device to send the books to.
        :type kindle: Kindle
        :param books: The list of books to be converted.
        :type books: list of Book
        """
        super().__init__()
        self.kindle = kindle
        self.books = books

    def run(self):
        """
        Start the conversion process for each book.
        """
        # Emit signal that conversion has started
        self.conversionStarted.emit()

        # Process each book individually
        for book in self.books:
            # Try to convert and send to the Kindle; emit appropriate signal based on the outcome
            if not self.convert(book):
                self.conversionError.emit(book)
            else:
                self.conversionSuccess.emit(book)

        # Emit signal when all conversions are finished
        self.conversionFinished.emit()

    def convert(self, book) -> bool:
        """
        Convert the book and send it to the Kindle device.

        :param book: The book to be converted.
        :type book: Book
        :return: True if the conversion is successful, False otherwise.
        :rtype: bool
        """
        try:
            # Send the book to the Kindle device
            self.kindle.sendToDevice(book)
            return True
        except Exception as e:
            # Log the error if conversion fails
            print(e)
            return False


class ImportWorker(QThread):
    """
    Worker thread to handle importing books into the library.

    :signal importStarted: Emitted when the import process starts.
    :signal importSuccess: Emitted when a book is successfully imported.
    :signal importError: Emitted when a book fails to import.
    :signal importFinished: Emitted when all books are processed.
    """
    importStarted = Signal()
    importSuccess = Signal(Book)
    importError = Signal(Book)
    importFinished = Signal()

    def __init__(self, library: Library, filePaths):
        """
        Initialize the ImportWorker.

        :param library: The library to import books into.
        :type library: Library
        :param filePaths: List of file paths to import.
        :type filePaths: list of str
        """
        super().__init__()
        self.library = library
        self.filePaths = filePaths

    def run(self):
        """
        Start the import process for each file path.
        """
        Log.info("Import started.")
        self.importStarted.emit()

        # Attempt to import each book file
        for filePath in self.filePaths:
            self.importBook(filePath)

        # Emit signal and log completion when all files are processed
        self.importFinished.emit()
        Log.info("Import finished.")
        self.msleep(100)

    def importBook(self, filePath: str):
        """
        Import a single book into the library.

        :param filePath: The path to the book file.
        :type filePath: str
        """
        try:
            # Add the book to the library
            book = self.library.addBook(filePath)
            if not book:
                # Handle the case where the book could not be added
                Log.info(f"library.addBook returned None for {filePath}")
                self.importError.emit(book)
            else:
                self.importSuccess.emit(book)
        except Exception as e:
            # Log any exceptions encountered during import
            Log.info(f"Error importing {filePath}: {e}")


class DownloadWorker(QThread):
    """
    Worker thread to handle downloading books from search results.

    :signal jobQueued: Emitted when a new download job is queued.
    :signal downloadComplete: Emitted when a download job is complete.
    :signal statusChanged: Emitted when the status of a job changes.
    """
    jobQueued = Signal(Job)
    downloadComplete = Signal(DownloadResult)
    statusChanged = Signal(Job)

    def __init__(self):
        """
        Initialize the DownloadWorker.
        """
        super().__init__()
        self.queue = Queue()
        self.hasJobs = False

    def run(self):
        """
        Start processing download jobs from the queue.
        """
        while True:
            try:
                # Fetch the next job from the queue
                job = self.queue.get(timeout=1)
                self.hasJobs = True

                # Attempt to download the file for the job
                filePath = self.download(job)
                if not filePath:
                    continue

                # Emit a signal when the download is complete
                result = DownloadResult(job, filePath)
                self.downloadComplete.emit(result)
            except Empty:
                continue
            finally:
                # Mark that no jobs are currently being processed
                self.hasJobs = False

    def enqueue(self, searchResult: SearchResult):
        """
        Add a new download job to the queue.

        :param searchResult: The search result to download.
        :type searchResult: SearchResult
        """
        # Create a new job from the search result and add it to the queue
        job = Job(searchResult.author, searchResult.series, searchResult.title, searchResult.format, searchResult.size,
                  searchResult.mirrors)
        self.queue.put(job)
        self.jobQueued.emit(job)

    def queueSize(self) -> int:
        """
        Get the size of the download queue.

        :return: The number of jobs in the queue.
        :rtype: int
        """
        # Calculate the total queue size, including any active jobs
        return self.queue.qsize() + (1 if self.hasJobs else 0)

    def download(self, job: Job) -> Optional[str]:
        """
        Download the book associated with a job.

        :param job: The job to download.
        :type job: Job
        :return: The file path of the downloaded book.
        :rtype: Optional[str]
        """
        Log.info(f"Downloading {job.title}")

        for url in job.mirrors:
            # Update the job status to "Starting"
            job.status = "Starting"
            self.statusChanged.emit(job)

            Log.info(f"Trying {url}")

            try:
                if not self.isRunning:
                    break

                # Send a GET request to the mirror URL
                res = requests.get(url, timeout=300)
                if res.status_code != 200:
                    print("Error:", res.status_code)
                    continue

                # Parse the HTML content to find download links
                doc = BeautifulSoup(res.text, "html.parser")
                if "library.lol" in url:
                    downloadUrls = [doc.select_one("div#download h2 a")["href"]]
                    mirrors = doc.select("ul > li > a")
                    for mirror in mirrors:
                        downloadUrls.append(mirror["href"])
                else:
                    relativeUrl = doc.select_one("a:contains('GET')")["href"]
                    domain = url.split("/")[2]
                    downloadUrls = [f"https://{domain}/{relativeUrl}"]

                # Attempt to download from each found URL
                for downloadUrl in downloadUrls:
                    Log.info(f"Downloading from {downloadUrl}")

                    try:
                        extension = job.format.lower()
                        res = requests.get(downloadUrl, stream=True, timeout=30)
                        if res.status_code != 200:
                            Log.info(f"Error: {res.status_code}")
                            continue

                        # Calculate the total content length for the download
                        totalLength = int(res.headers.get('content-length', 0))
                        if totalLength == 0:
                            Log.info("Error: 0 content length")
                            continue

                        Log.info(f"Downloading {totalLength} bytes")

                        # Save the downloaded content to a temporary file
                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as tempFile:
                            tempPath = tempFile.name
                            downloaded = 0
                            for data in res.iter_content(chunk_size=8192):
                                if data:
                                    tempFile.write(data)
                                    downloaded += len(data)
                                    percentage = int((downloaded / totalLength) * 100)
                                    job.status = f"{percentage}%"
                                    self.statusChanged.emit(job)

                        Log.info(f"Downloaded {job.title}")
                        job.status = "Success"
                        self.statusChanged.emit(job)
                        return tempPath
                    except Exception as e:
                        Log.info(f"Error downloading from mirror: {e}")
                        continue
            except Exception as e:
                Log.info(f"Error downloading {job.title}: {e}")
                continue

        # Log failure if no download succeeded
        Log.info(f"Failed to download {job.title}")
        job.status = "Error"
        self.statusChanged.emit(job)
        return None


class SearchWorker(QThread):
    """
    Worker thread to handle searching for books online.

    :signal newRecord: Emitted when a new search result is found.
    :signal searchComplete: Emitted when the search is complete.
    """
    newRecord = Signal(SearchResult)
    searchComplete = Signal()
    error = Signal(str)

    def __init__(self, author: str, title: str, format: str):
        """
        Initialize the SearchWorker.

        :param author: The author to search for.
        :type author: str
        :param title: The title to search for.
        :type title: str
        :param format: The format of the book to search for.
        :type format: str
        """
        super().__init__()
        self.author = author
        self.title = title
        self.format = format

    def run(self):
        """
        Start the search process.
        """
        try:
            self.search()
            self.searchComplete.emit()
        except Exception as e:
            self.error.emit(str(e))

    def search(self):
        """
        Perform the search for books online.
        """
        query = f"{self.author} {self.title}".strip()
        page = 1

        try:
            Log.info(f"Searching for {query}...")

            # Loop through multiple pages of search results
            while page < 10:
                if not self.isRunning():
                    break

                url = f"https://libgen.li/index.php?req={query}&res=100&page={page}"
                Log.info(f"Requesting {url}")
                res = requests.get(url)
                if res.status_code != 200:
                    raise Exception(f"HTTP Error {res.status_code}")

                # Parse the HTML content of the search results page
                doc = BeautifulSoup(res.text, "html.parser")
                table = doc.select_one("table#tablelibgen tbody")
                if not table:
                    break

                rows = table.select("tr")
                for row in rows:
                    columns = row.select("td")
                    title_cell = columns[0].select_one("a[data-toggle='tooltip']")
                    title = title_cell["title"]
                    title = html.unescape(title)
                    title = title.split("<br>")[1]
                    authors = columns[1].text.strip().split(";")
                    authorNames = ", ".join([self.fixAuthor(author) for author in authors])

                    # Truncate the author names if they are too long
                    if len(authorNames) > 40:
                        authorNames = authorNames[:40] + "..."

                    # Extract book series and language details
                    series = columns[0].select_one("b").text.strip() if columns[0].select_one("b") else ""
                    language = columns[4].text.strip()
                    if language.lower() != "english":
                        continue

                    # Extract file information like size and format
                    file_info = columns[6].select_one("nobr a").text.strip()
                    size = file_info.upper() if file_info else "N/A"
                    extension = columns[7].text.strip().upper()
                    if self.format and extension != self.format.upper():
                        continue

                    # Collect all download mirrors
                    mirrors = columns[8].select("a[data-toggle='tooltip']")
                    mirrorLinks = [f"https://libgen.li{mirror['href']}" for mirror in mirrors]

                    # Calculate a score for the search result based on fuzzy matching
                    author_score = fuzz.token_sort_ratio(self.author, authorNames)
                    title_score = fuzz.token_sort_ratio(self.title, title)
                    score = (author_score + title_score) / 2

                    # Emit the new search result record
                    self.newRecord.emit(SearchResult(authorNames, series, title, extension, size, score, mirrorLinks))

                # Move to the next page
                page += 1

            Log.info("Search complete.")
        except Exception as e:
            # Log any exceptions that occur during search
            Log.info(str(e))

    @staticmethod
    def fixAuthor(author: str) -> str:
        """
        Format an author's name from "Last, First" to "First Last".

        :param author: The author's name.
        :type author: str
        :return: The formatted author's name.
        :rtype: str
        """
        if "," in author:
            parts = author.split(",")
            return f"{parts[1].strip()} {parts[0].strip()}"
        return author
