import logging
import os
from sys import platform
from pathlib import Path


class Log:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Log, cls).__new__(cls)
            cls._instance._setup()
        return cls._instance

    @classmethod
    def _setup(cls):
        if cls._instance is None:
            if platform == "win32":
                logPath = Path(os.getenv('LOCALAPPDATA')) / 'Books' / 'Logs'
            elif platform == "darwin":
                logPath = Path.home() / 'Library' / 'Logs' / 'Books'
            else:
                logPath = Path.home() / '.local' / 'state' / 'books'

            logPath.mkdir(parents=True, exist_ok=True)

            logging.basicConfig(filename=str(logPath / 'books.log'), level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

            cls.logger = logging.getLogger(__name__)
            cls._instance = cls

    @classmethod
    def info(cls, message):
        cls._setup()
        cls.logger.info(message)
