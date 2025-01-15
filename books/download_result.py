from dataclasses import dataclass

from job import Job


@dataclass
class DownloadResult:
    job: Job
    file_path: str
