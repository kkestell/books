from __future__ import annotations

import asyncio
import sys

from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from library import Library
from main_window import MainWindow


def main():
    QApplication.setStyle("fusion")
    app = QApplication(sys.argv)
    app.setApplicationName("Thoth")

    event_loop = QEventLoop(app)
    asyncio.set_event_loop(event_loop)

    app_close_event = asyncio.Event()
    app.aboutToQuit.connect(app_close_event.set)

    library = Library()

    main_window = MainWindow(library)
    main_window.show()

    with event_loop:
        event_loop.run_until_complete(app_close_event.wait())


if __name__ == "__main__":
    main()
