import unittest

from yt_anki.ipa import approximate_russian_ipa


class IpaTests(unittest.TestCase):
    def test_approximate_russian_ipa(self):
        self.assertEqual(approximate_russian_ipa("\u0434\u0435\u043d\u044c"), "dʲen")

    def test_ignores_non_cyrillic(self):
        self.assertEqual(approximate_russian_ipa("123"), "")


if __name__ == "__main__":
    unittest.main()
