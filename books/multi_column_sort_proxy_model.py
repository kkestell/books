from datetime import datetime

from PySide6.QtCore import QSortFilterProxyModel, Qt, QModelIndex

from library_table_model import LibraryTableModel


class MultiColumnSortProxyModel(QSortFilterProxyModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title_filter_pattern = ''
        self.author_filter_pattern = ''
        self.series_filter_pattern = ''
        self.type_filter = None
        self.format_filter = None

    def set_title_filter_pattern(self, pattern):
        self.title_filter_pattern = pattern
        self.invalidateFilter()

    def set_author_filter_pattern(self, pattern):
        self.author_filter_pattern = pattern
        self.invalidateFilter()

    def set_series_filter_pattern(self, pattern):
        self.series_filter_pattern = pattern
        self.invalidateFilter()

    def set_type_filter(self, type_value):
        self.type_filter = type_value
        self.invalidateFilter()

    def set_format_filter(self, format_value):
        self.format_filter = format_value
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        model = self.sourceModel()

        if not isinstance(model, LibraryTableModel):
            return super().filterAcceptsRow(source_row, source_parent)

        index_title = model.index(source_row, model.headers.index("Title"), source_parent)
        index_author = model.index(source_row, model.headers.index("Author"), source_parent)
        index_series = model.index(source_row, model.headers.index("Series"), source_parent)
        index_type = model.index(source_row, model.headers.index("Type"), source_parent)
        index_format = model.index(source_row, model.headers.index("Format"), source_parent)

        data_title = model.data(index_title, Qt.ItemDataRole.DisplayRole) or ''
        data_author = model.data(index_author, Qt.ItemDataRole.DisplayRole) or ''
        data_series = model.data(index_series, Qt.ItemDataRole.DisplayRole) or ''
        data_type = model.data(index_type, Qt.ItemDataRole.DisplayRole) or ''
        data_format = model.data(index_format, Qt.ItemDataRole.DisplayRole) or ''

        if self.title_filter_pattern and self.title_filter_pattern.lower() not in data_title.lower():
            return False

        if self.author_filter_pattern and self.author_filter_pattern.lower() not in data_author.lower():
            return False

        if self.series_filter_pattern and self.series_filter_pattern.lower() not in data_series.lower():
            return False

        if self.type_filter and self.type_filter != data_type:
            return False

        if self.format_filter and self.format_filter != data_format:
            return False

        return True

    def lessThan(self, left: QModelIndex, right: QModelIndex) -> bool:
        model = self.sourceModel()

        if not isinstance(model, LibraryTableModel):
            return super().lessThan(left, right)

        author_index = model.headers.index("Author")
        series_index = model.headers.index("Series")
        title_index = model.headers.index("Title")
        published_index = model.headers.index("Year")

        if self.sortColumn() == author_index:
            left_author = model.data(left.siblingAtColumn(author_index), Qt.ItemDataRole.DisplayRole).lower()
            right_author = model.data(right.siblingAtColumn(author_index), Qt.ItemDataRole.DisplayRole).lower()

            left_series = model.data(left.siblingAtColumn(series_index), Qt.ItemDataRole.DisplayRole) or ''
            left_series = left_series.lower()

            right_series = model.data(right.siblingAtColumn(series_index), Qt.ItemDataRole.DisplayRole) or ''
            right_series = right_series.lower()

            left_title = model.data(left.siblingAtColumn(title_index), Qt.ItemDataRole.DisplayRole).lower()
            right_title = model.data(right.siblingAtColumn(title_index), Qt.ItemDataRole.DisplayRole).lower()

            if left_author != right_author:
                return left_author < right_author
            elif left_series != right_series:
                return left_series < right_series
            return left_title < right_title
        elif self.sortColumn() == published_index:
            left_date = model.data(left.siblingAtColumn(published_index), Qt.ItemDataRole.DisplayRole)
            right_date = model.data(right.siblingAtColumn(published_index), Qt.ItemDataRole.DisplayRole)

            try:
                left_date_parsed = datetime.strptime(left_date, "%Y-%m-%d")
            except (ValueError, TypeError):
                left_date_parsed = datetime.min

            try:
                right_date_parsed = datetime.strptime(right_date, "%Y-%m-%d")
            except (ValueError, TypeError):
                right_date_parsed = datetime.min

            return left_date_parsed < right_date_parsed
        else:
            return super().lessThan(left, right)
