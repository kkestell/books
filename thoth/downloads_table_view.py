from typing import cast

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableView, QMenu

from downloads_table_model import DownloadsTableModel


class DownloadsTableView(QTableView):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)

    def show_context_menu(self, pos):
        context_menu = QMenu(self)
        clear_action = context_menu.addAction("Clear Completed")

        action = context_menu.exec(self.viewport().mapToGlobal(pos))
        if action == clear_action:
            self.clear_completed()

    def clear_completed(self):
        download_model = cast(DownloadsTableModel, self.model())
        download_model.clear_completed()
