from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QPushButton, QHeaderView, \
    QMessageBox

from books.core.constants import ebookExtensions
from src.books.view_models.search_results_table_model import SearchResultsTableModel
from src.books.views.search_table_view import SearchTableView
from src.books.threads.search_thread import SearchThread


class SearchTab(QWidget):
    """
    Tab widget for searching and downloading books.
    """

    def __init__(self, parent, downloadWorker):
        """
        Initialize the SearchTab with the parent and download worker.

        :param parent: The parent widget.
        :type parent: QWidget
        :param downloadWorker: Worker to handle download jobs.
        :type downloadWorker: DownloadWorker
        """
        super().__init__(parent)

        # Search worker
        self.searchWorker = None

        # Download worker
        self.downloadWorker = downloadWorker

        # Layout
        self.layout = QVBoxLayout(self)

        # Search layout
        self.searchLayout = QHBoxLayout()
        self.layout.addLayout(self.searchLayout)

        # Query inputs
        self.authorInput = QLineEdit()
        self.authorInput.setPlaceholderText("Author...")
        self.authorInput.returnPressed.connect(self.startSearch)
        self.searchLayout.addWidget(self.authorInput)

        self.titleInput = QLineEdit()
        self.titleInput.setPlaceholderText("Title...")
        self.titleInput.returnPressed.connect(self.startSearch)
        self.searchLayout.addWidget(self.titleInput)

        # Format selection
        self.searchFormat = QComboBox()
        formats = ["Any Format"] + [ext.upper() for ext in ebookExtensions]
        self.searchFormat.addItems(formats)
        self.searchLayout.addWidget(self.searchFormat)

        # Search button
        self.searchButton = QPushButton("Search")
        self.searchButton.clicked.connect(self.startSearch)
        self.searchLayout.addWidget(self.searchButton)

        # Table setup
        self.modelData = []
        self.model = SearchResultsTableModel(self.modelData)

        self.tableView = SearchTableView()
        self.tableView.setModel(self.model)

        authorColumn = self.model.headers.index("Author")
        titleColumn = self.model.headers.index("Title")
        seriesColumn = self.model.headers.index("Series")
        mirrorsColumn = self.model.headers.index("Mirrors")

        header = self.tableView.horizontalHeader()
        # header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(authorColumn, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(titleColumn, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(seriesColumn, QHeaderView.ResizeMode.Stretch)
        self.tableView.setColumnHidden(mirrorsColumn, True)

        self.tableView.downloadRequested.connect(self.downloadFile)

        self.layout.addWidget(self.tableView)

    def startSearch(self):
        """
        Start a search based on the user's input.
        """
        if self.searchWorker:
            QMessageBox.warning(self, "Search in progress", "A search is already in progress. Please wait for it to finish before starting another search.")
            return

        author = self.authorInput.text()
        title = self.titleInput.text()

        fmt = self.searchFormat.currentText()
        if fmt == "Any Format":
            fmt = ""

        self.authorInput.setEnabled(False)
        self.searchFormat.setEnabled(False)
        self.searchButton.setEnabled(False)

        self.model.clearRows()

        self.searchWorker = SearchThread(author, title, fmt)
        self.searchWorker.newRecord.connect(self.addRecord)
        self.searchWorker.searchComplete.connect(self.searchComplete)
        self.searchWorker.error.connect(self.handleSearchError)
        self.searchWorker.start()

        print("Search started")

    def addRecord(self, record):
        """
        Add a search result record to the table.

        :param record: The search result record to add.
        :type record: SearchResult
        """
        self.model.addRows([record])
        # If any records have a series, show the series column; otherwise hide it
        if any([record.series for record in self.model.records]):
            self.tableView.showColumn(self.model.headers.index("Series"))
        else:
            self.tableView.hideColumn(self.model.headers.index("Series"))

    def searchComplete(self):
        """
        Handle the completion of a search.
        """
        self.authorInput.setEnabled(True)
        self.searchFormat.setEnabled(True)
        self.searchButton.setEnabled(True)
        self.searchWorker = None

    def handleSearchError(self, error_message: str):
        """
        Handle an error that occurred during the search.

        :param error_message: The error message.
        :type error_message: str
        """
        QMessageBox.critical(self, "Search Error", f"An error occurred: {error_message}")
        self.authorInput.setEnabled(True)
        self.searchFormat.setEnabled(True)
        self.searchButton.setEnabled(True)
        self.searchWorker = None

    def downloadFile(self, job):
        """
        Enqueue a download job for the selected book.

        :param job: The download job to enqueue.
        :type job: DownloadJob
        """
        self.downloadWorker.enqueue(job)
