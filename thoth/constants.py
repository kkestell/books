ebook_formats = {
    "AZW Files": "azw",
    "AZW3 Files": "azw3",
    "CHM Files": "chm",
    "DjVu Files": "djvu",
    "ePub Files": "epub",
    "FB2 Files": "fb2",
    "Mobi Files": "mobi",
    "PDF Files": "pdf",
    "RTF Files": "rtf",
    "Text Files": "txt"
}

ebook_types = [
    "Novel", "Novella", "Novelette", "Short Story", "Anthology", "Collection",
    "Omnibus", "Graphic Novel", "Comic", "Non-Fiction", "Cookbook", "Poetry", "Other"
]

ebook_extensions = list(ebook_formats.values())

all_formats_filter = "All Formats (" + " ".join(f"*.{ext}" for ext in ebook_extensions) + ")"

ebook_extensions_filter_string = all_formats_filter + ";;" + ";;".join(
    f"{name} (*.{ext})" for name, ext in ebook_formats.items())
