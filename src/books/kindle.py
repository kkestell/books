import os
import shutil
import subprocess
import tempfile

import psutil
from PySide6.QtCore import Signal, QThread

from config import Config
from log import Log
from models import Book, createBookFromFile


class Kindle(QThread):
    booksChanged = Signal(object)
    kindleConnected = Signal()
    kindleDisconnected = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.books = []
        self.device = None
        self.mountpoint = None

    def run(self):
        while True:
            self.refreshBooks()
            self.sleep(60)

    def refreshBooks(self):
        self.device = None
        self.mountpoint = None
        for device in psutil.disk_partitions():
            if 'kindle' in device.device.lower() or 'kindle' in device.mountpoint.lower():
                self.device = device.device
                self.mountpoint = device.mountpoint
                break

        if not self.mountpoint:
            self.kindleDisconnected.emit()
            return

        self.kindleConnected.emit()

        newBooks = []
        try:
            for root, dirs, files in os.walk(os.path.join(self.mountpoint, 'documents')):
                for file in files:
                    extensions = ['.azw', '.azw3', '.mobi', '.pdf', '.txt']
                    if os.path.splitext(file)[1].lower() in extensions:
                        book = createBookFromFile(os.path.join(root, file))
                        newBooks.append(book)
        except Exception as e:
            Log.info(f"Failed to read from device: {e}")
            return

        if sorted(newBooks) != sorted(self.books):
            self.books = newBooks
            self.booksChanged.emit(self.books)

    def sendToDevice(self, book: Book):
        if not self.mountpoint:
            Log.info("Kindle device not found.")
            return
        try:
            mobiPath = self.convertToMobi(book.path)
            if not mobiPath:
                Log.info("Failed to convert to MOBI.")
                return
            destination = os.path.join(self.mountpoint, 'documents', os.path.basename(mobiPath))
            shutil.copy(mobiPath, destination)
        except Exception as e:
            Log.info(f"Failed to copy file to device: {e}")

    def convertToMobi(self, sourcePath):
        try:
            tempDir = tempfile.mkdtemp()
            baseName = os.path.splitext(os.path.basename(sourcePath))[0]
            outputPath = os.path.join(tempDir, f"{baseName}.mobi")
            config = Config.load()
            args = []
            if config.pythonPath:
                args.append(config.pythonPath)
            args.append(config.ebookConvertPath)
            args.extend([sourcePath, outputPath, '--mobi-file-type=new', '--mobi-ignore-margins'])
            Log.info(f"Converting {sourcePath} to MOBI {args}")
            result = subprocess.run(args, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if result.returncode == 0:
                Log.info("Conversion successful.")
                return outputPath
            else:
                Log.info("Conversion failed with return code:", result.returncode)
                return None
        except subprocess.CalledProcessError as e:
            Log.info(f"An error occurred during conversion: {e}")
            return None
        except Exception as e:
            Log.info(f"An unexpected error occurred: {e}")
            return None
