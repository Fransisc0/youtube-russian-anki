import unittest

from yt_anki.translation import normalize_argos_language


class TranslationTests(unittest.TestCase):
    def test_normalizes_deepl_style_english(self):
        self.assertEqual(normalize_argos_language("EN-US"), "en")

    def test_normalizes_simple_language(self):
        self.assertEqual(normalize_argos_language("ru"), "ru")


if __name__ == "__main__":
    unittest.main()
