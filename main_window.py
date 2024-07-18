import os

from PySide6.QtWidgets import QMainWindow, QTabWidget, QFileDialog, QMessageBox

from kindle import Kindle
from log import Log
from models import Library
from tabs import LibraryTab, DownloadsTab, SearchTab
from workers import DownloadWorker, ImportWorker, ConversionWorker


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        Log.info("Starting up")

        # library

        self.library = Library()

        # download worker

        self.downloadWorker = DownloadWorker()

        self.downloadWorker.jobQueued.connect(self.downloadJobQueued)
        self.downloadWorker.statusChanged.connect(self.statusChanged)
        self.downloadWorker.downloadComplete.connect(self.downloadComplete)

        # import worker

        self.importWorker = None
        self.importCounter = 0

        # conversion worker

        self.conversionWorker = None

        # window

        self.setWindowTitle("Books")
        self.resize(1200, 800)

        # tabs

        self.tabs = QTabWidget(self)

        self.libraryTab = LibraryTab(self.library, self)
        self.libraryTab.bookRemoved.connect(self.updateLibraryTabTitle)
        self.libraryTab.sendToDeviceRequested.connect(self.sendBooksToDevice)
        self.tabs.addTab(self.libraryTab, "Library")
        self.updateLibraryTabTitle()

        self.searchTab = SearchTab(self, self.downloadWorker)
        self.tabs.addTab(self.searchTab, "Search")

        self.downloadsTab = DownloadsTab(self)
        self.tabs.addTab(self.downloadsTab, "Downloads")

        # kindle

        self.kindle = Kindle()
        self.kindle.booksChanged.connect(self.libraryTab.kindleBooksChanged)
        self.kindle.kindleConnected.connect(self.libraryTab.kindleConnected)
        self.kindle.kindleDisconnected.connect(self.libraryTab.kindleDisconnected)
        self.kindle.start()

        # menu bar

        menuBar = self.menuBar()
        fileMenu = menuBar.addMenu("File")
        importAction = fileMenu.addAction("Import Books...")
        importFromDirectoryAction = fileMenu.addAction("Import Books from Directory...")
        importAction.triggered.connect(self.importBooks)
        importFromDirectoryAction.triggered.connect(self.importBooksFromDirectory)
        debugMenu = menuBar.addMenu("Debug")
        resetLibraryAction = debugMenu.addAction("Reset Library")
        resetLibraryAction.triggered.connect(self.resetLibrary)
        helpMenu = menuBar.addMenu("Help")
        aboutAction = helpMenu.addAction("About")
        aboutAction.triggered.connect(self.about)

        # status bar

        statusBar = self.statusBar()
        statusBar.showMessage("Ready")

        # go!

        self.downloadWorker.start()
        self.setCentralWidget(self.tabs)

    def closeEvent(self, event):
        Log.info("Shutting down")
        self.downloadWorker.terminate()
        self.kindle.terminate()
        event.accept()

    def updateLibraryTabTitle(self):
        numBooks = self.libraryTab.librarySize()
        if numBooks == 0:
            self.tabs.setTabText(0, "Library")
        else:
            self.tabs.setTabText(0, f"Library ({numBooks})")

    def updateDownloadsTabTitle(self):
        numJobs = self.downloadWorker.queueSize()
        if numJobs == 0:
            self.tabs.setTabText(2, "Downloads")
        else:
            self.tabs.setTabText(2, f"Downloads ({numJobs})")

    def downloadJobQueued(self, job):
        self.downloadsTab.addJob(job)
        self.updateDownloadsTabTitle()

    def statusChanged(self, job):
        self.downloadsTab.updateStatus(job)

    def downloadComplete(self, downloadResult):
        self.libraryTab.importBookFromDownloadResult(downloadResult)
        self.updateDownloadsTabTitle()
        self.updateLibraryTabTitle()
        self.libraryTab.refreshTable()

    def doImport(self, filePaths):
        self.importWorker = ImportWorker(self.libraryTab.library, filePaths)
        self.importWorker.importStarted.connect(self.importStarted)
        self.importWorker.importSuccess.connect(self.importSuccess)
        self.importWorker.importError.connect(self.importError)
        self.importWorker.importFinished.connect(self.importFinished)
        self.importWorker.start()

    def importBooks(self):
        if self.importWorker:
            QMessageBox.warning(self, "Import in progress", "An import is already in progress. Please wait for it to finish before starting another import.")
            return
        filePaths, _ = QFileDialog.getOpenFileNames(self, "Select books", "", "ePub Files (*.epub);;Mobi Files (*.mobi);;AZW Files (*.azw);;AZW3 Files (*.azw3);;FB2 Files (*.fb2);;PDF Files (*.pdf);;RTF Files (*.rtf);;Text Files (*.txt);;DjVu Files (*.djvu);;CHM Files (*.chm)")
        if not filePaths:
            return
        self.doImport(filePaths)

    def importBooksFromDirectory(self):
        if self.importWorker:
            QMessageBox.warning(self, "Import in progress", "An import is already in progress. Please wait for it to finish before starting another import.")
            return
        directory = QFileDialog.getExistingDirectory(self, "Select directory")
        if not directory:
            return
        allFiles = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                extension = os.path.splitext(file)[1].lower()
                validExtensions = ['.epub', '.mobi', '.azw', '.azw3', '.fb2', '.pdf', '.rtf', '.txt', '.djvu', '.chm']
                if extension in validExtensions:
                    filePath = os.path.join(root, file)
                    allFiles.append(filePath)
        if not allFiles:
            return
        self.doImport(allFiles)

    def resetLibrary(self):
        reply = QMessageBox.question(self, 'Confirm Reset', 'Are you sure you want to reset the library?', QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.libraryTab.resetLibrary()
            self.updateLibraryTabTitle()

    def importStarted(self):
        self.importCounter = 0
        self.statusBar().showMessage("Importing books...")

    def importSuccess(self, book):
        self.statusBar().showMessage(f"Imported {book.title} by {book.author}")
        self.importCounter += 1
        if self.importCounter == 10:
            self.libraryTab.refreshTable()
            self.importCounter = 0

    def importError(self, book):
        self.statusBar().showMessage(f"Error importing {book.title} by {book.author}")

    def importFinished(self):
        self.statusBar().showMessage("Import complete")
        self.updateLibraryTabTitle()
        self.libraryTab.refreshTable()
        self.importWorker = None

    def sendBooksToDevice(self, books):
        self.conversionWorker = ConversionWorker(self.kindle, books)
        self.conversionWorker.conversionStarted.connect(self.conversionStarted)
        self.conversionWorker.conversionSuccess.connect(self.conversionSuccess)
        self.conversionWorker.conversionError.connect(self.conversionError)
        self.conversionWorker.conversionFinished.connect(self.conversionFinished)
        self.conversionWorker.start()

    def conversionStarted(self):
        self.statusBar().showMessage("Converting books...")

    def conversionSuccess(self, book):
        self.statusBar().showMessage(f"Converted {book.title} by {book.author}")
        self.libraryTab.newBookOnDevice(book)

    def conversionError(self, book):
        self.statusBar().showMessage(f"Error converting {book.title} by {book.author}")

    def conversionFinished(self):
        self.statusBar().showMessage("Conversion complete")
        self.conversionWorker = None

    def about(self):
        VERSION = "0.1.0"
        QMessageBox.about(self, f"About Books v{VERSION}", "Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted. The software is provided \"as is\" and the author disclaims all warranties with regard to this software including all implied warranties of merchantability and fitness. In no event shall the author be liable for any special, direct, indirect, or consequential damages or any damages whatsoever resulting from loss of use, data, or profits, whether in an action of contract, negligence or other tortious action, arising out of or in connection with the use or performance of this software.")
