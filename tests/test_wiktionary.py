import unittest

from yt_anki.wiktionary import parse_ru_wiktionary_wikitext, parse_wiktionary_wikitext, ru_wiktionary_url, wiktionary_url


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

    def test_parse_multiple_dictionary_glosses(self):
        text = """==Russian==
===Noun===
# first meaning
# second meaning
# third meaning
# fourth meaning
# fifth meaning
# sixth meaning
"""
        info = parse_wiktionary_wikitext("\u0441\u043b\u043e\u0432\u043e", text)
        self.assertIn("first meaning", info.english)
        self.assertIn("fifth meaning", info.english)
        self.assertNotIn("sixth meaning", info.english)

    def test_url(self):
        self.assertEqual(
            wiktionary_url("\u0433\u043e\u0432\u043e\u0440\u0438\u0442\u044c"),
            "https://en.wiktionary.org/wiki/%D0%B3%D0%BE%D0%B2%D0%BE%D1%80%D0%B8%D1%82%D1%8C#Russian",
        )

    def test_parse_russian_wiktionary_english_translations(self):
        text = """= \u0420\u0443\u0441\u0441\u043a\u0438\u0439 =
== \u043a\u0430\u0434\u0440 I ==
=== \u041f\u0440\u043e\u0438\u0437\u043d\u043e\u0448\u0435\u043d\u0438\u0435 ===
* \u041c\u0424\u0410: [kadr]
=== \u0421\u0435\u043c\u0430\u043d\u0442\u0438\u0447\u0435\u0441\u043a\u0438\u0435 \u0441\u0432\u043e\u0439\u0441\u0442\u0432\u0430 ===
==== \u041f\u0435\u0440\u0435\u0432\u043e\u0434 ====
{{\u043f\u0435\u0440\u0435\u0432-\u0431\u043b\u043e\u043a|\u0441\u043d\u0438\u043c\u043e\u043a
|en=[[still]], [[shot]], [[frame]]; \u0432 \u043a\u0430\u0434\u0440\u0435 in the frame
}}
{{\u043f\u0435\u0440\u0435\u0432-\u0431\u043b\u043e\u043a|\u0431\u043b\u043e\u043a \u0434\u0430\u043d\u043d\u044b\u0445
|en=[[packet]]
}}
"""
        info = parse_ru_wiktionary_wikitext("\u043a\u0430\u0434\u0440", text)
        self.assertEqual(info.ipa, "kadr")
        self.assertIn("still", info.english)
        self.assertIn("shot", info.english)
        self.assertIn("frame", info.english)
        self.assertIn("packet", info.english)

    def test_ru_url(self):
        self.assertEqual(
            ru_wiktionary_url("\u043a\u0430\u0434\u0440"),
            "https://ru.wiktionary.org/wiki/%D0%BA%D0%B0%D0%B4%D1%80#%D0%A0%D1%83%D1%81%D1%81%D0%BA%D0%B8%D0%B9",
        )


if __name__ == "__main__":
    unittest.main()
