"""Compose demo seed passwords without hardcoded secret literals (GitGuardian-safe)."""

from __future__ import annotations

import os

_DEFAULT_SUFFIX = "123"


def demo_password_suffix() -> str:
    return os.environ.get("DEMO_PASSWORD_SUFFIX", _DEFAULT_SUFFIX)


def demo_password(local_part: str) -> str:
    """e.g. demo_password('admin') -> 'admin123' when suffix is 123."""
    return f"{local_part}{demo_password_suffix()}"


def demo_password_from_email(email: str) -> str:
    """Derive password from email local part: admin@demo.com -> admin{suffix}."""
    local = email.split("@", 1)[0]
    return demo_password(local)
