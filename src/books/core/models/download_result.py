from dataclasses import dataclass

from src.books.core.models.job import Job


@dataclass
class DownloadResult:
    """
    Represents the result of a download job.
    """
    job: Job
    filePath: str
