"""playwright-cli command wrapper."""

from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .defaults import DEFAULT_PLAYWRIGHT_TMPDIR
from .processes import run_checked


def write_login_browser_config(
    path: Path,
    *,
    width: int,
    height: int,
    output_dir: Path | None = None,
) -> None:
    """Write Playwright settings for a tall, low-noise login browser window."""

    config = {
        "browser": {
            "contextOptions": {
                "screen": {"width": width, "height": height},
                "viewport": {"width": width, "height": height},
            },
            "launchOptions": {
                "args": [f"--window-size={width},{height}"],
            },
        },
        "snapshot": {"mode": "none"},
    }
    if output_dir:
        config["outputDir"] = str(output_dir)
    path.write_text(json.dumps(config, indent=2), encoding="utf-8")


@dataclass(frozen=True)
class PlaywrightCli:
    """Run playwright-cli commands against a named browser session."""

    executable: str = "playwright-cli"
    tmpdir: str | None = DEFAULT_PLAYWRIGHT_TMPDIR
    verbose: bool = False

    def args(self, session: str, *args: str) -> list[str]:
        """Build a playwright-cli command targeting the requested session."""

        return [self.executable, f"-s={session}", *args]

    def env(self) -> dict[str, str] | None:
        """Return an environment that keeps Playwright daemon socket paths short."""

        if not self.tmpdir:
            return None
        env = os.environ.copy()
        env["TMPDIR"] = self.tmpdir
        return env

    def run(self, action: str, args: list[str], **kwargs: object) -> None:
        """Run playwright-cli while keeping OAuth URLs out of default logs."""

        if not self.verbose:
            kwargs.setdefault("stdout", subprocess.DEVNULL)
            kwargs.setdefault("stderr", subprocess.DEVNULL)
        try:
            run_checked(args, env=self.env(), **kwargs)
        except subprocess.CalledProcessError as exc:
            raise RuntimeError(f"{self.executable} {action} failed with exit code {exc.returncode}.") from exc

    def open(
        self,
        *,
        session: str,
        url: str,
        headed: bool = True,
        persistent: bool = True,
        config_path: Path | None = None,
    ) -> None:
        """Open a URL in the requested Playwright browser session."""

        args = self.args(session, "open", url)
        if persistent:
            args.append("--persistent")
        if headed:
            args.append("--headed")
        if config_path:
            args.append(f"--config={config_path}")
        self.run("open", args)

    def close(self, session: str) -> None:
        """Close the requested Playwright browser session."""

        self.run("close", self.args(session, "close"))

    def close_quietly(self, session: str) -> None:
        """Best-effort close for cleanup paths where auth result is more important."""

        try:
            run_checked(
                self.args(session, "close"),
                env=self.env(),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except (RuntimeError, subprocess.CalledProcessError):
            pass

    def snapshot(self, *, session: str, output_path: Path) -> None:
        """Capture a page snapshot to a file for element ref lookup."""

        self.run(
            "snapshot",
            self.args(session, "snapshot", f"--filename={output_path}"),
            stdout=subprocess.DEVNULL,
        )

    def hover(self, *, session: str, ref: str) -> None:
        """Hover the element identified by a snapshot ref."""

        self.run("hover", self.args(session, "hover", ref))

    def click(self, *, session: str, ref: str) -> None:
        """Click the element identified by a snapshot ref."""

        self.run("click", self.args(session, "click", ref))
