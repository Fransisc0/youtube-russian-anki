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
    russian_sentence_marked: str = ""


FRONT_TEMPLATE = """
<div class="prompt">{{EnglishTranslation}}</div>
"""

BACK_TEMPLATE = """
{{FrontSide}}
<hr id="answer">
<div class="sentence">
{{#RussianSentenceMarked}}{{RussianSentenceMarked}}{{/RussianSentenceMarked}}
{{^RussianSentenceMarked}}{{RussianSentence}}{{/RussianSentenceMarked}}
</div>
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
.case-word {
  position: relative;
  display: inline-block;
  padding: 0 0.12em;
  border-radius: 0.22em;
  color: #111;
  outline: none;
}
.case-nomn { background: #dcecff; }
.case-gent { background: #ece4ff; }
.case-datv { background: #ddf3e4; }
.case-accs { background: #fff0c7; }
.case-ablt { background: #f8dce2; }
.case-loct { background: #d9f1ef; }
.case-unknown {
  background: #f0f0f0;
  border-bottom: 2px dotted #8a8a8a;
}
.gender-masc { color: #2d5f8b; }
.gender-femn { color: #9a4b5a; }
.gender-neut { color: #4f5661; }
.verb-word,
.motion-word {
  position: relative;
  display: inline-block;
  padding: 0 0.1em;
  outline: none;
}
.verb-word {
  border-bottom: 2px solid #8aa6bd;
}
.motion-word {
  border-bottom: 2px solid #7c9f6f;
  background: #eef6e9;
  border-radius: 0.22em;
}
.case-key {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 12px;
  font-size: 14px;
}
.case-chip {
  display: inline-block;
  padding: 2px 7px;
  border-radius: 999px;
  color: #222;
}
.gender-key-label,
.verb-key-label,
.motion-key-label {
  display: inline-block;
  padding: 2px 7px;
  border-radius: 999px;
  background: #f3f3f3;
}
.verb-key-label { border-bottom: 2px solid #8aa6bd; }
.motion-key-label {
  background: #eef6e9;
  border-bottom: 2px solid #7c9f6f;
}
.case-popover {
  display: none;
  position: absolute;
  z-index: 10;
  left: 0;
  top: 1.8em;
  min-width: 170px;
  max-width: 240px;
  padding: 8px 10px;
  border: 1px solid #d4d4d4;
  border-radius: 6px;
  box-shadow: 0 5px 18px rgba(0, 0, 0, 0.15);
  background: #fff;
  color: #111;
  font-size: 14px;
  line-height: 1.25;
  text-align: left;
}
.case-word:hover .case-popover,
.case-word:focus .case-popover,
.verb-word:hover .case-popover,
.verb-word:focus .case-popover,
.motion-word:hover .case-popover,
.motion-word:focus .case-popover {
  display: block;
}
.case-title,
.case-meta {
  display: block;
  margin-bottom: 5px;
}
.case-title { font-weight: 700; }
.case-meta { color: #555; }
.case-table {
  width: 100%;
  border-collapse: collapse;
}
.case-table th,
.case-table td {
  padding: 2px 4px;
  border-top: 1px solid #eee;
}
.case-table th {
  width: 42px;
  color: #555;
  font-weight: 600;
}
.motion-popover {
  min-width: 280px;
  max-width: 360px;
}
.motion-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 8px;
}
.motion-table th,
.motion-table td {
  padding: 4px 5px;
  border-top: 1px solid #eee;
  vertical-align: top;
}
.motion-table th {
  width: 72px;
  color: #334;
}
.motion-table span {
  color: #666;
  font-size: 12px;
}
.motion-current {
  background: #f4faef;
}
"""

MODEL_FIELDS = [
    "RussianSentence",
    "RussianSentenceMarked",
    "SentenceAudio",
    "EnglishTranslation",
    "WordGlosses",
    "VideoTitle",
    "VideoUrl",
    "Timestamp",
]


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
            self.ensure_model_fields(model_name)
            self.update_model(model_name)
            return
        self.invoke(
            "createModel",
            modelName=model_name,
            inOrderFields=MODEL_FIELDS,
            css=CSS,
            cardTemplates=[
                {
                    "Name": "Sentence Translation",
                    "Front": FRONT_TEMPLATE,
                    "Back": BACK_TEMPLATE,
                }
            ],
        )

    def ensure_model_fields(self, model_name: str) -> None:
        existing = self.invoke("modelFieldNames", modelName=model_name) or []
        for field in MODEL_FIELDS:
            if field not in existing:
                self.invoke("modelFieldAdd", modelName=model_name, fieldName=field, index=len(existing))
                existing.append(field)

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
            "RussianSentenceMarked": card.russian_sentence_marked,
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
