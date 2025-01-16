import logging
from pathlib import Path
from sys import platform

from PySide6.QtCore import QStandardPaths, QCoreApplication


class Log:
    _instance = None
    _logger = None
    _log_file_path = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Log, cls).__new__(cls)
            cls._setup()
        return cls._instance

    @classmethod
    def _setup(cls):
        if cls._logger:
            return

        app_name = QCoreApplication.applicationName()

        log_path = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))
        if platform == "darwin":
            log_path = Path.home() / "Library" / "Logs" / app_name

        log_path.mkdir(parents=True, exist_ok=True)
        cls._log_file_path = log_path / "log.txt"

        cls._logger = logging.getLogger(f"{app_name}Logger")
        cls._logger.setLevel(logging.DEBUG)

        file_handler = logging.FileHandler(str(cls._log_file_path), encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        cls._logger.addHandler(file_handler)

    @classmethod
    def adopt(cls, logger: logging.Logger, log_level: int = logging.DEBUG):
        logger.setLevel(log_level)
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
    def get_log_file_path(cls) -> Path:
        cls._setup()
        return cls._log_file_path
