from PySide6.QtCore import QThread, Signal

from src.books.core.library import Library
from src.books.core.log import Log
from src.books.core.models.book import Book


class ImportThread(QThread):
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
