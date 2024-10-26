from PySide6.QtCore import Signal, QStringListModel, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QCompleter, QHeaderView

from src.books.core.models.book import Book
from src.books.view_models.library_table_model import LibraryTableModel
from src.books.view_models.multi_column_sort_proxy_model import MultiColumnSortProxyModel
from src.books.views.library_table_view import LibraryTableView


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

        self.authorFilterEdit = QLineEdit()
        self.authorFilterEdit.setPlaceholderText("Filter by Author")
        self.titleFilterEdit = QLineEdit()
        self.titleFilterEdit.setPlaceholderText("Filter by Title")
        self.seriesFilterEdit = QLineEdit()
        self.seriesFilterEdit.setPlaceholderText("Filter by Series")
        self.typeFilterComboBox = QComboBox()
        self.typeFilterComboBox.addItem("All Types")
        self.formatFilterComboBox = QComboBox()
        self.formatFilterComboBox.addItem("All Formats")

        # Get unique titles, authors, series, and types
        authors = sorted(set(book.author for book in library.books))
        titles = sorted(set(book.title for book in library.books))
        series_list = sorted(set(book.series for book in library.books if book.series))
        types = sorted(set(book.type for book in library.books if book.type))
        formats = sorted(set(book.format for book in library.books if book.format))

        self.authorCompleterModel = QStringListModel(authors)
        self.authorCompleter = QCompleter(self.authorCompleterModel)
        self.authorCompleter.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.authorFilterEdit.setCompleter(self.authorCompleter)

        self.titleCompleterModel = QStringListModel(titles)
        self.titleCompleter = QCompleter(self.titleCompleterModel)
        self.titleCompleter.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.titleFilterEdit.setCompleter(self.titleCompleter)

        self.seriesCompleterModel = QStringListModel(series_list)
        self.seriesCompleter = QCompleter(self.seriesCompleterModel)
        self.seriesCompleter.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.seriesFilterEdit.setCompleter(self.seriesCompleter)

        # Populate type combo box
        self.typeFilterComboBox.addItems(types)

        # Populate format combo box
        self.formatFilterComboBox.addItems(formats)

        filterLayout.addWidget(self.authorFilterEdit)
        filterLayout.addWidget(self.titleFilterEdit)
        filterLayout.addWidget(self.seriesFilterEdit)
        filterLayout.addWidget(self.typeFilterComboBox)
        filterLayout.addWidget(self.formatFilterComboBox)

        self.layout.addLayout(filterLayout)

        # Table setup
        self.library = library
        self.library.bookRemoved.connect(self.refreshTable)
        self.library.bookRemoved.connect(self.bookRemoved)

        self.model = LibraryTableModel(self.library)
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
        self.authorFilterEdit.textChanged.connect(self.onAuthorFilterChanged)
        self.titleFilterEdit.textChanged.connect(self.onTitleFilterChanged)
        self.seriesFilterEdit.textChanged.connect(self.onSeriesFilterChanged)
        self.typeFilterComboBox.currentIndexChanged.connect(self.onTypeFilterChanged)
        self.formatFilterComboBox.currentIndexChanged.connect(self.onFormatFilterChanged)

    def onAuthorFilterChanged(self, text):
        self.proxyModel.setAuthorFilterPattern(text)

    def onTitleFilterChanged(self, text):
        self.proxyModel.setTitleFilterPattern(text)

    def onSeriesFilterChanged(self, text):
        self.proxyModel.setSeriesFilterPattern(text)

    def onTypeFilterChanged(self, _index):
        selected_type = self.typeFilterComboBox.currentText()
        if selected_type == "All Types":
            self.proxyModel.setTypeFilter(None)
        else:
            self.proxyModel.setTypeFilter(selected_type)

    def onFormatFilterChanged(self, _index):
        selected_format = self.formatFilterComboBox.currentText()
        if selected_format == "All Formats":
            self.proxyModel.setFormatFilter(None)
        else:
            self.proxyModel.setFormatFilter(selected_format)

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
        authors = sorted(set(book.author for book in self.library.books))
        titles = sorted(set(book.title for book in self.library.books))
        series_list = sorted(set(book.series for book in self.library.books if book.series))
        types = sorted(set(book.type for book in self.library.books if book.type))
        formats = sorted(set(book.format for book in self.library.books if book.format))

        self.authorCompleterModel.setStringList(authors)
        self.titleCompleterModel.setStringList(titles)
        self.seriesCompleterModel.setStringList(series_list)

        # Update type combo box
        current_type = self.typeFilterComboBox.currentText()
        self.typeFilterComboBox.clear()
        self.typeFilterComboBox.addItem("All Types")
        self.typeFilterComboBox.addItems(types)

        # Restore previous selection if possible
        index = self.typeFilterComboBox.findText(current_type)
        if index >= 0:
            self.typeFilterComboBox.setCurrentIndex(index)
        else:
            self.typeFilterComboBox.setCurrentIndex(0)  # Default to 'All'

        # Update format combo box
        current_format = self.formatFilterComboBox.currentText()
        self.formatFilterComboBox.clear()
        self.formatFilterComboBox.addItem("All Formats")
        self.formatFilterComboBox.addItems(formats)

        # Restore previous selection if possible
        index = self.formatFilterComboBox.findText(current_format)
        if index >= 0:
            self.formatFilterComboBox.setCurrentIndex(index)
        else:
            self.formatFilterComboBox.setCurrentIndex(0)

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
