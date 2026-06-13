from __future__ import annotations

import unittest
from pathlib import Path

from claude_auth.auth_button import click_first_enabled_matching_element


class FakePlaywright:
    def __init__(self) -> None:
        self.snapshots = 0
        self.hovered: list[str] = []
        self.clicked: list[str] = []
        self.sessions: list[str] = []

    def snapshot(self, *, session: str, output_path: Path) -> None:
        self.sessions.append(session)
        self.snapshots += 1
        if self.snapshots == 1:
            output_path.write_text('- button "Authorize" [disabled] [ref=b2]', encoding="utf-8")
        else:
            output_path.write_text('- button "Authorize" [ref=b2]', encoding="utf-8")

    def hover(self, *, session: str, ref: str) -> None:
        self.sessions.append(session)
        self.hovered.append(ref)

    def click(self, *, session: str, ref: str) -> None:
        self.sessions.append(session)
        self.clicked.append(ref)


class AuthButtonTests(unittest.TestCase):
    def test_waits_for_enabled_match_then_clicks(self) -> None:
        playwright = FakePlaywright()

        clicked = click_first_enabled_matching_element(
            playwright=playwright,  # type: ignore[arg-type]
            session="claude-auth-abc",
            keyword_pattern="auth|register",
            wait_timeout=1,
            poll_interval=0,
        )

        self.assertTrue(clicked)
        self.assertEqual(playwright.snapshots, 2)
        self.assertEqual(playwright.hovered, ["b2"])
        self.assertEqual(playwright.clicked, ["b2"])
        self.assertTrue(all(session == "claude-auth-abc" for session in playwright.sessions))


if __name__ == "__main__":
    unittest.main()
