import logging
import os
from sys import platform
from pathlib import Path
from PySide6.QtCore import QObject, Signal


class LogSignalEmitter(QObject):
    """
    A QObject class responsible for emitting log message signals.

    :signal logMessageSignal: Signal emitted with a log message as a string.
    """
    logMessageSignal = Signal(str)

    def __init__(self):
        """
        Initialize the LogSignalEmitter.
        """
        super().__init__()


class Log:
    """
    A singleton class for setting up and managing application logging.

    This class handles creating log files, logging messages to both
    a file and emitting them via signals for use in the UI.
    """
    _instance = None
    _logger = None
    _logFilePath = None
    _signalEmitter = None

    def __new__(cls):
        """
        Ensure only one instance of the Log class is created.

        :return: The single instance of the Log class.
        :rtype: Log
        """
        if cls._instance is None:
            cls._instance = super(Log, cls).__new__(cls)
            cls._setup()
        return cls._instance

    @classmethod
    def _setup(cls):
        """
        Set up the logger, file handler, and signal emitter for logging.
        """
        if cls._logger is None:
            # Determine the path to store log files based on the platform
            if platform == "win32":
                logPath = Path(os.getenv('LOCALAPPDATA')) / 'Books' / 'Logs'
            elif platform == "darwin":
                logPath = Path.home() / 'Library' / 'Logs' / 'Books'
            else:
                logPath = Path.home() / '.local' / 'state' / 'books'

            # Ensure the log directory exists
            logPath.mkdir(parents=True, exist_ok=True)
            cls._logFilePath = logPath / 'books.log'

            # Create the logger
            cls._logger = logging.getLogger('BooksLogger')
            cls._logger.setLevel(logging.INFO)

            # Create file handler to log messages to a file
            fh = logging.FileHandler(str(cls._logFilePath))
            fh.setLevel(logging.INFO)

            # Create a formatter for log messages
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

            # Add the formatter to the file handler
            fh.setFormatter(formatter)

            # Add the file handler to the logger
            cls._logger.addHandler(fh)

            # Create the signal emitter for UI logging
            cls._signalEmitter = LogSignalEmitter()

            # Create a signal handler to emit log messages as signals
            cls._signalHandler = LogSignalHandler(cls._signalEmitter)
            cls._signalHandler.setFormatter(formatter)

            # Add the signal handler to the logger
            cls._logger.addHandler(cls._signalHandler)

    @classmethod
    def info(cls, message: str):
        """
        Log an informational message.

        :param message: The message to log.
        :type message: str
        """
        cls._setup()
        cls._logger.info(message)

    @classmethod
    def getLogFilePath(cls) -> Path:
        """
        Get the path to the log file.

        :return: The path to the log file.
        :rtype: Path
        """
        cls._setup()
        return cls._logFilePath

    @classmethod
    def getLogSignalEmitter(cls) -> LogSignalEmitter:
        """
        Get the signal emitter for logging.

        :return: The signal emitter for log messages.
        :rtype: LogSignalEmitter
        """
        cls._setup()
        return cls._signalEmitter


class LogSignalHandler(logging.Handler):
    """
    A logging handler that emits log messages as signals.
    """

    def __init__(self, signalEmitter: LogSignalEmitter):
        """
        Initialize the LogSignalHandler.

        :param signalEmitter: The signal emitter to use for emitting log messages.
        :type signalEmitter: LogSignalEmitter
        """
        super().__init__()
        self.signalEmitter = signalEmitter

    def emit(self, record: logging.LogRecord):
        """
        Emit a log record as a signal.

        :param record: The log record to emit as a signal.
        :type record: logging.LogRecord
        """
        # Format the log record message
        msg = self.format(record)

        # Emit the log message signal
        self.signalEmitter.logMessageSignal.emit(msg)
