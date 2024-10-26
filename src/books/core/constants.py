ebookFormats = {
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

ebookExtensions = list(ebookFormats.values())

allFormatsFilter = "All Formats (" + " ".join(f"*.{ext}" for ext in ebookExtensions) + ")"

ebookExtensionsFilterString = allFormatsFilter + ";;" + ";;".join(f"{name} (*.{ext})" for name, ext in ebookFormats.items())
