"""Stable Playwright session naming."""

from __future__ import annotations

import hashlib

from .defaults import DEFAULT_SESSION_PREFIX


def session_name_for_email(email: str, prefix: str = DEFAULT_SESSION_PREFIX) -> str:
    """Return the stable Playwright session name for an email address."""

    normalized_email = email.strip().lower()
    digest = hashlib.sha256(normalized_email.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}-{digest}"
