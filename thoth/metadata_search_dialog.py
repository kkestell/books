from PySide6.QtCore import Signal, Slot, QModelIndex
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTableView, QMessageBox
import aiohttp
from qasync import asyncSlot

from metadata_result import MetadataResult
from metadata_table_model import MetadataTableModel


async def search_metadata(query: str) -> list[MetadataResult]:
    async with aiohttp.ClientSession() as session:
        url = f"https://www.googleapis.com/books/v1/volumes?q={query}"
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()

            results = []
            for item in data.get('items', []):
                volume_info = item.get('volumeInfo', {})
                title = volume_info.get('title', 'Unknown Title')
                authors = volume_info.get('authors', ['Unknown Author'])
                author = authors[0] if authors else 'Unknown Author'
                published = volume_info.get('publishedDate', 'Unknown')
                description = volume_info.get('description', 'No description available')

                result = MetadataResult(
                    title,
                    author,
                    published,
                    description
                )
                results.append(result)

            return results


class MetadataSearchDialog(QDialog):
    search_completed = Signal(dict)

    def __init__(self, book, parent=None):
        super().__init__(parent)
        self.search_task = None

        self.setWindowTitle("Search Metadata")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setText(f"{book.author} {book.title}".strip())
        search_layout.addWidget(self.search_input)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        self.table_view = QTableView()
        self.table_model = MetadataTableModel([])
        self.table_view.setModel(self.table_model)
        self.table_view.doubleClicked.connect(self.on_row_double_clicked)
        layout.addWidget(self.table_view)

        self.perform_search()

    @asyncSlot()
    async def perform_search(self):
        if self.search_task and not self.search_task.done():
            return

        query = self.search_input.text()
        self.search_button.setEnabled(False)

        try:
            results = await search_metadata(query)
            self.update_table_data(results)
        except Exception as e:
            QMessageBox.critical(self, "Search Error", str(e))
        finally:
            self.search_button.setEnabled(True)

    def update_table_data(self, data: list[MetadataResult]):
        self.table_model.set_records(data)
        for i in range(self.table_model.columnCount()):
            self.table_view.resizeColumnToContents(i)

    def on_row_double_clicked(self, index: QModelIndex):
        row_data = self.table_model.get_row(index.row())
        result = {
            "title": row_data.title,
            "author": row_data.author,
            "published": row_data.published,
            "description": row_data.description
        }
        self.search_completed.emit(result)
        self.accept()