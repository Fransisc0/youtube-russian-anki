from __future__ import annotations

from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .pipeline import VideoProcessor
from .security import is_allowed_youtube_url
from .settings import get_settings


class ProcessRequest(BaseModel):
    video_url: str
    language: str | None = None


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

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/process")
    def process(request: ProcessRequest):
        if not is_allowed_youtube_url(request.video_url):
            raise HTTPException(status_code=400, detail="Only YouTube watch URLs are supported.")
        try:
            return processor.process(request.video_url, request.language).__dict__
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("yt_anki.service:app", host=settings.service_host, port=settings.service_port, reload=True)
