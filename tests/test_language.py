import unittest

from yt_anki.language import RussianLemmatizer, unique_lemmas


class LanguageTests(unittest.TestCase):
    def test_extracts_cyrillic_tokens(self):
        tokens = RussianLemmatizer().extract("Я говорю по-русски, hello!")
        surfaces = [token.surface for token in tokens]
        self.assertIn("говорю", surfaces)
        self.assertNotIn("hello", surfaces)

    def test_unique_lemmas_tracks_surfaces(self):
        tokens = RussianLemmatizer().extract("дом дом")
        grouped = unique_lemmas(tokens)
        self.assertIn("дом", grouped)
        self.assertEqual(grouped["дом"], ["дом"])


if __name__ == "__main__":
    unittest.main()
