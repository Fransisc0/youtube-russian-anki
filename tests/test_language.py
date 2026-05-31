import unittest
from types import SimpleNamespace

from yt_anki.language import RussianLemmatizer, mark_sentence_cases, unique_lemmas


class FakeTag:
    def __init__(self, POS="", case="", number="", gender=""):
        self.POS = POS
        self.case = case
        self.number = number
        self.gender = gender


class FakeParse:
    def __init__(self, word, normal_form, tag, forms=None, score=1.0):
        self.word = word
        self.normal_form = normal_form
        self.tag = tag
        self.score = score
        self._forms = forms or {}

    def inflect(self, grammemes):
        for key, value in self._forms.items():
            if set(key).issubset(grammemes):
                return SimpleNamespace(word=value)
        return None


class FakeMorph:
    def __init__(self, parses):
        self.parses = parses

    def parse(self, word):
        return self.parses.get(word, [])


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

    def test_mark_sentence_highlights_case_word_and_bolds_current_form(self):
        forms = {
            ("nomn", "sing"): "\u0440\u0430\u0431\u043e\u0442\u043d\u0438\u043a",
            ("gent", "sing"): "\u0440\u0430\u0431\u043e\u0442\u043d\u0438\u043a\u0430",
            ("datv", "sing"): "\u0440\u0430\u0431\u043e\u0442\u043d\u0438\u043a\u0443",
            ("accs", "sing"): "\u0440\u0430\u0431\u043e\u0442\u043d\u0438\u043a\u0430",
            ("ablt", "sing"): "\u0440\u0430\u0431\u043e\u0442\u043d\u0438\u043a\u043e\u043c",
            ("loct", "sing"): "\u0440\u0430\u0431\u043e\u0442\u043d\u0438\u043a\u0435",
        }
        morph = FakeMorph(
            {
                "\u0440\u0430\u0431\u043e\u0442\u043d\u0438\u043a": [
                    FakeParse(
                        "\u0440\u0430\u0431\u043e\u0442\u043d\u0438\u043a",
                        "\u0440\u0430\u0431\u043e\u0442\u043d\u0438\u043a",
                        FakeTag(POS="NOUN", case="nomn", number="sing", gender="masc"),
                        forms,
                    )
                ]
            }
        )

        html = mark_sentence_cases("\u0440\u0430\u0431\u043e\u0442\u043d\u0438\u043a!", morph)

        self.assertIn("case-word case-nomn", html)
        self.assertIn("<b>\u0440\u0430\u0431\u043e\u0442\u043d\u0438\u043a</b>", html)
        self.assertIn("case-popover", html)
        self.assertIn("case-key", html)

    def test_mark_sentence_escapes_non_word_text(self):
        morph = FakeMorph({})
        html = mark_sentence_cases("\u0434\u043e\u043c <script>", morph)
        self.assertIn("&lt;script&gt;", html)
        self.assertNotIn("<script>", html)

    def test_ambiguous_case_uses_unknown_style(self):
        morph = FakeMorph(
            {
                "\u0441\u043b\u043e\u0432\u0430": [
                    FakeParse("\u0441\u043b\u043e\u0432\u0430", "\u0441\u043b\u043e\u0432\u043e", FakeTag(POS="NOUN", case="nomn"), score=0.6),
                    FakeParse("\u0441\u043b\u043e\u0432\u0430", "\u0441\u043b\u043e\u0432\u043e", FakeTag(POS="NOUN", case="gent"), score=0.59),
                ]
            }
        )

        html = mark_sentence_cases("\u0441\u043b\u043e\u0432\u0430", morph)

        self.assertIn("case-word case-unknown", html)
        self.assertIn("Ambiguous case", html)


if __name__ == "__main__":
    unittest.main()
