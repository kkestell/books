import os
import subprocess
import urllib.parse
from typing import cast

from PySide6.QtCore import Signal, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLineEdit, QComboBox, QLabel, QPushButton,
    QTableView, QMenu, QTextEdit, QHBoxLayout, QSizePolicy, QMessageBox
)

from config import Config
from models import Book, SearchResult
from table_models import MultiColumnSortProxyModel, LibraryModel, DownloadsModel, SearchResultsModel
from utils import run


class EditDialog(QDialog):
    """
    Dialog window for editing book metadata.

    :signal closed: Emitted when the dialog is closed, carrying the edited book object.
    """
    closed = Signal(Book)

    def __init__(self, book, parent=None):
        """
        Initialize the EditDialog with the given book.

        :param book: The book object to edit.
        :type book: Book
        :param parent: The parent widget.
        :type parent: QWidget, optional
        """
        super().__init__(parent)
        self.book = book
        self.setWindowTitle("Edit Book")
        self.layout = QVBoxLayout(self)

        # Extract book metadata with default values
        author = self.book.author or ""
        series = self.book.series or ""
        seriesNumber = str(self.book.seriesNumber) if self.book.seriesNumber else ""
        title = self.book.title or ""
        published = str(self.book.published) if self.book.published else ""
        bookType = self.book.type or ""
        description = self.book.description or ""

        # Title and Type Fields
        titleLayout = QVBoxLayout()
        titleLayout.addWidget(QLabel("Title"))
        self.titleField = QLineEdit(title)
        titleLayout.addWidget(self.titleField)

        typeLayout = QVBoxLayout()
        typeLayout.addWidget(QLabel("Type"))
        self.typeField = QComboBox()
        self.typeField.addItems([
            "Novel", "Novella", "Novelette", "Short Story", "Anthology", "Collection",
            "Omnibus", "Graphic Novel", "Comic", "Non-Fiction", "Cookbook", "Poetry", "Other"
        ])
        self.typeField.setCurrentText(bookType)
        typeLayout.addWidget(self.typeField)

        titleTypeLayout = QHBoxLayout()
        titleTypeLayout.addLayout(titleLayout)
        titleTypeLayout.addLayout(typeLayout)

        # Author and Published Fields
        authorLayout = QVBoxLayout()
        authorLayout.addWidget(QLabel("Author"))
        self.authorField = QLineEdit(author)
        authorLayout.addWidget(self.authorField)

        publishedLayout = QVBoxLayout()
        publishedLayout.addWidget(QLabel("Published"))
        self.publishedField = QLineEdit(published)
        self.publishedField.setMaximumWidth(100)
        publishedLayout.addWidget(self.publishedField)

        authorPublishedLayout = QHBoxLayout()
        authorPublishedLayout.addLayout(authorLayout)
        authorPublishedLayout.addLayout(publishedLayout)

        # Series and Series Number Fields
        seriesLayout = QVBoxLayout()
        seriesLayout.addWidget(QLabel("Series"))
        self.seriesField = QLineEdit(series)
        seriesLayout.addWidget(self.seriesField)

        seriesNumberLayout = QVBoxLayout()
        seriesNumberLayout.addWidget(QLabel("Series Number"))
        self.seriesNumberField = QLineEdit(seriesNumber)
        self.seriesNumberField.setMaximumWidth(100)
        seriesNumberLayout.addWidget(self.seriesNumberField)

        seriesSeriesNumberLayout = QHBoxLayout()
        seriesSeriesNumberLayout.addLayout(seriesLayout)
        seriesSeriesNumberLayout.addLayout(seriesNumberLayout)

        # Description Field
        descriptionLayout = QVBoxLayout()
        descriptionLayout.addWidget(QLabel("Description"))
        self.descriptionField = QTextEdit(description)
        self.descriptionField.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        descriptionLayout.addWidget(self.descriptionField)

        # Save Button
        saveButton = QPushButton("Save")
        saveButton.clicked.connect(self.saveChanges)
        saveButtonLayout = QHBoxLayout()
        saveButtonLayout.addStretch(1)
        saveButtonLayout.addWidget(saveButton)
        saveButtonLayout.addStretch(1)

        # Add all layouts to the main layout
        self.layout.addLayout(titleTypeLayout)
        self.layout.addLayout(authorPublishedLayout)
        self.layout.addLayout(seriesSeriesNumberLayout)
        self.layout.addLayout(descriptionLayout)
        self.layout.addLayout(saveButtonLayout)

        self.setMinimumSize(600, 400)

    def saveChanges(self):
        """
        Save the changes made to the book and emit the closed signal.
        """
        # Retrieve values from input fields
        author = self.authorField.text() or None
        series = self.seriesField.text() or None

        # Convert series number to int
        try:
            seriesNumber = int(self.seriesNumberField.text()) if self.seriesNumberField.text() else None
        except ValueError:
            seriesNumber = None

        # Ensure both series and seriesNumber are set or both are None
        if not series or seriesNumber is None:
            series = None
            seriesNumber = None

        title = self.titleField.text() or None
        published = self.publishedField.text() or None
        bookType = self.typeField.currentText() or None
        description = self.descriptionField.toPlainText() or None

        # Update the book object
        self.book.author = author
        self.book.series = series
        self.book.seriesNumber = seriesNumber
        self.book.title = title
        self.book.published = published
        self.book.type = bookType
        self.book.description = description

        self.accept()
        self.closed.emit(self.book)


