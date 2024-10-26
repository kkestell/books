from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from src.books.core.models.metadata_result import MetadataResult


class MetadataTableModel(QAbstractTableModel):
    """
    Model to handle the data for metadata search results.
    """

    def __init__(self, data: list[MetadataResult]):
        """
        Initialize the MetadataTableModel with data.

        :param data: List of metadata results.
        :type data: list[MetadataResult]
        """
        super().__init__()
        self.headers = ["Title", "Author", "Published", "Description"]
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
            return getattr(self.records[index.row()], self.headers[column].lower().replace(" ", "_"))
        if role == Qt.ItemDataRole.TextAlignmentRole:
            return Qt.AlignmentFlag.AlignLeft

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

    def setData(self, newData: list[MetadataResult]):
        """
        Set new data for the model.

        :param newData: List of new records to set.
        :type newData: list[MetadataResult]
        """
        self.beginResetModel()
        self.records = newData
        self.endResetModel()

    def getRow(self, index: int) -> MetadataResult:
        """
        Retrieve a specific row from the model.

        :param index: Index of the row to retrieve.
        :type index: int
        :return: The record at the specified index.
        :rtype: MetadataResult
        """
        return self.records[index]
