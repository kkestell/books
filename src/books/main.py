import sys

from PySide6.QtWidgets import (QApplication)

from src.books.core.fonts import getSansSerifFont
from src.books.windows.main_window import MainWindow


def main():
    """
    Main entry point for the application.
    """

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    font = getSansSerifFont()
    app.setFont(font)

    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    # import cProfile
    # import pstats
    # profiler = cProfile.Profile()
    # profiler.enable()
    main()
    # profiler.disable()
    # stats = pstats.Stats(profiler, stream=open('profile_results.txt', 'w')).sort_stats('cumulative')
    # stats.print_stats()
