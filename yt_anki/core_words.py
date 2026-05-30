from __future__ import annotations

from .wiktionary import WordInfo


CORE_RUSSIAN_WORDS: dict[str, tuple[str, str]] = {
    "\u0430": ("a", "and; but"),
    "\u0432": ("v", "in; into"),
    "\u0432\u043e": ("vo", "in; into"),
    "\u0438": ("i", "and"),
    "\u043c\u044b": ("m\u0268", "we"),
    "\u043e\u043d\u0438": ("\u0250\u02c8n\u02b2i", "they"),
    "\u043e\u043d": ("on", "he"),
    "\u043e\u043d\u0430": ("\u0250\u02c8na", "she"),
    "\u043e\u043d\u043e": ("\u0250\u02c8no", "it"),
    "\u044f": ("ja", "I"),
    "\u0442\u044b": ("t\u0268", "you"),
    "\u0432\u044b": ("v\u0268", "you"),
    "\u043f\u043e": ("po", "along; according to; by"),
    "\u0441": ("s", "with; from"),
    "\u0441\u043e": ("so", "with; from"),
    "\u043d\u0430": ("na", "on; at; to"),
    "\u043d\u0435": ("n\u02b2e", "not"),
    "\u0434\u0430": ("da", "yes; and; but"),
    "\u043a\u0430\u043a": ("kak", "how; as; like"),
    "\u0435\u0441\u043b\u0438": ("\u02c8jesl\u02b2i", "if"),
    "\u0442\u0430\u043a": ("tak", "so; thus; like that"),
    "\u0436\u0435": ("\u0290e", "emphatic particle; same; however"),
    "\u0447\u0442\u043e": ("\u0282to", "what; that"),
    "\u044d\u0442\u043e": ("\u02c8eto", "this; it"),
    "\u0441\u0435\u0433\u043e\u0434\u043d\u044f": ("s\u02b2\u026a\u02c8vodn\u02b2\u0259", "today"),
    "\u0441\u0443\u0442\u044c": ("sut\u02b2", "essence; point"),
    "\u0441\u043c\u043e\u0442\u0440\u0435\u0442\u044c": ("sm\u0250\u02c8tr\u02b2et\u02b2", "to watch; to look"),
    "\u0444\u0438\u043b\u044c\u043c": ("f\u02b2il\u02b2m", "film; movie"),
    "\u043c\u043d\u0435\u043d\u0438\u0435": ("\u02c8mn\u02b2en\u02b2\u026aje", "opinion"),
    "\u0433\u043e\u0441\u0443\u0434\u0430\u0440\u0441\u0442\u0432\u043e": ("\u0261\u0259s\u028a\u02c8darstv\u0259", "state; government"),
    "\u0434\u043e\u043b\u0436\u043d\u044b\u0439": ("\u02c8dol\u0290n\u0268j", "proper; due"),
    "\u0431\u044b\u0442\u044c": ("b\u0268t\u02b2", "to be"),
    "\u043e\u043f\u0440\u0435\u0434\u0435\u043b\u044f\u0442\u044c": ("\u0250pr\u02b2\u026ad\u02b2\u026a\u02c8l\u02b2at\u02b2", "to define; to determine"),
}

_CLITIC_SUFFIXES = ("-\u0442\u043e", "-\u0436\u0435", "-\u043b\u0438", "-\u043a\u0430", "-\u043d\u0438\u0431\u0443\u0434\u044c")


def dictionary_lookup_candidates(lemma: str) -> list[str]:
    candidates = [lemma]
    for suffix in _CLITIC_SUFFIXES:
        if lemma.endswith(suffix):
            base = lemma[: -len(suffix)]
            if base:
                candidates.append(base)
            break
    return candidates


def lookup_core_word(lemma: str) -> WordInfo | None:
    match = None
    for lookup in dictionary_lookup_candidates(lemma):
        match = CORE_RUSSIAN_WORDS.get(lookup)
        if match:
            break
    if not match:
        return None
    ipa, english = match
    return WordInfo(lemma=lemma, ipa=ipa, english=english, source_url="built-in")
