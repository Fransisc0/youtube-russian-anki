import unittest

from yt_anki.wiktionary import parse_wiktionary_wikitext, wiktionary_url


class WiktionaryTests(unittest.TestCase):
    def test_parse_ipa_and_gloss(self):
        text = """==Russian==
===Pronunciation===
* {{IPA|ru|\u0261\u0259v\u0250\u02c8r\u02b2it\u02b2}}
===Verb===
# to speak, to talk
# to say
"""
        info = parse_wiktionary_wikitext("\u0433\u043e\u0432\u043e\u0440\u0438\u0442\u044c", text)
        self.assertEqual(info.ipa, "\u0261\u0259v\u0250\u02c8r\u02b2it\u02b2")
        self.assertIn("to speak", info.english)

    def test_url(self):
        self.assertEqual(
            wiktionary_url("\u0433\u043e\u0432\u043e\u0440\u0438\u0442\u044c"),
            "https://en.wiktionary.org/wiki/%D0%B3%D0%BE%D0%B2%D0%BE%D1%80%D0%B8%D1%82%D1%8C#Russian",
        )


if __name__ == "__main__":
    unittest.main()
