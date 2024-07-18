# Books

## Configuration

TODO

### Example

```json
{
}
```

### Configuration Options

TODO

## Development

### System Dependencies

#### Arch Linux

Install `aur/python311`, `extra/patchelf`, and `extra/ccache`.

```
sudo pacman -Sy patchelf ccache
yay python311
```

#### Windows

Install [Visual Studio 2022](https://www.visualstudio.com/en-us/downloads/download-visual-studio-vs.aspx) and [Python 3.11](https://www.python.org/downloads/windows/).

#### macOS

Install Xcode and [Python 3.11](https://www.python.org/downloads/mac-osx/).

### Install PySide6 and Nuitka

```
pip install -r requirements.txt
```

### Build

#### Linux

```
python -m nuitka --standalone --plugin-enable=pyside6 --output-filename=books main.py
```

#### Windows

```
python -m nuitka --standalone --plugin-enable=pyside6 --disable-console --output-filename=books.exe main.py
```

#### macOS

```
python -m nuitka --macos-create-app-bundle --macos-app-icon=your-icon.png --plugin-enable=pyside6 --output-filename=books main.py
```