class DownloadsTableView(QTableView):
    """
    Table view for displaying download jobs.
    """
    def __init__(self, parent=None):
        """
        Initialize the DownloadsTableView.

        :param parent: The parent widget.
        :type parent: QWidget, optional
        """
        super().__init__(parent)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

    def showContextMenu(self, pos):
        """
        Display the context menu at the given position.

        :param pos: The position to show the context menu.
        :type pos: QPoint
        """
        contextMenu = QMenu(self)
        clearAction = contextMenu.addAction("Clear Completed")

        action = contextMenu.exec(self.viewport().mapToGlobal(pos))
        if action == clearAction:
            self.clearCompleted()

    def clearCompleted(self):
        """
        Clear all completed download jobs from the model.
        """
        downloadModel = cast(DownloadsModel, self.model())
        downloadModel.clearCompleted()


class LibraryTableView(QTableView):
    """
    Table view for displaying the library of books.

    :signal sendToDeviceRequested: Emitted when books are requested to be sent to a device.
    """
    sendToDeviceRequested = Signal(object)

    def __init__(self, parent=None):
        """
        Initialize the LibraryTableView.

        :param parent: The parent widget.
        :type parent: QWidget, optional
        """
        super().__init__(parent)

        self.isKindleConnected = False

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSortingEnabled(True)

    def showContextMenu(self, pos):
        """
        Display the context menu at the given position.

        :param pos: The position to show the context menu.
        :type pos: QPoint
        """
        contextMenu = QMenu(self)

        # Add actions to the context menu
        openAction = contextMenu.addAction("Open")
        editAction = contextMenu.addAction("Edit...")
        contextMenu.addSeparator()
        researchMenu = contextMenu.addMenu("Research")
        researchAuthorAction = researchMenu.addAction("Author")
        researchTitleAction = researchMenu.addAction("Title")
        contextMenu.addSeparator()
        showAction = contextMenu.addAction("Show in Folder")
        sendToDeviceAction = contextMenu.addAction("Send to Device")
        contextMenu.addSeparator()
        deleteAction = contextMenu.addAction("Delete...")

        # Disable 'Send to Device' if Kindle is not connected
        if not self.isKindleConnected:
            sendToDeviceAction.setDisabled(True)

        action = contextMenu.exec(self.viewport().mapToGlobal(pos))

        # Handle the selected action
        if action == openAction:
            self.handleOpenAction(pos)
        elif action == editAction:
            self.handleEditAction(pos)
        elif action == researchAuthorAction:
            self.handleResearchAuthorAction(pos)
        elif action == researchTitleAction:
            self.handleResearchTitleAction(pos)
        elif action == deleteAction:
            self.handleDeleteAction()
        elif action == showAction:
            self.handleShowAction(pos)
        elif action == sendToDeviceAction:
            self.handleSendToDeviceAction()

    def handleEditAction(self, pos):
        """
        Open the edit dialog for the selected book.

        :param pos: The position of the selected item.
        :type pos: QPoint
        """
        index = self.indexAt(pos)
        if not index.isValid():
            return

        proxyModel = cast(MultiColumnSortProxyModel, self.model())
        sourceIndex = proxyModel.mapToSource(index)
        sourceModel = cast(LibraryModel, proxyModel.sourceModel())

        bookId = sourceModel.data(
            sourceIndex.siblingAtColumn(sourceModel.headers.index('ID')),
            Qt.ItemDataRole.DisplayRole
        )

        book = sourceModel.library.getBookById(bookId)
        if book:
            editDialog = EditDialog(book)
            editDialog.closed.connect(self.onDialogClosed)
            editDialog.exec()

    def handleResearchAuthorAction(self, pos):
        """
        Open a browser to research the author of the selected book.

        :param pos: The position of the selected item.
        :type pos: QPoint
        """
        index = self.indexAt(pos)
        if not index.isValid():
            return

        proxyModel = cast(MultiColumnSortProxyModel, self.model())
        sourceIndex = proxyModel.mapToSource(index)
        sourceModel = cast(LibraryModel, proxyModel.sourceModel())

        bookId = sourceModel.data(
            sourceIndex.siblingAtColumn(sourceModel.headers.index('ID')),
            Qt.ItemDataRole.DisplayRole
        )

        book = sourceModel.library.getBookById(bookId)
        author = book.author

        urlEncodedAuthorName = urllib.parse.quote(author)
        url = f"https://www.fantasticfiction.com/search/?searchfor=author&keywords={urlEncodedAuthorName}"
        QDesktopServices.openUrl(QUrl(url))

    def handleResearchTitleAction(self, pos):
        """
        Open a browser to research the title of the selected book.

        :param pos: The position of the selected item.
        :type pos: QPoint
        """
        index = self.indexAt(pos)
        if not index.isValid():
            return

        proxyModel = cast(MultiColumnSortProxyModel, self.model())
        sourceIndex = proxyModel.mapToSource(index)
        sourceModel = cast(LibraryModel, proxyModel.sourceModel())

        bookId = sourceModel.data(
            sourceIndex.siblingAtColumn(sourceModel.headers.index('ID')),
            Qt.ItemDataRole.DisplayRole
        )

        book = sourceModel.library.getBookById(bookId)
        title = book.title

        urlEncodedTitle = urllib.parse.quote(title)
        url = f"https://www.fantasticfiction.com/search/?searchfor=book&keywords={urlEncodedTitle}"
        QDesktopServices.openUrl(QUrl(url))

    def handleDeleteAction(self):
        """
        Delete the selected books from the library.
        """
        selectedIndexes = self.selectionModel().selectedRows()
        if not selectedIndexes:
            return

        if len(selectedIndexes) == 1:
            message = "Are you sure you want to delete this book?"
        else:
            message = f"Are you sure you want to delete these {len(selectedIndexes)} books?"

        reply = QMessageBox.question(
            self, 'Confirm Delete', message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        proxyModel = cast(MultiColumnSortProxyModel, self.model())
        sourceModel = cast(LibraryModel, proxyModel.sourceModel())

        # Sort indexes in reverse order to prevent index shifts when deleting
        for index in sorted(selectedIndexes, reverse=True, key=lambda idx: idx.row()):
            sourceIndex = proxyModel.mapToSource(index)

            idColumn = sourceModel.headers.index('ID')
            bookId = sourceModel.data(
                sourceIndex.siblingAtColumn(idColumn),
                Qt.ItemDataRole.DisplayRole
            )

            book = sourceModel.library.getBookById(bookId)
            sourceModel.library.removeBook(book)
            sourceModel.removeRow(sourceIndex.row())

        # Reset the model after deletion
        self.model().beginResetModel()
        self.model().endResetModel()

    def handleOpenAction(self, pos):
        """
        Open the selected book in an external viewer.

        :param pos: The position of the selected item.
        :type pos: QPoint
        """
        index = self.indexAt(pos)
        if not index.isValid():
            return

        proxyModel = cast(MultiColumnSortProxyModel, self.model())
        sourceIndex = proxyModel.mapToSource(index)
        sourceModel = cast(LibraryModel, proxyModel.sourceModel())

        bookId = sourceModel.data(
            sourceIndex.siblingAtColumn(sourceModel.headers.index('ID')),
            Qt.ItemDataRole.DisplayRole
        )

        book = sourceModel.library.getBookById(bookId)

        QDesktopServices.openUrl(QUrl.fromLocalFile(book.path))

    def handleShowAction(self, pos):
        """
        Show the selected book in the file explorer.

        :param pos: The position of the selected item.
        :type pos: QPoint
        """
        index = self.indexAt(pos)
        if not index.isValid():
            return

        proxyModel = cast(MultiColumnSortProxyModel, self.model())
        sourceIndex = proxyModel.mapToSource(index)
        sourceModel = cast(LibraryModel, proxyModel.sourceModel())

        bookId = sourceModel.data(
            sourceIndex.siblingAtColumn(sourceModel.headers.index('ID')),
            Qt.ItemDataRole.DisplayRole
        )

        book = sourceModel.library.getBookById(bookId)
        path = book.path

        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path)))

    def handleSendToDeviceAction(self):
        """
        Send selected books to the connected Kindle device.
        """
        selectedIndexes = self.selectionModel().selectedRows()
        if not selectedIndexes:
            return

        booksNotAlreadyOnDevice = []

        for index in selectedIndexes:
            proxyModel = cast(MultiColumnSortProxyModel, self.model())
            sourceIndex = proxyModel.mapToSource(index)
            sourceModel = cast(LibraryModel, proxyModel.sourceModel())

            bookId = sourceModel.data(
                sourceIndex.siblingAtColumn(sourceModel.headers.index('ID')),
                Qt.ItemDataRole.DisplayRole
            )

            book = sourceModel.library.getBookById(bookId)

            onDevice = sourceModel.data(
                sourceIndex.siblingAtColumn(sourceModel.headers.index('On Device')),
                Qt.ItemDataRole.DisplayRole
            )
            if onDevice != "✓":
                booksNotAlreadyOnDevice.append(book)

        if not booksNotAlreadyOnDevice:
            return

        self.sendToDeviceRequested.emit(booksNotAlreadyOnDevice)

    def onDialogClosed(self, book):
        """
        Update the book in the library when the edit dialog is closed.

        :param book: The book object with updated metadata.
        :type book: Book
        """
        proxyModel = cast(MultiColumnSortProxyModel, self.model())
        sourceModel = cast(LibraryModel, proxyModel.sourceModel())

        sourceModel.library.updateBook(book)

    def setKindleConnected(self, connected):
        """
        Update the UI when a Kindle device is connected or disconnected.

        :param connected: True if Kindle is connected, False otherwise.
        :type connected: bool
        """
        self.isKindleConnected = connected
        if connected:
            self.setColumnHidden(0, False)
        else:
            self.setColumnHidden(0, True)

    def newBookOnDevice(self, book):
        """
        Add a new book to the device's book list.

        :param book: The book object to add to the device.
        :type book: Book
        """
        proxyModel = cast(MultiColumnSortProxyModel, self.model())
        sourceModel = cast(LibraryModel, proxyModel.sourceModel())

        sourceModel.newBookOnDevice(book)


