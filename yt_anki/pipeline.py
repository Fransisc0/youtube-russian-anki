from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .anki import AnkiCard, AnkiConnectClient
from .core_words import dictionary_lookup_candidates, lookup_core_word
from .db import LearnerDb
from .ipa import approximate_russian_ipa
from .language import RussianLemmatizer, unique_lemmas
from .media import clip_audio, fetch_video_assets
from .progress import ProgressCallback
from .settings import Settings
from .transcript import cues_to_sentences
from .translation import TranslationRequest, create_translator
from .wiktionary import WiktionaryClient, WordInfo


@dataclass(frozen=True)
class ProcessResult:
    video_title: str
    cards_created: int
    sentences_seen: int
    cards_deleted: int
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
    ipa_part = f", {ipa}" if ipa else ", IPA unavailable"
    english = info.english or "dictionary meaning unavailable"
    return f"{lemma} ({lemma}{ipa_part}) - {english}"


class VideoProcessor:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.db = LearnerDb(settings.db_path)
        self.lemmatizer = RussianLemmatizer()
        self.wiktionary = WiktionaryClient()
        self.translator = create_translator(settings)
        self.anki = AnkiConnectClient(settings.anki_connect_url)

    def process(
        self,
        video_url: str,
        language: str | None = None,
        repair: bool = False,
        progress: ProgressCallback | None = None,
    ) -> ProcessResult:
        language = language or self.settings.learner_language
        progress = progress or (lambda message, current=None, total=None: None)

        progress("Preparing folders", None, None)
        self.settings.media_dir.mkdir(parents=True, exist_ok=True)
        work_dir = self.settings.media_dir / "downloads"
        progress("Downloading transcript and audio", None, None)
        assets = fetch_video_assets(video_url, language, work_dir)
        progress("Building sentence list", None, None)
        sentences = cues_to_sentences(assets.captions)
        if not sentences:
            raise RuntimeError("Transcript was downloaded, but no full sentences could be built.")

        progress("Preparing Anki deck and note type", None, None)
        self.anki.ensure_deck(self.settings.anki_deck_name)
        self.anki.ensure_model(self.settings.anki_model_name)
        cards_deleted = 0
        if repair:
            progress("Deleting old cards for this video", None, None)
            cards_deleted = self.anki.delete_cards_for_video(
                self.settings.anki_deck_name,
                self.settings.anki_model_name,
                video_url,
            )

        cards_created = 0
        errors: list[str] = []

        for index, sentence in enumerate(sentences, start=1):
            progress("Finding new words", index, len(sentences))
            lemma_surfaces = unique_lemmas(self.lemmatizer.extract(sentence.text))
            if repair:
                new_lemmas = list(lemma_surfaces)
            else:
                new_lemmas = self.db.filter_new_lemmas(list(lemma_surfaces), language)
            if not new_lemmas:
                continue

            progress("Looking up word meanings and IPA", index, len(sentences))
            word_infos = [self._lookup_word(lemma, language, errors) for lemma in new_lemmas]
            glosses = "\n".join(format_gloss(lemma, info) for lemma, info in zip(new_lemmas, word_infos))
            progress("Translating sentence", index, len(sentences))
            translation = self.translator.translate(
                TranslationRequest(
                    text=sentence.text,
                    source_lang=language,
                    target_lang=self.settings.target_language,
                )
            )

            audio_clip: Path | None = None
            try:
                progress("Clipping sentence audio", index, len(sentences))
                audio_clip = clip_audio(
                    assets.audio_path,
                    max(0.0, sentence.start - self.settings.audio_pad_before),
                    sentence.end + self.settings.audio_pad_after,
                    self.settings.media_dir / "downloads" / f"{assets.video_id}_{index:04d}.mp3",
                )
            except Exception as exc:  # keep card creation going without audio
                raise RuntimeError(f"Audio clip failed for sentence {index}: {exc}") from exc

            card = AnkiCard(
                russian_sentence=sentence.text,
                sentence_audio_path=audio_clip,
                english_translation=translation,
                word_glosses=glosses,
                video_title=assets.video_title,
                video_url=video_url,
                timestamp=format_timestamp(sentence.start),
            )
            progress("Adding card to Anki", index, len(sentences))
            self.anki.add_card(self.settings.anki_deck_name, self.settings.anki_model_name, card)
            self.db.mark_seen(new_lemmas, language, video_url, sentence.text)
            cards_created += 1

        progress("Saving video history", len(sentences), len(sentences))
        self.db.mark_video(video_url, language, cards_created)
        return ProcessResult(
            video_title=assets.video_title,
            cards_created=cards_created,
            sentences_seen=len(sentences),
            cards_deleted=cards_deleted,
            errors=errors,
        )

    def _lookup_word(self, lemma: str, language: str, errors: list[str]) -> WordInfo:
        info = self._lookup_wiktionary_first(lemma, errors)
        if not info.english:
            core_info = lookup_core_word(lemma)
            if core_info:
                info = WordInfo(
                    lemma=lemma,
                    ipa=info.ipa or core_info.ipa,
                    english=core_info.english,
                    source_url=info.source_url or core_info.source_url,
                )
        if not info.ipa:
            info = WordInfo(
                lemma=info.lemma,
                ipa=approximate_russian_ipa(lemma),
                english=info.english,
                source_url=info.source_url,
            )
        return info

    def _lookup_wiktionary_first(self, lemma: str, errors: list[str]) -> WordInfo:
        best = WordInfo(lemma=lemma, ipa="", english="", source_url="")
        for candidate in dictionary_lookup_candidates(lemma):
            try:
                info = self.wiktionary.lookup(candidate)
            except Exception as exc:
                errors.append(f"Wiktionary lookup failed for {candidate}: {exc}")
                continue
            if info.english:
                return WordInfo(
                    lemma=lemma,
                    ipa=info.ipa,
                    english=info.english,
                    source_url=info.source_url,
                )
            if info.source_url and not best.source_url:
                best = WordInfo(lemma=lemma, ipa=best.ipa, english="", source_url=info.source_url)
            if info.ipa and not best.ipa:
                best = WordInfo(lemma=lemma, ipa=info.ipa, english="", source_url=info.source_url or best.source_url)
        return best
