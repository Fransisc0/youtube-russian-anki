from __future__ import annotations

from uuid import uuid4

from pydantic import BaseModel
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .pipeline import VideoProcessor
from .progress import JobStore
from .security import is_allowed_youtube_url
from .settings import get_settings


class ProcessRequest(BaseModel):
    video_url: str
    language: str | None = None
    repair: bool = False


def create_app() -> FastAPI:
    app = FastAPI(title="YouTube Russian-to-Anki Card Generator")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["https://www.youtube.com", "https://youtube.com"],
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    settings = get_settings()
    processor = VideoProcessor(settings)
    jobs = JobStore()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    def run_job(job_id: str, request: ProcessRequest) -> None:
        def progress(message: str, current: int | None = None, total: int | None = None) -> None:
            jobs.update(
                job_id,
                state="running",
                message=message,
                current=current,
                total=total,
            )

        try:
            jobs.update(job_id, state="running", message="Starting")
            result = processor.process(
                request.video_url,
                request.language,
                repair=request.repair,
                progress=progress,
            )
            jobs.update(
                job_id,
                state="complete",
                message="Complete",
                current=result.sentences_seen,
                total=result.sentences_seen,
                result=result.__dict__,
            )
        except Exception as exc:
            jobs.update(job_id, state="error", message="Failed", error=str(exc))

    @app.post("/process")
    def process(request: ProcessRequest, background_tasks: BackgroundTasks):
        if not is_allowed_youtube_url(request.video_url):
            raise HTTPException(status_code=400, detail="Only YouTube watch URLs are supported.")
        job_id = str(uuid4())
        jobs.create(job_id)
        background_tasks.add_task(run_job, job_id, request)
        return {"job_id": job_id}

    @app.get("/jobs/{job_id}")
    def job_status(job_id: str):
        status = jobs.get(job_id)
        if status is None:
            raise HTTPException(status_code=404, detail="Job not found.")
        return status.__dict__

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("yt_anki.service:app", host=settings.service_host, port=settings.service_port, reload=True)
