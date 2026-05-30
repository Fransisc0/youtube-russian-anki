import unittest

from yt_anki.wiktionary import parse_wiktionary_wikitext, wiktionary_url


class WiktionaryTests(unittest.TestCase):
    def test_parse_ipa_and_gloss(self):
        text = """==Russian==
===Pronunciation===
* {{IPA|ru|ɡəvɐˈrʲitʲ}}
===Verb===
# to speak, to talk
# to say
"""
        info = parse_wiktionary_wikitext("говорить", text)
        self.assertEqual(info.ipa, "ɡəvɐˈrʲitʲ")
        self.assertIn("to speak", info.english)

    def test_url(self):
        self.assertEqual(
            wiktionary_url("говорить"),
            "https://en.wiktionary.org/wiki/%D0%B3%D0%BE%D0%B2%D0%BE%D1%80%D0%B8%D1%82%D1%8C#Russian",
        )


if __name__ == "__main__":
    unittest.main()
