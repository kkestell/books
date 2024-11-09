from PySide6.QtCore import Signal, Slot, QModelIndex
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QTableView

from src.books.core.models.metadata_result import MetadataResult
from src.books.threads.metadata_search_thread import MetadataSearchThread
from src.books.view_models.metadata_table_model import MetadataTableModel


class MetadataSearchDialog(QDialog):
    """
    Dialog window for searching book metadata via the Google Books API.

    :signal search_completed: Emitted when a search is completed, carrying a dictionary of selected metadata.
    """
    searchCompleted = Signal(dict)

    def __init__(self, book, parent=None):
        """
        Initialize the SearchMetadataDialog with the given book object.

        :param book: The book object used to pre-fill the search query.
        :type book: Book
        :param parent: The parent widget.
        :type parent: QWidget, optional
        """
        super().__init__(parent)

        self.searchThread = None

        self.setWindowTitle("Search Metadata")
        self.setMinimumSize(600, 400)

        layout = QVBoxLayout(self)

        # Add search query input and button
        searchLayout = QHBoxLayout()
        self.searchInput = QLineEdit()
        self.searchInput.setText(f"{book.author} {book.title}".strip())
        searchLayout.addWidget(self.searchInput)
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.performSearch)
        searchLayout.addWidget(self.search_button)
        layout.addLayout(searchLayout)

        # Create and set up the table view
        self.tableView = QTableView()
        self.tableModel = MetadataTableModel([])
        self.tableView.setModel(self.tableModel)
        self.tableView.doubleClicked.connect(self.onRowDoubleClicked)
        layout.addWidget(self.tableView)

        # Automatically search when the dialog is opened
        self.performSearch()

    def performSearch(self):
        """
        Perform a search using the query entered in the search input field.
        """
        query = self.searchInput.text()
        self.searchThread = MetadataSearchThread(query)
        self.searchThread.searchComplete.connect(self.updateTableData)
        self.searchThread.start()

    @Slot(list)
    def updateTableData(self, data: list[MetadataResult]):
        """
        Update the table view with new search results.

        :param data: A list of MetadataRecord objects representing search results.
        :type data: list[MetadataResult]
        """
        self.tableModel.setRecords(data)
        for i in range(self.tableModel.columnCount()):
            self.tableView.resizeColumnToContents(i)

    def onRowDoubleClicked(self, index: QModelIndex):
        """
        Handle the event when a row in the table view is double-clicked.

        :param index: The index of the double-clicked row.
        :type index: QModelIndex
        """
        rowData = self.tableModel.getRow(index.row())
        result = {
            "title": rowData.title,
            "author": rowData.author,
            "published": rowData.published,
            "description": rowData.description
        }
        self.searchCompleted.emit(result)
        self.accept()
