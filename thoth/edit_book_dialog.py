from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QLineEdit, QComboBox, QTextEdit, \
    QSizePolicy, QStyle

import constants
from metadata_search_dialog import MetadataSearchDialog
from book import Book


class EditBookDialog(QDialog):
    closed = Signal(Book)

    def __init__(self, book: Book, parent=None):
        super().__init__(parent)
        self.book = book
        self.setWindowTitle("Edit Book")
        self.layout = QVBoxLayout(self)

        search_button = QPushButton("Search")
        search_button.clicked.connect(self.open_search_dialog)
        search_button_layout = QHBoxLayout()
        search_button_layout.addWidget(search_button)
        search_button_layout.addStretch(1)

        author = self.book.author or ""
        series = self.book.series or ""
        series_number = str(self.book.series_number) if self.book.series_number else ""
        title = self.book.title or ""
        published = str(self.book.published) if self.book.published else ""
        book_type = self.book.type or ""
        description = self.book.description or ""

        title_layout = QVBoxLayout()
        title_layout.addWidget(QLabel("Title"))
        self.title_field = QLineEdit(title)
        title_layout.addWidget(self.title_field)

        type_layout = QVBoxLayout()
        type_layout.addWidget(QLabel("Type"))
        self.type_field = QComboBox()
        self.type_field.addItems(constants.ebook_types)
        self.type_field.setCurrentText(book_type)
        type_layout.addWidget(self.type_field)

        title_type_layout = QHBoxLayout()
        title_type_layout.addLayout(title_layout)
        title_type_layout.addLayout(type_layout)

        author_layout = QVBoxLayout()
        author_layout.addWidget(QLabel("Author"))
        self.author_field = QLineEdit(author)
        author_layout.addWidget(self.author_field)

        published_layout = QVBoxLayout()
        published_layout.addWidget(QLabel("Published"))
        self.published_field = QLineEdit(published)
        self.published_field.setMaximumWidth(100)
        published_layout.addWidget(self.published_field)

        author_published_layout = QHBoxLayout()
        author_published_layout.addLayout(author_layout)
        author_published_layout.addLayout(published_layout)

        series_layout = QVBoxLayout()
        series_layout.addWidget(QLabel("Series"))
        self.series_field = QLineEdit(series)
        series_layout.addWidget(self.series_field)

        series_number_layout = QVBoxLayout()
        series_number_layout.addWidget(QLabel("Series Number"))
        self.series_number_field = QLineEdit(series_number)
        self.series_number_field.setMaximumWidth(100)
        series_number_layout.addWidget(self.series_number_field)

        series_series_number_layout = QHBoxLayout()
        series_series_number_layout.addLayout(series_layout)
        series_series_number_layout.addLayout(series_number_layout)

        description_layout = QVBoxLayout()
        description_layout.addWidget(QLabel("Description"))
        self.description_field = QTextEdit(description)
        self.description_field.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        description_layout.addWidget(self.description_field)

        save_button = QPushButton("Save")
        pixmap = QStyle.StandardPixmap.SP_DialogSaveButton
        icon = self.style().standardIcon(pixmap)
        save_button.setIcon(icon)
        save_button.clicked.connect(self.save_changes)
        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(save_button)
        button_layout.addStretch(1)

        self.layout.addLayout(search_button_layout)
        self.layout.addLayout(title_type_layout)
        self.layout.addLayout(author_published_layout)
        self.layout.addLayout(series_series_number_layout)
        self.layout.addLayout(description_layout)
        self.layout.addLayout(button_layout)

        self.setMinimumSize(600, 400)

    def save_changes(self):
        author = self.author_field.text() or None
        series = self.series_field.text() or None

        try:
            series_number = int(self.series_number_field.text()) if self.series_number_field.text() else None
        except ValueError:
            series_number = None

        if not series or series_number is None:
            series = None
            series_number = None

        title = self.title_field.text() or None
        published = self.published_field.text() or None
        book_type = self.type_field.currentText() or None
        description = self.description_field.toPlainText() or None

        self.book.author = author
        self.book.series = series
        self.book.series_number = series_number
        self.book.title = title
        self.book.published = published
        self.book.type = book_type
        self.book.description = description

        self.accept()
        self.closed.emit(self.book)

    def open_search_dialog(self):
        search_dialog = MetadataSearchDialog(self.book, self)
        search_dialog.search_completed.connect(self.update_fields_from_search)
        search_dialog.exec()

    def update_fields_from_search(self, results: dict):
        self.author_field.setText(results.get("author", ""))
        self.title_field.setText(results.get("title", ""))
        self.published_field.setText(results.get("published", ""))
        self.description_field.setPlainText(results.get("description", ""))
