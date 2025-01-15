from dataclasses import dataclass


@dataclass
class MetadataResult:
    title: str
    author: str
    published: str
    description: str
