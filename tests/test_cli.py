"""Tests for the command-line parser and entry point."""

from __future__ import annotations

import unittest
from unittest import mock

from claude_auth.cli import build_parser, main, normalize_argv


class CliTests(unittest.TestCase):
    """Tests for CLI argument normalization and dispatch."""

    def test_normalize_argv_treats_bare_email_as_login(self) -> None:
        """A bare email is treated as the login subcommand."""
        self.assertEqual(normalize_argv(["user@example.com"]), ["login", "user@example.com"])
        self.assertEqual(normalize_argv(["open-claude", "user@example.com"]), ["open-claude", "user@example.com"])

    def test_login_parser_accepts_grouped_options(self) -> None:
        """Login-specific option groups parse their configured values."""

        parser = build_parser()

        args = parser.parse_args(
            [
                "login",
                "user@example.com",
                "--auth-button-timeout",
                "2",
                "--login-browser-height",
                "1400",
            ]
        )

        self.assertEqual(args.email, "user@example.com")
        self.assertEqual(args.auth_button_timeout, 2)
        self.assertEqual(args.login_browser_height, 1400)

    def test_verbose_is_accepted_before_and_after_subcommand(self) -> None:
        """The verbose flag works before or after the subcommand."""

        parser = build_parser()

        before = parser.parse_args(["--verbose", "login", "user@example.com"])
        after = parser.parse_args(["login", "user@example.com", "--verbose"])

        self.assertTrue(before.verbose)
        self.assertTrue(after.verbose)

    def test_main_dispatches_login(self) -> None:
        """The entry point dispatches a bare email to login."""

        with mock.patch("claude_auth.cli.run_login", return_value=0) as run_login:
            result = main(["user@example.com"])

        self.assertEqual(result, 0)
        self.assertEqual(run_login.call_args.args[0].email, "user@example.com")
        self.assertFalse(run_login.call_args.args[0].verbose)

    def test_main_dispatches_verbose_login(self) -> None:
        """The entry point carries subcommand verbose through to login."""

        with mock.patch("claude_auth.cli.run_login", return_value=0) as run_login:
            result = main(["login", "user@example.com", "--verbose"])

        self.assertEqual(result, 0)
        self.assertTrue(run_login.call_args.args[0].verbose)


if __name__ == "__main__":
    unittest.main()
