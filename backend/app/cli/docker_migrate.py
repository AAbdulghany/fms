"""Docker migrate entrypoint — schema then seed (SEED_MODULE=test | pilot)."""

from __future__ import annotations

import os
import sys

from alembic import command
from alembic.config import Config

from app.database import SessionLocal, engine
from app.schema_ensure import ensure_schema
from app.services.platform_bootstrap import run_wave0_platform_bootstrap


def _upgrade_schema() -> None:
    cfg = Config("alembic.ini")
    command.upgrade(cfg, "head")
    ensure_schema(engine)
    with SessionLocal() as db:
        run_wave0_platform_bootstrap(db)
        db.commit()


def main() -> None:
    seed = os.environ.get("SEED_MODULE", "test").lower()
    # `pitch` is the pre-reorg name for the pilot dataset.
    if seed == "pitch":
        seed = "pilot"
    print("Applying database schema…")
    _upgrade_schema()
    print(f"Running seed: {seed}")
    if seed == "pilot":
        from app.cli.pilot_seed import seed_pilot

        with SessionLocal() as db:
            info = seed_pilot(db)
            db.commit()
            print("Pilot seeded:", info)
    else:
        from app.cli.test_seed import seed_data

        seed_data()
    from scripts.migrate_roles import migrate as migrate_roles

    migrate_roles()
    print("Migrate complete.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Migrate failed: {exc}", file=sys.stderr)
        raise
