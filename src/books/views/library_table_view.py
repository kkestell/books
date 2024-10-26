import os
import urllib.parse
from typing import cast

from PySide6.QtCore import Signal, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QTableView, QMenu, QMessageBox

from src.books.core.fonts import getSansSerifFont
from src.books.dialogs.edit_book_dialog import EditBookDialog
from src.books.view_models.multi_column_sort_proxy_model import MultiColumnSortProxyModel
from src.books.view_models.library_table_model import LibraryTableModel


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
        self.setFont(getSansSerifFont())


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
        sourceModel = cast(LibraryTableModel, proxyModel.sourceModel())

        bookId = sourceModel.data(
            sourceIndex.siblingAtColumn(sourceModel.headers.index('ID')),
            Qt.ItemDataRole.DisplayRole
        )

        book = sourceModel.library.getBookById(bookId)
        if book:
            editDialog = EditBookDialog(book)
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
        sourceModel = cast(LibraryTableModel, proxyModel.sourceModel())

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
        sourceModel = cast(LibraryTableModel, proxyModel.sourceModel())

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
        sourceModel = cast(LibraryTableModel, proxyModel.sourceModel())

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
        sourceModel = cast(LibraryTableModel, proxyModel.sourceModel())

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
        sourceModel = cast(LibraryTableModel, proxyModel.sourceModel())

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
            sourceModel = cast(LibraryTableModel, proxyModel.sourceModel())

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
        sourceModel = cast(LibraryTableModel, proxyModel.sourceModel())

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
        sourceModel = cast(LibraryTableModel, proxyModel.sourceModel())

        sourceModel.newBookOnDevice(book)
