import logging
import os
from sys import platform
from pathlib import Path
from PySide6.QtCore import QObject, Signal, QStandardPaths
from datetime import datetime


class LogSignalEmitter(QObject):
    messageLogged = Signal(dict)

    def __init__(self):
        super().__init__()


class SourceFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.source = "BOOKS"
        return True


class CustomFormatter(logging.Formatter):
    """Custom formatter to support ISO 8601 timestamps with microseconds and include a 'source'."""

    def formatTime(self, record, datefmt=None):
        # Use datetime.fromtimestamp to get the full timestamp with microseconds
        ct = datetime.fromtimestamp(record.created)
        if datefmt:
            # Format microseconds manually
            s = ct.strftime(datefmt)
            return s.replace('%f', f"{ct.microsecond:06d}"[:3])  # Show only milliseconds
        else:
            # Default ISO 8601 format with milliseconds
            return ct.strftime("%Y-%m-%dT%H:%M:%S.%f")[:23]  # Trim to milliseconds


class Log:
    _instance = None
    _logger = None
    _logFilePath = None
    _signalEmitter = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Log, cls).__new__(cls)
            cls._setup()
        return cls._instance

    @classmethod
    def _setup(cls):
        if cls._logger:
            return

        # Define log path based on platform
        logPath = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))
        if platform == "darwin":
            logPath = Path.home() / "Library" / "Logs" / "Books"

        logPath.mkdir(parents=True, exist_ok=True)
        cls._logFilePath = logPath / "log.txt"

        # Set up MusicLogger
        cls._logger = logging.getLogger("BooksLogger")
        cls._logger.setLevel(logging.DEBUG)

        # Use ISO 8601-compliant timestamp format with 'source' field
        fileHandler = logging.FileHandler(str(cls._logFilePath), encoding="utf-8")
        fileHandler.setLevel(logging.DEBUG)
        fileFormatter = CustomFormatter(
            "%(asctime)s - %(source)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S.%f"  # ISO 8601 format
        )
        fileHandler.setFormatter(fileFormatter)

        # Add the source filter to distinguish between "music" and "aioslsk"
        source_filter = SourceFilter()
        fileHandler.addFilter(source_filter)

        cls._logger.addHandler(fileHandler)

        # Signal emitter and handler
        cls._signalEmitter = LogSignalEmitter()
        cls._signalHandler = LogSignalHandler(cls._signalEmitter)
        cls._signalHandler.setFormatter(fileFormatter)
        cls._signalHandler.addFilter(source_filter)
        cls._logger.addHandler(cls._signalHandler)

    @classmethod
    def adopt(cls, logger: logging.Logger, logLevel: int = logging.DEBUG):
        logger.setLevel(logLevel)
        logger.propagate = True
        logger.parent = cls._logger

    @classmethod
    def error(cls, message: str):
        cls._setup()
        cls._logger.error(message)

    @classmethod
    def warning(cls, message: str):
        cls._setup()
        cls._logger.warning(message)

    @classmethod
    def info(cls, message: str):
        cls._setup()
        cls._logger.info(message)

    @classmethod
    def verbose(cls, message: str):
        cls._setup()
        cls._logger.debug(message)

    @classmethod
    def getLogFilePath(cls) -> Path:
        cls._setup()
        return cls._logFilePath

    @classmethod
    def getLogSignalEmitter(cls) -> LogSignalEmitter:
        cls._setup()
        return cls._signalEmitter


class LogSignalHandler(logging.Handler):
    def __init__(self, signalEmitter: LogSignalEmitter):
        super().__init__()
        self.signalEmitter = signalEmitter

    def emit(self, record: logging.LogRecord):
        entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "source": getattr(record, "source", "unknown").upper(),
            "level": record.levelname.upper(),
            "message": record.getMessage()
        }
        self.signalEmitter.messageLogged.emit(entry)
