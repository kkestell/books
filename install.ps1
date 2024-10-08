pdm run python -m nuitka --standalone --onefile --plugin-enable=pyside6 --output-filename=Books.exe --output-dir=publish --windows-console-mode=disable --windows-icon-from-ico=assets/icon.ico --include-data-file=assets/icon.png=assets/icon.png src/books/main.py

& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" install.iss
