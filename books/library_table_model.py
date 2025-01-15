from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from book import Book


class LibraryTableModel(QAbstractTableModel):
    def __init__(self, library):
        super().__init__()
        self.library = library
        self.headers = ["On Device", "Author", "Title", "Series", "Year", "Type", "Format", "Added", "ID"]
        self.kindle_books = []
        self.all_books = self.library.get_all_books()

    def rowCount(self, parent=QModelIndex()) -> int:
        return self.library.num_books

    def columnCount(self, parent=QModelIndex()) -> int:
        return 9

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            if not index.isValid() or not (0 <= index.row() < self.library.num_books):
                return None
            book = self.all_books[index.row()]
            column = index.column()
            if column == 0:
                if book.title in [kindle_book.title for kindle_book in self.kindle_books]:
                    return "✓"
                return ""
            elif column == 1:
                return book.author
            elif column == 2:
                return book.title
            elif column == 3:
                if book.series_number:
                    return f"{book.series} #{book.series_number}"
                return book.series
            elif column == 4:
                if book.published:
                    return book.published.split('-')[0]
            elif column == 5:
                return book.type
            elif column == 6:
                return book.format
            elif column == 7:
                return book.added
            elif column == 8:
                return str(book.id)
        if role == Qt.ItemDataRole.TextAlignmentRole and index.column() == 0:
            return Qt.AlignmentFlag.AlignCenter

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        if section == 0:
            return None
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]

    def set_kindle_books(self, books: list):
        self.kindle_books = books

    def new_book_on_device(self, book):
        if book not in self.kindle_books:
            self.kindle_books.append(book)

    def refresh_books(self):
        self.all_books = self.library.get_all_books()
        self.layoutChanged.emit()

    def update_book(self, updated_book: Book):
        row = next(i for i, book in enumerate(self.all_books) if book.id == updated_book.id)
        self.all_books[row] = updated_book
        self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount() - 1))