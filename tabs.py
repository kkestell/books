import re

import psutil
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHeaderView, QHBoxLayout, QLineEdit, QPushButton, QComboBox, QMessageBox

from custom_widgets import LibraryTableView, SearchTableView, DownloadsTableView
from models import Book
from table_models import LibraryModel, MultiColumnSortProxyModel, SearchResultsModel, DownloadsModel
from workers import SearchWorker


class LibraryTab(QWidget):
    bookRemoved = Signal(Book)
    sendToDeviceRequested = Signal(object)

    def __init__(self, library, kindle, parent=None):
        super().__init__(parent)

        self.kindle = kindle

        # layout

        self.layout = QVBoxLayout(self)

        # table

        self.library = library
        self.library.bookRemoved.connect(self.refreshTable)
        self.library.bookRemoved.connect(self.bookRemoved)

        self.model = LibraryModel(self.library)
        self.proxyModel = MultiColumnSortProxyModel()
        self.proxyModel.setSourceModel(self.model)

        self.tableView = LibraryTableView(self)
        self.tableView.setModel(self.proxyModel)
        self.proxyModel.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.proxyModel.setSortRole(Qt.DisplayRole)

        authorColumn = self.model.headers.index("Author")
        titleColumn = self.model.headers.index("Title")
        idColumn = self.model.headers.index("ID")
        onDeviceColumn = self.model.headers.index("On Device")

        self.proxyModel.sort(authorColumn, Qt.AscendingOrder)

        header = self.tableView.horizontalHeader()
        # header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(titleColumn, QHeaderView.ResizeMode.Stretch)
        self.tableView.setColumnHidden(idColumn, True)
        self.tableView.setColumnHidden(onDeviceColumn, True)
        self.tableView.setColumnWidth(onDeviceColumn, 26)
        self.tableView.resizeColumnsToContents()

        self.tableView.sendToDeviceRequested.connect(self.sendToDevice)

        self.layout.addWidget(self.tableView)

    def importBookFromDownloadResult(self, downloadResult):
        self.importBook(downloadResult.filePath, downloadResult.job)

    def importBook(self, filePath, job=None):
        self.library.addBook(filePath, job)

    def refreshTable(self):
        self.model.beginResetModel()
        self.model.endResetModel()
        self.tableView.resizeColumnsToContents()

    def librarySize(self):
        return self.library.numBooks

    def resetLibrary(self):
        self.library.reset()
        self.refreshTable()

    def kindleBooksChanged(self, books):
        self.model.setKindleBooks(books)
        self.refreshTable()

    def kindleConnected(self):
        self.tableView.setKindleConnected(True)

    def kindleDisconnected(self):
        self.tableView.setKindleConnected(False)

    def sendToDevice(self, books):
        self.sendToDeviceRequested.emit(books)

    def newBookOnDevice(self, book):
        self.tableView.newBookOnDevice(book)
        self.refreshTable()


class SearchTab(QWidget):
    def __init__(self, parent, downloadWorker):
        super().__init__(parent)

        # search worker

        self.searchWorker = None

        # download worker

        self.downloadWorker = downloadWorker

        # layout

        self.layout = QVBoxLayout(self)

        # search

        self.searchLayout = QHBoxLayout()
        self.layout.addLayout(self.searchLayout)

        # query

        self.searchInput = QLineEdit()
        self.searchInput.setPlaceholderText("Search...")
        self.searchInput.returnPressed.connect(self.startSearch)
        self.searchLayout.addWidget(self.searchInput, 1)

        # type

        self.searchType = QComboBox()
        self.searchType.addItems(["Fiction", "Non-Fiction"])
        self.searchType.currentIndexChanged.connect(self.updateSearchFormats)
        self.searchLayout.addWidget(self.searchType)

        # format

        self.searchFormat = QComboBox()
        self.searchLayout.addWidget(self.searchFormat)

        # search button

        self.searchButton = QPushButton("Search")
        self.searchButton.clicked.connect(self.startSearch)
        self.searchLayout.addWidget(self.searchButton)

        # table

        self.modelData = []
        self.model = SearchResultsModel(self.modelData)

        self.tableView = SearchTableView()
        self.tableView.setModel(self.model)

        titleColumn = self.model.headers.index("Title")
        mirrorsColumn = self.model.headers.index("Mirrors")

        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(titleColumn, QHeaderView.ResizeMode.Stretch)
        self.tableView.setColumnHidden(mirrorsColumn, True)

        self.tableView.downloadRequested.connect(self.downloadFile)

        self.layout.addWidget(self.tableView)

        # final set up

        self.updateSearchFormats()

    def updateSearchFormats(self):
        searchType = self.searchType.currentText()
        if searchType == "Fiction":
            formats = ["Any Format", "EPUB", "MOBI", "AZW", "AZW3", "FB2", "PDF", "RTF", "TXT"]
        else:
            formats = ["Any Format", "PDF", "DJVU", "CHM", "ZIP", "EPUB", "MOBI", "AZW", "AZW3", "RAR", "7Z"]
        self.searchFormat.clear()
        self.searchFormat.addItems(formats)

    def startSearch(self):
        if self.searchWorker:
            QMessageBox.warning(self, "Search in progress", "A search is already in progress. Please wait for it to finish before starting another search.")
            return
        query = self.searchInput.text()
        searchType = self.searchType.currentText()
        format = self.searchFormat.currentText()
        if format == "Any Format":
            format = ""

        if searchType == "Non-Fiction":
            self.tableView.hideColumn(self.model.headers.index("Series"))
        else:
            self.tableView.showColumn(self.model.headers.index("Series"))

        self.searchInput.setEnabled(False)
        self.searchType.setEnabled(False)
        self.searchFormat.setEnabled(False)
        self.searchButton.setEnabled(False)

        self.model.clearRows()

        self.searchWorker = SearchWorker(query, searchType, format)
        self.searchWorker.newRecord.connect(self.addRecord)
        self.searchWorker.searchComplete.connect(self.searchComplete)
        self.searchWorker.start()

        print("Search started")

    def addRecord(self, record):
        self.model.addRows([record])
        # if any records have a series, show the series column -- otherwise hide it
        if any([record.series for record in self.model.records]):
            self.tableView.showColumn(self.model.headers.index("Series"))
        else:
            self.tableView.hideColumn(self.model.headers.index("Series"))

    def searchComplete(self):
        self.searchInput.setEnabled(True)
        self.searchType.setEnabled(True)
        self.searchFormat.setEnabled(True)
        self.searchButton.setEnabled(True)
        self.searchWorker = None

    def downloadFile(self, job):
        self.downloadWorker.enqueue(job)


class DownloadsTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        # layout

        self.layout = QVBoxLayout(self)

        # table

        self.modelData = []
        self.model = DownloadsModel(self.modelData)

        self.tableView = DownloadsTableView()
        self.tableView.setModel(self.model)

        titleColumn = self.model.headers.index("Title")
        statusColumn = self.model.headers.index("Status")
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
        self.model.addRows([job])
        if any([record.series for record in self.model.records]):
            self.tableView.showColumn(self.model.headers.index("Series"))
        else:
            self.tableView.hideColumn(self.model.headers.index("Series"))

    def updateStatus(self, job):
        self.model.dataChanged.emit(self.model.index(self.model.records.index(job), 0), self.model.index(self.model.records.index(job), len(self.model.headers) - 1))
