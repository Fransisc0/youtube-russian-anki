from __future__ import annotations

import html
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
_SENTENCE_END_RE = re.compile(r"[.!?…][\"')\]]*$")


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
    text = re.sub(r"\s+", " ", text).strip()
    return text


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
        text = clean_caption_text(" ".join(lines[timing_index + 1 :]))
        if text:
            cues.append(
                CaptionCue(
                    start=parse_timestamp(match.group("start")),
                    end=parse_timestamp(match.group("end")),
                    text=text,
                )
            )
    return cues


def cues_to_sentences(cues: list[CaptionCue]) -> list[SentenceSegment]:
    segments: list[SentenceSegment] = []
    current_text: list[str] = []
    current_start: float | None = None
    current_end: float | None = None

    for cue in cues:
        if current_start is None:
            current_start = cue.start
        current_end = cue.end
        current_text.append(cue.text)
        joined = clean_caption_text(" ".join(current_text))
        if _SENTENCE_END_RE.search(joined):
            segments.append(SentenceSegment(current_start, current_end, joined))
            current_text = []
            current_start = None
            current_end = None

    if current_text and current_start is not None and current_end is not None:
        segments.append(
            SentenceSegment(current_start, current_end, clean_caption_text(" ".join(current_text)))
        )
    return segments
