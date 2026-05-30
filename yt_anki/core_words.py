from __future__ import annotations

from .wiktionary import WordInfo


CORE_RUSSIAN_WORDS: dict[str, tuple[str, str]] = {
    "а": ("a", "and; but"),
    "в": ("v", "in; into"),
    "во": ("vo", "in; into"),
    "и": ("i", "and"),
    "мы": ("mɨ", "we"),
    "они": ("ɐˈnʲi", "they"),
    "он": ("on", "he"),
    "она": ("ɐˈna", "she"),
    "оно": ("ɐˈno", "it"),
    "я": ("ja", "I"),
    "ты": ("tɨ", "you"),
    "вы": ("vɨ", "you"),
    "по": ("po", "along; according to; by"),
    "с": ("s", "with; from"),
    "со": ("so", "with; from"),
    "на": ("na", "on; at; to"),
    "не": ("nʲe", "not"),
    "что": ("ʂto", "what; that"),
    "это": ("ˈeto", "this; it"),
    "сегодня": ("sʲɪˈvodnʲə", "today"),
    "суть": ("sutʲ", "essence; point"),
    "смотреть": ("smɐˈtrʲetʲ", "to watch; to look"),
    "фильм": ("fʲilʲm", "film; movie"),
    "мнение": ("ˈmnʲenʲɪje", "opinion"),
    "государство": ("ɡəsʊˈdarstvə", "state; government"),
    "должный": ("ˈdolʐnɨj", "proper; due"),
    "быть": ("bɨtʲ", "to be"),
    "определять": ("ɐprʲɪdʲɪˈlʲatʲ", "to define; to determine"),
}


def lookup_core_word(lemma: str) -> WordInfo | None:
    match = CORE_RUSSIAN_WORDS.get(lemma)
    if not match:
        return None
    ipa, english = match
    return WordInfo(lemma=lemma, ipa=ipa, english=english, source_url="built-in")
