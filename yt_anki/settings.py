from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency present in normal runtime
    load_dotenv = None


if load_dotenv:
    load_dotenv()


@dataclass(frozen=True)
class Settings:
    translation_provider: str
    argos_auto_install: bool
    deepl_auth_key: str
    service_host: str
    service_port: int
    anki_connect_url: str
    anki_deck_name: str
    anki_model_name: str
    learner_language: str
    target_language: str
    data_dir: Path

    @property
    def db_path(self) -> Path:
        return self.data_dir / "learner.sqlite3"

    @property
    def media_dir(self) -> Path:
        return self.data_dir / "media"


def get_settings() -> Settings:
    data_dir = Path(os.getenv("DATA_DIR", "data"))
    return Settings(
        translation_provider=os.getenv("TRANSLATION_PROVIDER", "argos"),
        argos_auto_install=os.getenv("ARGOS_AUTO_INSTALL", "true").lower() in {"1", "true", "yes"},
        deepl_auth_key=os.getenv("DEEPL_AUTH_KEY", ""),
        service_host=os.getenv("SERVICE_HOST", "127.0.0.1"),
        service_port=int(os.getenv("SERVICE_PORT", "8766")),
        anki_connect_url=os.getenv("ANKI_CONNECT_URL", "http://127.0.0.1:8765"),
        anki_deck_name=os.getenv("ANKI_DECK_NAME", "YouTube Russian Sentences"),
        anki_model_name=os.getenv("ANKI_MODEL_NAME", "YouTube Russian Sentence"),
        learner_language=os.getenv("LEARNER_LANGUAGE", "ru"),
        target_language=os.getenv("TARGET_LANGUAGE", "EN-US"),
        data_dir=data_dir,
    )
