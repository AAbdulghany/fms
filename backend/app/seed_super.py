"""Backward-compatible shim — use app.cli.seed_super."""

from app.cli.seed_super import run

if __name__ == "__main__":
    run()
