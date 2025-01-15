import uuid
from dataclasses import dataclass, field


@dataclass
class Job:
    author: str
    series: str
    title: str
    format: str
    size: str
    mirrors: list
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "Queued"
