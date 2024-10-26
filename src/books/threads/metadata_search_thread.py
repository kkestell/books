import requests
from PySide6.QtCore import QThread, Signal

from src.books.core.models.metadata_result import MetadataResult


class MetadataSearchThread(QThread):
    """
    Thread for performing a search using the Google Books API.

    :signal search_complete: Emitted when the search is completed, carrying a list of MetadataRecord objects.
    :signal error_occurred: Emitted when an error occurs during the search, carrying an error message string.
    """
    searchComplete = Signal(list)
    errorOccurred = Signal(str)

    def __init__(self, query: str):
        """
        Initialize the SearchThread with the given search query.

        :param query: The search query string.
        :type query: str
        """
        super().__init__()
        self.query = query

    def run(self):
        """
        Execute the search query by making a request to the Google Books API and emit the results.

        If the request fails, the error_occurred signal is emitted with the error message.
        """
        try:
            url = f"https://www.googleapis.com/books/v1/volumes?q={self.query}"
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            results = []
            for item in data.get('items', []):
                volumeInfo = item.get('volumeInfo', {})
                title = volumeInfo.get('title', 'Unknown Title')
                authors = volumeInfo.get('authors', ['Unknown Author'])
                author = authors[0] if authors else 'Unknown Author'
                published = volumeInfo.get('publishedDate', 'Unknown')
                description = volumeInfo.get('description', 'No description available')

                result = MetadataResult(
                    title,
                    author,
                    published,
                    description
                )
                results.append(result)

            self.searchComplete.emit(results)
        except requests.RequestException as e:
            self.errorOccurred.emit(str(e))
