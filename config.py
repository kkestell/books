import json
import os
from sys import platform
from dataclasses import dataclass, asdict

from log import Log


@dataclass
class Config:
    libraryPath: str
    pythonPath: str | None
    ebookViewerPath: str | None
    ebookMetaPath: str | None
    ebookConvertPath: str | None

    _instance = None

    @staticmethod
    def load():
        if Config._instance is None:
            Config._instance = Config._loadConfig()
        return Config._instance

    @staticmethod
    def _configPath():
        if platform == 'win32':
            return os.path.join(os.getenv('APPDATA'), 'Books', 'config.json')
        elif platform == 'darwin':
            return os.path.join(os.getenv('HOME'), 'Library', 'Application Support', 'Books', 'config.json')
        return os.path.join(os.getenv('HOME'), '.config', 'books', 'config.json')

    @staticmethod
    def _createDefaultConfig():
        path = Config._configPath()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        config = Config(getDefaultLibraryPath(), None, getEbookMetaPath(), getEbookConvertPath())
        Log.info(f"Creating default config at {path}\n{asdict(config)}")
        with open(path, 'w') as file:
            json.dump(asdict(config), file)

    @staticmethod
    def _loadConfig():
        path = Config._configPath()
        if not os.path.exists(path):
            Config._createDefaultConfig()
        Log.info(f"Loading config from {path}")
        with open(path, 'r') as file:
            data = json.load(file)
            Log.info(f"Loaded config: {data}")
            return Config(**data)


def getEbookViewerPath():
    if platform == 'win32':
        return "C:\\Program Files\\Calibre2\\ebook-viewer.exe"
    elif platform == 'darwin':
        return "/Applications/calibre.app/Contents/MacOS/ebook-viewer"
    return "/usr/bin/ebook-viewer"


def getEbookMetaPath():
    if platform == 'win32':
        return "C:\\Program Files\\Calibre2\\ebook-meta.exe"
    elif platform == 'darwin':
        return "/Applications/calibre.app/Contents/MacOS/ebook-meta"
    return "/usr/bin/ebook-meta"


def getEbookConvertPath():
    if platform == 'win32':
        return "C:\\Program Files\\Calibre2\\ebook-convert.exe"
    elif platform == 'darwin':
        return "/Applications/calibre.app/Contents/MacOS/ebook-convert"
    return "/usr/bin/ebook-convert"


def getDefaultLibraryPath():
    if platform == 'win32':
        return os.path.join(os.getenv('USERPROFILE'), 'Books')
    return os.path.join(os.getenv('HOME'), 'Books')
