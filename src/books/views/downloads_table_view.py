from typing import cast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableView, QMenu

from src.books.view_models.downloads_table_model import DownloadsTableModel


class DownloadsTableView(QTableView):
    """
    Table view for displaying download jobs.
    """
    def __init__(self, parent=None):
        """
        Initialize the DownloadsTableView.

        :param parent: The parent widget.
        :type parent: QWidget, optional
        """
        super().__init__(parent)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.showContextMenu)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

    def showContextMenu(self, pos):
        """
        Display the context menu at the given position.

        :param pos: The position to show the context menu.
        :type pos: QPoint
        """
        contextMenu = QMenu(self)
        clearAction = contextMenu.addAction("Clear Completed")

        action = contextMenu.exec(self.viewport().mapToGlobal(pos))
        if action == clearAction:
            self.clearCompleted()

    def clearCompleted(self):
        """
        Clear all completed download jobs from the model.
        """
        downloadModel = cast(DownloadsTableModel, self.model())
        downloadModel.clearCompleted()
