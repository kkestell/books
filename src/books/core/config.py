import json
import os
from sys import platform
from dataclasses import dataclass, asdict
from typing import Optional

from src.books.core.log import Log

@dataclass
class Config:
    """
    Represents the configuration settings for the application.

    :param libraryPath: The path to the library directory.
    :type libraryPath: str
    :param pythonPath: The path to the Python interpreter, if set.
    :type pythonPath: Optional[str]
    :param ebookViewerPath: The path to the ebook viewer executable, if set.
    :type ebookViewerPath: Optional[str]
    :param ebookMetaPath: The path to the ebook metadata editor executable, if set.
    :type ebookMetaPath: Optional[str]
    :param ebookConvertPath: The path to the ebook converter executable, if set.
    :type ebookConvertPath: Optional[str]
    """
    libraryPath: str
    pythonPath: Optional[str]
    ebookViewerPath: Optional[str]
    ebookMetaPath: Optional[str]
    ebookConvertPath: Optional[str]

    _instance: Optional['Config'] = None

    @staticmethod
    def load() -> 'Config':
        """
        Loads the configuration as a singleton instance. If the configuration file
        does not exist, a default configuration is created.

        :return: The singleton instance of the configuration.
        :rtype: Config
        """
        if Config._instance is None:
            Config._instance = Config._loadConfig()
        return Config._instance

    @staticmethod
    def configPath() -> str:
        """
        Gets the path to the configuration file based on the platform.

        :return: The path to the configuration file.
        :rtype: str
        """
        if platform == 'win32':
            return os.path.join(os.getenv('APPDATA'), 'Books', 'config.json')
        elif platform == 'darwin':
            return os.path.join(os.getenv('HOME'), 'Library', 'Application Support', 'Books', 'config.json')
        return os.path.join(os.getenv('HOME'), '.config', 'books', 'config.json')

    @staticmethod
    def _createDefaultConfig() -> None:
        """
        Creates a default configuration file if none exists.
        The file is written in JSON format to the appropriate directory based on the platform.
        """
        path = Config.configPath()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        config = Config(
            libraryPath=getDefaultLibraryPath(),
            pythonPath=None,
            ebookViewerPath=getEbookViewerPath(),
            ebookMetaPath=getEbookMetaPath(),
            ebookConvertPath=getEbookConvertPath()
        )
        Log.info(f"Creating default config at {path}\n{asdict(config)}")

        # Write the default configuration to the file in JSON format
        with open(path, 'w', encoding="utf-8") as file:
            json.dump(asdict(config), file, indent=4)

    @staticmethod
    def _loadConfig() -> 'Config':
        """
        Loads the configuration from a file. If the file does not exist,
        it creates a default configuration.

        :return: The loaded configuration.
        :rtype: Config
        """
        path = Config.configPath()
        if not os.path.exists(path):
            Config._createDefaultConfig()
        Log.info(f"Loading config from {path}")

        # Read configuration from file
        with open(path, 'r', encoding="utf-8") as file:
            data = json.load(file)
            Log.info(f"Loaded config: {data}")
            return Config(**data)


def getEbookViewerPath() -> str:
    """
    Determines the default path to the ebook viewer executable based on the platform.

    :return: The path to the ebook viewer executable.
    :rtype: str
    """
    if platform == 'win32':
        return "C:\\Program Files\\Calibre2\\ebook-viewer.exe"
    elif platform == 'darwin':
        return "/Applications/calibre.app/Contents/MacOS/ebook-viewer"
    return "/usr/bin/ebook-viewer"


def getEbookMetaPath() -> str:
    """
    Determines the default path to the ebook metadata editor executable based on the platform.

    :return: The path to the ebook metadata editor executable.
    :rtype: str
    """
    if platform == 'win32':
        return "C:\\Program Files\\Calibre2\\ebook-meta.exe"
    elif platform == 'darwin':
        return "/Applications/calibre.app/Contents/MacOS/ebook-meta"
    return "/usr/bin/ebook-meta"


def getEbookConvertPath() -> str:
    """
    Determines the default path to the ebook converter executable based on the platform.

    :return: The path to the ebook converter executable.
    :rtype: str
    """
    if platform == 'win32':
        return "C:\\Program Files\\Calibre2\\ebook-convert.exe"
    elif platform == 'darwin':
        return "/Applications/calibre.app/Contents/MacOS/ebook-convert"
    return "/usr/bin/ebook-convert"


def getDefaultLibraryPath() -> str:
    """
    Determines the default path to the library directory based on the platform.

    :return: The default library path.
    :rtype: str
    """
    if platform == 'win32':
        return os.path.join(os.getenv('USERPROFILE'), 'Books')
    return os.path.join(os.getenv('HOME'), 'Books')
