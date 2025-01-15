from PySide6.QtWidgets import QWidget, QVBoxLayout, QHeaderView

from downloads_table_model import DownloadsTableModel
from downloads_table_view import DownloadsTableView


class DownloadsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.layout = QVBoxLayout(self)

        self.model_data = []
        self.model = DownloadsTableModel(self.model_data)

        self.table_view = DownloadsTableView()
        self.table_view.setModel(self.model)

        title_column = self.model.headers.index("Title")
        mirrors_column = self.model.headers.index("Mirrors")
        id_column = self.model.headers.index("ID")
        status_column = self.model.headers.index("Status")

        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(title_column, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(status_column, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(status_column, 150)
        self.table_view.setColumnHidden(mirrors_column, True)
        self.table_view.setColumnHidden(id_column, True)

        self.layout.addWidget(self.table_view)

    def add_job(self, job):
        self.model.add_rows([job])
        if any([record.series for record in self.model.records]):
            self.table_view.showColumn(self.model.headers.index("Series"))
        else:
            self.table_view.hideColumn(self.model.headers.index("Series"))

    def update_status(self, job):
        self.model.dataChanged.emit(self.model.index(self.model.records.index(job), 0), self.model.index(self.model.records.index(job), len(self.model.headers) - 1))
