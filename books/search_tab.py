from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                               QComboBox, QPushButton, QHeaderView, QMessageBox)
import asyncio
from qasync import asyncSlot

from constants import ebook_extensions
from search_results_table_model import SearchResultsTableModel
from search_table_view import SearchTableView
from search_thread import search_books


class SearchTab(QWidget):
    def __init__(self, parent, download_worker):
        super().__init__(parent)
        self.download_worker = download_worker
        self.search_task = None

        self.layout = QVBoxLayout(self)
        self.search_layout = QHBoxLayout()
        self.layout.addLayout(self.search_layout)

        self.author_input = QLineEdit()
        self.author_input.setPlaceholderText("Author...")
        self.author_input.returnPressed.connect(self.start_search)
        self.search_layout.addWidget(self.author_input)

        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Title...")
        self.title_input.returnPressed.connect(self.start_search)
        self.search_layout.addWidget(self.title_input)

        self.search_format = QComboBox()
        formats = ["Any Format"] + [ext.upper() for ext in ebook_extensions]
        self.search_format.addItems(formats)
        self.search_layout.addWidget(self.search_format)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.start_search)
        self.search_layout.addWidget(self.search_button)

        self.model_data = []
        self.model = SearchResultsTableModel(self.model_data)
        self.table_view = SearchTableView()
        self.table_view.setModel(self.model)

        author_column = self.model.headers.index("Author")
        title_column = self.model.headers.index("Title")
        series_column = self.model.headers.index("Series")
        mirrors_column = self.model.headers.index("Mirrors")

        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(author_column, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(title_column, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(series_column, QHeaderView.ResizeMode.Stretch)
        self.table_view.setColumnHidden(mirrors_column, True)

        self.table_view.download_requested.connect(self.download_file)
        self.layout.addWidget(self.table_view)

    @asyncSlot()
    async def start_search(self):
        if self.search_task and not self.search_task.done():
            QMessageBox.warning(self, "Search in progress",
                                "A search is already in progress. Please wait for it to finish.")
            return

        author = self.author_input.text()
        title = self.title_input.text()
        fmt = self.search_format.currentText()
        if fmt == "Any Format":
            fmt = ""

        self.set_controls_enabled(False)
        self.model.clear_rows()

        try:
            async for record in search_books(author, title, fmt):
                self.add_record(record)
                await asyncio.sleep(0)  # Let the UI breathe
        except Exception as e:
            self.handle_search_error(str(e))
        finally:
            self.search_complete()

    def set_controls_enabled(self, enabled: bool):
        self.author_input.setEnabled(enabled)
        self.title_input.setEnabled(enabled)
        self.search_format.setEnabled(enabled)
        self.search_button.setEnabled(enabled)

    def add_record(self, record):
        self.model.add_rows([record])
        if any([record.series for record in self.model.records]):
            self.table_view.showColumn(self.model.headers.index("Series"))
        else:
            self.table_view.hideColumn(self.model.headers.index("Series"))

    def search_complete(self):
        self.set_controls_enabled(True)

    def handle_search_error(self, error_message: str):
        QMessageBox.critical(self, "Search Error", f"An error occurred: {error_message}")
        self.set_controls_enabled(True)

    def download_file(self, job):
        self.download_worker.enqueue(job)