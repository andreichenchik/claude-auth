"""Claude CLI authentication helpers."""

from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from pathlib import Path

from .urls import extract_first_url


@dataclass(frozen=True)
class BrowserShim:
    """A no-op browser executable that records URLs Claude tries to open."""

    executable: Path
    url_file: Path


def create_browser_shim(directory: Path) -> BrowserShim:
    """Create a no-op browser executable that records Claude's auth URL."""

    url_file = directory / "browser-urls.txt"
    shim_path = directory / "browser-shim"
    shim_path.write_text(
        "#!/bin/sh\n"
        "{\n"
        "  for arg in \"$@\"; do\n"
        "    printf '%s\\n' \"$arg\"\n"
        "  done\n"
        "} >> \"$CLAUDE_AUTH_BROWSER_URL_FILE\"\n"
        "exit 0\n",
        encoding="utf-8",
    )
    shim_path.chmod(0o700)
    return BrowserShim(executable=shim_path, url_file=url_file)


def auth_env(shim: BrowserShim) -> dict[str, str]:
    """Return an environment that suppresses Claude's browser opener."""

    env = os.environ.copy()
    env["BROWSER"] = str(shim.executable)
    env["CLAUDE_AUTH_BROWSER_URL_FILE"] = str(shim.url_file)
    return env


def read_captured_browser_url(url_file: Path) -> str | None:
    """Return the first URL recorded by the Claude browser shim."""

    if not url_file.exists():
        return None
    return extract_first_url(url_file.read_text(encoding="utf-8", errors="replace"))


def start_auth_login(
    *,
    executable: str,
    email: str,
    env: dict[str, str],
) -> subprocess.Popen[str]:
    """Start `claude auth login` for an email address."""

    return subprocess.Popen(
        [executable, "auth", "login", "--claudeai", "--email", email],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        stdin=subprocess.DEVNULL,
        text=True,
        bufsize=1,
        env=env,
    )


def start_output_reader(
    process: subprocess.Popen[str],
    *,
    echo: bool = False,
) -> tuple[queue.Queue[str | None], threading.Thread]:
    """Consume process output and report the first complete URL seen."""

    urls: queue.Queue[str | None] = queue.Queue(maxsize=1)

    def read_output() -> None:
        sent_url = False
        recent = ""
        assert process.stdout is not None
        while True:
            chunk = process.stdout.read(1)
            if not chunk:
                break
            if echo:
                sys.stdout.write(chunk)
                sys.stdout.flush()

            if sent_url:
                continue
            recent = (recent + chunk)[-8000:]
            if not chunk.isspace() and chunk not in "<>'\"`),];}":
                continue
            url = extract_first_url(recent)
            if url:
                sent_url = True
                urls.put(url)

        if not sent_url:
            urls.put(extract_first_url(recent))

    thread = threading.Thread(target=read_output, name="claude-auth-output", daemon=True)
    thread.start()
    return urls, thread


def wait_for_auth_url(
    process: subprocess.Popen[str],
    *,
    timeout_seconds: float,
    browser_url_file: Path | None = None,
    verbose: bool = False,
) -> str:
    """Wait until Claude opens or prints an auth URL."""

    urls, _thread = start_output_reader(process, echo=verbose)
    if browser_url_file:
        deadline = time.monotonic() + timeout_seconds
        while time.monotonic() < deadline:
            captured_url = read_captured_browser_url(browser_url_file)
            if captured_url:
                return captured_url

            try:
                url = urls.get_nowait()
            except queue.Empty:
                url = None
            if url is None and process.poll() is not None:
                raise RuntimeError(
                    f"Claude auth exited with code {process.returncode} before opening an auth URL."
                )

            time.sleep(min(0.05, max(0.0, deadline - time.monotonic())))

        raise TimeoutError(
            f"Timed out after {timeout_seconds:g}s waiting for claude auth login to open a URL."
        )

    try:
        url = urls.get(timeout=timeout_seconds)
    except queue.Empty as exc:
        raise TimeoutError(
            f"Timed out after {timeout_seconds:g}s waiting for claude auth login to print a URL."
        ) from exc

    if url is None:
        return_code = process.poll()
        if return_code is None:
            raise RuntimeError("Claude auth output ended before a URL was printed.")
        raise RuntimeError(f"Claude auth exited with code {return_code} before printing a URL.")
    return url
