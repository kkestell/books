from PySide6.QtCore import Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout, QPushButton, QHBoxLayout, QLabel, QLineEdit, QComboBox, QTextEdit, \
    QSizePolicy, QStyle

from src.books.dialogs.metadata_search_dialog import MetadataSearchDialog
from src.books.core.models.book import Book


class EditBookDialog(QDialog):
    """
    Dialog window for editing book metadata.

    :signal closed: Emitted when the dialog is closed, carrying the edited book object.
    """
    closed = Signal(Book)

    def __init__(self, book: Book, parent=None):
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

        # Search button at the top (left aligned)
        searchButton = QPushButton("Search")
        searchButton.clicked.connect(self.openSearchDialog)
        searchButtonLayout = QHBoxLayout()
        searchButtonLayout.addWidget(searchButton)
        searchButtonLayout.addStretch(1)  # Pushes the button to the left

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
        pixmapi = QStyle.StandardPixmap.SP_DialogSaveButton
        icon = self.style().standardIcon(pixmapi)
        saveButton.setIcon(icon)
        saveButton.clicked.connect(self.saveChanges)
        buttonLayout = QHBoxLayout()
        buttonLayout.addStretch(1)
        buttonLayout.addWidget(saveButton)
        buttonLayout.addStretch(1)

        # Add all layouts to the main layout
        self.layout.addLayout(searchButtonLayout)  # Add the search button layout at the top
        self.layout.addLayout(titleTypeLayout)
        self.layout.addLayout(authorPublishedLayout)
        self.layout.addLayout(seriesSeriesNumberLayout)
        self.layout.addLayout(descriptionLayout)
        self.layout.addLayout(buttonLayout)

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

    def openSearchDialog(self):
        """Open the SearchMetadataDialog."""
        search_dialog = MetadataSearchDialog(self.book, self)
        search_dialog.searchCompleted.connect(self.updateFieldsFromSearch)
        search_dialog.exec()

    def updateFieldsFromSearch(self, results: dict):
        """
        Update fields with search results.

        :param results: The search results to update the fields with.
        :type results: dict
        """
        self.authorField.setText(results.get("author", ""))
        self.titleField.setText(results.get("title", ""))
        self.publishedField.setText(results.get("published", ""))
        self.descriptionField.setPlainText(results.get("description", ""))
