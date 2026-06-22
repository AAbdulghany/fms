"""Backward-compatible shim — use app.cli.docker_migrate."""

import sys

from app.cli.docker_migrate import main

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Migrate failed: {exc}", file=sys.stderr)
        raise
