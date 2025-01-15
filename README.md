# Books

Ebook library manager and LibGen client.

![Books](screenshot.png)

## Configuration

* **Linux**: `~/.config/books/config.json`
* **Windows**: `%APPDATA%\books\config.json`
* **macOS**: `~/Library/Application Support/books/config.json`

### Example

```json
{
  "libraryPath": "/home/kyle/Books",
  "pythonPath": "/usr/bin/python3",
  "ebookViewerPath": "/usr/bin/ebook-viewer",
  "ebookMetaPath": "/usr/bin/ebook-meta",
  "ebookConvertPath": "/usr/bin/ebook-convert"
}
```

### Configuration Options

* **libraryPath**: Path to the directory containing your eBooks.
* **pythonPath**: Path to the Python executable.
* **ebookViewerPath**: Path to the Calibre eBook viewer executable.
* **ebookMetaPath**: Path to the Calibre eBook metadata editor executable.
* **ebookConvertPath**: Path to the Calibre eBook converter executable.

## Development

### System Dependencies

#### Windows

Install [Visual Studio 2022](https://www.visualstudio.com/en-us/downloads/download-visual-studio-vs.aspx) and [Python 3.12](https://www.python.org/downloads/windows/).

#### macOS

Install Xcode and [Python 3.12](https://www.python.org/downloads/mac-osx/).

#### Linux

##### Arch

```
yay -S python-beautifulsoup4 pyside6 python-requests python-psutil python-dateutil python-lxml python-thefuzz python-nh3
```

### Build

#### Linux

```
python -m nuitka --standalone --plugin-enable=pyside6 --output-filename=books main.py
```

#### Windows

```
uv run python -m nuitka --standalone --plugin-enable=pyside6 --windows-console-mode=disable --output-filename=books.exe books/main.py
```

#### macOS

```
python -m nuitka --macos-create-app-bundle --macos-app-icon=your-icon.png --plugin-enable=pyside6 --output-filename=books main.py
```
