from __future__ import annotations

import html
import json
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class CaptionCue:
    start: float
    end: float
    text: str


@dataclass(frozen=True)
class SentenceSegment:
    start: float
    end: float
    text: str


_TIMING_RE = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2}[.,]\d{3})\s+-->\s+"
    r"(?P<end>\d{2}:\d{2}:\d{2}[.,]\d{3})"
)
_TAG_RE = re.compile(r"<[^>]+>")
_SENTENCE_END_RE = re.compile(r"[.!?][\"')\]]*$")
_SENTENCE_RE = re.compile(r"(.+?[.!?])(?:\s+|$)")


def parse_timestamp(value: str) -> float:
    hours, minutes, rest = value.replace(",", ".").split(":")
    seconds, millis = rest.split(".")
    return (
        int(hours) * 3600
        + int(minutes) * 60
        + int(seconds)
        + int(millis) / 1000
    )


def clean_caption_text(text: str) -> str:
    text = _TAG_RE.sub("", text)
    text = html.unescape(text)
    text = text.replace("\u00a0", " ")
    text = re.sub(r"(^|\s)>>\s*", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def collapse_repeated_lines(lines: list[str]) -> str:
    collapsed: list[str] = []
    for line in lines:
        cleaned = clean_caption_text(line)
        if not cleaned:
            continue
        if collapsed and cleaned.startswith(collapsed[-1]):
            collapsed[-1] = cleaned
            continue
        if collapsed and collapsed[-1].startswith(cleaned):
            continue
        collapsed.append(cleaned)
    return clean_caption_text(" ".join(collapsed))


def append_without_overlap(existing: str, addition: str) -> str:
    existing = clean_caption_text(existing)
    addition = clean_caption_text(addition)
    if not existing:
        return addition
    if not addition:
        return existing
    if addition.startswith(existing):
        return addition
    if existing.endswith(addition):
        return existing

    max_overlap = min(len(existing), len(addition))
    for size in range(max_overlap, 0, -1):
        if existing[-size:] == addition[:size]:
            return clean_caption_text(existing + addition[size:])
    return clean_caption_text(f"{existing} {addition}")


def split_complete_sentences(text: str) -> tuple[list[str], str]:
    text = clean_caption_text(text)
    sentences: list[str] = []
    last_end = 0
    for match in _SENTENCE_RE.finditer(text):
        sentence = clean_caption_text(match.group(1))
        if sentence:
            sentences.append(sentence)
        last_end = match.end()
    return sentences, clean_caption_text(text[last_end:])


def is_duplicate_or_fragment(sentence: str, recent_sentences: list[str]) -> bool:
    normalized = clean_caption_text(sentence).lower()
    if not normalized:
        return True
    for recent in recent_sentences[-6:]:
        recent_normalized = clean_caption_text(recent).lower()
        if normalized == recent_normalized:
            return True
        if normalized in recent_normalized:
            return True
    return False


def parse_vtt(contents: str) -> list[CaptionCue]:
    cues: list[CaptionCue] = []
    blocks = re.split(r"\n\s*\n", contents.replace("\r\n", "\n"))
    for block in blocks:
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        timing_index = next(
            (index for index, line in enumerate(lines) if _TIMING_RE.search(line)),
            None,
        )
        if timing_index is None:
            continue
        match = _TIMING_RE.search(lines[timing_index])
        if not match:
            continue
        start = parse_timestamp(match.group("start"))
        end = parse_timestamp(match.group("end"))
        if end - start < 0.05:
            continue
        text = collapse_repeated_lines(lines[timing_index + 1 :])
        if text:
            cues.append(
                CaptionCue(
                    start=start,
                    end=end,
                    text=text,
                )
            )
    return cues


def parse_json3(contents: str) -> list[CaptionCue]:
    payload = json.loads(contents)
    cues: list[CaptionCue] = []
    events = payload.get("events", [])
    for event_index, event in enumerate(events):
        segments = event.get("segs") or []
        if not segments:
            continue
        event_start = float(event.get("tStartMs", 0)) / 1000
        event_duration = float(event.get("dDurationMs", 0)) / 1000
        event_end = event_start + max(event_duration, 0.25)
        if event_index + 1 < len(events):
            next_event_start = float(events[event_index + 1].get("tStartMs", 0)) / 1000
            if next_event_start > event_start:
                event_end = min(event_end, next_event_start)
        timed_segments: list[tuple[float, str]] = []
        for segment in segments:
            text = clean_caption_text(segment.get("utf8", ""))
            if not text:
                continue
            offset = float(segment.get("tOffsetMs", 0)) / 1000
            timed_segments.append((event_start + offset, text))
        for index, (start, text) in enumerate(timed_segments):
            if index + 1 < len(timed_segments):
                end = timed_segments[index + 1][0]
            else:
                end = event_end
            if end <= start:
                end = start + 0.12
            cues.append(CaptionCue(start=start, end=end, text=text))
    return cues


def cues_to_sentences(cues: list[CaptionCue]) -> list[SentenceSegment]:
    segments: list[SentenceSegment] = []
    current_text = ""
    current_start: float | None = None
    current_end: float | None = None
    recent_sentences: list[str] = []

    for cue in cues:
        if current_start is None:
            current_start = cue.start
        current_end = cue.end
        current_text = append_without_overlap(current_text, cue.text)
        completed, remainder = split_complete_sentences(current_text)
        for sentence in completed:
            if not is_duplicate_or_fragment(sentence, recent_sentences):
                segments.append(SentenceSegment(current_start, current_end, sentence))
                recent_sentences.append(sentence)
        if completed:
            current_text = remainder
            current_start = cue.start if remainder else None
            current_end = cue.end if remainder else None

    if current_text and current_start is not None and current_end is not None:
        if _SENTENCE_END_RE.search(current_text) and not is_duplicate_or_fragment(current_text, recent_sentences):
            segments.append(SentenceSegment(current_start, current_end, clean_caption_text(current_text)))
    return segments
