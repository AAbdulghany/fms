"""Backward-compatible shim — use app.cli.report_template_sync_cli."""

from app.cli.report_template_sync_cli import main

if __name__ == "__main__":
    main()
