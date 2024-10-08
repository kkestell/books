from PySide6.QtCore import Qt, Signal, QStringListModel
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHeaderView, QHBoxLayout, QLineEdit, QPushButton, QComboBox, \
    QMessageBox, QCompleter, QLabel

from custom_widgets import LibraryTableView, SearchTableView, DownloadsTableView
from models import Book
from table_models import LibraryModel, MultiColumnSortProxyModel, SearchResultsModel, DownloadsModel
from workers import SearchWorker


class LibraryTab(QWidget):
    """
    Tab widget for displaying and managing the library of books.

    :signal bookRemoved: Emitted when a book is removed from the library.
    :signal sendToDeviceRequested: Emitted when books are requested to be sent to a device.
    """
    bookRemoved = Signal(Book)
    sendToDeviceRequested = Signal(object)

    def __init__(self, library, kindle, parent=None):
        """
        Initialize the LibraryTab with the library and Kindle.

        :param library: The library of books to be managed.
        :type library: Library
        :param kindle: The Kindle device for syncing books.
        :type kindle: Kindle
        :param parent: The parent widget.
        :type parent: QWidget, optional
        """
        super().__init__(parent)

        self.kindle = kindle

        # Layout
        self.layout = QVBoxLayout(self)

        # Filter controls
        filterLayout = QHBoxLayout()

        self.titleFilterEdit = QLineEdit()
        self.titleFilterEdit.setPlaceholderText("Filter by Title")
        self.authorFilterEdit = QLineEdit()
        self.authorFilterEdit.setPlaceholderText("Filter by Author")
        self.seriesFilterEdit = QLineEdit()
        self.seriesFilterEdit.setPlaceholderText("Filter by Series")
        self.typeFilterComboBox = QComboBox()
        self.typeFilterComboBox.addItem("All")  # Add 'All' option for no filtering

        # Get unique titles, authors, series, and types
        titles = sorted(set(book.title for book in library.books))
        authors = sorted(set(book.author for book in library.books))
        series_list = sorted(set(book.series for book in library.books if book.series))
        types = sorted(set(book.type for book in library.books if book.type))

        self.titleCompleterModel = QStringListModel(titles)
        self.titleCompleter = QCompleter(self.titleCompleterModel)
        self.titleCompleter.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.titleFilterEdit.setCompleter(self.titleCompleter)

        self.authorCompleterModel = QStringListModel(authors)
        self.authorCompleter = QCompleter(self.authorCompleterModel)
        self.authorCompleter.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.authorFilterEdit.setCompleter(self.authorCompleter)

        self.seriesCompleterModel = QStringListModel(series_list)
        self.seriesCompleter = QCompleter(self.seriesCompleterModel)
        self.seriesCompleter.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.seriesFilterEdit.setCompleter(self.seriesCompleter)

        # Populate type combo box
        self.typeFilterComboBox.addItems(types)

        filterLayout.addWidget(QLabel("Title:"))
        filterLayout.addWidget(self.titleFilterEdit)
        filterLayout.addWidget(QLabel("Author:"))
        filterLayout.addWidget(self.authorFilterEdit)
        filterLayout.addWidget(QLabel("Series:"))
        filterLayout.addWidget(self.seriesFilterEdit)
        filterLayout.addWidget(QLabel("Type:"))
        filterLayout.addWidget(self.typeFilterComboBox)

        self.layout.addLayout(filterLayout)

        # Table setup
        self.library = library
        self.library.bookRemoved.connect(self.refreshTable)
        self.library.bookRemoved.connect(self.bookRemoved)

        self.model = LibraryModel(self.library)
        self.proxyModel = MultiColumnSortProxyModel()
        self.proxyModel.setSourceModel(self.model)
        self.proxyModel.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxyModel.setSortRole(Qt.ItemDataRole.DisplayRole)

        self.tableView = LibraryTableView(self)
        self.tableView.setModel(self.proxyModel)

        authorColumn = self.model.headers.index("Author")
        titleColumn = self.model.headers.index("Title")
        idColumn = self.model.headers.index("ID")
        onDeviceColumn = self.model.headers.index("On Device")

        self.proxyModel.sort(authorColumn, Qt.SortOrder.AscendingOrder)

        header = self.tableView.horizontalHeader()
        # header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(titleColumn, QHeaderView.ResizeMode.Stretch)
        self.tableView.setColumnHidden(idColumn, True)
        self.tableView.setColumnHidden(onDeviceColumn, True)
        self.tableView.setColumnWidth(onDeviceColumn, 26)
        self.tableView.resizeColumnsToContents()

        self.tableView.sendToDeviceRequested.connect(self.sendToDevice)

        self.layout.addWidget(self.tableView)

        # Connect filter inputs to proxy model
        self.titleFilterEdit.textChanged.connect(self.onTitleFilterChanged)
        self.authorFilterEdit.textChanged.connect(self.onAuthorFilterChanged)
        self.seriesFilterEdit.textChanged.connect(self.onSeriesFilterChanged)
        self.typeFilterComboBox.currentIndexChanged.connect(self.onTypeFilterChanged)

    def onTitleFilterChanged(self, text):
        self.proxyModel.setTitleFilterPattern(text)

    def onAuthorFilterChanged(self, text):
        self.proxyModel.setAuthorFilterPattern(text)

    def onSeriesFilterChanged(self, text):
        self.proxyModel.setSeriesFilterPattern(text)

    def onTypeFilterChanged(self, index):
        selected_type = self.typeFilterComboBox.currentText()
        if selected_type == "All":
            self.proxyModel.setTypeFilter(None)
        else:
            self.proxyModel.setTypeFilter(selected_type)

    def importBookFromDownloadResult(self, downloadResult):
        """
        Import a book into the library from a download result.

        :param downloadResult: The result of a download.
        :type downloadResult: DownloadResult
        """
        self.importBook(downloadResult.filePath, downloadResult.job)

    def importBook(self, filePath, job=None):
        """
        Import a book into the library from a file path.

        :param filePath: The path to the book file.
        :type filePath: str
        :param job: The job associated with the download.
        :type job: Job, optional
        """
        self.library.addBook(filePath, job)

    def refreshTable(self):
        """
        Refresh the table view to reflect the current state of the library.
        """
        self.model.beginResetModel()
        self.model.endResetModel()
        self.tableView.resizeColumnsToContents()
        # Update completers
        self.updateCompleters()

    def updateCompleters(self):
        titles = sorted(set(book.title for book in self.library.books))
        authors = sorted(set(book.author for book in self.library.books))
        series_list = sorted(set(book.series for book in self.library.books if book.series))
        types = sorted(set(book.type for book in self.library.books if book.type))

        self.titleCompleterModel.setStringList(titles)
        self.authorCompleterModel.setStringList(authors)
        self.seriesCompleterModel.setStringList(series_list)

        # Update type combo box
        current_type = self.typeFilterComboBox.currentText()
        self.typeFilterComboBox.clear()
        self.typeFilterComboBox.addItem("All")
        self.typeFilterComboBox.addItems(types)
        # Restore previous selection if possible
        index = self.typeFilterComboBox.findText(current_type)
        if index >= 0:
            self.typeFilterComboBox.setCurrentIndex(index)
        else:
            self.typeFilterComboBox.setCurrentIndex(0)  # Default to 'All'

    def librarySize(self) -> int:
        """
        Get the size of the library.

        :return: The number of books in the library.
        :rtype: int
        """
        return self.library.numBooks

    def resetLibrary(self):
        """
        Reset the library to its initial state.
        """
        self.library.reset()
        self.refreshTable()

    def kindleBooksChanged(self, books):
        """
        Update the library with the books currently on the Kindle.

        :param books: The list of books on the Kindle.
        :type books: list
        """
        self.model.setKindleBooks(books)
        self.refreshTable()

    def kindleConnected(self):
        """
        Update the UI when a Kindle device is connected.
        """
        self.tableView.setKindleConnected(True)

    def kindleDisconnected(self):
        """
        Update the UI when a Kindle device is disconnected.
        """
        self.tableView.setKindleConnected(False)

    def sendToDevice(self, books):
        """
        Emit a signal to send selected books to the connected Kindle.

        :param books: The list of books to send.
        :type books: list
        """
        self.sendToDeviceRequested.emit(books)

    def newBookOnDevice(self, book):
        """
        Add a new book to the device and refresh the table.

        :param book: The book to add to the device.
        :type book: Book
        """
        self.tableView.newBookOnDevice(book)
        self.refreshTable()


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
        self.searchFormat.addItems(["Any Format", "EPUB", "MOBI", "AZW", "AZW3", "FB2", "PDF", "RTF", "TXT"])
        self.searchLayout.addWidget(self.searchFormat)

        # Search button
        self.searchButton = QPushButton("Search")
        self.searchButton.clicked.connect(self.startSearch)
        self.searchLayout.addWidget(self.searchButton)

        # Table setup
        self.modelData = []
        self.model = SearchResultsModel(self.modelData)

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

        self.searchWorker = SearchWorker(author, title, fmt)
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
        self.model = DownloadsModel(self.modelData)

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
