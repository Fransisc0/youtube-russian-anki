import unittest

from yt_anki.transcript import (
    CaptionCue,
    append_without_overlap,
    collapse_repeated_lines,
    cues_to_sentences,
    parse_timestamp,
    parse_json3,
    parse_vtt,
    split_complete_sentences,
)


class TranscriptTests(unittest.TestCase):
    def test_parse_timestamp(self):
        self.assertEqual(parse_timestamp("00:01:02.500"), 62.5)

    def test_parse_vtt_and_group_sentences(self):
        vtt = """WEBVTT

00:00:01.000 --> 00:00:02.000
Привет

00:00:02.000 --> 00:00:03.500
как дела?

00:00:04.000 --> 00:00:05.000
Хорошо.
"""
        cues = parse_vtt(vtt)
        self.assertEqual(len(cues), 3)
        sentences = cues_to_sentences(cues)
        self.assertEqual(len(sentences), 2)
        self.assertEqual(sentences[0].text, "Привет как дела?")
        self.assertEqual(sentences[0].start, 1.0)
        self.assertEqual(sentences[0].end, 3.5)

    def test_parse_vtt_skips_tiny_transition_cues(self):
        vtt = """WEBVTT

00:00:01.000 --> 00:00:01.010
duplicate

00:00:01.000 --> 00:00:02.000
real cue
"""
        cues = parse_vtt(vtt)
        self.assertEqual(len(cues), 1)
        self.assertEqual(cues[0].text, "real cue")

    def test_parse_json3(self):
        contents = """{
          "events": [
            {"tStartMs": 1000, "dDurationMs": 1500, "segs": [{"utf8": "Привет"}, {"utf8": " мир."}]},
            {"tStartMs": 2500, "dDurationMs": 1000, "segs": [{"utf8": "\\n"}]}
          ]
        }"""
        cues = parse_json3(contents)
        self.assertEqual(len(cues), 1)
        self.assertEqual(cues[0].text, "Привет мир.")
        self.assertEqual(cues[0].start, 1.0)
        self.assertEqual(cues[0].end, 2.5)

    def test_clean_caption_text_removes_speaker_marker(self):
        self.assertEqual(collapse_repeated_lines([">> Привет."]), "Привет.")

    def test_collapse_youtube_rolling_caption_lines(self):
        text = collapse_repeated_lines(
            [
                "Сегодня мы смотрим",
                "Сегодня мы смотрим фильм.",
            ]
        )
        self.assertEqual(text, "Сегодня мы смотрим фильм.")

    def test_append_without_overlap(self):
        self.assertEqual(
            append_without_overlap("Сегодня мы смотрим", "мы смотрим фильм."),
            "Сегодня мы смотрим фильм.",
        )

    def test_cues_to_sentences_dedupes_rolling_captions(self):
        cues = [
            CaptionCue(0.0, 1.0, "Сегодня мы смотрим"),
            CaptionCue(1.0, 2.0, "мы смотрим фильм."),
        ]
        sentences = cues_to_sentences(cues)
        self.assertEqual(sentences[0].text, "Сегодня мы смотрим фильм.")

    def test_split_complete_sentences_keeps_remainder(self):
        complete, remainder = split_complete_sentences("Первое. Второе? Незаконченное")
        self.assertEqual(complete, ["Первое.", "Второе?"])
        self.assertEqual(remainder, "Незаконченное")


if __name__ == "__main__":
    unittest.main()
