import unittest

from yt_anki.transcript import cues_to_sentences, parse_timestamp, parse_vtt


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


if __name__ == "__main__":
    unittest.main()
