from PySide6.QtWidgets import QMainWindow, QApplication
from PySide6.QtGui import QPalette, QColor, QGuiApplication
from PySide6.QtCore import Qt, QEvent, Signal
from enum import Enum
from dataclasses import dataclass
from typing import cast


class Theme(Enum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"


@dataclass
class ThemeColors:
    window: QColor
    window_text: QColor
    window_text_secondary: QColor
    base: QColor
    alternate_base: QColor
    text: QColor
    button: QColor
    button_text: QColor
    highlight: QColor
    highlighted_text: QColor
    link: QColor
    placeholder_text: QColor


class DarkThemeColors(ThemeColors):
    def __init__(self):
        super().__init__(
            window=QColor(50, 50, 50),
            window_text=QColor(220, 220, 220),
            window_text_secondary=QColor(150, 150, 150),
            base=QColor(40, 40, 40),
            alternate_base=QColor(55, 55, 55),
            text=QColor(220, 220, 220),
            button=QColor(50, 50, 50),
            button_text=QColor(200, 200, 200),
            highlight=QColor(60, 120, 200),
            highlighted_text=QColor(20, 20, 20),
            link=QColor(80, 140, 210),
            placeholder_text=QColor(140, 140, 140)
        )


class LightThemeColors(ThemeColors):
    def __init__(self):
        palette = QApplication.style().standardPalette()
        super().__init__(
            window=palette.color(QPalette.ColorRole.Window),
            window_text=palette.color(QPalette.ColorRole.WindowText),
            window_text_secondary=QColor(100, 100, 100),
            base=palette.color(QPalette.ColorRole.Base),
            alternate_base=palette.color(QPalette.ColorRole.AlternateBase),
            text=palette.color(QPalette.ColorRole.Text),
            button=palette.color(QPalette.ColorRole.Button),
            button_text=palette.color(QPalette.ColorRole.ButtonText),
            highlight=palette.color(QPalette.ColorRole.Highlight),
            highlighted_text=palette.color(QPalette.ColorRole.HighlightedText),
            link=palette.color(QPalette.ColorRole.Link),
            placeholder_text=palette.color(QPalette.ColorRole.PlaceholderText)
        )


class ThemedWindow(QMainWindow):
    theme_changed = Signal(Theme)

    def __init__(self, initial_theme: Theme = Theme.SYSTEM):
        super().__init__()
        self._current_theme = initial_theme
        self._dark_colors = DarkThemeColors()
        self._light_colors = LightThemeColors()
        self.update_theme()

    def changeEvent(self, event):
        if event.type() == QEvent.Type.ThemeChange and self._current_theme == Theme.SYSTEM:
            self.update_theme()
        super().changeEvent(event)

    @property
    def current_theme(self) -> Theme:
        return self._current_theme

    def set_theme(self, theme: Theme):
        if theme != self._current_theme:
            self._current_theme = theme
            self.update_theme()

    def get_dark_colors(self) -> ThemeColors:
        return self._dark_colors

    def get_light_colors(self) -> ThemeColors:
        return self._light_colors

    def update_theme(self):
        app = cast(QGuiApplication, QGuiApplication.instance())
        if app is None:
            return

        use_dark = False
        if self._current_theme == Theme.SYSTEM:
            use_dark = QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
        elif self._current_theme == Theme.DARK:
            use_dark = True

        colors = self.get_dark_colors() if use_dark else self.get_light_colors()

        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, colors.window)
        palette.setColor(QPalette.ColorRole.WindowText, colors.window_text)
        palette.setColor(QPalette.ColorRole.Base, colors.base)
        palette.setColor(QPalette.ColorRole.AlternateBase, colors.alternate_base)
        palette.setColor(QPalette.ColorRole.Text, colors.text)
        palette.setColor(QPalette.ColorRole.Button, colors.button)
        palette.setColor(QPalette.ColorRole.ButtonText, colors.button_text)
        palette.setColor(QPalette.ColorRole.Highlight, colors.highlight)
        palette.setColor(QPalette.ColorRole.HighlightedText, colors.highlighted_text)
        palette.setColor(QPalette.ColorRole.Link, colors.link)
        palette.setColor(QPalette.ColorRole.PlaceholderText, colors.placeholder_text)

        disabled_alpha = 127
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText,
                         QColor(colors.window_text).darker(disabled_alpha))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text,
                         QColor(colors.text).darker(disabled_alpha))
        palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText,
                         QColor(colors.button_text).darker(disabled_alpha))

        QGuiApplication.setPalette(palette)
        self.theme_changed.emit(self._current_theme)


def get_theme_colors(self) -> dict[str, str]:
    use_dark = False
    if self.current_theme == Theme.SYSTEM:
        use_dark = QGuiApplication.styleHints().colorScheme() == Qt.ColorScheme.Dark
    elif self.current_theme == Theme.DARK:
        use_dark = True

    colors = self.get_dark_colors() if use_dark else self.get_light_colors()
    return {
        'background': colors.window.name(),
        'text': colors.window_text.name(),
        'alt-text': colors.window_text_secondary.name(),
        'base': colors.base.name(),
        'alternate-base': colors.alternate_base.name(),
        'highlight': colors.highlight.name(),
        'highlight-text': colors.highlighted_text.name(),
    }
