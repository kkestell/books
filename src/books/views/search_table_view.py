from typing import cast

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import QTableView, QMenu

from src.books.core.models.search_result import SearchResult
from src.books.view_models.search_results_table_model import SearchResultsTableModel


class SearchTableView(QTableView):
    """
    Table view for displaying search results.

    :signal downloadRequested: Emitted when a search result is requested to be downloaded.
    """
    downloadRequested = Signal(SearchResult)

    def __init__(self, parent=None):
        """
        Initialize the SearchTableView.

        :param parent: The parent widget.
        :type parent: QWidget, optional
        """
        super().__init__(parent)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSortingEnabled(True)

    def showContextMenu(self, pos):
        """
        Display the context menu at the given position.

        :param pos: The position to show the context menu.
        :type pos: QPoint
        """
        contextMenu = QMenu(self)
        downloadAction = contextMenu.addAction("Download")

        action = contextMenu.exec(self.viewport().mapToGlobal(pos))
        if action == downloadAction:
            self.downloadSelectedRows()

    def downloadSelectedRows(self):
        """
        Emit a signal to download the selected search results.
        """
        selectedIndexes = self.selectionModel().selectedRows()
        for index in selectedIndexes:
            searchModel = cast(SearchResultsTableModel, self.model())
            searchResult = searchModel.getRow(index.row())
            self.downloadRequested.emit(searchResult)

    def getIdColumnIndex(self):
        """
        Get the index of the 'ID' column.

        :return: The index of the 'ID' column.
        :rtype: int
        """
        searchModel = cast(SearchResultsTableModel, self.model())
        return searchModel.headers.index('ID')
