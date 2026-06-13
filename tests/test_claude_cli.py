from __future__ import annotations

import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path

from claude_auth.claude_cli import auth_env, create_browser_shim, read_captured_browser_url, start_output_reader


class ClaudeCliTests(unittest.TestCase):
    def test_browser_shim_records_opened_auth_url(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            shim = create_browser_shim(Path(directory))
            env = auth_env(shim)

            self.assertEqual(env["BROWSER"], str(shim.executable))
            self.assertEqual(env["CLAUDE_AUTH_BROWSER_URL_FILE"], str(shim.url_file))
            subprocess_result = subprocess.run(
                [str(shim.executable), "https://example.com/callback?code=abc"],
                check=True,
                env=env,
            )

            self.assertEqual(subprocess_result.returncode, 0)
            self.assertEqual(
                read_captured_browser_url(shim.url_file),
                "https://example.com/callback?code=abc",
            )

    def test_output_reader_returns_complete_url_after_delimiter_without_echoing(self) -> None:
        class FakeProcess:
            stdout = io.StringIO("open https://example.com/auth?code=abc123\n")

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            urls, thread = start_output_reader(FakeProcess())
            self.assertEqual(urls.get(timeout=1), "https://example.com/auth?code=abc123")
            thread.join(timeout=1)

        self.assertEqual(output.getvalue(), "")

    def test_output_reader_echoes_when_verbose(self) -> None:
        class FakeProcess:
            stdout = io.StringIO("open https://example.com/auth?code=abc123\n")

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            urls, thread = start_output_reader(FakeProcess(), echo=True)
            self.assertEqual(urls.get(timeout=1), "https://example.com/auth?code=abc123")
            thread.join(timeout=1)

        self.assertIn("https://example.com/auth?code=abc123", output.getvalue())


if __name__ == "__main__":
    unittest.main()
