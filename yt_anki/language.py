from __future__ import annotations

from dataclasses import dataclass
from html import escape
import re


_CYRILLIC_WORD_RE = re.compile(r"[\u0400-\u04ff]+(?:-[\u0400-\u04ff]+)?")


@dataclass(frozen=True)
class TokenLemma:
    surface: str
    lemma: str


@dataclass
class GrammarToken:
    surface: str
    start: int
    end: int
    lower: str
    parses: list
    selected: object | None
    resolved_case: str = ""
    resolution_reason: str = ""


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
VERB_POS = {"VERB", "INFN", "PRTF", "PRTS", "GRND"}

PREPOSITION_CASES = {
    "\u043a": ("datv",),
    "\u043a\u043e": ("datv",),
    "\u043e": ("loct",),
    "\u043e\u0431": ("loct",),
    "\u043e\u0431\u043e": ("loct",),
    "\u043f\u0440\u0438": ("loct",),
    "\u0438\u0437": ("gent",),
    "\u0438\u0437\u043e": ("gent",),
    "\u043e\u0442": ("gent",),
    "\u043e\u0442\u043e": ("gent",),
    "\u0434\u043b\u044f": ("gent",),
    "\u0431\u0435\u0437": ("gent",),
    "\u0443": ("gent",),
    "\u0434\u043e": ("gent",),
    "\u043f\u043e\u0441\u043b\u0435": ("gent",),
    "\u0441": ("ablt", "gent"),
    "\u0441\u043e": ("ablt", "gent"),
    "\u0437\u0430": ("ablt", "accs"),
    "\u043f\u043e\u0434": ("ablt", "accs"),
    "\u043d\u0430\u0434": ("ablt", "accs"),
    "\u0432": ("loct", "accs"),
    "\u0432\u043e": ("loct", "accs"),
    "\u043d\u0430": ("loct", "accs"),
}

MOTION_VERBS = {
    "\u0438\u0434\u0442\u0438": ("one-way / currently going on foot", "to go, to be walking somewhere"),
    "\u0445\u043e\u0434\u0438\u0442\u044c": ("habitual, repeated, or round-trip walking", "to go regularly, to walk around"),
    "\u043f\u043e\u0439\u0442\u0438": ("start going / set off", "to go, to start walking"),
    "\u043f\u0440\u0438\u0439\u0442\u0438": ("arrive by walking", "to come, to arrive"),
    "\u0443\u0439\u0442\u0438": ("leave / go away", "to leave, to go away"),
    "\u0437\u0430\u0439\u0442\u0438": ("enter briefly / stop by", "to come in, to stop by"),
    "\u0432\u044b\u0439\u0442\u0438": ("exit / go out", "to go out, to exit"),
    "\u043f\u0435\u0440\u0435\u0439\u0442\u0438": ("cross / go across", "to cross, to go over"),
    "\u0441\u0445\u043e\u0434\u0438\u0442\u044c": ("make a quick round trip", "to go and come back"),
}

PERSON_ROWS = (
    ("1sg", {"1per", "sing"}),
    ("2sg", {"2per", "sing"}),
    ("3sg", {"3per", "sing"}),
    ("1pl", {"1per", "plur"}),
    ("2pl", {"2per", "plur"}),
    ("3pl", {"3per", "plur"}),
)
PAST_ROWS = (
    ("masc", {"past", "sing", "masc"}),
    ("femn", {"past", "sing", "femn"}),
    ("neut", {"past", "sing", "neut"}),
    ("plur", {"past", "plur"}),
)


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
    if morph is None:
        return escape(text)
    tokens = _analyze_sentence(text, morph)
    parts: list[str] = []
    cursor = 0
    any_marked = False
    for token in tokens:
        parts.append(escape(text[cursor : token.start]))
        marked = _render_token(token)
        parts.append(marked)
        any_marked = any_marked or marked != escape(token.surface)
        cursor = token.end
    parts.append(escape(text[cursor:]))
    rendered = "".join(parts)
    if any_marked:
        rendered += _grammar_key_html()
    return rendered