class SearchTableView(QTableView):
    """
    Table view for displaying search results.

    :signal downloadRequested: Emitted when a search result is requested to be downloaded.
    """
    downloadRequested = Signal(SearchResult)

    def __init__(self, parent=None):
        """
        Initialize the SearchTableView.

        :param parent: The parent widget.
        :type parent: QWidget, optional
        """
        super().__init__(parent)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSortingEnabled(True)

    def showContextMenu(self, pos):
        """
        Display the context menu at the given position.

        :param pos: The position to show the context menu.
        :type pos: QPoint
        """
        contextMenu = QMenu(self)
        downloadAction = contextMenu.addAction("Download")

        action = contextMenu.exec(self.viewport().mapToGlobal(pos))
        if action == downloadAction:
            self.downloadSelectedRows()

    def downloadSelectedRows(self):
        """
        Emit a signal to download the selected search results.
        """
        selectedIndexes = self.selectionModel().selectedRows()
        for index in selectedIndexes:
            searchModel = cast(SearchResultsModel, self.model())
            searchResult = searchModel.getRow(index.row())
            self.downloadRequested.emit(searchResult)

    def getIdColumnIndex(self):
        """
        Get the index of the 'ID' column.

        :return: The index of the 'ID' column.
        :rtype: int
        """
        searchModel = cast(SearchResultsModel, self.model())
        return searchModel.headers.index('ID')
