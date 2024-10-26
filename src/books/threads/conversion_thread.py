from PySide6.QtCore import QThread, Signal

from src.books.core.models.book import Book


class ConversionThread(QThread):
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
