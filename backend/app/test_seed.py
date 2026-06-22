"""Backward-compatible shim — use app.cli.test_seed."""

from app.cli.test_seed import seed_data

__all__ = ["seed_data"]
