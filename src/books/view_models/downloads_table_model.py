from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt


class DownloadsTableModel(QAbstractTableModel):
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
