from datetime import datetime

from PySide6.QtCore import QSortFilterProxyModel, Qt, QModelIndex

from src.books.view_models.library_table_model import LibraryTableModel


class MultiColumnSortProxyModel(QSortFilterProxyModel):
    """
    Proxy model for multi-column sorting and filtering.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.titleFilterPattern = ''
        self.authorFilterPattern = ''
        self.seriesFilterPattern = ''
        self.typeFilter = None
        self.formatFilter = None

    def setTitleFilterPattern(self, pattern):
        self.titleFilterPattern = pattern
        self.invalidateFilter()

    def setAuthorFilterPattern(self, pattern):
        self.authorFilterPattern = pattern
        self.invalidateFilter()

    def setSeriesFilterPattern(self, pattern):
        self.seriesFilterPattern = pattern
        self.invalidateFilter()

    def setTypeFilter(self, type_value):
        self.typeFilter = type_value
        self.invalidateFilter()

    def setFormatFilter(self, format_value):
        self.formatFilter = format_value
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()

        if not isinstance(model, LibraryTableModel):
            return super().filterAcceptsRow(source_row, source_parent)

        # Filter based on title, author, series, and type
        indexTitle = model.index(source_row, model.headers.index("Title"), source_parent)
        indexAuthor = model.index(source_row, model.headers.index("Author"), source_parent)
        indexSeries = model.index(source_row, model.headers.index("Series"), source_parent)
        indexType = model.index(source_row, model.headers.index("Type"), source_parent)
        indexFormat = model.index(source_row, model.headers.index("Format"), source_parent)

        dataTitle = model.data(indexTitle, Qt.ItemDataRole.DisplayRole) or ''
        dataAuthor = model.data(indexAuthor, Qt.ItemDataRole.DisplayRole) or ''
        dataSeries = model.data(indexSeries, Qt.ItemDataRole.DisplayRole) or ''
        dataType = model.data(indexType, Qt.ItemDataRole.DisplayRole) or ''
        dataFormat = model.data(indexFormat, Qt.ItemDataRole.DisplayRole) or ''

        # Case-insensitive matching
        if self.titleFilterPattern and self.titleFilterPattern.lower() not in dataTitle.lower():
            return False

        if self.authorFilterPattern and self.authorFilterPattern.lower() not in dataAuthor.lower():
            return False

        if self.seriesFilterPattern and self.seriesFilterPattern.lower() not in dataSeries.lower():
            return False

        if self.typeFilter and self.typeFilter != dataType:
            return False

        if self.formatFilter and self.formatFilter != dataFormat:
            return False

        return True

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        """
        Compare two items for sorting.

        :param left: The left index to compare.
        :type left: QModelIndex
        :param right: The right index to compare.
        :type right: QModelIndex
        :return: True if left is less than right, False otherwise.
        :rtype: bool
        """
        model = self.sourceModel()

        if not isinstance(model, LibraryTableModel):
            return super().lessThan(left, right)

        authorIndex = model.headers.index("Author")
        seriesIndex = model.headers.index("Series")
        titleIndex = model.headers.index("Title")
        publishedIndex = model.headers.index("Year")

        if self.sortColumn() == authorIndex:
            leftAuthor = model.data(left.siblingAtColumn(authorIndex), Qt.ItemDataRole.DisplayRole).lower()
            rightAuthor = model.data(right.siblingAtColumn(authorIndex), Qt.ItemDataRole.DisplayRole).lower()

            leftSeries = model.data(left.siblingAtColumn(seriesIndex), Qt.ItemDataRole.DisplayRole) or ''
            leftSeries = leftSeries.lower()

            rightSeries = model.data(right.siblingAtColumn(seriesIndex), Qt.ItemDataRole.DisplayRole) or ''
            rightSeries = rightSeries.lower()

            leftTitle = model.data(left.siblingAtColumn(titleIndex), Qt.ItemDataRole.DisplayRole).lower()
            rightTitle = model.data(right.siblingAtColumn(titleIndex), Qt.ItemDataRole.DisplayRole).lower()

            if leftAuthor != rightAuthor:
                return leftAuthor < rightAuthor
            elif leftSeries != rightSeries:
                return leftSeries < rightSeries
            return leftTitle < rightTitle
        elif self.sortColumn() == publishedIndex:
            leftDate = model.data(left.siblingAtColumn(publishedIndex), Qt.ItemDataRole.DisplayRole)
            rightDate = model.data(right.siblingAtColumn(publishedIndex), Qt.ItemDataRole.DisplayRole)

            try:
                leftDateParsed = datetime.strptime(leftDate, "%Y-%m-%d")
            except (ValueError, TypeError):
                leftDateParsed = datetime.min

            try:
                rightDateParsed = datetime.strptime(rightDate, "%Y-%m-%d")
            except (ValueError, TypeError):
                rightDateParsed = datetime.min

            return leftDateParsed < rightDateParsed
        else:
            return super().lessThan(left, right)
