.PHONY: install

install:
	python -m nuitka --standalone --plugin-enable=pyside6 --output-filename=books main.py
	cp icon.png main.dist/
	rm -rf ~/.local/bin/books
	mv main.dist ~/.local/bin/books
	@mkdir -p $(HOME)/.local/share/applications
	@{ \
	echo "[Desktop Entry]"; \
	echo "Name=Books"; \
	echo "Exec=$(HOME)/.local/bin/books/books"; \
	echo "Icon=$(HOME)/.local/bin/books/icon.png"; \
	echo "Type=Application"; \
	echo "Categories=Utility;"; \
	} > $(HOME)/.local/share/applications/books.desktop