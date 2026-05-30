from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AnkiCard:
    russian_sentence: str
    sentence_audio_path: Path | None
    english_translation: str
    word_glosses: str
    video_title: str
    video_url: str
    timestamp: str


FRONT_TEMPLATE = """
<div class="prompt">{{EnglishTranslation}}</div>
"""

BACK_TEMPLATE = """
{{FrontSide}}
<hr id="answer">
<div class="sentence">{{RussianSentence}}</div>
<div class="audio">{{SentenceAudio}}</div>
<div class="glosses">{{WordGlosses}}</div>
"""

CSS = """
.card {
  font-family: Arial, sans-serif;
  font-size: 28px;
  line-height: 1.45;
  text-align: left;
  color: #111;
  background: #fff;
}
.prompt { margin-bottom: 18px; }
.sentence { margin-bottom: 18px; }
.audio { margin: 16px 0; }
.glosses { margin-top: 18px; font-size: 20px; white-space: pre-line; }
"""


class AnkiConnectClient:
    def __init__(self, url: str) -> None:
        self.url = url

    def invoke(self, action: str, **params):
        import requests

        response = requests.post(
            self.url,
            json={"action": action, "version": 6, "params": params},
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("error"):
            raise RuntimeError(f"AnkiConnect {action} failed: {payload['error']}")
        return payload.get("result")

    def ensure_deck(self, deck_name: str) -> None:
        self.invoke("createDeck", deck=deck_name)

    def ensure_model(self, model_name: str) -> None:
        names = self.invoke("modelNames")
        if model_name in names:
            self.update_model(model_name)
            return
        self.invoke(
            "createModel",
            modelName=model_name,
            inOrderFields=[
                "RussianSentence",
                "SentenceAudio",
                "EnglishTranslation",
                "WordGlosses",
                "VideoTitle",
                "VideoUrl",
                "Timestamp",
            ],
            css=CSS,
            cardTemplates=[
                {
                    "Name": "Sentence Translation",
                    "Front": FRONT_TEMPLATE,
                    "Back": BACK_TEMPLATE,
                }
            ],
        )

    def update_model(self, model_name: str) -> None:
        self.invoke(
            "updateModelTemplates",
            model={
                "name": model_name,
                "templates": {
                    "Sentence Translation": {
                        "Front": FRONT_TEMPLATE,
                        "Back": BACK_TEMPLATE,
                    }
                },
            },
        )
        self.invoke("updateModelStyling", model={"name": model_name, "css": CSS})

    def delete_cards_for_video(self, deck_name: str, model_name: str, video_url: str) -> int:
        query = f'deck:"{deck_name}" note:"{model_name}" "VideoUrl:{video_url}"'
        note_ids = self.invoke("findNotes", query=query)
        if note_ids:
            self.invoke("deleteNotes", notes=note_ids)
        return len(note_ids or [])

    def add_card(self, deck_name: str, model_name: str, card: AnkiCard) -> int:
        fields = {
            "RussianSentence": card.russian_sentence,
            "SentenceAudio": "",
            "EnglishTranslation": card.english_translation,
            "WordGlosses": card.word_glosses,
            "VideoTitle": card.video_title,
            "VideoUrl": card.video_url,
            "Timestamp": card.timestamp,
        }
        note = {
            "deckName": deck_name,
            "modelName": model_name,
            "fields": fields,
            "tags": ["youtube", "russian", "sentence-mining"],
        }
        if card.sentence_audio_path:
            filename = card.sentence_audio_path.name
            note["audio"] = [
                {
                    "path": str(card.sentence_audio_path.resolve()),
                    "filename": filename,
                    "fields": ["SentenceAudio"],
                }
            ]
        return self.invoke("addNote", note=note)
