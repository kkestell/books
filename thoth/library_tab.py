from PySide6.QtCore import Signal, QStringListModel, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QCompleter, QHeaderView

from book import Book
from library_table_model import LibraryTableModel
from multi_column_sort_proxy_model import MultiColumnSortProxyModel
from library_table_view import LibraryTableView


class LibraryTab(QWidget):
    book_removed = Signal(Book)
    send_to_device_requested = Signal(object)

    def __init__(self, library, kindle, parent=None):
        super().__init__(parent)

        self.kindle = kindle

        self.layout = QVBoxLayout(self)

        filter_layout = QHBoxLayout()

        self.author_filter_edit = QLineEdit()
        self.author_filter_edit.setPlaceholderText("Filter by Author")
        self.title_filter_edit = QLineEdit()
        self.title_filter_edit.setPlaceholderText("Filter by Title")
        self.series_filter_edit = QLineEdit()
        self.series_filter_edit.setPlaceholderText("Filter by Series")
        self.type_filter_combo_box = QComboBox()
        self.type_filter_combo_box.addItem("All Types")
        self.format_filter_combo_box = QComboBox()
        self.format_filter_combo_box.addItem("All Formats")

        all_books = library.get_all_books()
        authors = sorted(set(book.author for book in all_books))
        titles = sorted(set(book.title for book in all_books))
        series_list = sorted(set(book.series for book in all_books if book.series))
        types = sorted(set(book.type for book in all_books if book.type))
        formats = sorted(set(book.format for book in all_books if book.format))

        self.author_completer_model = QStringListModel(authors)
        self.author_completer = QCompleter(self.author_completer_model)
        self.author_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.author_filter_edit.setCompleter(self.author_completer)

        self.title_completer_model = QStringListModel(titles)
        self.title_completer = QCompleter(self.title_completer_model)
        self.title_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.title_filter_edit.setCompleter(self.title_completer)

        self.series_completer_model = QStringListModel(series_list)
        self.series_completer = QCompleter(self.series_completer_model)
        self.series_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.series_filter_edit.setCompleter(self.series_completer)

        self.type_filter_combo_box.addItems(types)

        self.format_filter_combo_box.addItems(formats)

        filter_layout.addWidget(self.author_filter_edit)
        filter_layout.addWidget(self.title_filter_edit)
        filter_layout.addWidget(self.series_filter_edit)
        filter_layout.addWidget(self.type_filter_combo_box)
        filter_layout.addWidget(self.format_filter_combo_box)

        self.layout.addLayout(filter_layout)

        self.library = library
        self.library.book_removed.connect(self.refresh_table)
        self.library.book_removed.connect(self.book_removed)

        self.model = LibraryTableModel(self.library)
        self.proxy_model = MultiColumnSortProxyModel()
        self.proxy_model.setSourceModel(self.model)
        self.proxy_model.setSortCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.proxy_model.setSortRole(Qt.ItemDataRole.DisplayRole)

        self.table_view = LibraryTableView(self)
        self.table_view.setModel(self.proxy_model)

        on_device_column = self.model.headers.index("On Device")
        author_column = self.model.headers.index("Author")
        title_column = self.model.headers.index("Title")
        series_column = self.model.headers.index("Series")
        year_column = self.model.headers.index("Year")
        type_column = self.model.headers.index("Type")
        format_column = self.model.headers.index("Format")
        added_column = self.model.headers.index("Added")

        self.proxy_model.sort(author_column, Qt.SortOrder.AscendingOrder)

        header = self.table_view.horizontalHeader()

        self.table_view.setColumnHidden(on_device_column, True)
        self.table_view.setColumnWidth(on_device_column, 26)

        header.setSectionResizeMode(author_column, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(title_column, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(series_column, QHeaderView.ResizeMode.Stretch)

        header.setSectionResizeMode(year_column, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(type_column, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(format_column, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(added_column, QHeaderView.ResizeMode.ResizeToContents)

        self.table_view.setColumnHidden(self.model.headers.index("ID"), True)

        self.table_view.send_to_device_requested.connect(self.send_to_device)

        self.layout.addWidget(self.table_view)

        self.author_filter_edit.textChanged.connect(self.on_author_filter_changed)
        self.title_filter_edit.textChanged.connect(self.on_title_filter_changed)
        self.series_filter_edit.textChanged.connect(self.on_series_filter_changed)
        self.type_filter_combo_box.currentIndexChanged.connect(self.on_type_filter_changed)
        self.format_filter_combo_box.currentIndexChanged.connect(self.on_format_filter_changed)

    def on_author_filter_changed(self, text):
        self.proxy_model.set_author_filter_pattern(text)

    def on_title_filter_changed(self, text):
        self.proxy_model.set_title_filter_pattern(text)

    def on_series_filter_changed(self, text):
        self.proxy_model.set_series_filter_pattern(text)

    def on_type_filter_changed(self, _index):
        selected_type = self.type_filter_combo_box.currentText()
        if selected_type == "All Types":
            self.proxy_model.set_type_filter(None)
        else:
            self.proxy_model.set_type_filter(selected_type)

    def on_format_filter_changed(self, _index):
        selected_format = self.format_filter_combo_box.currentText()
        if selected_format == "All Formats":
            self.proxy_model.set_format_filter(None)
        else:
            self.proxy_model.set_format_filter(selected_format)

    def import_book_from_download_result(self, download_result):
        self.import_book(download_result.file_path, download_result.job)

    def import_book(self, file_path, job=None):
        self.library.add_book(file_path, job)

    def refresh_table(self):
        self.model.refresh_books()
        self.model.beginResetModel()
        self.model.endResetModel()
        self.table_view.resizeColumnsToContents()
        self.update_completers()

    def update_completers(self):
        all_books = self.library.get_all_books()
        authors = sorted(set(book.author for book in all_books))
        titles = sorted(set(book.title for book in all_books))
        series_list = sorted(set(book.series for book in all_books if book.series))
        types = sorted(set(book.type for book in all_books if book.type))
        formats = sorted(set(book.format for book in all_books if book.format))

        self.author_completer_model.setStringList(authors)
        self.title_completer_model.setStringList(titles)
        self.series_completer_model.setStringList(series_list)

        current_type = self.type_filter_combo_box.currentText()
        self.type_filter_combo_box.clear()
        self.type_filter_combo_box.addItem("All Types")
        self.type_filter_combo_box.addItems(types)

        index = self.type_filter_combo_box.findText(current_type)
        if index >= 0:
            self.type_filter_combo_box.setCurrentIndex(index)
        else:
            self.type_filter_combo_box.setCurrentIndex(0)  # Default to 'All'

        current_format = self.format_filter_combo_box.currentText()
        self.format_filter_combo_box.clear()
        self.format_filter_combo_box.addItem("All Formats")
        self.format_filter_combo_box.addItems(formats)

        index = self.format_filter_combo_box.findText(current_format)
        if index >= 0:
            self.format_filter_combo_box.setCurrentIndex(index)
        else:
            self.format_filter_combo_box.setCurrentIndex(0)

    def library_size(self) -> int:
        return self.library.num_books

    def reset_library(self):
        self.library.reset()
        self.refresh_table()

    def kindle_books_changed(self, books):
        self.model.set_kindle_books(books)
        self.refresh_table()

    def kindle_connected(self):
        self.table_view.set_kindle_connected(True)

    def kindle_disconnected(self):
        self.table_view.set_kindle_connected(False)

    def send_to_device(self, books):
        self.send_to_device_requested.emit(books)

    def new_book_on_device(self, book):
        self.table_view.new_book_on_device(book)
        self.refresh_table()
