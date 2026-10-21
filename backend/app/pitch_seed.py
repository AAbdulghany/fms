"""Backward-compatible shim — use app.cli.pilot_seed."""

from app.cli.pilot_seed import SEED_USERS, seed_pilot, seed_pitch_demo

__all__ = ["SEED_USERS", "seed_pilot", "seed_pitch_demo"]
