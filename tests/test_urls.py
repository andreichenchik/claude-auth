"""Tests for URL extraction helpers."""

from __future__ import annotations

import unittest

from claude_auth.urls import extract_first_url


class UrlTests(unittest.TestCase):
    """Tests for parsing URLs from command output."""

    def test_extract_first_url_strips_ansi_and_trailing_punctuation(self) -> None:
        """ANSI sequences and trailing punctuation are excluded from URLs."""
        output = "open \x1b[32mhttps://example.com/auth?code=abc\x1b[0m)."

        self.assertEqual(extract_first_url(output), "https://example.com/auth?code=abc")


if __name__ == "__main__":
    unittest.main()
