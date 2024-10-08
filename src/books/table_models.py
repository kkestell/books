import re
from datetime import datetime

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QSortFilterProxyModel


class DownloadsModel(QAbstractTableModel):
    """
    Model to handle the data for download jobs.
    """

    def __init__(self, data):
        """
        Initialize the DownloadsModel with data.

        :param data: List of download records.
        :type data: list
        """
        super().__init__()
        self.headers = ["Author", "Title", "Series", "Format", "Size", "Mirrors", "Status", "ID"]
        self.records = data

    def rowCount(self, parent=QModelIndex()) -> int:
        """
        Get the number of rows in the model.

        :param parent: The parent index.
        :type parent: QModelIndex
        :return: Number of rows.
        :rtype: int
        """
        return len(self.records)

    def columnCount(self, parent=QModelIndex()) -> int:
        """
        Get the number of columns in the model.

        :param parent: The parent index.
        :type parent: QModelIndex
        :return: Number of columns.
        :rtype: int
        """
        return len(self.headers)

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
        if not index.isValid() or not (0 <= index.row() < len(self.records)):
            return None
        column = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            return getattr(self.records[index.row()], self.headers[column].lower())
        if role == Qt.ItemDataRole.TextAlignmentRole and column == self.headers.index("Status"):
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
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]

    def clearRows(self):
        """
        Clear all rows from the model.
        """
        self.beginResetModel()
        self.records = []
        self.endResetModel()

    def addRows(self, newRows):
        """
        Add new rows to the model.

        :param newRows: List of new records to add.
        :type newRows: list
        """
        self.beginInsertRows(QModelIndex(), len(self.records), len(self.records) + len(newRows) - 1)
        self.records.extend(newRows)
        self.endInsertRows()

    def getRow(self, index: int):
        """
        Retrieve a specific row from the model.

        :param index: Index of the row to retrieve.
        :type index: int
        :return: The record at the specified index.
        :rtype: Any
        """
        return self.records[index]

    def clearCompleted(self):
        """
        Clear all completed download jobs from the model.
        """
        self.beginResetModel()
        self.records = [record for record in self.records if record.status != "Success" and record.status != "Error"]
        self.endResetModel()


