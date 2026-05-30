from __future__ import annotations


_VOWELS = set("аеёиоуыэюя")
_MAP = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "ɡ",
    "д": "d",
    "е": "je",
    "ё": "jo",
    "ж": "ʐ",
    "з": "z",
    "и": "i",
    "й": "j",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "x",
    "ц": "t͡s",
    "ч": "t͡ɕ",
    "ш": "ʂ",
    "щ": "ɕː",
    "ы": "ɨ",
    "э": "e",
    "ю": "ju",
    "я": "ja",
}


def approximate_russian_ipa(word: str) -> str:
    letters = [char.lower() for char in word if "\u0400" <= char <= "\u04ff"]
    if not letters:
        return ""
    output: list[str] = []
    for index, char in enumerate(letters):
        if char in {"ь", "ъ"}:
            continue
        if char == "е" and index > 0 and letters[index - 1] not in _VOWELS and letters[index - 1] not in {"ь", "ъ"}:
            output.append("ʲe")
            continue
        if char == "ю" and index > 0 and letters[index - 1] not in _VOWELS and letters[index - 1] not in {"ь", "ъ"}:
            output.append("ʲu")
            continue
        if char == "я" and index > 0 and letters[index - 1] not in _VOWELS and letters[index - 1] not in {"ь", "ъ"}:
            output.append("ʲa")
            continue
        output.append(_MAP.get(char, char))
    return "".join(output)
