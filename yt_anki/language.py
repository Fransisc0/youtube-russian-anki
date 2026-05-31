from __future__ import annotations

from html import escape
import re
from dataclasses import dataclass


_CYRILLIC_WORD_RE = re.compile(r"[\u0400-\u04ff]+(?:-[\u0400-\u04ff]+)?")


@dataclass(frozen=True)
class TokenLemma:
    surface: str
    lemma: str


CASE_LABELS = {
    "nomn": "Nom",
    "gent": "Gen",
    "datv": "Dat",
    "accs": "Acc",
    "ablt": "Ins",
    "loct": "Prep",
}
CASE_NAMES = {
    "nomn": "Nominative",
    "gent": "Genitive",
    "datv": "Dative",
    "accs": "Accusative",
    "ablt": "Instrumental",
    "loct": "Prepositional",
}
CASE_ORDER = ("nomn", "gent", "datv", "accs", "ablt", "loct")
CASE_BEARING_POS = {"NOUN", "ADJF", "PRTF", "NPRO", "NUMR"}


class RussianLemmatizer:
    def __init__(self, morph=None) -> None:
        if morph is not None:
            self._morph = morph
            return
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
            lower = surface.lower().replace("\u0451", "\u0435")
            if self._morph:
                parsed = self._morph.parse(lower)
                lemma = parsed[0].normal_form if parsed else lower
            else:
                lemma = lower
            items.append(TokenLemma(surface=surface, lemma=lemma))
        return items

    def mark_sentence(self, text: str) -> str:
        return mark_sentence_cases(text, self._morph)


def unique_lemmas(tokens: list[TokenLemma]) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for token in tokens:
        result.setdefault(token.lemma, [])
        if token.surface not in result[token.lemma]:
            result[token.lemma].append(token.surface)
    return result


def mark_sentence_cases(text: str, morph) -> str:
    parts: list[str] = []
    cursor = 0
    for match in _CYRILLIC_WORD_RE.finditer(text):
        parts.append(escape(text[cursor : match.start()]))
        surface = match.group(0)
        parts.append(_mark_token(surface, morph))
        cursor = match.end()
    parts.append(escape(text[cursor:]))
    marked = "".join(parts)
    if marked != escape(text):
        marked += _case_key_html()
    return marked


def _mark_token(surface: str, morph) -> str:
    if morph is None:
        return escape(surface)
    lower = surface.lower().replace("\u0451", "\u0435")
    parses = morph.parse(lower)
    if not parses:
        return escape(surface)
    parsed = parses[0]
    pos = _tag_value(parsed, "POS")
    if pos not in CASE_BEARING_POS:
        return escape(surface)
    case = _tag_value(parsed, "case")
    if not case:
        return _span(surface, "unknown", _popup_html(parsed, surface, ""))
    if _is_case_ambiguous(parses, case):
        return _span(surface, "unknown", _popup_html(parsed, surface, ""))
    return _span(surface, case, _popup_html(parsed, surface, case))


def _is_case_ambiguous(parses, selected_case: str) -> bool:
    selected_score = getattr(parses[0], "score", 1.0)
    cases = {selected_case}
    for parse in parses[1:4]:
        score = getattr(parse, "score", selected_score)
        if selected_score - score > 0.05:
            continue
        case = _tag_value(parse, "case")
        if case:
            cases.add(case)
    return len(cases) > 1


def _popup_html(parsed, surface: str, current_case: str) -> str:
    lemma = escape(getattr(parsed, "normal_form", surface.lower()))
    details = _details(parsed, current_case)
    rows = []
    for case in CASE_ORDER:
        form = _inflect(parsed, case)
        value = escape(form or "")
        if case == current_case and value:
            value = f"<b>{value}</b>"
        rows.append(f"<tr><th>{CASE_LABELS[case]}</th><td>{value}</td></tr>")
    return (
        '<span class="case-popover" role="tooltip">'
        f'<span class="case-title">{lemma}</span>'
        f'<span class="case-meta">{escape(details)}</span>'
        '<table class="case-table">'
        + "".join(rows)
        + "</table></span>"
    )


def _details(parsed, current_case: str) -> str:
    pieces = []
    pos = _tag_value(parsed, "POS")
    number = _tag_value(parsed, "number")
    gender = _tag_value(parsed, "gender")
    if current_case:
        pieces.append(CASE_NAMES.get(current_case, current_case))
    else:
        pieces.append("Ambiguous case")
    if number:
        pieces.append(number)
    if gender:
        pieces.append(gender)
    if pos:
        pieces.append(pos)
    return " · ".join(pieces)


def _inflect(parsed, case: str) -> str:
    grammemes = {case}
    number = _tag_value(parsed, "number")
    gender = _tag_value(parsed, "gender")
    pos = _tag_value(parsed, "POS")
    if number:
        grammemes.add(number)
    if gender and number != "plur" and pos in {"ADJF", "PRTF"}:
        grammemes.add(gender)
    inflected = parsed.inflect(grammemes) if hasattr(parsed, "inflect") else None
    return getattr(inflected, "word", "") if inflected else ""


def _span(surface: str, case: str, popup: str) -> str:
    return (
        f'<span class="case-word case-{escape(case)}" tabindex="0">'
        f"{escape(surface)}{popup}</span>"
    )


def _tag_value(parsed, name: str) -> str:
    tag = getattr(parsed, "tag", None)
    return getattr(tag, name, "") or ""


def _case_key_html() -> str:
    chips = "".join(
        f'<span class="case-chip case-{case}">{label}</span>' for case, label in CASE_LABELS.items()
    )
    return f'<div class="case-key">{chips}</div>'
