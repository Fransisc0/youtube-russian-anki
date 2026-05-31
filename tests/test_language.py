import unittest
from types import SimpleNamespace

from yt_anki.language import RussianLemmatizer, mark_sentence_cases, unique_lemmas


class FakeTag:
    def __init__(self, POS="", case="", number="", gender="", tense="", person="", aspect="", mood=""):
        self.POS = POS
        self.case = case
        self.number = number
        self.gender = gender
        self.tense = tense
        self.person = person
        self.aspect = aspect
        self.mood = mood


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

    def test_preposition_resolves_ambiguous_case(self):
        forms = {("loct", "sing"): "\u0434\u043e\u043c\u0435", ("accs", "sing"): "\u0434\u043e\u043c"}
        morph = FakeMorph(
            {
                "\u0434\u043e\u043c\u0435": [
                    FakeParse("\u0434\u043e\u043c\u0435", "\u0434\u043e\u043c", FakeTag(POS="NOUN", case="nomn", number="sing", gender="masc"), forms, 0.6),
                    FakeParse("\u0434\u043e\u043c\u0435", "\u0434\u043e\u043c", FakeTag(POS="NOUN", case="loct", number="sing", gender="masc"), forms, 0.59),
                ]
            }
        )

        html = mark_sentence_cases("\u0432 \u0434\u043e\u043c\u0435", morph)

        self.assertIn("case-word case-loct", html)
        self.assertIn("Resolved by preposition", html)

    def test_preposition_resolves_accusative_when_location_case_unavailable(self):
        morph = FakeMorph(
            {
                "\u0434\u043e\u043c": [
                    FakeParse("\u0434\u043e\u043c", "\u0434\u043e\u043c", FakeTag(POS="NOUN", case="accs", number="sing", gender="masc"))
                ]
            }
        )

        html = mark_sentence_cases("\u0432 \u0434\u043e\u043c", morph)

        self.assertIn("case-word case-accs", html)

    def test_preposition_resolves_instrumental_and_genitive(self):
        morph = FakeMorph(
            {
                "\u0434\u0440\u0443\u0433\u043e\u043c": [
                    FakeParse("\u0434\u0440\u0443\u0433\u043e\u043c", "\u0434\u0440\u0443\u0433", FakeTag(POS="NOUN", case="ablt", number="sing", gender="masc"))
                ],
                "\u0434\u0440\u0443\u0433\u0430": [
                    FakeParse("\u0434\u0440\u0443\u0433\u0430", "\u0434\u0440\u0443\u0433", FakeTag(POS="NOUN", case="gent", number="sing", gender="masc"))
                ],
            }
        )

        self.assertIn("case-word case-ablt", mark_sentence_cases("\u0441 \u0434\u0440\u0443\u0433\u043e\u043c", morph))
        self.assertIn("case-word case-gent", mark_sentence_cases("\u0431\u0435\u0437 \u0434\u0440\u0443\u0433\u0430", morph))

    def test_agreement_resolves_adjective_case(self):
        morph = FakeMorph(
            {
                "\u043d\u043e\u0432\u043e\u0433\u043e": [
                    FakeParse("\u043d\u043e\u0432\u043e\u0433\u043e", "\u043d\u043e\u0432\u044b\u0439", FakeTag(POS="ADJF", case="accs", number="sing", gender="masc"), score=0.6),
                    FakeParse("\u043d\u043e\u0432\u043e\u0433\u043e", "\u043d\u043e\u0432\u044b\u0439", FakeTag(POS="ADJF", case="gent", number="sing", gender="masc"), score=0.59),
                ],
                "\u0434\u0440\u0443\u0433\u0430": [
                    FakeParse("\u0434\u0440\u0443\u0433\u0430", "\u0434\u0440\u0443\u0433", FakeTag(POS="NOUN", case="gent", number="sing", gender="masc"))
                ],
            }
        )

        html = mark_sentence_cases("\u043d\u043e\u0432\u043e\u0433\u043e \u0434\u0440\u0443\u0433\u0430", morph)

        self.assertIn("Resolved by agreement", html)

    def test_gender_tint_classes_are_added(self):
        morph = FakeMorph(
            {
                "\u0434\u0440\u0443\u0433": [FakeParse("\u0434\u0440\u0443\u0433", "\u0434\u0440\u0443\u0433", FakeTag(POS="NOUN", case="nomn", number="sing", gender="masc"))],
                "\u043c\u0430\u043c\u0430": [FakeParse("\u043c\u0430\u043c\u0430", "\u043c\u0430\u043c\u0430", FakeTag(POS="NOUN", case="nomn", number="sing", gender="femn"))],
                "\u043e\u043a\u043d\u043e": [FakeParse("\u043e\u043a\u043d\u043e", "\u043e\u043a\u043d\u043e", FakeTag(POS="NOUN", case="nomn", number="sing", gender="neut"))],
            }
        )

        html = mark_sentence_cases("\u0434\u0440\u0443\u0433 \u043c\u0430\u043c\u0430 \u043e\u043a\u043d\u043e", morph)

        self.assertIn("gender-masc", html)
        self.assertIn("gender-femn", html)
        self.assertIn("gender-neut", html)
        self.assertIn("Masc", html)

    def test_present_verb_popup_bolds_current_form(self):
        forms = {
            ("1per", "sing"): "\u0438\u0434\u0443",
            ("2per", "sing"): "\u0438\u0434\u0435\u0448\u044c",
            ("3per", "sing"): "\u0438\u0434\u0435\u0442",
        }
        morph = FakeMorph(
            {
                "\u0438\u0434\u0443": [
                    FakeParse("\u0438\u0434\u0443", "\u0438\u0434\u0442\u0438", FakeTag(POS="VERB", tense="pres", person="1per", number="sing", aspect="impf"), forms)
                ]
            }
        )

        html = mark_sentence_cases("\u0438\u0434\u0443", morph)

        self.assertIn("motion-word", html)
        self.assertIn("<b>\u0438\u0434\u0443</b>", html)
        self.assertIn("one-way", html)

    def test_past_verb_popup_bolds_current_form(self):
        forms = {
            ("past", "sing", "masc"): "\u0434\u0435\u043b\u0430\u043b",
            ("past", "sing", "femn"): "\u0434\u0435\u043b\u0430\u043b\u0430",
            ("past", "sing", "neut"): "\u0434\u0435\u043b\u0430\u043b\u043e",
            ("past", "plur"): "\u0434\u0435\u043b\u0430\u043b\u0438",
        }
        morph = FakeMorph(
            {
                "\u0434\u0435\u043b\u0430\u043b": [
                    FakeParse("\u0434\u0435\u043b\u0430\u043b", "\u0434\u0435\u043b\u0430\u0442\u044c", FakeTag(POS="VERB", tense="past", number="sing", gender="masc", aspect="impf"), forms)
                ]
            }
        )

        html = mark_sentence_cases("\u0434\u0435\u043b\u0430\u043b", morph)

        self.assertIn("verb-word", html)
        self.assertIn("<b>\u0434\u0435\u043b\u0430\u043b</b>", html)
        self.assertNotIn("motion-word", html)

    def test_core_motion_verbs_map_to_motion_popup(self):
        for surface, lemma in {
            "\u0445\u043e\u0434\u0438\u043b": "\u0445\u043e\u0434\u0438\u0442\u044c",
            "\u043f\u043e\u0448\u0435\u043b": "\u043f\u043e\u0439\u0442\u0438",
            "\u043f\u0440\u0438\u0448\u0435\u043b": "\u043f\u0440\u0438\u0439\u0442\u0438",
            "\u0443\u0448\u0435\u043b": "\u0443\u0439\u0442\u0438",
            "\u0437\u0430\u0448\u0435\u043b": "\u0437\u0430\u0439\u0442\u0438",
            "\u0432\u044b\u0448\u0435\u043b": "\u0432\u044b\u0439\u0442\u0438",
            "\u043f\u0435\u0440\u0435\u0448\u0435\u043b": "\u043f\u0435\u0440\u0435\u0439\u0442\u0438",
            "\u0441\u0445\u043e\u0434\u0438\u043b": "\u0441\u0445\u043e\u0434\u0438\u0442\u044c",
        }.items():
            with self.subTest(surface=surface):
                morph = FakeMorph({surface: [FakeParse(surface, lemma, FakeTag(POS="VERB", tense="past", number="sing", gender="masc"))]})
                html = mark_sentence_cases(surface, morph)
                self.assertIn("motion-word", html)
                self.assertIn(f"<b>{lemma}</b>", html)


if __name__ == "__main__":
    unittest.main()
