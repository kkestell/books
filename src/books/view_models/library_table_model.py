from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class LibraryTableModel(QAbstractTableModel):
    """
    Model to handle the data for a library of books.
    """

    def __init__(self, library):
        """
        Initialize the LibraryModel with the library object.

        :param library: The library containing the books.
        :type library: Library
        """
        super().__init__()
        self.library = library
        self.headers = ["On Device", "Author", "Title", "Series", "Year", "Type", "Format", "Added", "ID"]
        self.kindleBooks = []

    def rowCount(self, parent=QModelIndex()) -> int:
        """
        Get the number of rows in the model.

        :param parent: The parent index.
        :type parent: QModelIndex
        :return: Number of rows.
        :rtype: int
        """
        return self.library.numBooks

    def columnCount(self, parent=QModelIndex()) -> int:
        """
        Get the number of columns in the model.

        :param parent: The parent index.
        :type parent: QModelIndex
        :return: Number of columns.
        :rtype: int
        """
        return 9

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        """
        Retrieve the data for a given index and role.

        :param index: The index to get data from.
        :type index: QModelIndex
        :param role: The role of the data.
        :type role: Qt.ItemDataRole
        :return: The data for the given index and role.
        :rtype: Any
        """
        if role == Qt.ItemDataRole.DisplayRole:
            if not index.isValid() or not (0 <= index.row() < self.library.numBooks):
                return None
            book = self.library.books[index.row()]
            column = index.column()
            if column == 0:
                if book.title in [kindleBook.title for kindleBook in self.kindleBooks]:
                    return "✓"
                return ""
            elif column == 1:
                return book.author
            elif column == 2:
                return book.title
            elif column == 3:
                if book.seriesNumber:
                    return f"{book.series} #{book.seriesNumber}"
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
        """
        Get the header data for a given section, orientation, and role.

        :param section: The section of the header.
        :type section: int
        :param orientation: The orientation of the header (horizontal/vertical).
        :type orientation: Qt.Orientation
        :param role: The role of the header data.
        :type role: Qt.ItemDataRole
        :return: The header data.
        :rtype: str
        """
        if section == 0:
            return None
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]

    def setKindleBooks(self, books: list):
        """
        Set the list of books on the connected Kindle device.

        :param books: The list of books on the Kindle.
        :type books: list
        """
        self.kindleBooks = books

    def newBookOnDevice(self, book):
        """
        Add a new book to the list of books on the Kindle device.

        :param book: The book to add.
        :type book: Book
        """
        if book not in self.kindleBooks:
            self.kindleBooks.append(book)
