import re

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class SearchResultsTableModel(QAbstractTableModel):
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
