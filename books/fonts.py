from PySide6.QtGui import QFont


def get_sans_serif_font() -> QFont:
    preferred_fonts = [
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

    for name in preferred_fonts:
        font = QFont(name, 10)
        if font.family():
            font.setStyleHint(QFont.StyleHint.SansSerif)
            return font

    font = QFont()
    font.setStyleHint(QFont.StyleHint.SansSerif)
    font.setPointSize(10)
    return font
