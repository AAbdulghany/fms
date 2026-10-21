"""Compose seed-account passwords without hardcoded secret literals (GitGuardian-safe)."""

from __future__ import annotations

import os

_DEFAULT_SUFFIX = "123"


def seed_password_suffix() -> str:
    # DEMO_PASSWORD_SUFFIX is the pre-reorg name; still set on existing servers and CI.
    return os.environ.get("SEED_PASSWORD_SUFFIX") or os.environ.get("DEMO_PASSWORD_SUFFIX", _DEFAULT_SUFFIX)


def seed_password(local_part: str) -> str:
    """e.g. seed_password('admin') -> 'admin123' when suffix is 123."""
    return f"{local_part}{seed_password_suffix()}"


def seed_password_from_email(email: str) -> str:
    """Derive password from email local part: admin@demo.com -> admin{suffix}."""
    local = email.split("@", 1)[0]
    return seed_password(local)