def _analyze_sentence(text: str, morph) -> list[GrammarToken]:
    tokens: list[GrammarToken] = []
    for match in _CYRILLIC_WORD_RE.finditer(text):
        surface = match.group(0)
        lower = surface.lower().replace("\u0451", "\u0435")
        parses = morph.parse(lower)
        tokens.append(
            GrammarToken(
                surface=surface,
                start=match.start(),
                end=match.end(),
                lower=lower,
                parses=parses,
                selected=parses[0] if parses else None,
            )
        )
    for index, token in enumerate(tokens):
        if not token.selected:
            continue
        if _pos(token.selected) in CASE_BEARING_POS:
            _resolve_case(tokens, index)
    _resolve_agreement(tokens)
    return tokens


def _resolve_case(tokens: list[GrammarToken], index: int) -> None:
    token = tokens[index]
    current = _case(token.selected)
    if not current:
        return
    candidates = _case_candidates(token)
    previous = tokens[index - 1].lower if index > 0 else ""
    governed = PREPOSITION_CASES.get(previous)
    if governed:
        for wanted in governed:
            if wanted in candidates:
                _select_case(token, wanted, f"Resolved by preposition: {previous} + {wanted}")
                return
    if len(candidates) == 1:
        _select_case(token, current, "")
        return
    previous_verb = _nearest_previous(tokens, index, VERB_POS)
    next_verb = _nearest_next(tokens, index, VERB_POS)
    if previous_verb and "accs" in candidates and not governed:
        _select_case(token, "accs", "Resolved as likely direct object")
    elif next_verb and "nomn" in candidates and not governed:
        _select_case(token, "nomn", "Resolved as likely subject")


def _resolve_agreement(tokens: list[GrammarToken]) -> None:
    for index, token in enumerate(tokens):
        if not token.selected or _pos(token.selected) not in {"ADJF", "PRTF", "NPRO", "NUMR"}:
            continue
        if token.resolved_case and token.resolution_reason:
            continue
        noun = _nearest_noun(tokens, index)
        if not noun or not noun.resolved_case:
            continue
        if _agrees(token.selected, noun.selected) and noun.resolved_case in _case_candidates(token):
            _select_case(token, noun.resolved_case, "Resolved by agreement")


def _render_token(token: GrammarToken) -> str:
    if not token.selected:
        return escape(token.surface)
    lemma = getattr(token.selected, "normal_form", token.lower)
    if lemma in MOTION_VERBS:
        return _motion_span(token)
    if _pos(token.selected) in VERB_POS:
        return _verb_span(token)
    if _pos(token.selected) not in CASE_BEARING_POS:
        return escape(token.surface)
    case = token.resolved_case
    if not case or _is_unresolved_ambiguous(token):
        return _case_span(token, "unknown", _case_popup_html(token, ""))
    return _case_span(token, case, _case_popup_html(token, case))


def _case_popup_html(token: GrammarToken, current_case: str) -> str:
    parsed = token.selected
    lemma = escape(getattr(parsed, "normal_form", token.lower))
    rows = []
    for case in CASE_ORDER:
        form = _inflect(parsed, {case, *_number_grammemes(parsed), *_gender_grammemes(parsed, case)})
        value = escape(form or "")
        if case == current_case and value:
            value = f"<b>{value}</b>"
        rows.append(f"<tr><th>{CASE_LABELS[case]}</th><td>{value}</td></tr>")
    details = _case_details(parsed, current_case, token.resolution_reason)
    return _popover(lemma, details, '<table class="case-table">' + "".join(rows) + "</table>")


def _verb_popup_html(token: GrammarToken) -> str:
    parsed = token.selected
    lemma = escape(getattr(parsed, "normal_form", token.lower))
    rows = _past_rows(parsed, token.lower) if _tag_value(parsed, "tense") == "past" else _person_rows(parsed, token.lower)
    details = _verb_details(parsed)
    if not rows:
        return _popover(lemma, details, "")
    return _popover(lemma, details, '<table class="case-table">' + "".join(rows) + "</table>")


