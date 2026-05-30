import unittest

from yt_anki.language import RussianLemmatizer, unique_lemmas


class LanguageTests(unittest.TestCase):
    def test_extracts_cyrillic_tokens(self):
        tokens = RussianLemmatizer().extract("\u042f \u0433\u043e\u0432\u043e\u0440\u044e \u043f\u043e-\u0440\u0443\u0441\u0441\u043a\u0438, hello!")
        surfaces = [token.surface for token in tokens]
        self.assertIn("\u0433\u043e\u0432\u043e\u0440\u044e", surfaces)
        self.assertNotIn("hello", surfaces)

    def test_unique_lemmas_tracks_surfaces(self):
        tokens = RussianLemmatizer().extract("\u0434\u043e\u043c \u0434\u043e\u043c")
        grouped = unique_lemmas(tokens)
        self.assertIn("\u0434\u043e\u043c", grouped)
        self.assertEqual(grouped["\u0434\u043e\u043c"], ["\u0434\u043e\u043c"])


if __name__ == "__main__":
    unittest.main()
