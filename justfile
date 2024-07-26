install:
    pdm run python -m nuitka --standalone --plugin-enable=pyside6 --output-filename=books src/books/main.py
    cp assets/icon.png main.dist/
    rm -rf ~/.local/bin/books
    mv main.dist ~/.local/bin/books
