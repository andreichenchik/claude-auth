"""Command-line interface for the Claude auth helper."""

from __future__ import annotations

import argparse
import os
import sys
from collections.abc import Sequence

from .auth_flow import LoginConfig, OpenClaudeConfig, run_login, run_open_claude
from .defaults import (
    DEFAULT_AUTH_BUTTON_POLL_SECONDS,
    DEFAULT_AUTH_BUTTON_TIMEOUT_SECONDS,
    DEFAULT_AUTH_COMPLETION_TIMEOUT_SECONDS,
    DEFAULT_CLAUDE_URL,
    DEFAULT_LOGIN_BROWSER_HEIGHT,
    DEFAULT_LOGIN_BROWSER_WIDTH,
    DEFAULT_PLAYWRIGHT_TMPDIR,
    DEFAULT_SESSION_PREFIX,
    DEFAULT_URL_TIMEOUT_SECONDS,
)


def add_verbose_argument(parser: argparse.ArgumentParser) -> None:
    """Add the shared raw-output debug flag to a parser."""

    parser.add_argument(
        "--verbose",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Show raw Claude and playwright-cli output, including auth URLs.",
    )


def run_login_command(args: argparse.Namespace) -> int:
    """Convert parsed arguments into a login automation run."""

    return run_login(
        LoginConfig(
            email=args.email,
            claude_cli=args.claude_cli,
            playwright_cli=args.playwright_cli,
            playwright_tmpdir=args.playwright_tmpdir,
            session_prefix=args.session_prefix,
            url_timeout=args.url_timeout,
            click_pattern=args.click_pattern,
            auth_button_timeout=args.auth_button_timeout,
            auth_button_poll_interval=args.auth_button_poll_interval,
            auth_completion_timeout=args.auth_completion_timeout,
            login_browser_width=args.login_browser_width,
            login_browser_height=args.login_browser_height,
            verbose=args.verbose,
        )
    )


def run_open_claude_command(args: argparse.Namespace) -> int:
    """Convert parsed arguments into an open-Claude browser run."""

    return run_open_claude(
        OpenClaudeConfig(
            email=args.email,
            url=args.url,
            playwright_cli=args.playwright_cli,
            playwright_tmpdir=args.playwright_tmpdir,
            session_prefix=args.session_prefix,
            verbose=args.verbose,
        )
    )


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser for the auth helper."""

    parser = argparse.ArgumentParser(
        description="Open Claude auth in stable email-scoped playwright-cli sessions.",
    )
    parser.add_argument(
        "--claude-cli",
        default=os.environ.get("CLAUDE_CLI", "claude"),
        help="Claude CLI executable to run. Defaults to CLAUDE_CLI or 'claude'.",
    )
    parser.add_argument(
        "--playwright-cli",
        default=os.environ.get("PLAYWRIGHT_CLI", "playwright-cli"),
        help="playwright-cli executable to run. Defaults to PLAYWRIGHT_CLI or 'playwright-cli'.",
    )
    parser.add_argument(
        "--playwright-tmpdir",
        default=os.environ.get("PLAYWRIGHT_TMPDIR", DEFAULT_PLAYWRIGHT_TMPDIR),
        help=(
            "Temp directory for playwright-cli daemon sockets. "
            f"Defaults to PLAYWRIGHT_TMPDIR or {DEFAULT_PLAYWRIGHT_TMPDIR}."
        ),
    )
    parser.add_argument(
        "--session-prefix",
        default=DEFAULT_SESSION_PREFIX,
        help=f"Prefix for email-derived Playwright sessions. Default: {DEFAULT_SESSION_PREFIX}.",
    )
    parser.set_defaults(verbose=False)
    add_verbose_argument(parser)

    subparsers = parser.add_subparsers(dest="command", required=True)

    login_parser = subparsers.add_parser(
        "login",
        help="Run claude auth login and click the auth URL.",
    )
    login_parser.add_argument("email", help="Email address for Claude auth and session selection.")
    add_verbose_argument(login_parser)

    timing_group = login_parser.add_argument_group("timing")
    timing_group.add_argument(
        "--url-timeout",
        type=float,
        default=DEFAULT_URL_TIMEOUT_SECONDS,
        help=f"Seconds to wait for claude auth login to open a URL. Default: {DEFAULT_URL_TIMEOUT_SECONDS:g}.",
    )
    timing_group.add_argument(
        "--auth-button-timeout",
        type=float,
        default=DEFAULT_AUTH_BUTTON_TIMEOUT_SECONDS,
        help=(
            "Seconds to wait for the first matching auth/register element to become enabled. "
            f"Default: {DEFAULT_AUTH_BUTTON_TIMEOUT_SECONDS:g}."
        ),
    )
    timing_group.add_argument(
        "--auth-button-poll-interval",
        type=float,
        default=DEFAULT_AUTH_BUTTON_POLL_SECONDS,
        help=(
            "Seconds between auth/register element snapshots while waiting. "
            f"Default: {DEFAULT_AUTH_BUTTON_POLL_SECONDS:g}."
        ),
    )
    timing_group.add_argument(
        "--auth-completion-timeout",
        type=float,
        default=DEFAULT_AUTH_COMPLETION_TIMEOUT_SECONDS,
        help=(
            "Seconds to wait for claude auth login to finish after clicking authorize. "
            f"Default: {DEFAULT_AUTH_COMPLETION_TIMEOUT_SECONDS:g}."
        ),
    )

    browser_group = login_parser.add_argument_group("login browser")
    browser_group.add_argument(
        "--click-pattern",
        default="auth|register",
        help="Case-insensitive regex for selecting the element to click from the snapshot. Default: auth|register.",
    )
    browser_group.add_argument(
        "--login-browser-width",
        type=int,
        default=DEFAULT_LOGIN_BROWSER_WIDTH,
        help=f"Width for the headed login browser. Default: {DEFAULT_LOGIN_BROWSER_WIDTH}.",
    )
    browser_group.add_argument(
        "--login-browser-height",
        type=int,
        default=DEFAULT_LOGIN_BROWSER_HEIGHT,
        help=f"Height for the headed login browser. Default: {DEFAULT_LOGIN_BROWSER_HEIGHT}.",
    )
    login_parser.set_defaults(func=run_login_command)

    open_parser = subparsers.add_parser(
        "open-claude",
        help="Open claude.ai in the stable session for an email.",
    )
    open_parser.add_argument("email", help="Email address used to select the Playwright session.")
    add_verbose_argument(open_parser)
    open_parser.add_argument(
        "--url",
        default=DEFAULT_CLAUDE_URL,
        help=f"URL to open in that session. Default: {DEFAULT_CLAUDE_URL}.",
    )
    open_parser.set_defaults(func=run_open_claude_command)

    return parser


def normalize_argv(argv: Sequence[str]) -> list[str]:
    """Treat a bare email argument as `login EMAIL` for quick command-line use."""

    if not argv:
        return list(argv)
    first = argv[0]
    commands = {"login", "open-claude"}
    if first in commands or first.startswith("-"):
        return list(argv)
    return ["login", *argv]


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line entry point."""

    parser = build_parser()
    args = parser.parse_args(normalize_argv(sys.argv[1:] if argv is None else argv))
    return args.func(args)
