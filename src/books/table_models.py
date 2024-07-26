import re

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, QSortFilterProxyModel


class DownloadsModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self.headers = ["Author", "Title", "Series", "Format", "Size", "Mirrors", "Status", "ID"]
        self.records = data
    
    def rowCount(self, parent=QModelIndex()):
        return len(self.records)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)
    
    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.records)):
            return None
        column = index.column()
        if role == Qt.DisplayRole:
            return getattr(self.records[index.row()], self.headers[column].lower())
        if role == Qt.TextAlignmentRole and column == self.headers.index("Status"):
            return Qt.AlignCenter
    
    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]

    def clearRows(self):
        self.beginResetModel()
        self.records = []
        self.endResetModel()

    def addRows(self, newRows):
        self.beginInsertRows(QModelIndex(), len(self.records), len(self.records) + len(newRows) - 1)
        self.records.extend(newRows)
        self.endInsertRows()

    def getRow(self, index):
        return self.records[index]

    def clearCompleted(self):
        self.beginResetModel()
        self.records = [record for record in self.records if record.status != "Success" and record.status != "Error"]
        self.endResetModel()


class SearchResultsModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self.headers = ["Author", "Title", "Series", "Format", "Size", "Mirrors"]
        self.records = data

    def rowCount(self, parent=QModelIndex()):
        return len(self.records)

    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.records)):
            return None
        book = self.records[index.row()]
        column = index.column()
        if role == Qt.DisplayRole:
            return getattr(book, self.headers[column].lower())

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]

    def clearRows(self):
        self.beginResetModel()
        self.records = []
        self.endResetModel()

    def addRows(self, newRows):
        self.beginInsertRows(QModelIndex(), len(self.records), len(self.records) + len(newRows) - 1)
        self.records.extend(newRows)
        self.endInsertRows()

    def sort(self, column, order):
        self.layoutAboutToBeChanged.emit()
        if self.headers[column].lower() == 'size':
            self.records.sort(key=lambda x: self.convertSizeToBytes(getattr(x, 'size')), reverse=order == Qt.DescendingOrder)
        else:
            self.records.sort(key=lambda x: getattr(x, self.headers[column].lower()), reverse=order == Qt.DescendingOrder)
        self.layoutChanged.emit()

    def convertSizeToBytes(self, size_str):
        units = {'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
        size_regex = re.compile(r"(\d+(?:\.\d+)?)(\s*?)(KB|MB|GB|TB)")
        match = size_regex.match(size_str)
        if match:
            value, _, unit = match.groups()
            return float(value) * units[unit]
        return 0

    def getRow(self, index):
        return self.records[index]


class LibraryModel(QAbstractTableModel):
    def __init__(self, library):
        super().__init__()
        self.library = library
        self.headers = ["On Device", "Author", "Title", "Series", "Published", "Type", "Format", "Added", "ID"]
        self.kindleBooks = []

    def rowCount(self, parent=QModelIndex()):
        return self.library.numBooks

    def columnCount(self, parent=QModelIndex()):
        return 9

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.DisplayRole:
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
        if role == Qt.TextAlignmentRole and index.column() == 0:
            return Qt.AlignCenter

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if section == 0:
            return None
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]

    def setKindleBooks(self, books):
        self.kindleBooks = books

    def newBookOnDevice(self, book):
        if book not in self.kindleBooks:
            self.kindleBooks.append(book)


class MultiColumnSortProxyModel(QSortFilterProxyModel):
    def lessThan(self, left, right):
        model = self.sourceModel()

        authorIndex = model.headers.index("Author")
        seriesNumber = model.headers.index("Series")
        titleIndex = model.headers.index("Title")
        publishedIndex = model.headers.index("Published")

        if self.sortColumn() == authorIndex:
            leftAuthor = model.data(left.siblingAtColumn(authorIndex), Qt.DisplayRole).lower()
            rightAuthor = model.data(right.siblingAtColumn(authorIndex), Qt.DisplayRole).lower()

            leftSeries = model.data(left.siblingAtColumn(seriesNumber), Qt.DisplayRole)
            if leftSeries:
                leftSeries = leftSeries.lower()
            else:
                leftSeries = ""

            rightSeries = model.data(right.siblingAtColumn(seriesNumber), Qt.DisplayRole)
            if rightSeries:
                rightSeries = rightSeries.lower()
            else:
                rightSeries = ""

            leftTitle = model.data(left.siblingAtColumn(titleIndex), Qt.DisplayRole).lower()
            rightTitle = model.data(right.siblingAtColumn(titleIndex), Qt.DisplayRole).lower()

            if leftAuthor != rightAuthor:
                return leftAuthor < rightAuthor
            elif leftSeries != rightSeries:
                return leftSeries < rightSeries
            return leftTitle < rightTitle
        elif self.sortColumn() == publishedIndex:
            leftYear = model.data(left.siblingAtColumn(publishedIndex), Qt.DisplayRole)
            try:
                leftYear = int(leftYear)
            except:
                leftYear = 0
            rightYear = model.data(right.siblingAtColumn(publishedIndex), Qt.DisplayRole)
            try:
                rightYear = int(rightYear)
            except:
                rightYear = 0
            return leftYear < rightYear
        else:
            return super().lessThan(left, right)
