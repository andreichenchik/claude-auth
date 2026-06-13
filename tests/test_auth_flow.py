"""Tests for high-level Claude auth flows."""

from __future__ import annotations

import io
import unittest
from unittest import mock

from claude_auth import auth_flow
from claude_auth.auth_flow import LoginConfig, OpenClaudeConfig, run_login, run_open_claude


class FakeProcess:
    """Fake Claude auth subprocess used by flow tests."""

    stdout = io.StringIO()

    def __init__(self) -> None:
        self.terminated = False
        self.killed = False

    def poll(self) -> None:
        """Pretend the process is still running."""

        return None

    def wait(self, timeout: float | None = None) -> int:
        """Return success unless a timeout should be simulated."""

        if timeout is not None and not self.terminated:
            raise auth_flow.subprocess.TimeoutExpired("fake-claude", timeout)
        return 143 if self.terminated else 0

    def terminate(self) -> None:
        """Record that graceful termination was requested."""

        self.terminated = True

    def kill(self) -> None:
        """Record that forceful termination was requested."""

        self.killed = True


class FakePlaywright:
    """Fake Playwright wrapper that records browser calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, object]]] = []

    def close_quietly(self, session: str) -> None:
        """Record a best-effort close call."""

        self.calls.append(("close_quietly", {"session": session}))

    def open(self, **kwargs: object) -> None:
        """Record an open call and its keyword arguments."""

        self.calls.append(("open", kwargs))


class AuthFlowTests(unittest.TestCase):
    """Tests for login and browser-opening orchestration."""

    def test_run_login_opens_auth_url_headed_and_stops_auth_process_on_click_failure(self) -> None:
        """A click failure stops Claude auth and closes the Playwright session."""
        fake_process = FakeProcess()
        fake_playwright = FakePlaywright()
        config = LoginConfig(
            email="user@example.com",
            claude_cli="claude",
            playwright_cli="playwright-cli",
            auth_button_poll_interval=0.01,
            auth_button_timeout=0.1,
            auth_completion_timeout=1.0,
            url_timeout=1.0,
        )

        with (
            mock.patch.object(auth_flow, "PlaywrightCli", return_value=fake_playwright),
            mock.patch.object(auth_flow, "start_auth_login", return_value=fake_process),
            mock.patch.object(auth_flow, "wait_for_auth_url", return_value="https://example.com/auth"),
            mock.patch.object(auth_flow, "click_first_enabled_matching_element", return_value=False),
        ):
            result = run_login(config)

        self.assertEqual(result, 1)
        self.assertTrue(fake_process.terminated)
        self.assertFalse(fake_process.killed)
        open_call = next(call for call in fake_playwright.calls if call[0] == "open")
        self.assertTrue(open_call[1]["headed"])
        self.assertEqual(open_call[1]["url"], "https://example.com/auth")
        self.assertEqual(fake_playwright.calls[-1][0], "close_quietly")

    def test_run_open_claude_opens_headed_persistent_session(self) -> None:
        """Opening Claude uses a headed, persistent Playwright session."""

        fake_playwright = FakePlaywright()

        with mock.patch.object(auth_flow, "PlaywrightCli", return_value=fake_playwright):
            result = run_open_claude(OpenClaudeConfig(email="user@example.com", url="https://claude.ai"))

        self.assertEqual(result, 0)
        self.assertEqual(fake_playwright.calls[0][0], "open")
        self.assertTrue(fake_playwright.calls[0][1]["headed"])
        self.assertTrue(fake_playwright.calls[0][1]["persistent"])


if __name__ == "__main__":
    unittest.main()
