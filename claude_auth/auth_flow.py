"""High-level Claude authentication flows."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .auth_button import click_first_enabled_matching_element
from .claude_cli import auth_env, create_browser_shim, start_auth_login, wait_for_auth_url
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
from .playwright_cli import PlaywrightCli, write_login_browser_config
from .processes import terminate_process
from .session import session_name_for_email


@dataclass(frozen=True)
class LoginConfig:
    """Settings for one `claude auth login` automation run."""

    email: str
    claude_cli: str = "claude"
    playwright_cli: str = "playwright-cli"
    playwright_tmpdir: str | None = DEFAULT_PLAYWRIGHT_TMPDIR
    session_prefix: str = DEFAULT_SESSION_PREFIX
    url_timeout: float = DEFAULT_URL_TIMEOUT_SECONDS
    click_pattern: str = "auth|register"
    auth_button_timeout: float = DEFAULT_AUTH_BUTTON_TIMEOUT_SECONDS
    auth_button_poll_interval: float = DEFAULT_AUTH_BUTTON_POLL_SECONDS
    auth_completion_timeout: float = DEFAULT_AUTH_COMPLETION_TIMEOUT_SECONDS
    login_browser_width: int = DEFAULT_LOGIN_BROWSER_WIDTH
    login_browser_height: int = DEFAULT_LOGIN_BROWSER_HEIGHT
    verbose: bool = False


@dataclass(frozen=True)
class OpenClaudeConfig:
    """Settings for opening Claude in an email-scoped browser session."""

    email: str
    url: str = DEFAULT_CLAUDE_URL
    playwright_cli: str = "playwright-cli"
    playwright_tmpdir: str | None = DEFAULT_PLAYWRIGHT_TMPDIR
    session_prefix: str = DEFAULT_SESSION_PREFIX
    verbose: bool = False


def run_login(config: LoginConfig) -> int:
    """Run Claude auth login and complete it through the matching browser session."""

    session = session_name_for_email(config.email, config.session_prefix)
    playwright = PlaywrightCli(config.playwright_cli, config.playwright_tmpdir, config.verbose)
    print(f"Using Playwright session: {session}", file=sys.stderr)

    with tempfile.TemporaryDirectory(prefix="claude-auth-browser-") as directory:
        temp_dir = Path(directory)
        browser_shim = create_browser_shim(temp_dir)
        login_config_path = temp_dir / "playwright-login-config.json"
        write_login_browser_config(
            login_config_path,
            width=config.login_browser_width,
            height=config.login_browser_height,
            output_dir=temp_dir / "playwright-output",
        )

        try:
            process = start_auth_login(
                executable=config.claude_cli,
                email=config.email,
                env=auth_env(browser_shim),
            )
        except FileNotFoundError:
            print(f"Command not found: {config.claude_cli}", file=sys.stderr)
            return 127

        try:
            url = wait_for_auth_url(
                process,
                timeout_seconds=config.url_timeout,
                browser_url_file=browser_shim.url_file,
                verbose=config.verbose,
            )
            print(f"\nOpening auth URL in headed Playwright session: {session}", file=sys.stderr)
            playwright.close_quietly(session)
            playwright.open(
                session=session,
                url=url,
                headed=True,
                persistent=True,
                config_path=login_config_path,
            )

            clicked = click_first_enabled_matching_element(
                playwright=playwright,
                session=session,
                keyword_pattern=config.click_pattern,
                wait_timeout=config.auth_button_timeout,
                poll_interval=config.auth_button_poll_interval,
            )
            if not clicked:
                terminate_process(process)
                return 1

            try:
                return_code = process.wait(timeout=config.auth_completion_timeout)
                if return_code == 0 and not config.verbose:
                    print("Login successful.", file=sys.stderr)
                return return_code
            except subprocess.TimeoutExpired:
                print(
                    f"Timed out after {config.auth_completion_timeout:g}s waiting for claude auth login to finish.",
                    file=sys.stderr,
                )
                terminate_process(process)
                return 1
        except (RuntimeError, TimeoutError, subprocess.CalledProcessError) as exc:
            print(str(exc), file=sys.stderr)
            terminate_process(process)
            return 1
        except KeyboardInterrupt:
            terminate_process(process)
            raise
        finally:
            playwright.close_quietly(session)


def run_open_claude(config: OpenClaudeConfig) -> int:
    """Open Claude in the stable Playwright session for the provided email."""

    session = session_name_for_email(config.email, config.session_prefix)
    playwright = PlaywrightCli(config.playwright_cli, config.playwright_tmpdir, config.verbose)
    print(f"Using Playwright session: {session}", file=sys.stderr)
    try:
        playwright.open(session=session, url=config.url, headed=True, persistent=True)
    except (RuntimeError, subprocess.CalledProcessError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0
