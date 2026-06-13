"""Helpers for reading playwright-cli accessibility snapshots."""

from __future__ import annotations

import re
from pathlib import Path

REF_RE = re.compile(r"\bref=([A-Za-z0-9_-]+)")
DISABLED_RE = re.compile(r"(?:\bdisabled\b|aria-disabled\s*=\s*true)", re.IGNORECASE)


def is_disabled_snapshot_line(line: str) -> bool:
    """Return whether a snapshot line describes a disabled element."""

    return bool(DISABLED_RE.search(line))


def find_first_ref_in_snapshot(snapshot_path: Path, keyword_pattern: str) -> tuple[str, str] | None:
    """Find the first element ref on a snapshot line matching the keyword pattern."""

    keywords = re.compile(keyword_pattern, re.IGNORECASE)
    for line in snapshot_path.read_text(encoding="utf-8").splitlines():
        if not keywords.search(line):
            continue
        ref_match = REF_RE.search(line)
        if ref_match:
            return ref_match.group(1), line.strip()
    return None


def find_first_enabled_ref_in_snapshot(
    snapshot_path: Path,
    keyword_pattern: str,
) -> tuple[str, str] | None:
    """Return the first matching element ref only when it is enabled."""

    first_match = find_first_ref_in_snapshot(snapshot_path, keyword_pattern)
    if not first_match:
        return None
    _ref, line = first_match
    if is_disabled_snapshot_line(line):
        return None
    return first_match
