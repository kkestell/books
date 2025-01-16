from PySide6.QtCore import QThread, Signal

from book import Book


class ConversionThread(QThread):
    conversion_started = Signal()
    conversion_success = Signal(Book)
    conversion_error = Signal(Book)
    conversion_finished = Signal()

    def __init__(self, kindle, books):
        super().__init__()
        self.kindle = kindle
        self.books = books

    def run(self):
        self.conversion_started.emit()

        for book in self.books:
            if not self.convert(book):
                self.conversion_error.emit(book)
            else:
                self.conversion_success.emit(book)

        self.conversion_finished.emit()

    def convert(self, book) -> bool:
        try:
            self.kindle.send_to_device(book)
            return True
        except Exception as e:
            print(e)
            return False
