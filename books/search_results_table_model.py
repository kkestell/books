import re

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class SearchResultsTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self.headers = ["Author", "Title", "Series", "Format", "Size", "Score", "Mirrors"]
        self.records = data

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.records)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.headers)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.records)):
            return None
        book = self.records[index.row()]
        column = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            return getattr(book, self.headers[column].lower())

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]

    def clear_rows(self):
        self.beginResetModel()
        self.records = []
        self.endResetModel()

    def add_rows(self, new_rows):
        self.beginInsertRows(QModelIndex(), len(self.records), len(self.records) + len(new_rows) - 1)
        self.records.extend(new_rows)
        self.endInsertRows()

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder):
        self.layoutAboutToBeChanged.emit()
        if self.headers[column].lower() == 'size':
            self.records.sort(key=lambda x: self.convert_size_to_bytes(getattr(x, 'size')), reverse=order == Qt.SortOrder.DescendingOrder)
        else:
            self.records.sort(key=lambda x: getattr(x, self.headers[column].lower()), reverse=order == Qt.SortOrder.DescendingOrder)
        self.layoutChanged.emit()

    def get_row(self, index: int):
        return self.records[index]

    @staticmethod
    def convert_size_to_bytes(size_str: str) -> float:
        units = {'KB': 1024, 'MB': 1024**2, 'GB': 1024**3, 'TB': 1024**4}
        size_regex = re.compile(r"(\d+(?:\.\d+)?)(\s*?)(KB|MB|GB|TB)")
        match = size_regex.match(size_str)
        if match:
            value, _, unit = match.groups()
            return float(value) * units[unit]
        return 0