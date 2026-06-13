from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from claude_auth.playwright_cli import PlaywrightCli, write_login_browser_config


class PlaywrightCliTests(unittest.TestCase):
    def test_args_include_session(self) -> None:
        cli = PlaywrightCli("playwright-cli")

        self.assertEqual(
            cli.args("claude-auth-abc", "open", "https://claude.ai"),
            ["playwright-cli", "-s=claude-auth-abc", "open", "https://claude.ai"],
        )

    def test_env_uses_short_tmpdir(self) -> None:
        env = PlaywrightCli(tmpdir="/tmp").env()

        self.assertIsNotNone(env)
        assert env is not None
        self.assertEqual(env["TMPDIR"], "/tmp")

    def test_open_builds_headed_persistent_config_command(self) -> None:
        calls: list[dict[str, object]] = []

        class FakePlaywright(PlaywrightCli):
            def env(self) -> dict[str, str]:
                return {"TMPDIR": "/tmp"}

        cli = FakePlaywright("playwright-cli", "/tmp")

        with mock.patch("claude_auth.playwright_cli.run_checked") as run_checked:
            cli.open(
                session="claude-auth-abc",
                url="https://example.com",
                headed=True,
                persistent=True,
                config_path=Path("config.json"),
            )
            calls.append({"args": run_checked.call_args.args[0], **run_checked.call_args.kwargs})

        self.assertEqual(
            calls[0]["args"],
            [
                "playwright-cli",
                "-s=claude-auth-abc",
                "open",
                "https://example.com",
                "--persistent",
                "--headed",
                "--config=config.json",
            ],
        )
        self.assertEqual(calls[0]["env"], {"TMPDIR": "/tmp"})
        self.assertIs(calls[0]["stdout"], subprocess.DEVNULL)
        self.assertIs(calls[0]["stderr"], subprocess.DEVNULL)

    def test_verbose_open_allows_raw_command_output(self) -> None:
        cli = PlaywrightCli("playwright-cli", "/tmp", verbose=True)

        with mock.patch("claude_auth.playwright_cli.run_checked") as run_checked:
            cli.open(session="claude-auth-abc", url="https://example.com")

        self.assertNotIn("stdout", run_checked.call_args.kwargs)
        self.assertNotIn("stderr", run_checked.call_args.kwargs)

    def test_write_login_browser_config_sets_tall_viewport(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "config.json"
            write_login_browser_config(
                config_path,
                width=1280,
                height=1200,
                output_dir=Path(directory) / "pw-output",
            )

            config = json.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual(config["browser"]["contextOptions"]["viewport"], {"width": 1280, "height": 1200})
        self.assertEqual(config["browser"]["contextOptions"]["screen"], {"width": 1280, "height": 1200})
        self.assertEqual(config["browser"]["launchOptions"]["args"], ["--window-size=1280,1200"])
        self.assertEqual(config["snapshot"], {"mode": "none"})
        self.assertEqual(config["outputDir"], str(Path(directory) / "pw-output"))


if __name__ == "__main__":
    unittest.main()
