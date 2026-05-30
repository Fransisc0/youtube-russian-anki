import unittest

from yt_anki.transcript import (
    CaptionCue,
    append_without_overlap,
    collapse_repeated_lines,
    cues_to_sentences,
    parse_json3,
    parse_timestamp,
    parse_vtt,
    split_complete_sentences,
)


class TranscriptTests(unittest.TestCase):
    def test_parse_timestamp(self):
        self.assertEqual(parse_timestamp("00:01:02.500"), 62.5)

    def test_parse_vtt_and_group_sentences(self):
        vtt = """WEBVTT

00:00:01.000 --> 00:00:02.000
\u041f\u0440\u0438\u0432\u0435\u0442

00:00:02.000 --> 00:00:03.500
\u043a\u0430\u043a \u0434\u0435\u043b\u0430?

00:00:04.000 --> 00:00:05.000
\u0425\u043e\u0440\u043e\u0448\u043e.
"""
        cues = parse_vtt(vtt)
        self.assertEqual(len(cues), 3)
        sentences = cues_to_sentences(cues)
        self.assertEqual(len(sentences), 2)
        self.assertEqual(sentences[0].text, "\u041f\u0440\u0438\u0432\u0435\u0442 \u043a\u0430\u043a \u0434\u0435\u043b\u0430?")
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

    def test_parse_json3_uses_segment_offsets(self):
        contents = """{
          "events": [
            {"tStartMs": 1000, "dDurationMs": 1500, "segs": [
              {"utf8": "\u041f\u0440\u0438\u0432\u0435\u0442"},
              {"utf8": " \u043c\u0438\u0440.", "tOffsetMs": 500}
            ]},
            {"tStartMs": 2500, "dDurationMs": 1000, "segs": [{"utf8": "\\n"}]}
          ]
        }"""
        cues = parse_json3(contents)
        self.assertEqual(len(cues), 2)
        self.assertEqual(cues[0].text, "\u041f\u0440\u0438\u0432\u0435\u0442")
        self.assertEqual(cues[1].text, "\u043c\u0438\u0440.")
        self.assertEqual(cues[0].start, 1.0)
        self.assertEqual(cues[0].end, 1.5)
        self.assertEqual(cues[1].start, 1.5)
        self.assertEqual(cues[1].end, 2.5)

    def test_json3_sentence_timing_uses_segment_offsets(self):
        contents = """{
          "events": [
            {"tStartMs": 1000, "dDurationMs": 2000, "segs": [
              {"utf8": "One."},
              {"utf8": " Two.", "tOffsetMs": 500}
            ]},
            {"tStartMs": 1800, "dDurationMs": 200, "segs": [{"utf8": "\\n"}]}
          ]
        }"""
        sentences = cues_to_sentences(parse_json3(contents))
        self.assertEqual([sentence.text for sentence in sentences], ["One.", "Two."])
        self.assertEqual(sentences[0].start, 1.0)
        self.assertEqual(sentences[0].end, 1.5)
        self.assertEqual(sentences[1].start, 1.5)
        self.assertEqual(sentences[1].end, 1.8)

    def test_clean_caption_text_removes_speaker_marker(self):
        self.assertEqual(collapse_repeated_lines([">> \u041f\u0440\u0438\u0432\u0435\u0442."]), "\u041f\u0440\u0438\u0432\u0435\u0442.")

    def test_collapse_youtube_rolling_caption_lines(self):
        text = collapse_repeated_lines(
            [
                "\u0421\u0435\u0433\u043e\u0434\u043d\u044f \u043c\u044b \u0441\u043c\u043e\u0442\u0440\u0438\u043c",
                "\u0421\u0435\u0433\u043e\u0434\u043d\u044f \u043c\u044b \u0441\u043c\u043e\u0442\u0440\u0438\u043c \u0444\u0438\u043b\u044c\u043c.",
            ]
        )
        self.assertEqual(text, "\u0421\u0435\u0433\u043e\u0434\u043d\u044f \u043c\u044b \u0441\u043c\u043e\u0442\u0440\u0438\u043c \u0444\u0438\u043b\u044c\u043c.")

    def test_append_without_overlap(self):
        self.assertEqual(
            append_without_overlap(
                "\u0421\u0435\u0433\u043e\u0434\u043d\u044f \u043c\u044b \u0441\u043c\u043e\u0442\u0440\u0438\u043c",
                "\u043c\u044b \u0441\u043c\u043e\u0442\u0440\u0438\u043c \u0444\u0438\u043b\u044c\u043c.",
            ),
            "\u0421\u0435\u0433\u043e\u0434\u043d\u044f \u043c\u044b \u0441\u043c\u043e\u0442\u0440\u0438\u043c \u0444\u0438\u043b\u044c\u043c.",
        )

    def test_cues_to_sentences_dedupes_rolling_captions(self):
        cues = [
            CaptionCue(0.0, 1.0, "\u0421\u0435\u0433\u043e\u0434\u043d\u044f \u043c\u044b \u0441\u043c\u043e\u0442\u0440\u0438\u043c"),
            CaptionCue(1.0, 2.0, "\u043c\u044b \u0441\u043c\u043e\u0442\u0440\u0438\u043c \u0444\u0438\u043b\u044c\u043c."),
        ]
        sentences = cues_to_sentences(cues)
        self.assertEqual(sentences[0].text, "\u0421\u0435\u0433\u043e\u0434\u043d\u044f \u043c\u044b \u0441\u043c\u043e\u0442\u0440\u0438\u043c \u0444\u0438\u043b\u044c\u043c.")

    def test_split_complete_sentences_keeps_remainder(self):
        complete, remainder = split_complete_sentences("\u041f\u0435\u0440\u0432\u043e\u0435. \u0412\u0442\u043e\u0440\u043e\u0435? \u041d\u0435\u0437\u0430\u043a\u043e\u043d\u0447\u0435\u043d\u043d\u043e\u0435")
        self.assertEqual(complete, ["\u041f\u0435\u0440\u0432\u043e\u0435.", "\u0412\u0442\u043e\u0440\u043e\u0435?"])
        self.assertEqual(remainder, "\u041d\u0435\u0437\u0430\u043a\u043e\u043d\u0447\u0435\u043d\u043d\u043e\u0435")


if __name__ == "__main__":
    unittest.main()
