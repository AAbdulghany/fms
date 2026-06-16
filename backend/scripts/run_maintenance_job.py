#!/usr/bin/env python3
"""Run due maintenance schedules (Phase 3.1 cron)."""

from app.database import SessionLocal
from app.services.maintenance_schedules import run_due_schedules


def main() -> None:
    db = SessionLocal()
    try:
        n = run_due_schedules(db)
        db.commit()
        print(f"Created {n} preventive work order(s)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
