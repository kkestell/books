from dataclasses import dataclass
from zipfile import ZipFile

from bs4 import BeautifulSoup


@dataclass
class Epub:
    title: str
    author: str
    series: str
    seriesNumber: int
    type: str
    date: str
    language: str

def getMetadata(metadata, tag, attrs=None):
    if attrs:
        value = metadata.find(tag, attrs)
    else:
        value = metadata.find(tag)
    if value:
        if value.has_attr('content'):
            value = value['content']
        else:
            value = value.text
    return value

def loadEpub(path):
    with ZipFile(path, 'r') as epub:
        files = epub.namelist()
        opf = [file for file in files if file.endswith('.opf')][0]
        with epub.open(opf) as file:
            opf = file.read()
        opf = BeautifulSoup(opf, 'xml')
        metadata = opf.find('metadata')
        title = getMetadata(metadata, 'dc:title')
        author = getMetadata(metadata, 'dc:creator')
        series = getMetadata(metadata, 'meta', {'name': 'calibre:series'})
        seriesNumber = getMetadata(metadata, 'meta', {'name': 'calibre:series_index'})
        bookType = getMetadata(metadata, 'dc:type')
        date = getMetadata(metadata, 'dc:date')
        language = getMetadata(metadata, 'dc:language')
        return Epub(title, author, series, seriesNumber, bookType, date, language)
