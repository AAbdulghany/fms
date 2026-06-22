"""Backward-compatible shim — use app.cli.seed."""

from app.cli.seed import run

if __name__ == "__main__":
    run()
