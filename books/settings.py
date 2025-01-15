import sys
from pathlib import Path
import json
from pydantic_settings import BaseSettings
from PySide6.QtCore import QStandardPaths


class Settings(BaseSettings):
    library_path: str = ""
    python_path: str = ""
    ebook_viewer_path: str = ""
    ebook_meta_path: str = ""
    ebook_convert_path: str = ""

    def save(self, path: Path = None) -> None:
        if path is None:
            path = self._get_default_path()

        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(self.model_dump(), indent=2))

    @staticmethod
    def _get_default_path() -> Path:
        if sys.platform == 'win32':
            base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
        elif sys.platform == 'darwin':
            base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
        else:
            base = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.ConfigLocation)

        return Path(base) / "config.json"

    @staticmethod
    def _get_platform_defaults() -> dict:
        if sys.platform == 'win32':
            library_path = Path.home() / "Books"
            calibre_base = Path("C:\\Program Files\\Calibre2")
            return {
                "library_path": str(library_path),
                "python_path": "",
                "ebook_viewer_path": str(calibre_base / "ebook-viewer.exe"),
                "ebook_meta_path": str(calibre_base / "ebook-meta.exe"),
                "ebook_convert_path": str(calibre_base / "ebook-convert.exe")
            }
        elif sys.platform == 'darwin':
            home = Path.home()
            return {
                "library_path": str(home / "Books"),
                "python_path": "",
                "ebook_viewer_path": "/Applications/calibre.app/Contents/MacOS/ebook-viewer",
                "ebook_meta_path": "/Applications/calibre.app/Contents/MacOS/ebook-meta",
                "ebook_convert_path": "/Applications/calibre.app/Contents/MacOS/ebook-convert"
            }
        else:
            home = Path.home()
            return {
                "library_path": str(home / "Books"),
                "python_path": "",
                "ebook_viewer_path": "/usr/bin/ebook-viewer",
                "ebook_meta_path": "/usr/bin/ebook-meta",
                "ebook_convert_path": "/usr/bin/ebook-convert"
            }

    @classmethod
    def load(cls, path: Path = None) -> "Settings":
        if path is None:
            path = cls._get_default_path()

        settings = cls()

        if path.exists():
            try:
                settings = cls.model_validate(json.loads(path.read_text()))
            except Exception as e:
                print(f"Error loading settings: {e}")
                settings = cls()

        defaults = settings._get_platform_defaults()
        modified = False

        for key, default_value in defaults.items():
            current_value = getattr(settings, key)
            if not current_value:
                setattr(settings, key, default_value)
                modified = True

        if modified or not path.exists():
            settings.save(path)

        return settings
