# claude-auth agent instructions

- Keep the runtime script dependency-free unless a dependency is explicitly justified.
- Keep `claude-auth.py` as the thin uv script entrypoint; put implementation in `claude_auth/` modules.
- Avoid printing OAuth URLs, tokens, emails from real runs, or other auth-sensitive values in normal output.
- Use `--verbose` only for debugging raw Claude/playwright-cli output.
- Keep Playwright login artifacts out of the project directory; temporary output should be cleaned up automatically.
- After finishing code changes, run:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile claude-auth.py claude_auth/*.py tests/*.py
uv run --group dev pylint claude_auth tests claude-auth.py
```

- If a check cannot be run, mention exactly why and what remains unverified.
