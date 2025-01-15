import tempfile
from queue import Queue, Empty
from typing import Optional

import requests
from PySide6.QtCore import QThread, Signal
from bs4 import BeautifulSoup

from log import Log
from download_result import DownloadResult
from job import Job
from search_result import SearchResult


class DownloadThread(QThread):
    job_queued = Signal(Job)
    download_complete = Signal(DownloadResult)
    status_changed = Signal(Job)

    def __init__(self):
        super().__init__()
        self.queue = Queue()
        self.has_jobs = False

    def run(self):
        while True:
            try:
                job = self.queue.get(timeout=1)
                self.has_jobs = True

                file_path = self.download(job)
                if not file_path:
                    continue

                result = DownloadResult(job, file_path)
                self.download_complete.emit(result)
            except Empty:
                continue
            finally:
                self.has_jobs = False

    def enqueue(self, result: SearchResult):
        job = Job(result.author, result.series, result.title, result.format, result.size, result.mirrors)
        self.queue.put(job)
        self.job_queued.emit(job)

    def queue_size(self) -> int:
        return self.queue.qsize() + (1 if self.has_jobs else 0)

    def download(self, job: Job) -> str | None:
        Log.info(f"Downloading {job.title}")

        for url in job.mirrors:
            job.status = "Starting"
            self.status_changed.emit(job)

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
                    urls = [doc.select_one("div#download h2 a")["href"]]
                    mirrors = doc.select("ul > li > a")
                    for mirror in mirrors:
                        urls.append(mirror["href"])
                else:
                    relative_url = doc.select_one("a:contains('GET')")["href"]
                    domain = url.split("/")[2]
                    urls = [f"https://{domain}/{relative_url}"]

                for download_url in urls:
                    Log.info(f"Downloading from {download_url}")

                    try:
                        extension = job.format.lower()
                        res = requests.get(download_url, stream=True, timeout=30)
                        if res.status_code != 200:
                            Log.info(f"Error: {res.status_code}")
                            continue

                        total_length = int(res.headers.get('content-length', 0))
                        if total_length == 0:
                            Log.info("Error: 0 content length")
                            continue

                        Log.info(f"Downloading {total_length} bytes")

                        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{extension}") as temp_file:
                            temp_path = temp_file.name
                            downloaded = 0
                            for data in res.iter_content(chunk_size=8192):
                                if data:
                                    temp_file.write(data)
                                    downloaded += len(data)
                                    percentage = int((downloaded / total_length) * 100)
                                    job.status = f"{percentage}%"
                                    self.status_changed.emit(job)

                        Log.info(f"Downloaded {job.title}")
                        job.status = "Success"
                        self.status_changed.emit(job)
                        return temp_path
                    except Exception as e:
                        Log.info(f"Error downloading from mirror: {e}")
                        continue
            except Exception as e:
                Log.info(f"Error downloading {job.title}: {e}")
                continue

        Log.info(f"Failed to download {job.title}")
        job.status = "Error"
        self.status_changed.emit(job)
        return None
