from dataclasses import dataclass


@dataclass
class SearchResult:
    author: str
    series: str
    title: str
    format: str
    size: str
    score: int
    mirrors: list
