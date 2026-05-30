import unittest

from yt_anki.pipeline import VideoProcessor, format_gloss
from yt_anki.wiktionary import WordInfo


class PipelineDictionaryTests(unittest.TestCase):
    def test_wiktionary_is_used_before_core_fallback(self):
        class FakeWiktionary:
            def __init__(self):
                self.lookups = []

            def lookup(self, lemma):
                self.lookups.append(lemma)
                return WordInfo(
                    lemma=lemma,
                    ipa="wik-ipa",
                    english="Wiktionary meaning",
                    source_url="wiktionary-url",
                )

        processor = VideoProcessor.__new__(VideoProcessor)
        processor.wiktionary = FakeWiktionary()

        info = processor._lookup_word("\u043c\u044b", "ru", [])

        self.assertEqual(processor.wiktionary.lookups, ["\u043c\u044b"])
        self.assertEqual(info.english, "Wiktionary meaning")
        self.assertEqual(info.source_url, "wiktionary-url")

    def test_core_dictionary_only_fills_missing_wiktionary_meaning(self):
        class FakeWiktionary:
            def lookup(self, lemma):
                return WordInfo(lemma=lemma, ipa="", english="", source_url="wiktionary-url")

        processor = VideoProcessor.__new__(VideoProcessor)
        processor.wiktionary = FakeWiktionary()

        info = processor._lookup_word("\u043c\u044b", "ru", [])

        self.assertEqual(info.english, "we")
        self.assertEqual(info.source_url, "wiktionary-url")

    def test_wiktionary_retries_hyphen_clitic_base_word(self):
        class FakeWiktionary:
            def __init__(self):
                self.lookups = []

            def lookup(self, lemma):
                self.lookups.append(lemma)
                if lemma == "\u043a\u0438\u043d\u043e":
                    return WordInfo(
                        lemma=lemma,
                        ipa="kino",
                        english="cinema; film",
                        source_url="wiktionary-kino",
                    )
                return WordInfo(lemma=lemma, ipa="", english="", source_url="wiktionary-missing")

        processor = VideoProcessor.__new__(VideoProcessor)
        processor.wiktionary = FakeWiktionary()

        info = processor._lookup_word("\u043a\u0438\u043d\u043e-\u0442\u043e", "ru", [])

        self.assertEqual(processor.wiktionary.lookups, ["\u043a\u0438\u043d\u043e-\u0442\u043e", "\u043a\u0438\u043d\u043e"])
        self.assertEqual(info.lemma, "\u043a\u0438\u043d\u043e-\u0442\u043e")
        self.assertEqual(info.english, "cinema; film")
        self.assertEqual(info.source_url, "wiktionary-kino")

    def test_russian_wiktionary_fills_missing_english_wiktionary_meaning(self):
        class FakeWiktionary:
            def __init__(self):
                self.lookups = []

            def lookup(self, lemma):
                self.lookups.append(("en", lemma))
                return WordInfo(lemma=lemma, ipa="", english="", source_url="en-url")

            def lookup_ru(self, lemma):
                self.lookups.append(("ru", lemma))
                return WordInfo(lemma=lemma, ipa="kadr", english="still; shot; frame", source_url="ru-url")

        processor = VideoProcessor.__new__(VideoProcessor)
        processor.wiktionary = FakeWiktionary()

        info = processor._lookup_word("\u043a\u0430\u0434\u0440", "ru", [])

        self.assertEqual(processor.wiktionary.lookups, [("en", "\u043a\u0430\u0434\u0440"), ("ru", "\u043a\u0430\u0434\u0440")])
        self.assertEqual(info.english, "still; shot; frame")
        self.assertEqual(info.source_url, "ru-url")

    def test_missing_dictionary_meaning_does_not_call_translator(self):
        class FakeWiktionary:
            def lookup(self, lemma):
                return WordInfo(lemma=lemma, ipa="", english="", source_url="url")

        class ExplodingTranslator:
            def translate(self, request):
                raise AssertionError("word glosses must not use machine translation")

        processor = VideoProcessor.__new__(VideoProcessor)
        processor.wiktionary = FakeWiktionary()
        processor.translator = ExplodingTranslator()

        info = processor._lookup_word("\u0441\u043b\u043e\u0432\u043e", "ru", [])
        self.assertEqual(info.english, "")
        self.assertIn("dictionary meaning unavailable", format_gloss(info.lemma, info))


if __name__ == "__main__":
    unittest.main()
