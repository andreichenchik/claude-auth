from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from claude_auth.snapshots import find_first_enabled_ref_in_snapshot, find_first_ref_in_snapshot


class SnapshotTests(unittest.TestCase):
    def test_find_first_ref_in_snapshot_matches_auth_or_register_line(self) -> None:
        snapshot = """
- button "Continue" [ref=a1]
- button "Authorize Claude" [ref=b2]
- link "Register" [ref=c3]
""".strip()
        with tempfile.TemporaryDirectory() as directory:
            snapshot_path = Path(directory) / "snapshot.yml"
            snapshot_path.write_text(snapshot, encoding="utf-8")

            match = find_first_ref_in_snapshot(snapshot_path, "auth|register")

        self.assertEqual(match, ("b2", '- button "Authorize Claude" [ref=b2]'))

    def test_find_first_enabled_ref_waits_when_first_match_is_disabled(self) -> None:
        snapshot = """
- button "Authorize Claude" [disabled] [ref=b2]
- link "Register" [ref=c3]
""".strip()
        with tempfile.TemporaryDirectory() as directory:
            snapshot_path = Path(directory) / "snapshot.yml"
            snapshot_path.write_text(snapshot, encoding="utf-8")

            match = find_first_enabled_ref_in_snapshot(snapshot_path, "auth|register")

        self.assertIsNone(match)

    def test_find_first_enabled_ref_returns_first_match_when_enabled(self) -> None:
        snapshot = '- button "Authorize Claude" [ref=b2]'
        with tempfile.TemporaryDirectory() as directory:
            snapshot_path = Path(directory) / "snapshot.yml"
            snapshot_path.write_text(snapshot, encoding="utf-8")

            match = find_first_enabled_ref_in_snapshot(snapshot_path, "auth|register")

        self.assertEqual(match, ("b2", '- button "Authorize Claude" [ref=b2]'))


if __name__ == "__main__":
    unittest.main()
