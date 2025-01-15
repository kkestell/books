from typing import cast

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QTableView, QMenu

from search_result import SearchResult
from search_results_table_model import SearchResultsTableModel


class SearchTableView(QTableView):
    download_requested = Signal(SearchResult)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSortingEnabled(True)

    def show_context_menu(self, pos):
        context_menu = QMenu(self)
        download_action = context_menu.addAction("Download")

        action = context_menu.exec(self.viewport().mapToGlobal(pos))
        if action == download_action:
            self.download_selected_rows()

    def download_selected_rows(self):
        selected_indexes = self.selectionModel().selectedRows()
        for index in selected_indexes:
            search_model = cast(SearchResultsTableModel, self.model())
            search_result = search_model.get_row(index.row())
            self.download_requested.emit(search_result)

    def get_id_column_index(self):
        search_model = cast(SearchResultsTableModel, self.model())
        return search_model.headers.index('ID')
