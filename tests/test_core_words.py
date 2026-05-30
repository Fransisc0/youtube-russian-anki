import unittest

from yt_anki.core_words import lookup_core_word


class CoreWordsTests(unittest.TestCase):
    def test_lookup_core_word_fixes_we(self):
        info = lookup_core_word("\u043c\u044b")
        self.assertIsNotNone(info)
        self.assertEqual(info.english, "we")
        self.assertEqual(info.ipa, "m\u0268")

    def test_unknown_returns_none(self):
        self.assertIsNone(lookup_core_word("nonexistent"))

    def test_common_words_have_dictionary_meanings(self):
        expected = {
            "\u0434\u0430": "yes; and; but",
            "\u043a\u0430\u043a": "how; as; like",
            "\u0435\u0441\u043b\u0438": "if",
            "\u0442\u0430\u043a": "so; thus; like that",
            "\u0436\u0435": "emphatic particle; same; however",
        }
        for lemma, english in expected.items():
            with self.subTest(lemma=lemma):
                info = lookup_core_word(lemma)
                self.assertIsNotNone(info)
                self.assertEqual(info.english, english)


if __name__ == "__main__":
    unittest.main()