class SearchResultsModel(QAbstractTableModel):
    """
    Model to handle the data for search results.
    """

    def __init__(self, data):
        """
        Initialize the SearchResultsModel with data.

        :param data: List of search result records.
        :type data: list
        """
        super().__init__()
        self.headers = ["Author", "Title", "Series", "Format", "Size", "Score", "Mirrors"]
        self.records = data

    def rowCount(self, parent=QModelIndex()) -> int:
        """
        Get the number of rows in the model.

        :param parent: The parent index.
        :type parent: QModelIndex
        :return: Number of rows.
        :rtype: int
        """
        return len(self.records)

    def columnCount(self, parent=QModelIndex()) -> int:
        """
        Get the number of columns in the model.

        :param parent: The parent index.
        :type parent: QModelIndex
        :return: Number of columns.
        :rtype: int
        """
        return len(self.headers)

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
        if not index.isValid() or not (0 <= index.row() < len(self.records)):
            return None
        book = self.records[index.row()]
        column = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            return getattr(book, self.headers[column].lower())

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
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]

    def clearRows(self):
        """
        Clear all rows from the model.
        """
        self.beginResetModel()
        self.records = []
        self.endResetModel()

    def addRows(self, newRows):
        """
        Add new rows to the model.

        :param newRows: List of new records to add.
        :type newRows: list
        """
        self.beginInsertRows(QModelIndex(), len(self.records), len(self.records) + len(newRows) - 1)
        self.records.extend(newRows)
        self.endInsertRows()

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):
        """
        Sort the model's data by a specific column.

        :param column: The column index to sort by.
        :type column: int
        :param order: The sort order (ascending or descending).
        :type order: Qt.SortOrder
        """
        self.layoutAboutToBeChanged.emit()
        if self.headers[column].lower() == 'size':
            self.records.sort(key=lambda x: self.convertSizeToBytes(getattr(x, 'size')), reverse=order == Qt.SortOrder.DescendingOrder)
        else:
            self.records.sort(key=lambda x: getattr(x, self.headers[column].lower()), reverse=order == Qt.SortOrder.DescendingOrder)
        self.layoutChanged.emit()

    @staticmethod
    def convertSizeToBytes(size_str: str) -> float:
        """
        Convert a human-readable size string to bytes.

        :param size_str: The size string to convert (e.g., "10 MB").
        :type size_str: str
        :return: The size in bytes.
        :rtype: float
        """
        units = {'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
        size_regex = re.compile(r"(\d+(?:\.\d+)?)(\s*?)(KB|MB|GB|TB)")
        match = size_regex.match(size_str)
        if match:
            value, _, unit = match.groups()
            return float(value) * units[unit]
        return 0

    def getRow(self, index: int):
        """
        Retrieve a specific row from the model.

        :param index: Index of the row to retrieve.
        :type index: int
        :return: The record at the specified index.
        :rtype: Any
        """
        return self.records[index]


class LibraryModel(QAbstractTableModel):
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
        self.headers = ["On Device", "Author", "Title", "Series", "Published", "Type", "Format", "Added", "ID"]
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
                return book.published
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


class MultiColumnSortProxyModel(QSortFilterProxyModel):
    """
    Proxy model for multi-column sorting and filtering.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.titleFilterPattern = ''
        self.authorFilterPattern = ''
        self.seriesFilterPattern = ''
        self.typeFilter = None  # None means no filtering

    def setTitleFilterPattern(self, pattern):
        self.titleFilterPattern = pattern
        self.invalidateFilter()

    def setAuthorFilterPattern(self, pattern):
        self.authorFilterPattern = pattern
        self.invalidateFilter()

    def setSeriesFilterPattern(self, pattern):
        self.seriesFilterPattern = pattern
        self.invalidateFilter()

    def setTypeFilter(self, type_value):
        self.typeFilter = type_value
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()

        if not isinstance(model, LibraryModel):
            return super().filterAcceptsRow(source_row, source_parent)

        # Filter based on title, author, series, and type
        index_title = model.index(source_row, model.headers.index("Title"), source_parent)
        index_author = model.index(source_row, model.headers.index("Author"), source_parent)
        index_series = model.index(source_row, model.headers.index("Series"), source_parent)
        index_type = model.index(source_row, model.headers.index("Type"), source_parent)

        data_title = model.data(index_title, Qt.ItemDataRole.DisplayRole) or ''
        data_author = model.data(index_author, Qt.ItemDataRole.DisplayRole) or ''
        data_series = model.data(index_series, Qt.ItemDataRole.DisplayRole) or ''
        data_type = model.data(index_type, Qt.ItemDataRole.DisplayRole) or ''

        # Case-insensitive matching
        if self.titleFilterPattern and self.titleFilterPattern.lower() not in data_title.lower():
            return False

        if self.authorFilterPattern and self.authorFilterPattern.lower() not in data_author.lower():
            return False

        if self.seriesFilterPattern and self.seriesFilterPattern.lower() not in data_series.lower():
            return False

        if self.typeFilter and self.typeFilter != data_type:
            return False

        return True

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        """
        Compare two items for sorting.

        :param left: The left index to compare.
        :type left: QModelIndex
        :param right: The right index to compare.
        :type right: QModelIndex
        :return: True if left is less than right, False otherwise.
        :rtype: bool
        """
        model = self.sourceModel()

        if not isinstance(model, LibraryModel):
            return super().lessThan(left, right)

        authorIndex = model.headers.index("Author")
        seriesIndex = model.headers.index("Series")
        titleIndex = model.headers.index("Title")
        publishedIndex = model.headers.index("Published")

        if self.sortColumn() == authorIndex:
            leftAuthor = model.data(left.siblingAtColumn(authorIndex), Qt.ItemDataRole.DisplayRole).lower()
            rightAuthor = model.data(right.siblingAtColumn(authorIndex), Qt.ItemDataRole.DisplayRole).lower()

            leftSeries = model.data(left.siblingAtColumn(seriesIndex), Qt.ItemDataRole.DisplayRole) or ''
            leftSeries = leftSeries.lower()

            rightSeries = model.data(right.siblingAtColumn(seriesIndex), Qt.ItemDataRole.DisplayRole) or ''
            rightSeries = rightSeries.lower()

            leftTitle = model.data(left.siblingAtColumn(titleIndex), Qt.ItemDataRole.DisplayRole).lower()
            rightTitle = model.data(right.siblingAtColumn(titleIndex), Qt.ItemDataRole.DisplayRole).lower()

            if leftAuthor != rightAuthor:
                return leftAuthor < rightAuthor
            elif leftSeries != rightSeries:
                return leftSeries < rightSeries
            return leftTitle < rightTitle
        elif self.sortColumn() == publishedIndex:
            leftDate = model.data(left.siblingAtColumn(publishedIndex), Qt.ItemDataRole.DisplayRole)
            rightDate = model.data(right.siblingAtColumn(publishedIndex), Qt.ItemDataRole.DisplayRole)

            try:
                leftDateParsed = datetime.strptime(leftDate, "%Y-%m-%d")
            except (ValueError, TypeError):
                leftDateParsed = datetime.min

            try:
                rightDateParsed = datetime.strptime(rightDate, "%Y-%m-%d")
            except (ValueError, TypeError):
                rightDateParsed = datetime.min

            return leftDateParsed < rightDateParsed
        else:
            return super().lessThan(left, right)