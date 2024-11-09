from PySide6.QtGui import QFont


def getMonospacedFont() -> QFont:
    """
    Get a preferred monospaced font, depending on the platform.

    :return: The preferred monospaced font.
    :rtype: QFont
    """
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
            return font

    font = QFont()
    font.setStyleHint(QFont.StyleHint.Monospace)
    font.setPointSize(10)
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
            return font

    font = QFont()
    font.setStyleHint(QFont.StyleHint.SansSerif)
    font.setPointSize(10)
    return font
