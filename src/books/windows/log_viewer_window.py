from PySide6.QtWidgets import QMainWindow, QTableView, QHeaderView, QCheckBox, QLabel, QWidget, QVBoxLayout, QHBoxLayout

from src.books.core.fonts import getMonospacedFont
from src.books.core.log import Log
from src.books.core.models.log_entry import LogEntry
from src.books.threads.log_file_loader_thread import LogFileLoaderThread
from src.books.view_models.log_table_model import LogTableModel


class LogViewerWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Log Viewer")
        self.resize(800, 600)

        self.logFilePath = Log.getLogFilePath()

        # Create the table view widget for displaying log content
        self.tableView = QTableView(self)
        self.logModel = LogTableModel()
        self.tableView.setModel(self.logModel)

        # Set preferred monospaced fonts
        font = getMonospacedFont()
        self.tableView.setFont(font)

        # Set up columns
        header = self.tableView.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setStretchLastSection(True)

        # Create the 'Follow' checkbox
        self.followCheckBox = QCheckBox("Follow", self)
        self.followCheckBox.setChecked(True)  # Default to checked

        # Create a label to display the log file path
        self.pathLabel = QLabel(self)
        self.pathLabel.setText(f"Log file: {self.logFilePath}")

        # Set up the central widget and layout
        centralWidget = QWidget()
        mainLayout = QVBoxLayout(centralWidget)
        mainLayout.setContentsMargins(0, 0, 0, 0)
        mainLayout.setSpacing(0)

        # Add the table view to the layout
        mainLayout.addWidget(self.tableView)

        # Add the checkbox and path label to the layout
        bottomLayout = QHBoxLayout()
        bottomLayout.setContentsMargins(5, 5, 5, 5)
        bottomLayout.addWidget(self.pathLabel)
        bottomLayout.addStretch()
        bottomLayout.addWidget(self.followCheckBox)

        mainLayout.addLayout(bottomLayout)

        self.setCentralWidget(centralWidget)

        # Start the worker thread to load the log file
        self.logFileLoader = None
        self.startLogFileLoader()

        # Connect to the log message signal for real-time updates
        self.logSignalEmitter = Log.getLogSignalEmitter()
        self.logSignalEmitter.messageLogged.connect(self.appendLogMessage)


    def startLogFileLoader(self):
        self.logFileLoader = LogFileLoaderThread(self.logFilePath)
        self.logFileLoader.logContentLoaded.connect(self.loadLogContent)
        self.logFileLoader.start()

    def loadLogContent(self, log_entries: list):
        self.logModel = LogTableModel(log_entries)
        self.tableView.setModel(self.logModel)
        self.tableView.resizeRowsToContents()

        if self.followCheckBox.isChecked():
            self.tableView.scrollToBottom()

    def appendLogMessage(self, log_dict: dict):
        entry = LogEntry(log_dict["timestamp"], log_dict["level"].upper(), log_dict["message"])
        self.logModel.appendLogEntry(entry)

        if self.followCheckBox.isChecked():
            self.tableView.scrollToBottom()
