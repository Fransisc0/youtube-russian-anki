from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import quote


@dataclass(frozen=True)
class WordInfo:
    lemma: str
    ipa: str
    english: str
    source_url: str


_IPA_RE = re.compile(r"\{\{IPA\|ru\|([^}|]+)")
_GLOSS_RE = re.compile(r"^#\s+(?![:*#])(.+)$", re.MULTILINE)
_TEMPLATE_RE = re.compile(r"\{\{[^{}]*\}\}")
_LINK_RE = re.compile(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]")
_REF_RE = re.compile(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", re.DOTALL)


def wiktionary_url(lemma: str) -> str:
    return f"https://en.wiktionary.org/wiki/{quote(lemma)}#Russian"


def _strip_wiki_markup(text: str) -> str:
    text = _REF_RE.sub("", text)
    text = _LINK_RE.sub(r"\1", text)
    text = _TEMPLATE_RE.sub("", text)
    text = re.sub(r"'{2,}", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ;.")


def parse_wiktionary_wikitext(lemma: str, wikitext: str) -> WordInfo:
    russian_match = re.search(
        r"^==Russian==\s*(?P<body>.*?)(?=^==[^=]+==|\Z)",
        wikitext,
        re.MULTILINE | re.DOTALL,
    )
    body = russian_match.group("body") if russian_match else wikitext
    ipa_match = _IPA_RE.search(body)
    ipa = ipa_match.group(1).strip() if ipa_match else ""

    glosses: list[str] = []
    for match in _GLOSS_RE.finditer(body):
        cleaned = _strip_wiki_markup(match.group(1))
        if cleaned and not cleaned.startswith(("Used to", "Alternative form")):
            glosses.append(cleaned)
        if len(glosses) >= 2:
            break

    return WordInfo(
        lemma=lemma,
        ipa=ipa,
        english="; ".join(glosses),
        source_url=wiktionary_url(lemma),
    )


class WiktionaryClient:
    def lookup(self, lemma: str) -> WordInfo:
        import requests

        response = requests.get(
            "https://en.wiktionary.org/w/api.php",
            params={
                "action": "query",
                "format": "json",
                "prop": "revisions",
                "titles": lemma,
                "rvprop": "content",
                "rvslots": "main",
                "formatversion": "2",
                "origin": "*",
            },
            timeout=30,
            headers={"User-Agent": "yt-anki-language-cards/0.1"},
        )
        response.raise_for_status()
        pages = response.json().get("query", {}).get("pages", [])
        if not pages or pages[0].get("missing"):
            return WordInfo(lemma=lemma, ipa="", english="", source_url=wiktionary_url(lemma))
        wikitext = pages[0]["revisions"][0]["slots"]["main"]["content"]
        return parse_wiktionary_wikitext(lemma, wikitext)
