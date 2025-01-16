import asyncio
import os
from typing import AsyncGenerator

from PySide6.QtCore import QUrl, Qt
from PySide6.QtGui import QIcon, QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog, QMessageBox, QWidget,
    QVBoxLayout, QTabWidget, QSplitter, QLabel
)
from qasync import asyncSlot

from book import Book
from constants import ebook_extensions, ebook_extensions_filter_string
from download_thread import DownloadThread
from downloads_tab import DownloadsTab
from search_tab import SearchTab
from library import Library
from library_tab import LibraryTab
from log import Log
from settings import Settings
from themed_window import ThemedWindow


async def import_books(library: Library, file_paths: list[str]) -> AsyncGenerator[tuple[Book, bool], None]:
    Log.info("Import started.")
    for path in file_paths:
        try:
            book = library.add_book(path)
            if not book:
                Log.info(f"library.add_book returned None for {path}")
                yield book, False
            else:
                yield book, True
            await asyncio.sleep(0)
        except Exception as e:
            Log.info(f"Error importing {path}: {e}")
            import traceback
            traceback.print_exc()
            yield Book(path=path), False


class MainWindow(ThemedWindow):
    def __init__(self, library: Library) -> None:
        super().__init__()
        Log.info("Starting up")

        icon_path = "assets/icon.png"
        self.setWindowIcon(QIcon(icon_path))

        self._library = library
        self._download_thread = DownloadThread()
        self._import_thread = None
        self._conversion_thread = None

        self.setWindowTitle("Thoth")
        self.resize(1280, 800)
        self.setAcceptDrops(True)

        central_widget = QWidget(self)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.tab_widget = QTabWidget()

        self.library_tab = LibraryTab(self._library, self)
        self.library_tab.book_removed.connect(self.update_library_count)
        self.library_tab.send_to_device_requested.connect(self.send_books_to_device)
        self.tab_widget.addTab(self.library_tab, "Library")

        libgen_tab = QWidget()
        libgen_layout = QVBoxLayout(libgen_tab)
        libgen_layout.setContentsMargins(0, 0, 0, 0)

        self.libgen_splitter = QSplitter(Qt.Orientation.Vertical)
        self.search_tab = SearchTab(self, self._download_thread)

        downloads_container = QWidget()
        downloads_layout = QVBoxLayout(downloads_container)
        downloads_layout.setContentsMargins(0, 0, 0, 0)

        downloads_label = QLabel("Downloads")
        downloads_label.setStyleSheet("font-weight: bold; margin-left: 8px;")
        downloads_layout.addWidget(downloads_label)

        self.downloads_tab = DownloadsTab(self)
        downloads_layout.addWidget(self.downloads_tab)

        self.libgen_splitter.addWidget(self.search_tab)
        self.libgen_splitter.addWidget(downloads_container)
        self.libgen_splitter.setSizes([int(self.height() * 0.6), int(self.height() * 0.4)])

        libgen_layout.addWidget(self.libgen_splitter)
        self.tab_widget.addTab(libgen_tab, "LibGen")

        main_layout.addWidget(self.tab_widget)
        self.setCentralWidget(central_widget)

        self.setup_menus()
        self.statusBar().showMessage("Ready")

        self._download_thread.job_queued.connect(self.download_job_queued)
        self._download_thread.status_changed.connect(self.status_changed)
        self._download_thread.download_complete.connect(self.download_complete)
        self._download_thread.start()

        self.import_task = None

    def setup_menus(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("File")
        import_action = file_menu.addAction("Import Books...")
        import_from_directory_action = file_menu.addAction("Import Books from Directory...")
        import_action.triggered.connect(self.import_books)
        import_from_directory_action.triggered.connect(self.import_books_from_directory)

        # debug_menu = menu_bar.addMenu("Debug")
        # show_config_file_action = debug_menu.addAction("Edit Configuration File")
        # show_config_file_action.triggered.connect(self.edit_config_file)

        help_menu = menu_bar.addMenu("Help")
        about_action = help_menu.addAction("About")
        about_action.triggered.connect(self.show_about_box)

    def update_library_count(self):
        num_books = self.library_tab.library_size()
        if num_books == 0:
            self.setWindowTitle("Books")
        else:
            self.setWindowTitle(f"Books ({num_books})")

    def download_job_queued(self, job):
        self.downloads_tab.add_job(job)

    def status_changed(self, job):
        self.downloads_tab.update_status(job)

    def download_complete(self, download_result):
        self.library_tab.import_book_from_download_result(download_result)
        self.library_tab.refresh_table()

    async def do_import(self, file_paths: list[str]):
        self.statusBar().showMessage("Import started...")
        try:
            async for book, success in import_books(self.library_tab.library, file_paths):
                if success:
                    self.handle_import_success(book)
                else:
                    self.handle_import_error(book)
                await asyncio.sleep(0)
            self.handle_import_finished()
        except Exception as e:
            self.statusBar().showMessage(f"Import failed: {str(e)}")
            Log.info(f"Import failed: {str(e)}")
        finally:
            self.import_task = None

    @asyncSlot()
    async def import_books(self):
        if self.import_task and not self.import_task.done():
            QMessageBox.warning(
                self,
                "Import in progress",
                "An import is already in progress. Please wait for it to finish."
            )
            return

        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select books",
            "",
            ebook_extensions_filter_string,
            options=QFileDialog.Option.DontUseNativeDialog
        )

        if not file_paths:
            return

        self.import_task = asyncio.create_task(self.do_import(file_paths))

    @asyncSlot()
    async def import_books_from_directory(self):
        if self.import_task and not self.import_task.done():
            QMessageBox.warning(
                self,
                "Import in progress",
                "An import is already in progress. Please wait for it to finish."
            )
            return

        directory = QFileDialog.getExistingDirectory(self, "Select directory",
                                                     options=QFileDialog.Option.DontUseNativeDialog)
        if not directory:
            return

        all_files = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                extension = os.path.splitext(file)[1].lower()
                valid_extensions = [f".{ext}" for ext in ebook_extensions]
                if extension in valid_extensions:
                    file_path = os.path.join(root, file)
                    all_files.append(file_path)

        if not all_files:
            return

        await self.do_import(all_files)

    def reset_library(self):
        reply = QMessageBox.question(
            self,
            'Confirm Reset',
            'Are you sure you want to reset the library? This will delete all of your books.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.library_tab.reset_library()

    def handle_import_success(self, book: Book):
        self.statusBar().showMessage(f"Imported {book.title} by {book.author}")

    def handle_import_error(self, book: Book):
        self.statusBar().showMessage(f"Error importing {book.title} by {book.author}")

    def handle_import_finished(self):
        self.statusBar().showMessage("Import complete")
        self.library_tab.refresh_table()

    def send_books_to_device(self, books: list[Book]):
        pass

    def show_about_box(self):
        version = "0.5.0"
        QMessageBox.about(
            self,
            f"Thoth v{version}",
            "For know ye, O man, that all of the future is an open book to him who can read."
        )

    @staticmethod
    def edit_config_file():
        config_path = Settings.get_default_settings_path()
        QDesktopServices.openUrl(QUrl.fromLocalFile(config_path))

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    extension = os.path.splitext(url.toLocalFile())[1].lower()
                    valid_extensions = [f".{ext}" for ext in ebook_extensions]
                    if extension in valid_extensions:
                        event.accept()
                        return
        event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            file_paths = []
            urls = event.mimeData().urls()
            for url in urls:
                if url.isLocalFile():
                    extension = os.path.splitext(url.toLocalFile())[1].lower()
                    valid_extensions = [f".{ext}" for ext in ebook_extensions]
                    if extension in valid_extensions:
                        file_paths.append(url.toLocalFile())
            if file_paths:
                self.do_import(file_paths)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()