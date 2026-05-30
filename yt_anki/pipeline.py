from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .anki import AnkiCard, AnkiConnectClient
from .db import LearnerDb
from .deepl_client import DeepLClient
from .language import RussianLemmatizer, unique_lemmas
from .media import clip_audio, fetch_video_assets
from .settings import Settings
from .transcript import cues_to_sentences
from .wiktionary import WiktionaryClient, WordInfo


@dataclass(frozen=True)
class ProcessResult:
    video_title: str
    cards_created: int
    sentences_seen: int
    errors: list[str]


def format_timestamp(seconds: float) -> str:
    whole = int(seconds)
    hours = whole // 3600
    minutes = (whole % 3600) // 60
    secs = whole % 60
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_gloss(lemma: str, info: WordInfo) -> str:
    ipa = info.ipa
    if ipa and not (ipa.startswith("/") and ipa.endswith("/")):
        ipa = f"/{ipa}/"
    ipa_part = f", {ipa}" if ipa else ""
    english = info.english or "unavailable"
    return f"{lemma} ({lemma}{ipa_part}) - {english}"


class VideoProcessor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.db = LearnerDb(settings.db_path)
        self.lemmatizer = RussianLemmatizer()
        self.wiktionary = WiktionaryClient()
        self.deepl = DeepLClient(settings.deepl_auth_key)
        self.anki = AnkiConnectClient(settings.anki_connect_url)

    def process(self, video_url: str, language: str | None = None) -> ProcessResult:
        language = language or self.settings.learner_language
        if not self.settings.deepl_auth_key:
            raise RuntimeError("DEEPL_AUTH_KEY is required before creating Anki cards.")

        self.settings.media_dir.mkdir(parents=True, exist_ok=True)
        work_dir = self.settings.media_dir / "downloads"
        assets = fetch_video_assets(video_url, language, work_dir)
        sentences = cues_to_sentences(assets.captions)
        if not sentences:
            raise RuntimeError("Transcript was downloaded, but no full sentences could be built.")

        self.anki.ensure_deck(self.settings.anki_deck_name)
        self.anki.ensure_model(self.settings.anki_model_name)

        cards_created = 0
        errors: list[str] = []

        for index, sentence in enumerate(sentences, start=1):
            lemma_surfaces = unique_lemmas(self.lemmatizer.extract(sentence.text))
            new_lemmas = self.db.filter_new_lemmas(list(lemma_surfaces), language)
            if not new_lemmas:
                continue

            word_infos = [self._lookup_word(lemma, errors) for lemma in new_lemmas]
            glosses = "\n".join(format_gloss(lemma, info) for lemma, info in zip(new_lemmas, word_infos))
            translation = self.deepl.translate(
                sentence.text,
                source_lang=language,
                target_lang=self.settings.target_language,
            )

            audio_clip: Path | None = None
            try:
                audio_clip = clip_audio(
                    assets.audio_path,
                    sentence.start,
                    sentence.end,
                    self.settings.media_dir / "clips" / f"{assets.video_id}_{index:04d}.mp3",
                )
            except Exception as exc:  # keep card creation going without audio
                errors.append(f"Audio clip failed for sentence {index}: {exc}")

            card = AnkiCard(
                russian_sentence=sentence.text,
                sentence_audio_path=audio_clip,
                english_translation=translation,
                word_glosses=glosses,
                video_title=assets.video_title,
                video_url=video_url,
                timestamp=format_timestamp(sentence.start),
            )
            self.anki.add_card(self.settings.anki_deck_name, self.settings.anki_model_name, card)
            self.db.mark_seen(new_lemmas, language, video_url, sentence.text)
            cards_created += 1

        self.db.mark_video(video_url, language, cards_created)
        return ProcessResult(
            video_title=assets.video_title,
            cards_created=cards_created,
            sentences_seen=len(sentences),
            errors=errors,
        )

    def _lookup_word(self, lemma: str, errors: list[str]) -> WordInfo:
        try:
            return self.wiktionary.lookup(lemma)
        except Exception as exc:
            errors.append(f"Wiktionary lookup failed for {lemma}: {exc}")
            return WordInfo(lemma=lemma, ipa="", english="", source_url="")
