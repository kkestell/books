import sys

from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (QApplication)

from main_window import MainWindow
from log import Log


def main():
    """
    Main entry point for the application.
    """
    app = QApplication(sys.argv)
    font = getPreferredFont()
    app.setFont(font)
    window = MainWindow()
    window.show()
    app.exec()


def getPreferredFont() -> QFont:
    """
    Get a preferred proportional font, depending on the platform.

    Returns
    -------
    QFont
        The preferred proportional font.
    """
    preferredFonts = [
        "Segoe UI",            # Windows (still widely used)
        "SF Pro Text",         # macOS (updated from San Francisco)
        "Helvetica Neue",      # macOS (updated from Helvetica)
        "Arial",               # Windows/macOS/Linux (still widely used)
        "Roboto",              # Android/Chrome OS
        "Noto Sans",           # Google Fonts, good for multilingual support
        "Inter",               # Popular modern cross-platform font
        "Open Sans",           # Google Fonts, still popular
        "Lato",                # Google Fonts, modern and widely used
        "Source Sans Pro",     # Adobe, open-source
        "Ubuntu",              # Ubuntu (still relevant for Linux)
        "Fira Sans",           # Mozilla's font, good for technical content
        "Verdana Pro",         # Updated version of Verdana
        "Tahoma"               # Still used, especially on Windows
    ]

    # Check availability and return the first available font
    for fontName in preferredFonts:
        font = QFont(fontName, 10)
        if not font.family():  # If the font is available
            font.setStyleHint(QFont.StyleHint.SansSerif)
            return font

    # If none of the preferred fonts are available, use the system's default sans-serif font
    font = QFont()
    font.setStyleHint(QFont.StyleHint.SansSerif)
    font.setPointSize(10)
    Log.info(f"Using default font: {font.family()}")
    return font


if __name__ == "__main__":
    # import cProfile
    # import pstats
    # profiler = cProfile.Profile()
    # profiler.enable()
    main()
    # profiler.disable()
    # stats = pstats.Stats(profiler, stream=open('profile_results.txt', 'w')).sort_stats('cumulative')
    # stats.print_stats()
