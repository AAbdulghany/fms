"""CLI: sync STD-INSP v2 template across all tenants.

Usage (from backend/):
    python -m app.report_template_sync_cli
    python -m app.cli.report_template_sync_cli
"""

from __future__ import annotations

from app.database import SessionLocal
from app.services.report_template_sync import sync_std_insp_all_tenants


def main() -> None:
    db = SessionLocal()
    try:
        counts = sync_std_insp_all_tenants(db)
        db.commit()
        print(
            "STD-INSP sync complete — "
            f"created={counts['created']}, "
            f"updated={counts['updated']}, "
            f"unchanged={counts['unchanged']}"
        )
    except Exception as exc:
        db.rollback()
        raise SystemExit(f"Sync failed: {exc}") from exc
    finally:
        db.close()


if __name__ == "__main__":
    main()
