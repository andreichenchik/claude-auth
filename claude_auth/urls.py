"""URL parsing helpers for CLI output."""

from __future__ import annotations

import re

ANSI_RE = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
URL_RE = re.compile(r"https?://[^\s<>'\"`]+")


def strip_ansi(text: str) -> str:
    """Remove terminal color/control sequences before parsing command output."""

    return ANSI_RE.sub("", text)


def extract_first_url(text: str) -> str | None:
    """Return the first HTTP(S) URL from CLI output, if one is present."""

    match = URL_RE.search(strip_ansi(text))
    if not match:
        return None
    return match.group(0).rstrip(".),];}")
