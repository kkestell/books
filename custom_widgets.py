import os
import subprocess

from PySide6.QtCore import Signal, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QComboBox, QLabel, QPushButton, QTableView, QMenu, QTextEdit, QHBoxLayout, QSizePolicy, QMessageBox

from config import Config
from models import Book, SearchResult


class EditDialog(QDialog):
    closed = Signal(Book)

    def __init__(self, book, parent=None):
        super().__init__(parent)
        self.book = book
        self.setWindowTitle("Edit Book")
        self.layout = QVBoxLayout(self)

        author = self.book.author if self.book.author else ""
        series = self.book.series if self.book.series else ""
        seriesNumber = str(self.book.seriesNumber) if self.book.seriesNumber else ""
        title = self.book.title if self.book.title else ""
        published = str(self.book.published) if self.book.published else ""
        bookType = self.book.type if self.book.type else ""
        description = self.book.description if self.book.description else ""

        # Title and Type
        titleLayout = QVBoxLayout()
        titleLayout.addWidget(QLabel("Title"))
        self.titleField = QLineEdit(title)
        titleLayout.addWidget(self.titleField)

        typeLayout = QVBoxLayout()
        typeLayout.addWidget(QLabel("Type"))
        self.typeField = QComboBox()
        self.typeField.addItems(["Novel", "Novella", "Short Story", "Anthology", "Collection", "Omnibus", "Graphic Novel", "Comic", "Non-Fiction", "Cookbook", "Poetry", "Other"])
        self.typeField.setCurrentText(bookType)
        typeLayout.addWidget(self.typeField)

        titleTypeLayout = QHBoxLayout()
        titleTypeLayout.addLayout(titleLayout)
        titleTypeLayout.addLayout(typeLayout)

        # Author and Published
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

        # Series and Series Number
        seriesLayout = QVBoxLayout()
        seriesLayout.addWidget(QLabel("Series"))
        self.seriesField = QLineEdit(series)
        seriesLayout.addWidget(self.seriesField)

        seriesNumberLayout = QVBoxLayout()
        seriesNumberLayout.addWidget(QLabel("Series Number"))
        self.seriesNumberField = QLineEdit(str(seriesNumber))
        self.seriesNumberField.setMaximumWidth(100)
        seriesNumberLayout.addWidget(self.seriesNumberField)

        seriesSeriesNumberLayout = QHBoxLayout()
        seriesSeriesNumberLayout.addLayout(seriesLayout)
        seriesSeriesNumberLayout.addLayout(seriesNumberLayout)

        # Description
        descriptionLayout = QVBoxLayout()
        descriptionLayout.addWidget(QLabel("Description"))
        self.descriptionField = QTextEdit(description)
        self.descriptionField.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        descriptionLayout.addWidget(self.descriptionField)

        # Save button
        saveButton = QPushButton("Save")
        saveButton.clicked.connect(self.saveChanges)
        saveButtonLayout = QHBoxLayout()
        saveButtonLayout.addStretch(1)
        saveButtonLayout.addWidget(saveButton)
        saveButtonLayout.addStretch(1)

        # Adding all to the main layout
        self.layout.addLayout(titleTypeLayout)
        self.layout.addLayout(authorPublishedLayout)
        self.layout.addLayout(seriesSeriesNumberLayout)
        self.layout.addLayout(descriptionLayout)
        self.layout.addLayout(saveButtonLayout)

        self.setMinimumSize(600, 400)

    def saveChanges(self):
        author = self.authorField.text() if self.authorField.text() else None
        series = self.seriesField.text() if self.seriesField.text() else None
        try:
            seriesNumber = int(self.seriesNumberField.text()) if self.seriesNumberField.text() else None
        except ValueError:
            seriesNumber = None
        # series and seriesNumber must both be set or both be None
        if not series or not seriesNumber:
            series = None
            seriesNumber = None
        title = self.titleField.text() if self.titleField.text() else None
        published = self.publishedField.text() if self.publishedField.text() else None
        bookType = self.typeField.currentText() if self.typeField.currentText() else None
        description = self.descriptionField.toPlainText() if self.descriptionField.toPlainText() else None
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
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.setSelectionBehavior(QTableView.SelectRows)

    def showContextMenu(self, pos):
        contextMenu = QMenu(self)
        clearAction = contextMenu.addAction("Clear Completed")

        action = contextMenu.exec(self.viewport().mapToGlobal(pos))
        if action == clearAction:
            self.clearCompleted()

    def clearCompleted(self):
        self.model().clearCompleted()

