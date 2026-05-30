from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS seen_lemmas (
    lemma TEXT PRIMARY KEY,
    language TEXT NOT NULL,
    first_seen_video_url TEXT,
    first_seen_sentence TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS processed_videos (
    video_url TEXT PRIMARY KEY,
    language TEXT NOT NULL,
    processed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cards_created INTEGER NOT NULL
);
"""


class LearnerDb:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _init(self) -> None:
        with self._connect() as conn:
            conn.executescript(SCHEMA)

    def filter_new_lemmas(self, lemmas: list[str], language: str) -> list[str]:
        if not lemmas:
            return []
        placeholders = ",".join("?" for _ in lemmas)
        with self._connect() as conn:
            rows = conn.execute(
                f"SELECT lemma FROM seen_lemmas WHERE language = ? AND lemma IN ({placeholders})",
                [language, *lemmas],
            ).fetchall()
        seen = {row[0] for row in rows}
        return [lemma for lemma in lemmas if lemma not in seen]

    def mark_seen(
        self,
        lemmas: list[str],
        language: str,
        video_url: str,
        sentence: str,
    ) -> None:
        with self._connect() as conn:
            conn.executemany(
                """
                INSERT OR IGNORE INTO seen_lemmas
                    (lemma, language, first_seen_video_url, first_seen_sentence)
                VALUES (?, ?, ?, ?)
                """,
                [(lemma, language, video_url, sentence) for lemma in lemmas],
            )

    def mark_video(self, video_url: str, language: str, cards_created: int) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO processed_videos
                    (video_url, language, cards_created)
                VALUES (?, ?, ?)
                """,
                (video_url, language, cards_created),
            )
