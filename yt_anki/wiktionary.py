from __future__ import annotations

import re
from html import unescape
from html.parser import HTMLParser
from dataclasses import dataclass
from typing import Callable
from urllib.parse import quote


@dataclass(frozen=True)
class WordInfo:
    lemma: str
    ipa: str
    english: str
    source_url: str
    stressed: str = ""


_IPA_RE = re.compile(r"\{\{IPA\|ru\|([^}|]+)")
_GLOSS_RE = re.compile(r"^#\s+(?![:*#])(.+)$", re.MULTILINE)
_TEMPLATE_RE = re.compile(r"\{\{[^{}]*\}\}")
_LINK_RE = re.compile(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]")
_REF_RE = re.compile(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", re.DOTALL)
_RU_EN_TRANSLATION_RE = re.compile(r"^\|\s*en\s*=\s*(.+)$", re.MULTILINE)
_RU_EN_TEMPLATE_RE = re.compile(r"\{\{(?:t|t\+|t-|\u043f\u0435\u0440\u0435\u0432)\|en\|([^}|]+)")
_RU_IPA_RE = re.compile(r"(?:\u041c\u0424\u0410|IPA)[^\n\[]*\[([^\]]+)\]")
_CYRILLIC_WITH_STRESS_RE = re.compile(
    r"[\u0400-\u04ff][\u0400-\u04ff\u0301\u0300 -]*[\u0301\u0300][\u0400-\u04ff\u0301\u0300 -]*"
)
_USER_AGENT = "youtube-russian-anki/0.1 (https://github.com/Fransisc0/youtube-russian-anki)"


class _HtmlTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return re.sub(r"\s+", " ", unescape("".join(self.parts))).strip()


def wiktionary_url(lemma: str) -> str:
    return f"https://en.wiktionary.org/wiki/{quote(lemma)}#Russian"


def ru_wiktionary_url(lemma: str) -> str:
    fragment = "%D0%A0%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9"
    return f"https://ru.wiktionary.org/wiki/{quote(lemma)}#{fragment}"


def _strip_wiki_markup(text: str) -> str:
    text = _REF_RE.sub("", text)
    text = _LINK_RE.sub(r"\1", text)
    text = _TEMPLATE_RE.sub("", text)
    text = re.sub(r"'{2,}", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ;.")


def _strip_html(text: str) -> str:
    parser = _HtmlTextExtractor()
    parser.feed(text)
    return parser.text()


def _strip_wiki_templates(text: str) -> str:
    previous = None
    while previous != text:
        previous = text
        text = _TEMPLATE_RE.sub("", text)
    return text


def _first_stressed_russian(text: str) -> str:
    text = _strip_wiki_templates(text)
    text = _LINK_RE.sub(r"\1", text)
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    match = _CYRILLIC_WITH_STRESS_RE.search(text)
    return re.sub(r"\s+", " ", match.group(0)).strip(" -;,.()") if match else ""


def parse_rest_definition_json(lemma: str, data: dict) -> WordInfo:
    glosses: list[str] = []
    for entry in data.get("ru", []):
        for definition in entry.get("definitions", []):
            cleaned = _strip_html(definition.get("definition", ""))
            if cleaned and cleaned not in glosses:
                glosses.append(cleaned)
            if len(glosses) >= 5:
                break
        if len(glosses) >= 5:
            break
    return WordInfo(
        lemma=lemma,
        ipa="",
        english="; ".join(glosses),
        source_url=wiktionary_url(lemma),
    )


def parse_wiktionary_wikitext(lemma: str, wikitext: str) -> WordInfo:
    russian_match = re.search(
        r"^==Russian==\s*(?P<body>.*?)(?=^==[^=]+==|\Z)",
        wikitext,
        re.MULTILINE | re.DOTALL,
    )
    body = russian_match.group("body") if russian_match else wikitext
    ipa_match = _IPA_RE.search(body)
    ipa = ipa_match.group(1).strip() if ipa_match else ""
    stressed = _first_stressed_russian(body)

    glosses: list[str] = []
    for match in _GLOSS_RE.finditer(body):
        cleaned = _strip_wiki_markup(match.group(1))
        if cleaned and not cleaned.startswith(("Used to", "Alternative form")) and cleaned not in glosses:
            glosses.append(cleaned)
        if len(glosses) >= 5:
            break

    return WordInfo(
        lemma=lemma,
        ipa=ipa,
        english="; ".join(glosses),
        source_url=wiktionary_url(lemma),
        stressed=stressed,
    )


def _split_ru_translation_items(text: str) -> list[str]:
    text = _strip_wiki_markup(text)
    text = re.sub(r"\([^)]*\)", "", text)
    text = re.sub(r"\b(?:m|f|n|c|\u0441\u0440|\u043c|\u0436)\.?\b", "", text)
    text = re.sub(r"\b(?:in|the|a|an)\b.*$", "", text)
    pieces = re.split(r"[,;]", text)
    cleaned = []
    for piece in pieces:
        piece = re.sub(r"[^A-Za-z -]", "", piece).strip()
        if piece and piece not in cleaned:
            cleaned.append(piece)
    return cleaned


def parse_ru_wiktionary_wikitext(lemma: str, wikitext: str) -> WordInfo:
    russian_match = re.search(
        "^=\\s*(?:\u0420\u0443\u0441\u0441\u043a\u0438\u0439|\\{\\{-ru-\\}\\})\\s*=\\s*"
        "(?P<body>.*?)(?=^=\\s*[^=\\n]+\\s*=|\\Z)",
        wikitext,
        re.MULTILINE | re.DOTALL,
    )
    body = russian_match.group("body") if russian_match else wikitext
    ipa_match = _RU_IPA_RE.search(body)
    ipa = ipa_match.group(1).strip() if ipa_match else ""
    stressed = _first_stressed_russian(body)

    translations: list[str] = []
    for match in _RU_EN_TEMPLATE_RE.finditer(body):
        for item in _split_ru_translation_items(match.group(1)):
            if item not in translations:
                translations.append(item)
        if len(translations) >= 8:
            break

    if len(translations) < 8:
        for match in _RU_EN_TRANSLATION_RE.finditer(body):
            for item in _split_ru_translation_items(match.group(1)):
                if item not in translations:
                    translations.append(item)
            if len(translations) >= 8:
                break

    return WordInfo(
        lemma=lemma,
        ipa=ipa,
        english="; ".join(translations[:8]),
        source_url=ru_wiktionary_url(lemma),
        stressed=stressed,
    )


class WiktionaryClient:
    def lookup(self, lemma: str) -> WordInfo:
        info = self._lookup(
            lemma=lemma,
            api_url="https://en.wiktionary.org/w/api.php",
            missing_url=wiktionary_url(lemma),
            parser=parse_wiktionary_wikitext,
        )
        if info.english:
            return info
        try:
            rest_info = self._lookup_rest_definition(lemma)
        except Exception:
            return info
        return WordInfo(
            lemma=lemma,
            ipa=info.ipa,
            english=rest_info.english,
            source_url=info.source_url or rest_info.source_url,
            stressed=info.stressed,
        )

    def lookup_ru(self, lemma: str) -> WordInfo:
        return self._lookup(
            lemma=lemma,
            api_url="https://ru.wiktionary.org/w/api.php",
            missing_url=ru_wiktionary_url(lemma),
            parser=parse_ru_wiktionary_wikitext,
        )

    def _lookup(
        self,
        lemma: str,
        api_url: str,
        missing_url: str,
        parser: Callable[[str, str], WordInfo],
    ) -> WordInfo:
        import requests

        response = requests.get(
            api_url,
            params={
                "action": "query",
                "format": "json",
                "prop": "revisions",
                "titles": lemma,
                "rvprop": "content",
                "rvslots": "main",
                "formatversion": "2",
                "origin": "*",
                "redirects": "1",
            },
            timeout=30,
            headers={"User-Agent": _USER_AGENT},
        )
        response.raise_for_status()
        pages = response.json().get("query", {}).get("pages", [])
        if not pages or pages[0].get("missing"):
            return WordInfo(lemma=lemma, ipa="", english="", source_url=missing_url)
        wikitext = pages[0]["revisions"][0]["slots"]["main"]["content"]
        return parser(lemma, wikitext)

    def _lookup_rest_definition(self, lemma: str) -> WordInfo:
        import requests

        response = requests.get(
            f"https://en.wiktionary.org/api/rest_v1/page/definition/{quote(lemma)}",
            timeout=30,
            headers={"User-Agent": _USER_AGENT},
        )
        if response.status_code == 404:
            return WordInfo(lemma=lemma, ipa="", english="", source_url=wiktionary_url(lemma))
        response.raise_for_status()
        return parse_rest_definition_json(lemma, response.json())
