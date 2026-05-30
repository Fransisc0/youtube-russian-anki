import unittest

from yt_anki.pipeline import VideoProcessor, format_gloss
from yt_anki.wiktionary import WordInfo


class PipelineDictionaryTests(unittest.TestCase):
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
