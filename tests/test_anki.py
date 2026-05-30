import unittest
from pathlib import Path

from yt_anki.anki import AnkiCard
from yt_anki.pipeline import format_gloss, format_timestamp
from yt_anki.wiktionary import WordInfo


class AnkiPayloadTests(unittest.TestCase):
    def test_card_shape_dataclass(self):
        card = AnkiCard(
            russian_sentence="Я говорю.",
            sentence_audio_path=Path("clip.mp3"),
            english_translation="I speak.",
            word_glosses="говорить (говорить, /ɡəvɐˈrʲitʲ/) - to speak",
            video_title="Test",
            video_url="https://youtube.com/watch?v=abc",
            timestamp="0:01",
        )
        self.assertEqual(card.russian_sentence, "Я говорю.")

    def test_format_gloss(self):
        info = WordInfo("говорить", "ɡəvɐˈrʲitʲ", "to speak", "url")
        self.assertEqual(
            format_gloss("говорить", info),
            "говорить (говорить, /ɡəvɐˈrʲitʲ/) - to speak",
        )

    def test_format_timestamp(self):
        self.assertEqual(format_timestamp(65), "1:05")


if __name__ == "__main__":
    unittest.main()
