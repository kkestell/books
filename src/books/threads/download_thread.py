import tempfile
from queue import Queue, Empty
from typing import Optional

import requests
from PySide6.QtCore import QThread, Signal
from bs4 import BeautifulSoup

from src.books.core.log import Log
from src.books.core.models.download_result import DownloadResult
from src.books.core.models.job import Job
from src.books.core.models.search_result import SearchResult


class DownloadThread(QThread):
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
