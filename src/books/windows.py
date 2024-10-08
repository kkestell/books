import os
from pathlib import Path

from PySide6.QtCore import QThread, Signal, Qt
from PySide6.QtGui import QTextCursor, QFont, QFontDatabase, QTextOption
from PySide6.QtWidgets import (
    QMainWindow, QTextEdit, QVBoxLayout, QWidget, QCheckBox, QHBoxLayout,
    QLabel
)
from log import Log


class LogFileLoader(QThread):
    """
    Worker thread to efficiently load the last N lines of a log file.

    :signal logContentLoaded: Emitted when the content of the log file is loaded.
    """
    logContentLoaded = Signal(str)

    def __init__(self, logFilePath: Path):
        """
        Initialize the LogFileLoader with the path to the log file.

        :param logFilePath: The path to the log file.
        :type logFilePath: Path
        """
        super().__init__()
        self.logFilePath = logFilePath
        self.numLines = 1000  # Number of lines to read

    def run(self):
        """
        Read the last N lines of the log file and emit them when done.
        """
        try:
            # Efficiently read the last N lines of the file
            lines = self.tail(self.logFilePath, self.numLines)
            content = ''.join(lines)
            self.logContentLoaded.emit(content)
        except Exception as e:
            self.logContentLoaded.emit(f"Error reading log file: {e}")

    @staticmethod
    def tail(filename: Path, n: int) -> list:
        """
        Read the last n lines from a file efficiently.

        :param filename: The path to the file.
        :type filename: Path
        :param n: The number of lines to read.
        :type n: int
        :return: A list of the last n lines in the file.
        :rtype: list of str
        """
        with open(filename, 'rb') as f:
            # Move to the end of the file
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            block_size = 1024
            blocks = []
            lines_found = 0
            position = file_size

            while position > 0 and lines_found < n:
                if position - block_size > 0:
                    position -= block_size
                else:
                    block_size = position
                    position = 0

                f.seek(position)
                block = f.read(block_size)
                blocks.insert(0, block)
                lines_found += block.count(b'\n')

            content = b''.join(blocks)
            lines = content.splitlines()[-n:]
            return [line.decode('utf-8', errors='replace') + '\n' for line in lines]


class LogViewerWindow(QMainWindow):
    """
    Main window for displaying log file content with real-time updates.
    """

    def __init__(self):
        """
        Initialize the LogViewerWindow.
        """
        super().__init__()

        self.setWindowTitle("Log Viewer")
        self.resize(800, 600)

        self.logFilePath = Log.getLogFilePath()

        # Create the text edit widget for displaying log content
        self.textEdit = QTextEdit(self)
        self.textEdit.setReadOnly(True)

        # Set preferred monospaced fonts
        font = self.getPreferredMonospacedFont()
        self.textEdit.setFont(font)

        # Disable word wrap
        self.textEdit.setWordWrapMode(QTextOption.WrapMode.NoWrap)

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

        # Add the text edit to the layout
        mainLayout.addWidget(self.textEdit)

        # Add the checkbox and path label to the layout
        bottomLayout = QHBoxLayout()
        bottomLayout.setContentsMargins(5, 5, 5, 5)
        bottomLayout.addWidget(self.pathLabel)
        bottomLayout.addStretch()
        bottomLayout.addWidget(self.followCheckBox)

        mainLayout.addLayout(bottomLayout)

        self.setCentralWidget(centralWidget)

        # Show a loading message initially
        self.textEdit.setPlainText("Loading log file...")
        self.textEdit.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Start the worker thread to load the log file
        self.logFileLoader = None
        self.startLogFileLoader()

        # Connect to the log message signal for real-time updates
        self.logSignalEmitter = Log.getLogSignalEmitter()
        self.logSignalEmitter.logMessageSignal.connect(self.appendLogMessage)

    @staticmethod
    def getPreferredMonospacedFont() -> QFont:
        """
        Get a preferred monospaced font, depending on the platform.

        :return: The preferred monospaced font.
        :rtype: QFont
        """
        fontDatabase = QFontDatabase()
        preferredFonts = [
            "Cascadia Code",      # Windows
            "Consolas",           # Windows
            "Courier New",        # Windows
            "Menlo",              # macOS
            "Monaco",             # macOS
            "Ubuntu Mono",        # Ubuntu
            "DejaVu Sans Mono",   # Linux
            "Liberation Mono",    # Linux
            "Noto Mono",          # Linux
            "monospace"           # Generic monospace
        ]

        for fontName in preferredFonts:
            if fontName in fontDatabase.families():
                font = QFont(fontName)
                font.setStyleHint(QFont.StyleHint.Monospace)
                return font

        # If none of the preferred fonts are available, use the system's default monospace font
        font = QFont()
        font.setStyleHint(QFont.StyleHint.Monospace)
        return font

    def startLogFileLoader(self):
        """
        Start the worker thread to load the log file content.
        """
        self.logFileLoader = LogFileLoader(self.logFilePath)
        self.logFileLoader.logContentLoaded.connect(self.loadLogContent)
        self.logFileLoader.start()

    def loadLogContent(self, content: str):
        """
        Load the log content into the text edit widget.

        :param content: The content of the log file.
        :type content: str
        """
        # Clear the loading message alignment
        self.textEdit.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.textEdit.setPlainText(content)

        if self.followCheckBox.isChecked():
            # Move cursor to the start of the last line
            self.textEdit.moveCursor(QTextCursor.MoveOperation.End)
            self.textEdit.moveCursor(QTextCursor.MoveOperation.StartOfLine)
            self.textEdit.ensureCursorVisible()

    def appendLogMessage(self, message: str):
        """
        Append a new log message to the text edit widget.

        :param message: The new log message to append.
        :type message: str
        """
        # Append the new log message to the text edit
        self.textEdit.append(message)

        if self.followCheckBox.isChecked():
            # Move cursor to the start of the last line
            self.textEdit.moveCursor(QTextCursor.MoveOperation.End)
            self.textEdit.moveCursor(QTextCursor.MoveOperation.StartOfLine)
            self.textEdit.ensureCursorVisible()
