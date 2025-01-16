import os
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

import psutil
from PySide6.QtCore import QThread, Signal
from settings import Settings

from constants import ebook_extensions
from log import Log
from book import create_book_from_file, Book


class KindleMonitorThread(QThread):
    books_changed = Signal(object)
    kindle_connected = Signal()
    kindle_disconnected = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.books = []
        self.device = None
        self.mountpoint = None
        self.running = False

    def run(self):
        self.running = True
        Log.info("Kindle thread started.")
        while self.running:
            self.refresh_devices()
            self.sleep(1)
        Log.info("Kindle thread stopped.")

    def stop(self):
        self.running = False
        Log.info("Kindle thread stop requested.")

    def refresh_devices(self):
        new_device = None
        new_mountpoint = None

        for device in psutil.disk_partitions():
            if 'kindle' in device.device.lower() or 'kindle' in device.mountpoint.lower():
                new_device = device.device
                new_mountpoint = device.mountpoint
                break
            else:
                if os.name == 'nt':
                    volume_label = self.get_volume_label(device.device)
                    if volume_label and 'kindle' in volume_label.lower():
                        new_device = device.device
                        new_mountpoint = device.mountpoint
                        break

        if self.mountpoint and not new_mountpoint:
            self.mountpoint = None
            Log.info("Kindle disconnected.")
            self.kindle_disconnected.emit()
            return

        if new_mountpoint and new_mountpoint != self.mountpoint:
            Log.info(f"Kindle connected at {new_mountpoint}")
            self.mountpoint = new_mountpoint
            self.kindle_connected.emit()
            self.refresh_books()

        self.device = new_device

    def refresh_books(self):
        new_books = []
        try:
            documents_path = os.path.join(self.mountpoint, 'documents')
            Log.info(f"Looking for books in {documents_path}")

            book_file_paths = []
            for root, dirs, files in os.walk(documents_path):
                for file in files:
                    extensions = [f".{ext}" for ext in ebook_extensions]
                    if os.path.splitext(file)[1].lower() in extensions:
                        book_path = os.path.join(root, file)
                        book_file_paths.append(book_path)

            with ThreadPoolExecutor() as executor:
                future_to_path = {executor.submit(create_book_from_file, path): path for path in book_file_paths}
                for future in as_completed(future_to_path):
                    path = future_to_path[future]
                    try:
                        book = future.result()
                        new_books.append(book)
                    except Exception as e:
                        Log.info(f"Error processing file {path}: {e}")

        except Exception as e:
            Log.info(f"Failed to read from device: {e}")
            return

        if sorted(new_books) != sorted(self.books):
            self.books = new_books
            self.books_changed.emit(self.books)

    @staticmethod
    def get_volume_label(drive_letter: str) -> str | None:
        if os.name != 'nt':
            return None

        try:
            from ctypes import wintypes, create_unicode_buffer, sizeof, windll, byref, c_wchar_p
        except ImportError:
            return None

        if not drive_letter.endswith('\\'):
            drive_letter += '\\'

        vol_name_buf = create_unicode_buffer(1024)
        fs_name_buf = create_unicode_buffer(1024)
        serial_number = wintypes.DWORD()
        max_component_len = wintypes.DWORD()
        file_system_flags = wintypes.DWORD()

        ret = windll.kernel32.GetVolumeInformationW(
            c_wchar_p(drive_letter),
            vol_name_buf,
            sizeof(vol_name_buf),
            byref(serial_number),
            byref(max_component_len),
            byref(file_system_flags),
            fs_name_buf,
            sizeof(fs_name_buf)
        )
        if ret:
            return vol_name_buf.value
        else:
            return None

    def send_to_device(self, book: Book) -> None:
        if not self.mountpoint:
            Log.info("Kindle device not found.")
            return

        try:
            mobi_path = self.convert_to_azw3(book)
            if not mobi_path:
                Log.info("Failed to convert to MOBI.")
                return

            destination = os.path.join(self.mountpoint, 'documents', os.path.basename(mobi_path))
            shutil.copy(mobi_path, destination)
            Log.info(f"Copied {mobi_path} to {destination}")
        except Exception as e:
            Log.info(f"Failed to copy file to device: {e}")

    @staticmethod
    def convert_to_azw3(book: Book) -> str | None:
        try:
            source_path = book.path
            temp_dir = tempfile.mkdtemp()
            base_name = os.path.splitext(os.path.basename(source_path))[0]
            output_path = os.path.join(temp_dir, f"{base_name}.azw3")
            settings = Settings.load()
            args = []

            if settings.python_path:
                args.append(settings.python_path)

            args.append(settings.ebook_convert_path)
            args.extend([
                source_path,
                output_path,
                '--output-profile', 'kindle'
            ])

            if book.series:
                if book.series_number:
                    args.extend(['--title', f"{book.title} ({book.series} #{book.series_number})"])
                else:
                    args.extend(['--title', f"{book.title} ({book.series})"])

            Log.info(f"Converting {source_path} to MOBI with args: {args}")

            result = subprocess.run(args, capture_output=True, text=True, encoding='utf-8')

            if result.returncode == 0:
                Log.info("Conversion successful.")
                return output_path
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
