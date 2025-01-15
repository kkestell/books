from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from metadata_result import MetadataResult


class MetadataTableModel(QAbstractTableModel):
    def __init__(self, data: list[MetadataResult]):
        super().__init__()
        self.headers = ["Title", "Author", "Published", "Description"]
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
            return getattr(self.records[index.row()], self.headers[column].lower().replace(" ", "_"))
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignLeft

    def headerData(self, section: int, orientation: Qt.Orientation, role=Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.headers[section]

    def clear_rows(self):
        self.beginResetModel()
        self.records = []
        self.endResetModel()

    def set_records(self, new_data: list[MetadataResult]):
        self.beginResetModel()
        self.records = new_data
        self.endResetModel()

    def get_row(self, index: int) -> MetadataResult:
        return self.records[index]
