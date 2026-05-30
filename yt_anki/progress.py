from __future__ import annotations

from dataclasses import dataclass, field
from threading import Lock
from typing import Callable


ProgressCallback = Callable[[str, int | None, int | None], None]


@dataclass
class JobStatus:
    job_id: str
    state: str = "queued"
    message: str = "Queued"
    current: int | None = None
    total: int | None = None
    result: dict | None = None
    error: str | None = None


class JobStore:
    def __init__(self) -> None:
        self._jobs: dict[str, JobStatus] = {}
        self._lock = Lock()

    def create(self, job_id: str) -> JobStatus:
        with self._lock:
            status = JobStatus(job_id=job_id)
            self._jobs[job_id] = status
            return status

    def update(
        self,
        job_id: str,
        *,
        state: str | None = None,
        message: str | None = None,
        current: int | None = None,
        total: int | None = None,
        result: dict | None = None,
        error: str | None = None,
    ) -> None:
        with self._lock:
            status = self._jobs[job_id]
            if state is not None:
                status.state = state
            if message is not None:
                status.message = message
            status.current = current
            status.total = total
            if result is not None:
                status.result = result
            if error is not None:
                status.error = error

    def get(self, job_id: str) -> JobStatus | None:
        with self._lock:
            return self._jobs.get(job_id)