def _motion_popup_html(token: GrammarToken) -> str:
    parsed = token.selected
    lemma = getattr(parsed, "normal_form", token.lower)
    rows = []
    for motion_lemma, (context, english) in MOTION_VERBS.items():
        row_class = ' class="motion-current"' if motion_lemma == lemma else ""
        label = escape(motion_lemma)
        if motion_lemma == lemma:
            label = f"<b>{label}</b>"
        rows.append(
            f"<tr{row_class}><th>{label}</th><td>{escape(english)}<br><span>{escape(context)}</span></td></tr>"
        )
    verb_table = _verb_popup_html(token)
    return (
        '<span class="case-popover motion-popover" role="tooltip">'
        f'<span class="case-title">{escape(lemma)} | motion verb</span>'
        f'<span class="case-meta">{escape(_verb_details(parsed))}</span>'
        '<table class="motion-table">'
        + "".join(rows)
        + "</table>"
        + verb_table.replace('<span class="case-popover" role="tooltip">', '<span class="embedded-popover">').replace(
            "</span>", "</span>", 1
        )
        + "</span>"
    )


def _person_rows(parsed, current_lower: str) -> list[str]:
    rows = []
    for label, grammemes in PERSON_ROWS:
        form = _inflect(parsed, grammemes)
        value = _bold_if_current(form, current_lower)
        rows.append(f"<tr><th>{label}</th><td>{value}</td></tr>")
    return rows


def _past_rows(parsed, current_lower: str) -> list[str]:
    rows = []
    for label, grammemes in PAST_ROWS:
        form = _inflect(parsed, grammemes)
        value = _bold_if_current(form, current_lower)
        rows.append(f"<tr><th>{label}</th><td>{value}</td></tr>")
    return rows


def _bold_if_current(form: str, current_lower: str) -> str:
    value = escape(form or "")
    if form and form.replace("\u0451", "\u0435") == current_lower:
        return f"<b>{value}</b>"
    return value


def _case_span(token: GrammarToken, case: str, popup: str) -> str:
    classes = f"case-word case-{escape(case)} {_gender_class(token.selected)}".strip()
    return f'<span class="{classes}" tabindex="0">{escape(token.surface)}{popup}</span>'


def _verb_span(token: GrammarToken) -> str:
    return f'<span class="verb-word {_gender_class(token.selected)}" tabindex="0">{escape(token.surface)}{_verb_popup_html(token)}</span>'


def _motion_span(token: GrammarToken) -> str:
    return (
        f'<span class="motion-word {_gender_class(token.selected)}" tabindex="0">'
        f"{escape(token.surface)}{_motion_popup_html(token)}</span>"
    )


def _popover(title: str, meta: str, body: str) -> str:
    return (
        '<span class="case-popover" role="tooltip">'
        f'<span class="case-title">{title}</span>'
        f'<span class="case-meta">{escape(meta)}</span>'
        f"{body}</span>"
    )


def _case_details(parsed, current_case: str, reason: str) -> str:
    pieces = [CASE_NAMES.get(current_case, current_case) if current_case else "Ambiguous case"]
    for value in (_tag_value(parsed, "number"), _tag_value(parsed, "gender"), _pos(parsed)):
        if value:
            pieces.append(value)
    if reason:
        pieces.append(reason)
    return " | ".join(pieces)


def _verb_details(parsed) -> str:
    pieces = []
    for value in (
        _pos(parsed),
        _tag_value(parsed, "aspect"),
        _tag_value(parsed, "tense"),
        _tag_value(parsed, "mood"),
        _tag_value(parsed, "person"),
        _tag_value(parsed, "number"),
        _tag_value(parsed, "gender"),
    ):
        if value:
            pieces.append(value)
    return " | ".join(pieces) if pieces else "Verb form"


