import ctypes
import os
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

import psutil
from PySide6.QtCore import QThread, Signal

from books.core.constants import ebookExtensions
from src.books.core.config import Config
from src.books.core.log import Log
from src.books.core.models.book import createBookFromFile, Book


class KindleMonitorThread(QThread):
    """
    A thread that monitors Kindle device connection and manages books on the device.

    :signal booksChanged: Emitted when the list of books on the Kindle changes.
    :signal kindleConnected: Emitted when the Kindle device is connected.
    :signal kindleDisconnected: Emitted when the Kindle device is disconnected.
    """

    booksChanged = Signal(object)
    kindleConnected = Signal()
    kindleDisconnected = Signal()

    def __init__(self, parent=None):
        """
        Initialize the Kindle thread.

        :param parent: The parent QObject, if any.
        :type parent: QObject, optional
        """
        super().__init__(parent)
        self.books = []
        self.device = None
        self.mountpoint = None
        self.running = False

    def run(self):
        """
        Main loop that monitors Kindle device connection.
        """
        self.running = True
        Log.info("Kindle thread started.")
        while self.running:
            # Refresh device status
            self.refreshDevices()
            self.sleep(1)
        Log.info("Kindle thread stopped.")

    def stop(self):
        """
        Stop the Kindle thread.
        """
        self.running = False
        Log.info("Kindle thread stop requested.")

    def refreshDevices(self):
        """
        Check for connected Kindle devices and update status.
        """
        new_device = None
        new_mountpoint = None

        # Iterate over all disk partitions to find Kindle device
        for device in psutil.disk_partitions():
            if 'kindle' in device.device.lower() or 'kindle' in device.mountpoint.lower():
                new_device = device.device
                new_mountpoint = device.mountpoint
                break
            else:
                # Windows-specific code to check volume label
                if os.name == 'nt':
                    volume_label = self.getVolumeLabel(device.device)
                    if volume_label and 'kindle' in volume_label.lower():
                        new_device = device.device
                        new_mountpoint = device.mountpoint
                        break

        if self.mountpoint and not new_mountpoint:
            # Kindle was disconnected
            self.mountpoint = None
            Log.info("Kindle disconnected.")
            self.kindleDisconnected.emit()
            return

        if new_mountpoint and new_mountpoint != self.mountpoint:
            # Kindle was connected
            Log.info(f"Kindle connected at {new_mountpoint}")
            self.mountpoint = new_mountpoint
            self.kindleConnected.emit()
            self.refreshBooks()

        self.device = new_device

    def refreshBooks(self):
        """
        Refresh the list of books on the Kindle device.

        This method collects all supported book files from the Kindle device
        and processes them in parallel to create `Book` objects.
        """
        newBooks = []
        try:
            documents_path = os.path.join(self.mountpoint, 'documents')
            Log.info(f"Looking for books in {documents_path}")

            # Collect all book file paths
            book_file_paths = []
            for root, dirs, files in os.walk(documents_path):
                for file in files:
                    extensions = [f".{ext}" for ext in ebookExtensions]
                    if os.path.splitext(file)[1].lower() in extensions:
                        bookPath = os.path.join(root, file)
                        book_file_paths.append(bookPath)

            # Process the book files in parallel to create Book objects
            with ThreadPoolExecutor() as executor:
                future_to_path = {executor.submit(createBookFromFile, path): path for path in book_file_paths}
                for future in as_completed(future_to_path):
                    path = future_to_path[future]
                    try:
                        book = future.result()
                        newBooks.append(book)
                    except Exception as e:
                        Log.info(f"Error processing file {path}: {e}")

        except Exception as e:
            Log.info(f"Failed to read from device: {e}")
            return

        # If the list of books has changed, emit the booksChanged signal
        if sorted(newBooks) != sorted(self.books):
            self.books = newBooks
            self.booksChanged.emit(self.books)

    @staticmethod
    def getVolumeLabel(driveLetter: str) -> Optional[str]:
        """
        Retrieve the volume label for a given drive letter on Windows.

        :param driveLetter: The drive letter (e.g., 'E:\\').
        :type driveLetter: str
        :return: The volume label if found, otherwise None.
        :rtype: Optional[str]
        """
        if not driveLetter.endswith('\\'):
            driveLetter += '\\'

        volNameBuf = ctypes.create_unicode_buffer(1024)
        fsNameBuf = ctypes.create_unicode_buffer(1024)
        serialNumber = ctypes.wintypes.DWORD()
        maxComponentLen = ctypes.wintypes.DWORD()
        fileSystemFlags = ctypes.wintypes.DWORD()

        # Call Windows API GetVolumeInformationW to get volume label
        ret = ctypes.windll.kernel32.GetVolumeInformationW(
            ctypes.c_wchar_p(driveLetter),
            volNameBuf,
            ctypes.sizeof(volNameBuf),
            ctypes.byref(serialNumber),
            ctypes.byref(maxComponentLen),
            ctypes.byref(fileSystemFlags),
            fsNameBuf,
            ctypes.sizeof(fsNameBuf)
        )
        if ret:
            return volNameBuf.value
        else:
            return None

    def sendToDevice(self, book: Book) -> None:
        """
        Convert a book to MOBI format and send it to the Kindle device.

        If the Kindle device is not connected or the conversion fails, the method logs
        the appropriate message and takes no action.

        :param book: The book to send to the device.
        :type book: Book
        """
        if not self.mountpoint:
            Log.info("Kindle device not found.")
            return

        try:
            mobiPath = self.convertToMobi(book)
            if not mobiPath:
                Log.info("Failed to convert to MOBI.")
                return

            # Copy the MOBI file to the Kindle 'documents' directory
            destination = os.path.join(self.mountpoint, 'documents', os.path.basename(mobiPath))
            shutil.copy(mobiPath, destination)
            Log.info(f"Copied {mobiPath} to {destination}")
        except Exception as e:
            Log.info(f"Failed to copy file to device: {e}")

    @staticmethod
    def convertToMobi(book: Book) -> Optional[str]:
        """
        Convert a book to MOBI format using ebook-convert.

        :param book: The book to convert.
        :type book: Book
        :return: The path to the converted MOBI file, or None if conversion failed.
        :rtype: Optional[str]
        """
        try:
            sourcePath = book.path
            tempDir = tempfile.mkdtemp()
            baseName = os.path.splitext(os.path.basename(sourcePath))[0]
            outputPath = os.path.join(tempDir, f"{baseName}.azw3")
            config = Config.load()
            args = []

            if config.pythonPath:
                args.append(config.pythonPath)

            args.append(config.ebookConvertPath)
            args.extend([
                sourcePath,
                outputPath,
                '--output-profile', 'kindle'
            ])

            if book.series:
                if book.seriesNumber:
                    # Include series information in the title
                    args.extend(['--title', f"{book.title} ({book.series} #{book.seriesNumber})"])
                else:
                    args.extend(['--title', f"{book.title} ({book.series})"])

            Log.info(f"Converting {sourcePath} to MOBI with args: {args}")

            result = subprocess.run(args, capture_output=True, text=True, encoding='utf-8')

            if result.returncode == 0:
                Log.info("Conversion successful.")
                return outputPath
            else:
                Log.info(f"Conversion failed with return code: {result.returncode}")
                Log.info(f"Standard Output: {result.stdout}")
                Log.info(f"Standard Error: {result.stderr}")
                return None

        except subprocess.CalledProcessError as e:
            Log.info(f"Conversion failed: {e}")
            return None
        except Exception as e:
            Log.info(f"An unexpected error occurred: {e}")
            return None
