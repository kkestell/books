from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex


class LogTableModel(QAbstractTableModel):
    def __init__(self, log_entries=None):
        super().__init__()
        self.log_entries = log_entries or []
        self.headers = ["Timestamp", "Level", "Message"]

    def rowCount(self, parent=None):
        return len(self.log_entries)

    def columnCount(self, parent=None):
        return 3

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole:
            entry = self.log_entries[index.row()]
            if index.column() == 0:
                return entry.timestamp
            elif index.column() == 1:
                return entry.level
            elif index.column() == 2:
                return entry.message
        return None

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.headers[section]
        return None

    def appendLogEntry(self, entry):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self.log_entries.append(entry)
        self.endInsertRows()
