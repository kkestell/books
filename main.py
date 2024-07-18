import cProfile
import pstats
import sys

from PySide6.QtWidgets import (QApplication)

from main_window import MainWindow


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    # profiler = cProfile.Profile()
    # profiler.enable()
    main()
    # profiler.disable()
    # stats = pstats.Stats(profiler, stream=open('profile_results.txt', 'w')).sort_stats('cumulative')
    # stats.print_stats()