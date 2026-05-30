import unittest

from yt_anki.security import is_allowed_youtube_url


class SecurityTests(unittest.TestCase):
    def test_allows_youtube_watch_url(self):
        self.assertTrue(is_allowed_youtube_url("https://www.youtube.com/watch?v=abc123"))

    def test_allows_short_youtube_url(self):
        self.assertTrue(is_allowed_youtube_url("https://youtu.be/abc123"))

    def test_rejects_non_youtube_url(self):
        self.assertFalse(is_allowed_youtube_url("https://example.com/watch?v=abc123"))

    def test_rejects_youtube_without_video_id(self):
        self.assertFalse(is_allowed_youtube_url("https://www.youtube.com/watch"))


if __name__ == "__main__":
    unittest.main()
