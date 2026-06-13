"""Wait for and click Claude OAuth authorization controls."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path

from .defaults import DEFAULT_AUTH_BUTTON_POLL_SECONDS, DEFAULT_AUTH_BUTTON_TIMEOUT_SECONDS
from .playwright_cli import PlaywrightCli
from .snapshots import find_first_enabled_ref_in_snapshot, find_first_ref_in_snapshot


def click_first_enabled_matching_element(
    *,
    playwright: PlaywrightCli,
    session: str,
    keyword_pattern: str,
    wait_timeout: float = DEFAULT_AUTH_BUTTON_TIMEOUT_SECONDS,
    poll_interval: float = DEFAULT_AUTH_BUTTON_POLL_SECONDS,
) -> bool:
    """Wait for a matching enabled element ref, then hover and click it."""

    snapshot_path: Path | None = None
    deadline = time.monotonic() + wait_timeout
    try:
        with tempfile.NamedTemporaryFile(
            prefix="claude-auth-snapshot-",
            suffix=".yml",
            delete=False,
        ) as snapshot_file:
            snapshot_path = Path(snapshot_file.name)

        print(
            f"Waiting up to {wait_timeout:g}s for an enabled element matching /{keyword_pattern}/...",
            file=sys.stderr,
        )
        while True:
            playwright.snapshot(session=session, output_path=snapshot_path)

            match = find_first_enabled_ref_in_snapshot(snapshot_path, keyword_pattern)
            if match:
                break

            if time.monotonic() >= deadline:
                disabled_match = find_first_ref_in_snapshot(snapshot_path, keyword_pattern)
                if disabled_match:
                    print(
                        f"Timed out waiting for matching element to become enabled: {disabled_match[1]}",
                        file=sys.stderr,
                    )
                else:
                    print(f"No element matching /{keyword_pattern}/ found.", file=sys.stderr)
                print(f"Snapshot kept at: {snapshot_path}", file=sys.stderr)
                return False

            time.sleep(min(poll_interval, max(0.0, deadline - time.monotonic())))

        ref, _line = match
        print("Authorization button is enabled; clicking.", file=sys.stderr)
        playwright.hover(session=session, ref=ref)
        playwright.click(session=session, ref=ref)
        snapshot_path.unlink(missing_ok=True)
        return True
    except subprocess.CalledProcessError as exc:
        print(f"playwright-cli command failed with exit code {exc.returncode}", file=sys.stderr)
        if snapshot_path:
            print(f"Snapshot path: {snapshot_path}", file=sys.stderr)
        return False
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        if snapshot_path:
            print(f"Snapshot path: {snapshot_path}", file=sys.stderr)
        return False