class LibraryTableView(QTableView):
    sendToDeviceRequested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.isKindleConnected = False
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSortingEnabled(True)

    def showContextMenu(self, pos):
        contextMenu = QMenu(self)
        openAction = contextMenu.addAction("Open")
        editAction = contextMenu.addAction("Edit...")
        contextMenu.addSeparator()
        showAction = contextMenu.addAction("Show in Folder")
        sendToDeviceAction = contextMenu.addAction("Send to Device")
        contextMenu.addSeparator()
        deleteAction = contextMenu.addAction("Delete...")

        if not self.isKindleConnected:
            sendToDeviceAction.setDisabled(True)

        action = contextMenu.exec(self.viewport().mapToGlobal(pos))
        if action == openAction:
            self.handleOpenAction(pos)
        elif action == editAction:
            self.handleEditAction(pos)
        elif action == deleteAction:
            self.handleDeleteAction()
        elif action == showAction:
            self.handleShowAction(pos)
        elif action == sendToDeviceAction:
            self.handleSendToDeviceAction()

    def handleEditAction(self, pos):
        index = self.indexAt(pos)

        if index.isValid():
            sourceIndex = self.model().mapToSource(index)
            bookId = self.model().sourceModel().data(sourceIndex.siblingAtColumn(self.model().sourceModel().headers.index('ID')), Qt.DisplayRole)
            book = self.model().sourceModel().library.getBookById(bookId)
            if book:
                editDialog = EditDialog(book)
                editDialog.closed.connect(self.onDialogClosed)
                editDialog.exec()

    def handleDeleteAction(self):
        selectedIndexes = self.selectionModel().selectedRows()
        if not selectedIndexes:
            return
        if len(selectedIndexes) == 1:
            message = "Are you sure you want to delete this book?"
        else:
            message = f"Are you sure you want to delete these {len(selectedIndexes)} books?"
        reply = QMessageBox.question(self, 'Confirm Reset', message, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        for index in selectedIndexes:
            sourceIndex = self.model().mapToSource(index)
            idIndex = self.model().sourceModel().headers.index('ID')
            bookId = self.model().sourceModel().data(sourceIndex.siblingAtColumn(idIndex), Qt.DisplayRole)
            book = self.model().sourceModel().library.getBookById(bookId)
            self.model().sourceModel().library.removeBook(book)
            self.model().sourceModel().removeRow(index.row())
        self.model().beginResetModel()
        self.model().endResetModel()

    def handleOpenAction(self, pos):
        index = self.indexAt(pos)
        if index.isValid():
            sourceIndex = self.model().mapToSource(index)
            bookId = self.model().sourceModel().data(sourceIndex.siblingAtColumn(self.model().sourceModel().headers.index('ID')), Qt.DisplayRole)
            book = self.model().sourceModel().library.getBookById(bookId)
            path = book.path
            # QDesktopServices.openUrl(QUrl.fromLocalFile(path))
            config = Config.load()
            args = []
            if config.pythonPath:
                args.append(config.pythonPath)
            args.append(config.ebookViewerPath)
            args.append(path)
            subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def handleShowAction(self, pos):
        index = self.indexAt(pos)
        if index.isValid():
            sourceIndex = self.model().mapToSource(index)
            bookId = self.model().sourceModel().data(sourceIndex.siblingAtColumn(self.model().sourceModel().headers.index('ID')), Qt.DisplayRole)
            book = self.model().sourceModel().library.getBookById(bookId)
            path = book.path
            QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(path)))

    def handleSendToDeviceAction(self):
        selectedIndexes = self.selectionModel().selectedRows()
        if not selectedIndexes:
            return
        booksNotAlreadyOnDevice = []
        for index in selectedIndexes:
            sourceIndex = self.model().mapToSource(index)
            bookId = self.model().sourceModel().data(sourceIndex.siblingAtColumn(self.model().sourceModel().headers.index('ID')), Qt.DisplayRole)
            book = self.model().sourceModel().library.getBookById(bookId)
            onDevice = self.model().sourceModel().data(sourceIndex.siblingAtColumn(self.model().sourceModel().headers.index('On Device')), Qt.DisplayRole)
            if onDevice != "✓":
                booksNotAlreadyOnDevice.append(book)
        if not booksNotAlreadyOnDevice:
            return
        self.sendToDeviceRequested.emit(booksNotAlreadyOnDevice)

    def onDialogClosed(self, book):
        self.model().sourceModel().library.updateBook(book)

    def setKindleConnected(self, connected):
        self.isKindleConnected = connected
        if connected:
            self.setColumnHidden(0, False)
        else:
            self.setColumnHidden(0, True)

    def newBookOnDevice(self, book):
        self.model().sourceModel().newBookOnDevice(book)


class SearchTableView(QTableView):
    downloadRequested = Signal(SearchResult)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.setSortingEnabled(True)

    def showContextMenu(self, pos):
        contextMenu = QMenu(self)
        downloadAction = contextMenu.addAction("Download")

        action = contextMenu.exec(self.viewport().mapToGlobal(pos))
        if action == downloadAction:
            self.downloadSelectedRows()

    def downloadSelectedRows(self):
        selectedIndexes = self.selectionModel().selectedRows()
        for index in selectedIndexes:
            searchResult = self.model().getRow(index.row())
            self.downloadRequested.emit(searchResult)

    def getIdColumnIndex(self):
        return self.model().sourceModel().headers.index('ID')

