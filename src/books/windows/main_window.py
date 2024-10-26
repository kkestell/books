import os
import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QIcon, QDesktopServices, QDragEnterEvent, QDropEvent
from PySide6.QtWidgets import QMainWindow, QTabWidget, QFileDialog, QMessageBox

from books.core.constants import ebookExtensions, ebookExtensionsFilterString
from src.books.core.config import Config
from src.books.core.library import Library
from src.books.core.log import Log
from src.books.core.models.book import Book
from src.books.tabs.library_tab import LibraryTab
from src.books.threads.conversion_thread import ConversionThread
from src.books.threads.download_thread import DownloadThread
from src.books.threads.import_thread import ImportThread
from src.books.threads.kindle_monitor_thread import KindleMonitorThread
from src.books.windows.log_viewer_window import LogViewerWindow
from src.books.tabs.downloads_tab import DownloadsTab
from src.books.tabs.search_tab import SearchTab


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        Log.info("Starting up")

        # Verify Calibre tools before proceeding
        if not self.verifyCalibreTools():
            sys.exit(1)

        # Set the window icon
        # this file is in /src/books/windows/main_window.py and the icon is in /assets/icon.png
        # basedir is /
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        icon_path = os.path.join(base_dir, "assets", "icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        # else:
        #     icon_path = os.path.join(os.path.dirname(os.path.dirname(base_dir)), "assets", "icon.png")
        #     if os.path.exists(icon_path):
        #         self.setWindowIcon(QIcon(icon_path))

        # Initialize the library
        self.library = Library()

        # Initialize the download worker
        self.downloadWorker = DownloadThread()

        # Connect download worker signals to slots
        self.downloadWorker.jobQueued.connect(self.downloadJobQueued)
        self.downloadWorker.statusChanged.connect(self.statusChanged)
        self.downloadWorker.downloadComplete.connect(self.downloadComplete)

        # Initialize the import worker
        self.importWorker = None
        self.importCounter = 0

        # Initialize the conversion worker
        self.conversionWorker = None

        # Set up the main window
        self.setWindowTitle("Books")
        self.resize(1200, 800)

        # Enable drag and drop
        self.setAcceptDrops(True)

        # Create and set up tabs
        self.tabs = QTabWidget(self)

        # Library tab
        self.libraryTab = LibraryTab(self.library, self)
        self.libraryTab.bookRemoved.connect(self.updateLibraryTabTitle)
        self.libraryTab.sendToDeviceRequested.connect(self.sendBooksToDevice)
        self.tabs.addTab(self.libraryTab, "Library")
        self.updateLibraryTabTitle()

        # Search tab
        self.searchTab = SearchTab(self, self.downloadWorker)
        self.tabs.addTab(self.searchTab, "Search")

        # Downloads tab
        self.downloadsTab = DownloadsTab(self)
        self.tabs.addTab(self.downloadsTab, "Downloads")

        # Set up Kindle device monitoring
        self.kindle = KindleMonitorThread()
        self.kindle.booksChanged.connect(self.libraryTab.kindleBooksChanged)
        self.kindle.kindleConnected.connect(self.libraryTab.kindleConnected)
        self.kindle.kindleDisconnected.connect(self.libraryTab.kindleDisconnected)
        self.kindle.start()

        # Create menu bar and add actions
        menuBar = self.menuBar()

        # File menu
        fileMenu = menuBar.addMenu("File")
        importAction = fileMenu.addAction("Import Books...")
        importFromDirectoryAction = fileMenu.addAction("Import Books from Directory...")
        importAction.triggered.connect(self.importBooks)
        importFromDirectoryAction.triggered.connect(self.importBooksFromDirectory)

        # Debug menu
        debugMenu = menuBar.addMenu("Debug")
        logViewerAction = debugMenu.addAction("View Logs")
        logViewerAction.triggered.connect(self.showLogViewer)
        showConfigFileAction = debugMenu.addAction("Edit Configuration File")
        showConfigFileAction.triggered.connect(self.editConfigFile)
        # debugMenu.addSeparator()
        # resetLibraryAction = debugMenu.addAction("Reset Library")
        # resetLibraryAction.triggered.connect(self.resetLibrary)

        # Help menu
        helpMenu = menuBar.addMenu("Help")
        aboutAction = helpMenu.addAction("About")
        aboutAction.triggered.connect(self.showAboutBox)

        # Set up the status bar
        statusBar = self.statusBar()
        statusBar.showMessage("Ready")

        # Start the download worker
        self.downloadWorker.start()

        # Set the central widget
        self.setCentralWidget(self.tabs)

        # Show the log viewer window
        self.logViewerWindow = None

    def verifyCalibreTools(self) -> bool:
        """
        Verify that the required Calibre tools exist.

        :return: True if all tools are found, False otherwise.
        :rtype: bool
        """
        config = Config.load()
        missingTools = []

        tools = [
            ("ebook-viewer", config.ebookViewerPath),
            ("ebook-meta", config.ebookMetaPath),
            ("ebook-convert", config.ebookConvertPath)
        ]

        for toolName, toolPath in tools:
            if not toolPath or not os.path.exists(toolPath):
                missingTools.append(toolPath)

        if missingTools:
            message = (
                f"The following Calibre tools were not found: {', '.join(missingTools)}\n\n"
                "Please ensure Calibre is installed or update your configuration file "
                "with the correct paths.\n\n"
                f"Configuration file location: {Config.configPath()}\n\n"
                "The application will now exit."
            )
            QMessageBox.critical(self, "Missing Calibre Tools", message)
            return False

        return True

    def closeEvent(self, event):
        """
        Handle the window close event by performing cleanup.

        :param event: The close event triggered when the window is closed.
        :type event: QCloseEvent
        """
        Log.info("Shutting down")

        # Close the log viewer window
        if self.logViewerWindow:
            self.logViewerWindow.close()

        # Terminate the download worker
        if self.downloadWorker:
            Log.info("Terminating download worker")
            self.downloadWorker.terminate()
            self.downloadWorker.wait()

        # Terminate the import worker if running
        if self.importWorker:
            Log.info("Terminating import worker")
            self.importWorker.terminate()
            self.importWorker.wait()

        # Terminate the conversion worker if running
        if self.conversionWorker:
            Log.info("Terminating conversion worker")
            self.conversionWorker.terminate()
            self.conversionWorker.wait()

        # Terminate the Kindle thread
        if self.kindle:
            Log.info("Terminating Kindle thread")
            self.kindle.stop()
            self.kindle.wait()

        event.accept()

    def updateLibraryTabTitle(self):
        """
        Update the library tab title to include the number of books.
        """
        numBooks = self.libraryTab.librarySize()
        if numBooks == 0:
            self.tabs.setTabText(0, "Library")
        else:
            self.tabs.setTabText(0, f"Library ({numBooks})")

    def updateDownloadsTabTitle(self):
        """
        Update the downloads tab title to include the number of jobs.
        """
        numJobs = self.downloadWorker.queueSize()
        if numJobs == 0:
            self.tabs.setTabText(2, "Downloads")
        else:
            self.tabs.setTabText(2, f"Downloads ({numJobs})")

    def downloadJobQueued(self, job):
        """
        Handle a new download job being queued.

        :param job: The download job that was added to the queue.
        :type job: DownloadJob
        """
        self.downloadsTab.addJob(job)
        self.updateDownloadsTabTitle()

    def statusChanged(self, job):
        """
        Update the status of a download job.

        :param job: The download job whose status has changed.
        :type job: DownloadJob
        """
        self.downloadsTab.updateStatus(job)

    def downloadComplete(self, downloadResult):
        """
        Handle the completion of a download.

        :param downloadResult: The result of the completed download.
        :type downloadResult: DownloadResult
        """
        self.libraryTab.importBookFromDownloadResult(downloadResult)
        self.updateDownloadsTabTitle()
        self.updateLibraryTabTitle()
        self.libraryTab.refreshTable()

    def doImport(self, filePaths: list[str]):
        """
        Start the import worker to import books from given file paths.

        :param filePaths: The file paths of the books to import.
        :type filePaths: list[str]
        """
        self.importWorker = ImportThread(self.libraryTab.library, filePaths)

        # Connect import worker signals to slots
        self.importWorker.importStarted.connect(self.importStarted)
        self.importWorker.importSuccess.connect(self.importSuccess)
        self.importWorker.importError.connect(self.importError)
        self.importWorker.importFinished.connect(self.importFinished)

        self.importWorker.start()

    def importBooks(self):
        """
        Import books from selected files using a file dialog.
        """
        if self.importWorker:
            QMessageBox.warning(
                self,
                "Import in progress",
                "An import is already in progress. Please wait for it to finish before starting another import."
            )
            return

        filePaths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select books",
            "",
            ebookExtensionsFilterString
        )
        if not filePaths:
            return

        self.doImport(filePaths)

    def importBooksFromDirectory(self):
        """
        Import books from a selected directory using a file dialog.
        """
        if self.importWorker:
            QMessageBox.warning(
                self,
                "Import in progress",
                "An import is already in progress. Please wait for it to finish before starting another import."
            )
            return

        directory = QFileDialog.getExistingDirectory(self, "Select directory")
        if not directory:
            return

        # Collect all valid book files from the directory
        allFiles = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                extension = os.path.splitext(file)[1].lower()
                validExtensions = [f".{ext}" for ext in ebookExtensions]
                if extension in validExtensions:
                    filePath = os.path.join(root, file)
                    allFiles.append(filePath)

        if not allFiles:
            return

        self.doImport(allFiles)

    def resetLibrary(self):
        """
        Reset the library after user confirmation.
        """
        reply = QMessageBox.question(
            self,
            'Confirm Reset',
            'Are you sure you want to reset the library? This will delete all of your books.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.libraryTab.resetLibrary()
            self.updateLibraryTabTitle()

    def importStarted(self):
        """
        Handle the start of the import process.
        """
        self.importCounter = 0
        self.statusBar().showMessage("Importing books...")

    def importSuccess(self, book):
        """
        Handle the successful import of a book.

        :param book: The book object that was successfully imported.
        :type book: Book
        """
        self.statusBar().showMessage(f"Imported {book.title} by {book.author}")
        self.importCounter += 1

        # Refresh the table every 10 books
        if self.importCounter == 10:
            self.libraryTab.refreshTable()
            self.importCounter = 0

    def importError(self, book):
        """
        Handle an error during the import of a book.

        :param book: The book object that caused the import error.
        :type book: Book
        """
        self.statusBar().showMessage(f"Error importing {book.title} by {book.author}")

    def importFinished(self):
        """
        Handle the completion of the import process.
        """
        self.statusBar().showMessage("Import complete")
        self.updateLibraryTabTitle()
        self.libraryTab.refreshTable()
        self.importWorker = None

    def sendBooksToDevice(self, books: list[Book]):
        """
        Start the conversion worker to send books to the device.

        :param books: The books to send to the connected device.
        :type books: list[Book]
        """
        self.conversionWorker = ConversionThread(self.kindle, books)

        # Connect conversion worker signals to slots
        self.conversionWorker.conversionStarted.connect(self.conversionStarted)
        self.conversionWorker.conversionSuccess.connect(self.conversionSuccess)
        self.conversionWorker.conversionError.connect(self.conversionError)
        self.conversionWorker.conversionFinished.connect(self.conversionFinished)

        self.conversionWorker.start()

    def conversionStarted(self):
        """
        Handle the start of the conversion process.
        """
        self.statusBar().showMessage("Converting books...")

    def conversionSuccess(self, book):
        """
        Handle the successful conversion of a book.

        :param book: The book object that was successfully converted.
        :type book: Book
        """
        self.statusBar().showMessage(f"Converted {book.title} by {book.author}")
        self.libraryTab.newBookOnDevice(book)

    def conversionError(self, book):
        """
        Handle an error during the conversion of a book.

        :param book: The book object that caused the conversion error.
        :type book: Book
        """
        self.statusBar().showMessage(f"Error converting {book.title} by {book.author}")

    def conversionFinished(self):
        """
        Handle the completion of the conversion process.
        """
        self.statusBar().showMessage("Conversion complete")
        self.conversionWorker = None

    def showAboutBox(self):
        """
        Display the About dialog.
        """
        VERSION = "0.2.0"
        QMessageBox.about(
            self,
            f"Books v{VERSION}",
            "\"We are of opinion that instead of letting books grow moldy behind an iron grating, far from the vulgar gaze, it is better to let them wear out by being read.\"\n\n— Jules Verne"
        )

    def showLogViewer(self):
        """
        Show the log viewer window.
        """
        self.logViewerWindow = LogViewerWindow()
        self.logViewerWindow.show()

    @staticmethod
    def editConfigFile():
        configPath = Config.configPath()
        QDesktopServices.openUrl(QUrl.fromLocalFile(configPath))

    def dragEnterEvent(self, event):
        """
        Handle the drag enter event.

        :param event: The drag enter event.
        :type event: QDragEnterEvent
        """
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    extension = os.path.splitext(url.toLocalFile())[1].lower()
                    validExtensions = [f".{ext}" for ext in ebookExtensions]
                    if extension in validExtensions:
                        event.accept()
                        return
        event.ignore()

    def dropEvent(self, event):
        """
        Handle the drop event.

        :param event: The drop event.
        :type event: QDropEvent
        """
        if event.mimeData().hasUrls():
            filePaths = []
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    extension = os.path.splitext(url.toLocalFile())[1].lower()
                    validExtensions = [f".{ext}" for ext in ebookExtensions]
                    if extension in validExtensions:
                        filePaths.append(url.toLocalFile())
            if filePaths:
                self.doImport(filePaths)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()
