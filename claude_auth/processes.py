"""Small subprocess helpers shared by CLI integrations."""

from __future__ import annotations

import subprocess
from collections.abc import Sequence


def run_checked(args: Sequence[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    """Run a command and raise a clear error if the executable is missing."""

    try:
        return subprocess.run(args, check=True, text=True, **kwargs)
    except FileNotFoundError as exc:
        raise RuntimeError(f"Command not found: {args[0]}") from exc


def terminate_process(process: subprocess.Popen[str]) -> None:
    """Stop a child process without leaving it running in the background."""

    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