def _inflect(parsed, grammemes: set[str]) -> str:
    inflected = parsed.inflect(grammemes) if hasattr(parsed, "inflect") else None
    return getattr(inflected, "word", "") if inflected else ""


def _select_case(token: GrammarToken, case: str, reason: str) -> None:
    for parse in token.parses:
        if _case(parse) == case:
            token.selected = parse
            token.resolved_case = case
            token.resolution_reason = reason
            return
    token.resolved_case = case
    token.resolution_reason = reason


def _is_unresolved_ambiguous(token: GrammarToken) -> bool:
    if token.resolution_reason:
        return False
    return len(_case_candidates(token)) > 1


def _case_candidates(token: GrammarToken) -> set[str]:
    if not token.parses:
        return set()
    selected_score = getattr(token.parses[0], "score", 1.0)
    cases = set()
    for parse in token.parses[:4]:
        score = getattr(parse, "score", selected_score)
        if selected_score - score > 0.05:
            continue
        case = _case(parse)
        if case:
            cases.add(case)
    return cases


def _nearest_previous(tokens: list[GrammarToken], index: int, pos_values: set[str]) -> GrammarToken | None:
    for candidate in reversed(tokens[max(0, index - 3) : index]):
        if candidate.selected and _pos(candidate.selected) in pos_values:
            return candidate
    return None


def _nearest_next(tokens: list[GrammarToken], index: int, pos_values: set[str]) -> GrammarToken | None:
    for candidate in tokens[index + 1 : index + 4]:
        if candidate.selected and _pos(candidate.selected) in pos_values:
            return candidate
    return None


def _nearest_noun(tokens: list[GrammarToken], index: int) -> GrammarToken | None:
    for candidate in tokens[index + 1 : index + 4]:
        if candidate.selected and _pos(candidate.selected) == "NOUN":
            return candidate
    for candidate in reversed(tokens[max(0, index - 3) : index]):
        if candidate.selected and _pos(candidate.selected) == "NOUN":
            return candidate
    return None


def _agrees(left, right) -> bool:
    left_number = _tag_value(left, "number")
    right_number = _tag_value(right, "number")
    left_gender = _tag_value(left, "gender")
    right_gender = _tag_value(right, "gender")
    if left_number and right_number and left_number != right_number:
        return False
    if left_number != "plur" and left_gender and right_gender and left_gender != right_gender:
        return False
    return True


def _number_grammemes(parsed) -> set[str]:
    number = _tag_value(parsed, "number")
    return {number} if number else set()


def _gender_grammemes(parsed, case: str = "") -> set[str]:
    gender = _tag_value(parsed, "gender")
    number = _tag_value(parsed, "number")
    if gender and number != "plur" and _pos(parsed) in {"ADJF", "PRTF"}:
        return {gender}
    return set()


def _gender_class(parsed) -> str:
    gender = _tag_value(parsed, "gender")
    number = _tag_value(parsed, "number")
    if number == "plur":
        return ""
    if gender in {"masc", "femn", "neut"}:
        return f"gender-{gender}"
    return ""


def _pos(parsed) -> str:
    return _tag_value(parsed, "POS")


def _case(parsed) -> str:
    return _tag_value(parsed, "case")


def _tag_value(parsed, name: str) -> str:
    tag = getattr(parsed, "tag", None)
    return getattr(tag, name, "") or ""


def _grammar_key_html() -> str:
    case_chips = "".join(
        f'<span class="case-chip case-{case}">{label}</span>' for case, label in CASE_LABELS.items()
    )
    gender_chips = (
        '<span class="gender-key-label gender-masc">Masc</span>'
        '<span class="gender-key-label gender-femn">Fem</span>'
        '<span class="gender-key-label gender-neut">Neut</span>'
    )
    verb_chips = '<span class="verb-key-label">Verb</span><span class="motion-key-label">Motion</span>'
    return f'<div class="case-key">{case_chips}{gender_chips}{verb_chips}</div>'
