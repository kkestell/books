import os
import re
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from src.books.core.models.log_entry import LogEntry


class LogFileLoaderThread(QThread):
    logContentLoaded = Signal(list)

    def __init__(self, logFilePath: Path):
        super().__init__()
        self.logFilePath = logFilePath
        self.numLines = 1000

    def run(self):
        try:
            lines = self.tail(self.logFilePath, self.numLines)
            log_entries = [self.parse_log_line(line) for line in lines]
            self.logContentLoaded.emit(log_entries)
        except Exception as e:
            self.logContentLoaded.emit([LogEntry(str(datetime.now()), "ERROR", f"Error reading log file: {e}")])

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
        with open(filename, "rb") as f:
            # Move to the end of the file
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            block_size = 1024
            blocks = []
            linesFound = 0
            position = file_size

            while position > 0 and linesFound < n:
                if position - block_size > 0:
                    position -= block_size
                else:
                    block_size = position
                    position = 0

                f.seek(position)
                block = f.read(block_size)
                blocks.insert(0, block)
                linesFound += block.count(b"\n")

            content = b"".join(blocks)
            lines = content.splitlines()[-n:]
            return [line.decode("utf-8", errors="replace") + "\n" for line in lines]

    @staticmethod
    def parse_log_line(line: str) -> LogEntry:
        pattern = r"(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}) - (\w+) - (\w+) - (.+)"
        match = re.match(pattern, line)
        if match:
            timestamp, source, level, message = match.groups()
            return LogEntry(timestamp, source, level, message)
        return LogEntry(str(datetime.now()), "BOOKS", "ERROR", f"Failed to parse log line: {line}")
