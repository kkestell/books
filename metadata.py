from olclient.openlibrary import OpenLibrary
from pprint import pprint
import olclient.common as common


def search():
    ol = OpenLibrary()
    results = ol.Work.search("The Great Gatsby")
    pass
