import html
import tempfile
from queue import Empty, Queue

import requests
from PySide6.QtCore import QThread, Signal
from bs4 import BeautifulSoup

from log import Log
from models import SearchResult, Job, DownloadResult, Book


class ConversionWorker(QThread):
    conversionStarted = Signal()
    conversionSuccess = Signal(Book)
    conversionError = Signal(Book)
    conversionFinished = Signal()

    def __init__(self, kindle, books):
        super().__init__()
        self.kindle = kindle
        self.books = books

    def run(self):
        self.conversionStarted.emit()
        for book in self.books:
            if not self.convert(book):
                self.conversionError.emit(book)
            else:
                self.conversionSuccess.emit(book)
        self.conversionFinished.emit()

    def convert(self, book):
        try:
            self.kindle.sendToDevice(book)
            return True
        except Exception as e:
            print(e)
            return False


class ImportWorker(QThread):
    importStarted = Signal()
    importSuccess = Signal(Book)
    importError = Signal(Book)
    importFinished = Signal()

    def __init__(self, library, filePaths):
        super().__init__()
        self.library = library
        self.filePaths = filePaths

    def run(self):
        Log.info("Import started.")
        self.importStarted.emit()
        for filePath in self.filePaths:
            self.importBook(filePath)
        self.importFinished.emit()
        Log.info("Import finished.")
        self.msleep(100)

    def importBook(self, filePath):
        book = self.library.addBook(filePath)
        if not book:
            self.importError.emit(book)
        else:
            self.importSuccess.emit(book)


class DownloadWorker(QThread):
    jobQueued = Signal(Job)
    downloadComplete = Signal(DownloadResult)
    statusChanged = Signal(Job)

    def __init__(self):
        super().__init__()
        self.queue = Queue()
        self.hasJobs = False

    def run(self):
        while True:
            try:
                job = self.queue.get(timeout=1)
                self.hasJobs = True
                filePath = self.download(job)
                if not filePath:
                    # fixme: handle error
                    continue
                result = DownloadResult(job, filePath)
                self.downloadComplete.emit(result)
            except Empty:
                continue
            finally:
                self.hasJobs = False

    def enqueue(self, searchResult):
        job = Job(searchResult.author, searchResult.series, searchResult.title, searchResult.format, searchResult.size, searchResult.mirrors)
        self.queue.put(job)
        self.jobQueued.emit(job)

    def queueSize(self):
        return self.queue.qsize() + (1 if self.hasJobs else 0)

    def download(self, job):
        Log.info(f"Downloading {job.title}")

        for url in job.mirrors:
            job.status = "Starting"
            self.statusChanged.emit(job)

            Log.info(f"Trying {url}")

            try:
                if not self.isRunning:
                    break
                res = requests.get(url, timeout=300)
                if res.status_code != 200:
                    print("Error:", res.status_code)
                    continue
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
                    pass

                for downloadUrl in downloadUrls:
                    Log.info(f"Downloading from {downloadUrl}")

                    try:
                        extension = job.format.lower()

                        res = requests.get(downloadUrl, stream=True, timeout=30)
                        if res.status_code != 200:
                            Log.info(f"Error: {res.status_code}")
                            continue

                        totalLength = int(res.headers.get('content-length', 0))
                        if totalLength == 0:
                            Log.info("Error: 0 content length")
                            continue

                        Log.info(f"Downloading {totalLength} bytes")

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

        Log.info(f"Failed to download {job.title}")
        job.status = "Error"
        self.statusChanged.emit(job)
        return None


class SearchWorker(QThread):
    newRecord = Signal(SearchResult)
    searchComplete = Signal()

    def __init__(self, query, format):
        super().__init__()
        self.query = query
        self.format = format

    def run(self):
        self.search()
        self.searchComplete.emit()

    def search(self):
        page = 1
        try:
            Log.info(f"Searching for {self.query}...")
            while page < 10:
                if not self.isRunning:
                    break
                url = f"https://libgen.li/index.php?req={self.query}&res=100&page={page}"
                Log.info(f"Requesting {url}")
                res = requests.get(url)
                if res.status_code != 200:
                    raise Exception(f"HTTP Error {res.status_code}")
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
                    authors = columns[1].text.strip()
                    authorNames = self.fixAuthor(authors)
                    if len(authorNames) > 40:
                        authorNames = authorNames[:40] + "..."
                    series = columns[0].select_one("b")
                    if series:
                        series = series.text.strip()
                    else:
                        series = ""
                    language = columns[4].text.strip()
                    if language.lower() != "english":
                        continue
                    file_info = columns[6].select_one("nobr a").text.strip()
                    size = file_info.upper() if file_info else "N/A"
                    extension = columns[7].text.strip().upper()
                    if self.format and extension != self.format.upper():
                        continue
                    mirrors = columns[8].select("a[data-toggle='tooltip']")
                    mirrorLinks = [f"https://libgen.li{mirror['href']}" for mirror in mirrors]
                    self.newRecord.emit(SearchResult(authorNames, series, title, extension, size, mirrorLinks))
                page += 1
            Log.info("Search complete.")
        except Exception as e:
            Log.info(e)
            pass

    @staticmethod
    def fixAuthor(author):
        if "," in author:
            parts = author.split(",")
            return f"{parts[1].strip()} {parts[0].strip()}"
        return author
