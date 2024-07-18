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
        job.status = "Starting"
        self.statusChanged.emit(job)

        for url in job.mirrors:
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
                    download_url = doc.select_one("div#download h2 a")["href"]
                else:
                    download_url = doc.select_one("a")["href"]

                extension = download_url.split(".")[-1]

                res = requests.get(download_url, stream=True, timeout=10)
                if res.status_code != 200:
                    print("Error:", res.status_code)
                    continue

                totalLength = int(res.headers.get('content-length', 0))
                if totalLength == 0:
                    print("Error: 0 content length")
                    continue

                print(f"Downloading {totalLength} bytes")

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
                Log.info(f"Error downloading {job.title}: {e}")
                pass

        Log.info(f"Failed to download {job.title}")
        job.status = "Error"
        self.statusChanged.emit(job)
        return None


class SearchWorker(QThread):
    newRecord = Signal(SearchResult)
    searchComplete = Signal()

    def __init__(self, query, search_type, format):
        super().__init__()
        self.query = query
        self.search_type = search_type
        self.format = format

    def run(self):
        if self.search_type == "Fiction":
            self.searchFiction()
        else:
            self.searchNonFiction()
        self.searchComplete.emit()

    def searchFiction(self):
        page = 1
        try:
            Log.info(f"Searching for {self.query}...")
            while page < 10:
                if not self.isRunning:
                    break
                url = f"https://libgen.is/fiction/?q={self.query}&language=English&format={self.format}&page={page}"
                Log.info(f"Requesting {url}")
                res = requests.get(url)
                if res.status_code != 200:
                    raise Exception(f"HTTP Error {res.status_code}")
                doc = BeautifulSoup(res.text, "html.parser")
                table = doc.select_one("table.catalog tbody")
                if not table:
                    break
                rows = table.select("tr")
                for row in rows:
                    columns = row.select("td")
                    authors = columns[0].findAll("a")
                    authorNames = ", ".join([self.fixAuthor(author.text) for author in authors])
                    if len(authorNames) > 40:
                        authorNames = authorNames[:40] + "..."
                    series = columns[1].text.strip()
                    title = columns[2].find("a").text.strip()
                    language = columns[3].text.strip()
                    if language.lower() != "english":
                        continue
                    file = columns[4].text
                    extension, size = [p.strip().upper() for p in file.split("/")]
                    mirrors = columns[5].findAll("a")
                    mirrorLinks = [mirror["href"] for mirror in mirrors]
                    self.newRecord.emit(SearchResult(authorNames, series, title, extension, size, mirrorLinks))
                page += 1
            Log.info("Search complete.")
        except Exception as e:
            Log.info(e)
            pass

    def searchNonFiction(self):
        page = 1
        try:
            Log.info(f"Searching for {self.query}...")
            while page < 10:
                url = f"https://libgen.is/search.php?req={self.query}&open=0&res=100&view=simple&phrase=1&column=def&page={page}"
                Log.info(f"Requesting {url}")
                res = requests.get(url)
                if res.status_code != 200:
                    raise Exception(f"HTTP Error {res.status_code}")
                doc = BeautifulSoup(res.text, "html.parser")
                table = doc.select_one("table.c")
                if not table:
                    return
                rows = table.select("tr")[1:]
                for row in rows:
                    columns = row.select("td")
                    authors = columns[1].findAll("a")
                    authorNames = ", ".join([self.fixAuthor(author.text) for author in authors])
                    if len(authorNames) > 40:
                        authorNames = authorNames[:40].strip() + "..."
                    title = columns[2].find("a").find(string=True).strip()
                    language = columns[6].text.strip()
                    if language.lower() != "english":
                        continue
                    size = columns[7].text.strip().upper()
                    extension = columns[8].text.strip().upper()
                    if self.format and self.format != extension:
                        continue
                    mirrors = columns[9].findAll("a")
                    mirrorLinks = [mirror["href"] for mirror in mirrors]
                    self.newRecord.emit(SearchResult(authorNames, "", title, extension, size, mirrorLinks))
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
