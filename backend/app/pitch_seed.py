"""Backward-compatible shim — use app.cli.pitch_seed."""

from app.cli.pitch_seed import SEED_USERS, seed_pitch_demo

__all__ = ["SEED_USERS", "seed_pitch_demo"]
