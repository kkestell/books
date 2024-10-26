from PySide6.QtWidgets import QWidget, QVBoxLayout, QHeaderView

from src.books.view_models.downloads_table_model import DownloadsTableModel
from src.books.views.downloads_table_view import DownloadsTableView


class DownloadsTab(QWidget):
    """
    Tab widget for managing download jobs.
    """

    def __init__(self, parent=None):
        """
        Initialize the DownloadsTab.

        :param parent: The parent widget.
        :type parent: QWidget, optional
        """
        super().__init__(parent)

        # Layout
        self.layout = QVBoxLayout(self)

        # Table setup
        self.modelData = []
        self.model = DownloadsTableModel(self.modelData)

        self.tableView = DownloadsTableView()
        self.tableView.setModel(self.model)

        titleColumn = self.model.headers.index("Title")
        mirrorsColumn = self.model.headers.index("Mirrors")
        idColumn = self.model.headers.index("ID")
        statusColumn = self.model.headers.index("Status")

        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(titleColumn, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(statusColumn, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(statusColumn, 150)
        self.tableView.setColumnHidden(mirrorsColumn, True)
        self.tableView.setColumnHidden(idColumn, True)

        self.layout.addWidget(self.tableView)

    def addJob(self, job):
        """
        Add a download job to the table.

        :param job: The download job to add.
        :type job: DownloadJob
        """
        self.model.addRows([job])
        if any([record.series for record in self.model.records]):
            self.tableView.showColumn(self.model.headers.index("Series"))
        else:
            self.tableView.hideColumn(self.model.headers.index("Series"))

    def updateStatus(self, job):
        """
        Update the status of a download job in the table.

        :param job: The download job to update.
        :type job: DownloadJob
        """
        self.model.dataChanged.emit(self.model.index(self.model.records.index(job), 0), self.model.index(self.model.records.index(job), len(self.model.headers) - 1))
