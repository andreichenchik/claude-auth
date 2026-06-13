# claude-auth

Small helper script for signing Claude Code into a Claude.ai account through a stable, email-scoped `playwright-cli` browser session.

## What it does

`claude-auth.py login EMAIL`:

1. Starts `claude auth login --claudeai --email EMAIL`.
2. Suppresses Claude CLI's default browser opener with a temporary no-op `BROWSER` shim.
3. Captures the automatic OAuth callback URL that Claude tried to open.
4. Opens that URL with `playwright-cli` in a stable session derived from the email.
5. Waits for an enabled `Authorize`/`Register` control and clicks it.
6. Waits for Claude CLI to finish, then closes the temporary Playwright login browser.

`claude-auth.py open-claude EMAIL` opens `https://claude.ai` in the same stable session for that email.

## Requirements

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- `claude` CLI available on `PATH`
- `playwright-cli` available on `PATH`

## Usage

```bash
./claude-auth.py login user@example.com
```

A bare email is treated as `login`:

```bash
./claude-auth.py user@example.com
```

Open Claude in the same email-scoped browser session:

```bash
./claude-auth.py open-claude user@example.com
```

Show raw Claude and Playwright output for debugging. This can include OAuth URLs, so avoid sharing it:

```bash
./claude-auth.py login user@example.com --verbose
```

Useful login tuning flags:

```bash
./claude-auth.py login user@example.com \
  --auth-button-timeout 120 \
  --auth-button-poll-interval 0.5 \
  --login-browser-height 1400
```

## Development

Install/sync dev tools:

```bash
uv sync --group dev
```

Run checks:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile claude-auth.py claude_auth/*.py tests/*.py
uv run --group dev pylint claude_auth tests claude-auth.py
```

## Notes

- The Playwright session name is `claude-auth-<stable-email-hash>`.
- The script uses `TMPDIR=/tmp` for `playwright-cli` to avoid long Unix socket paths on macOS.
- Login is headed because Claude.ai/Cloudflare blocks the headless OAuth page.
- Default output is intentionally quiet and avoids printing OAuth URLs.
