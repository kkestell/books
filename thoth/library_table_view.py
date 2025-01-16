import os
import urllib.parse
from typing import cast

from PySide6.QtCore import Signal, Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QTableView, QMenu, QMessageBox

from book import Book
from fonts import get_sans_serif_font
from edit_book_dialog import EditBookDialog
from multi_column_sort_proxy_model import MultiColumnSortProxyModel
from library_table_model import LibraryTableModel


class LibraryTableView(QTableView):
    send_to_device_requested = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.is_kindle_connected = False

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSortingEnabled(True)
        self.setFont(get_sans_serif_font())

    def show_context_menu(self, pos):
        context_menu = QMenu(self)

        open_action = context_menu.addAction("Open")
        edit_action = context_menu.addAction("Edit...")
        context_menu.addSeparator()
        research_menu = context_menu.addMenu("Research")
        research_author_action = research_menu.addAction("Author")
        research_title_action = research_menu.addAction("Title")
        context_menu.addSeparator()
        show_action = context_menu.addAction("Show in Folder")
        send_to_device_action = context_menu.addAction("Send to Device")
        context_menu.addSeparator()
        delete_action = context_menu.addAction("Delete...")

        if not self.is_kindle_connected:
            send_to_device_action.setDisabled(True)

        action = context_menu.exec(self.viewport().mapToGlobal(pos))

        if action == open_action:
            self.handle_open_action(pos)
        elif action == edit_action:
            self.handle_edit_action(pos)
        elif action == research_author_action:
            self.handle_research_author_action(pos)
        elif action == research_title_action:
            self.handle_research_title_action(pos)
        elif action == delete_action:
            self.handle_delete_action()
        elif action == show_action:
            self.handle_show_action(pos)
        elif action == send_to_device_action:
            self.handle_send_to_device_action()

    def handle_edit_action(self, pos):
        book = self._get_book_from_index(self.indexAt(pos))
        if not book:
            return

        edit_dialog = EditBookDialog(book)
        edit_dialog.closed.connect(self.on_dialog_closed)
        edit_dialog.exec()

    def handle_research_author_action(self, pos):
        book = self._get_book_from_index(self.indexAt(pos))
        if not book:
            return

        url_encoded_author_name = urllib.parse.quote(book.author)
        url = f"https://www.fantasticfiction.com/search/?searchfor=author&keywords={url_encoded_author_name}"
        QDesktopServices.openUrl(QUrl(url))

    def handle_research_title_action(self, pos):
        book = self._get_book_from_index(self.indexAt(pos))
        if not book:
            return

        url_encoded_title = urllib.parse.quote(book.title)
        url = f"https://www.fantasticfiction.com/search/?searchfor=book&keywords={url_encoded_title}"
        QDesktopServices.openUrl(QUrl(url))

    def handle_delete_action(self):
        selected_indexes = self.selectionModel().selectedRows()
        if not selected_indexes:
            return

        if len(selected_indexes) == 1:
            message = "Are you sure you want to delete this book?"
        else:
            message = f"Are you sure you want to delete these {len(selected_indexes)} books?"

        reply = QMessageBox.question(
            self, 'Confirm Delete', message,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        proxy_model = cast(MultiColumnSortProxyModel, self.model())
        source_model = cast(LibraryTableModel, proxy_model.sourceModel())

        for index in sorted(selected_indexes, reverse=True, key=lambda idx: idx.row()):
            book = self._get_book_from_index(index)
            if book:
                source_index = proxy_model.mapToSource(index)
                source_model.library.remove_book(book)
                source_model.removeRow(source_index.row())

        self.model().beginResetModel()
        self.model().endResetModel()

    def handle_open_action(self, pos):
        book = self._get_book_from_index(self.indexAt(pos))
        if not book:
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(book.path))

    def handle_show_action(self, pos):
        book = self._get_book_from_index(self.indexAt(pos))
        if not book:
            return

        QDesktopServices.openUrl(QUrl.fromLocalFile(os.path.dirname(book.path)))

    def handle_send_to_device_action(self):
        selected_indexes = self.selectionModel().selectedRows()
        if not selected_indexes:
            return

        books_not_already_on_device = []
        proxy_model = cast(MultiColumnSortProxyModel, self.model())
        source_model = cast(LibraryTableModel, proxy_model.sourceModel())

        for index in selected_indexes:
            book = self._get_book_from_index(index)
            if not book:
                continue

            source_index = proxy_model.mapToSource(index)
            on_device = source_model.data(
                source_index.siblingAtColumn(source_model.headers.index('On Device')),
                Qt.ItemDataRole.DisplayRole
            )
            if on_device != "✓":
                books_not_already_on_device.append(book)

        if not books_not_already_on_device:
            return

        self.send_to_device_requested.emit(books_not_already_on_device)

    def on_dialog_closed(self, book):
        proxy_model = cast(MultiColumnSortProxyModel, self.model())
        source_model = cast(LibraryTableModel, proxy_model.sourceModel())
        source_model.library.update_book(book)
        source_model.update_book(book)

    def set_kindle_connected(self, connected):
        self.is_kindle_connected = connected
        if connected:
            self.setColumnHidden(0, False)
        else:
            self.setColumnHidden(0, True)

    def new_book_on_device(self, book):
        proxy_model = cast(MultiColumnSortProxyModel, self.model())
        source_model = cast(LibraryTableModel, proxy_model.sourceModel())
        source_model.new_book_on_device(book)

    def _get_book_from_index(self, index) -> Book | None:
        if not index.isValid():
            return None

        proxy_model = cast(MultiColumnSortProxyModel, self.model())
        source_index = proxy_model.mapToSource(index)
        source_model = cast(LibraryTableModel, proxy_model.sourceModel())

        book_id = source_model.data(
            source_index.siblingAtColumn(source_model.headers.index('ID')),
            Qt.ItemDataRole.DisplayRole
        )

        return source_model.library.get_book_by_id(book_id)
