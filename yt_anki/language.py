from __future__ import annotations

import re
from dataclasses import dataclass


_CYRILLIC_WORD_RE = re.compile(r"[А-Яа-яЁё]+(?:-[А-Яа-яЁё]+)?")


@dataclass(frozen=True)
class TokenLemma:
    surface: str
    lemma: str


class RussianLemmatizer:
    def __init__(self) -> None:
        try:
            import pymorphy3
        except ImportError:
            self._morph = None
        else:
            self._morph = pymorphy3.MorphAnalyzer()

    def extract(self, text: str) -> list[TokenLemma]:
        items: list[TokenLemma] = []
        for match in _CYRILLIC_WORD_RE.finditer(text):
            surface = match.group(0)
            lower = surface.lower().replace("ё", "е")
            if self._morph:
                parsed = self._morph.parse(lower)
                lemma = parsed[0].normal_form if parsed else lower
            else:
                lemma = lower
            items.append(TokenLemma(surface=surface, lemma=lemma))
        return items


def unique_lemmas(tokens: list[TokenLemma]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for token in tokens:
        result.setdefault(token.lemma, [])
        if token.surface not in result[token.lemma]:
            result[token.lemma].append(token.surface)
    return result
