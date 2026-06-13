#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Run Claude auth automation from the local source tree."""

from __future__ import annotations

from claude_auth.cli import main


if __name__ == "__main__":
    raise SystemExit(main())
