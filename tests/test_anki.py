import unittest
from pathlib import Path

from yt_anki.anki import AnkiCard, AnkiConnectClient, BACK_TEMPLATE, FRONT_TEMPLATE, MODEL_FIELDS
from yt_anki.pipeline import format_gloss, format_timestamp
from yt_anki.wiktionary import WordInfo


class AnkiPayloadTests(unittest.TestCase):
    def test_card_shape_dataclass(self):
        card = AnkiCard(
            russian_sentence="\u042f \u0433\u043e\u0432\u043e\u0440\u044e.",
            sentence_audio_path=Path("clip.mp3"),
            english_translation="I speak.",
            word_glosses="\u0433\u043e\u0432\u043e\u0440\u0438\u0442\u044c (\u0433\u043e\u0432\u043e\u0440\u0438\u0442\u044c, /\u0261\u0259v\u0250\u02c8r\u02b2it\u02b2/) - to speak",
            video_title="Test",
            video_url="https://youtube.com/watch?v=abc",
            timestamp="0:01",
        )
        self.assertEqual(card.russian_sentence, "\u042f \u0433\u043e\u0432\u043e\u0440\u044e.")

    def test_format_gloss(self):
        info = WordInfo("\u0433\u043e\u0432\u043e\u0440\u0438\u0442\u044c", "\u0261\u0259v\u0250\u02c8r\u02b2it\u02b2", "to speak", "url", "\u0433\u043e\u0432\u043e\u0440\u0438\u0301\u0442\u044c")
        self.assertEqual(
            format_gloss("\u0433\u043e\u0432\u043e\u0440\u0438\u0442\u044c", info),
            "\u0433\u043e\u0432\u043e\u0440\u0438\u0442\u044c (\u0433\u043e\u0432\u043e\u0440\u0438\u0301\u0442\u044c, /\u0261\u0259v\u0250\u02c8r\u02b2it\u02b2/) - to speak",
        )

    def test_format_gloss_marks_missing_ipa(self):
        info = WordInfo("\u0434\u0435\u043d\u044c", "", "day", "url")
        self.assertEqual(format_gloss("\u0434\u0435\u043d\u044c", info), "\u0434\u0435\u043d\u044c (\u0434\u0435\u043d\u044c, IPA unavailable) - day")

    def test_front_prompts_with_english(self):
        self.assertIn("{{EnglishTranslation}}", FRONT_TEMPLATE)
        self.assertNotIn("{{RussianSentence}}", FRONT_TEMPLATE)
        self.assertNotIn("{{SentenceAudio}}", FRONT_TEMPLATE)

    def test_back_template_includes_russian_and_one_audio(self):
        self.assertIn("{{RussianSentence}}", BACK_TEMPLATE)
        self.assertIn("{{RussianSentenceMarked}}", BACK_TEMPLATE)
        self.assertIn("{{SentenceAudio}}", BACK_TEMPLATE)
        self.assertEqual(BACK_TEMPLATE.count("{{SentenceAudio}}"), 1)

    def test_add_card_lets_ankiconnect_populate_sound_field_once(self):
        calls = []

        class FakeClient(AnkiConnectClient):
            def invoke(self, action, **params):
                calls.append((action, params))
                return 123

        card = AnkiCard(
            russian_sentence="test",
            sentence_audio_path=Path("clip.mp3"),
            english_translation="test",
            word_glosses="word",
            video_title="video",
            video_url="url",
            timestamp="0:01",
        )
        FakeClient("unused").add_card("deck", "model", card)
        note = calls[0][1]["note"]
        self.assertEqual(note["fields"]["SentenceAudio"], "")
        self.assertIn("RussianSentenceMarked", note["fields"])
        self.assertEqual(note["audio"][0]["fields"], ["SentenceAudio"])

    def test_new_model_includes_marked_sentence_field(self):
        self.assertIn("RussianSentenceMarked", MODEL_FIELDS)
        self.assertLess(MODEL_FIELDS.index("RussianSentence"), MODEL_FIELDS.index("RussianSentenceMarked"))

    def test_existing_model_adds_missing_marked_sentence_field(self):
        calls = []

        class FakeClient(AnkiConnectClient):
            def invoke(self, action, **params):
                calls.append((action, params))
                if action == "modelFieldNames":
                    return [
                        "RussianSentence",
                        "SentenceAudio",
                        "EnglishTranslation",
                        "WordGlosses",
                        "VideoTitle",
                        "VideoUrl",
                        "Timestamp",
                    ]
                return None

        FakeClient("unused").ensure_model_fields("model")

        add_calls = [params for action, params in calls if action == "modelFieldAdd"]
        self.assertEqual(add_calls[0]["fieldName"], "RussianSentenceMarked")

    def test_format_timestamp(self):
        self.assertEqual(format_timestamp(65), "1:05")


if __name__ == "__main__":
    unittest.main()
