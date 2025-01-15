from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class DownloadsTableModel(QAbstractTableModel):
    def __init__(self, data):
        super().__init__()
        self.headers = ["Author", "Title", "Series", "Format", "Size", "Mirrors", "Status", "ID"]
        self.records = data

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self.records)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.headers)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self.records)):
            return None
        column = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            return getattr(self.records[index.row()], self.headers[column].lower())
        if role == Qt.ItemDataRole.TextAlignmentRole and column == self.headers.index("Status"):
            return Qt.AlignmentFlag.AlignCenter

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

    def get_row(self, index: int):
        return self.records[index]

    def clear_completed(self):
        self.beginResetModel()
        self.records = [record for record in self.records if record.status != "Success" and record.status != "Error"]
        self.endResetModel()
