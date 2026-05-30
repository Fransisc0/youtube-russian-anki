import unittest

from yt_anki.core_words import lookup_core_word


class CoreWordsTests(unittest.TestCase):
    def test_lookup_core_word_fixes_we(self):
        info = lookup_core_word("\u043c\u044b")
        self.assertIsNotNone(info)
        self.assertEqual(info.english, "we")
        self.assertEqual(info.ipa, "mɨ")

    def test_unknown_returns_none(self):
        self.assertIsNone(lookup_core_word("nonexistent"))


if __name__ == "__main__":
    unittest.main()
