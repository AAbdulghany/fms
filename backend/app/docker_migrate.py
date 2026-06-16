"""Docker migrate entrypoint — schema then seed (dev or demo)."""

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
    print("Applying database schema…")
    _upgrade_schema()
    print(f"Running seed: {seed}")
    if seed == "pitch":
        from app.pitch_seed import seed_pitch_demo

        with SessionLocal() as db:
            info = seed_pitch_demo(db)
            db.commit()
            print("Pitch demo seeded:", info)
    else:
        from app.test_seed import seed_data

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
