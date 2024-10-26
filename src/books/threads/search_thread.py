import html

import requests
from PySide6.QtCore import QThread, Signal
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

from src.books.core.log import Log
from src.books.core.models.search_result import SearchResult


class SearchThread(QThread):
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
