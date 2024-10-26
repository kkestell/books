from PySide6.QtGui import QFont, QFontDatabase

from src.books.core.log import Log


def getMonospacedFont() -> QFont:
    """
    Get a preferred monospaced font, depending on the platform.

    :return: The preferred monospaced font.
    :rtype: QFont
    """
    fontDatabase = QFontDatabase()
    preferredFonts = [
        "Cascadia Code",
        "Consolas",
        "Courier New",
        "Menlo",
        "Monaco",
        "Ubuntu Mono",
        "DejaVu Sans Mono",
        "Liberation Mono",
        "Noto Mono",
        "monospace",
    ]

    for fontName in preferredFonts:
        font = QFont(fontName, 10)
        if font.family():
            font.setStyleHint(QFont.StyleHint.Monospace)
            Log.info(f"Using default font: {font.family()}")
            return font

    font = QFont()
    font.setStyleHint(QFont.StyleHint.Monospace)
    font.setPointSize(10)
    Log.info(f"Using default font: {font.family()}")
    return font


def getSansSerifFont() -> QFont:
    """
    Get a preferred proportional font, depending on the platform.

    Returns
    -------
    QFont
        The preferred proportional font.
    """
    preferredFonts = [
        "Segoe UI",
        "SF Pro Text",
        "Helvetica Neue",
        "Arial",
        "Roboto",
        "Noto Sans",
        "Inter",
        "Open Sans",
        "Lato",
        "Source Sans Pro",
        "Ubuntu",
        "Fira Sans",
        "Verdana Pro",
        "Tahoma"
    ]

    for fontName in preferredFonts:
        font = QFont(fontName, 10)
        if font.family():
            font.setStyleHint(QFont.StyleHint.SansSerif)
            Log.info(f"Using preferred font: {font.family()}")
            return font

    font = QFont()
    font.setStyleHint(QFont.StyleHint.SansSerif)
    font.setPointSize(10)
    Log.info(f"Using default font: {font.family()}")
    return font
