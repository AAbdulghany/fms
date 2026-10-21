"""A1 catalog seed tests — U1-U5."""

from __future__ import annotations

import pytest
from sqlalchemy.orm import Session

from app.models.asset_types import AssetTypeTemplate, AssetTypeTemplateVertical, Vertical
from app.services.asset_type_catalog import ensure_vertical_catalog
from app.services.asset_type_catalog_data import TEMPLATE_SEED, VERTICAL_SEED


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_db(db_session: Session) -> Session:
    ensure_vertical_catalog(db_session)
    db_session.commit()
    return db_session


# ---------------------------------------------------------------------------
# U1 — creates all verticals and templates on empty DB
# ---------------------------------------------------------------------------


def test_u1_creates_verticals_and_templates(db_session: Session) -> None:
    counts = ensure_vertical_catalog(db_session)
    db_session.commit()

    verticals = db_session.query(Vertical).all()
    templates = db_session.query(AssetTypeTemplate).all()

    assert counts["verticals"] == len(VERTICAL_SEED)
    assert counts["templates"] == len(TEMPLATE_SEED)
    assert len(verticals) == len(VERTICAL_SEED)
    assert len(templates) == len(TEMPLATE_SEED)


# ---------------------------------------------------------------------------
# U2 — second run creates no new rows
# ---------------------------------------------------------------------------


def test_u2_idempotent(seeded_db: Session) -> None:
    from sqlalchemy import select

    v_count_before = len(seeded_db.scalars(select(Vertical)).all())
    t_count_before = len(seeded_db.scalars(select(AssetTypeTemplate)).all())

    ensure_vertical_catalog(seeded_db)
    seeded_db.commit()

    v_count_after = len(seeded_db.scalars(select(Vertical)).all())
    t_count_after = len(seeded_db.scalars(select(AssetTypeTemplate)).all())

    assert v_count_before == v_count_after
    assert t_count_before == t_count_after


# ---------------------------------------------------------------------------
# U3 — changing content increments version by 1
# ---------------------------------------------------------------------------


def test_u3_version_incremented_on_content_change(db_session: Session) -> None:
    ensure_vertical_catalog(db_session)
    db_session.commit()

    # Patch one template's EN name and re-run
    first_code = TEMPLATE_SEED[0]["code"]
    original_name = TEMPLATE_SEED[0]["name_en"]

    from sqlalchemy import select

    tmpl = db_session.scalar(
        select(AssetTypeTemplate).where(AssetTypeTemplate.code == first_code)
    )
    assert tmpl is not None
    old_version = tmpl.version

    # Simulate seed data change by directly changing the template name in DB
    # and then running ensure with the original (unchanged) seed data → no increment
    # OR: patch the seed dict and re-run to force an update.
    # Since we can't import and mutate TEMPLATE_SEED here, we simulate by
    # modifying the row directly and calling the upsert logic:
    tmpl.name_en = "Changed Name For Test"
    db_session.flush()

    # Run ensure again with the original seed (which differs from stored row)
    ensure_vertical_catalog(db_session)
    db_session.commit()

    db_session.expire(tmpl)
    tmpl = db_session.scalar(
        select(AssetTypeTemplate).where(AssetTypeTemplate.code == first_code)
    )
    assert tmpl is not None
    # The seed name is original_name, the DB had "Changed Name For Test" → update fired
    assert tmpl.version == old_version + 1
    assert tmpl.name_en == original_name


# ---------------------------------------------------------------------------
# U4 — every template has valid name_en, name_ar and allowed frequency
# ---------------------------------------------------------------------------


def test_u4_seed_data_valid() -> None:
    allowed_freq = {"monthly", "quarterly", "yearly", None}
    for spec in TEMPLATE_SEED:
        assert spec["name_en"], f"{spec['code']} missing name_en"
        assert spec["name_ar"], f"{spec['code']} missing name_ar"
        assert spec.get("default_frequency") in allowed_freq, (
            f"{spec['code']} has invalid frequency {spec.get('default_frequency')}"
        )


# ---------------------------------------------------------------------------
# U5 — every vertical has at least one recommended template
# ---------------------------------------------------------------------------


def test_u5_every_vertical_has_a_template(db_session: Session) -> None:
    ensure_vertical_catalog(db_session)
    db_session.commit()

    from sqlalchemy import select

    verticals = db_session.scalars(
        select(Vertical).where(Vertical.is_active.is_(True))
    ).all()

    for v in verticals:
        # Universal templates (no tags) apply to every vertical
        universal_count = sum(
            1
            for spec in TEMPLATE_SEED
            if not spec["verticals"]  # empty list = universal
        )
        specific_tags = db_session.scalars(
            select(AssetTypeTemplateVertical.template_id).where(
                AssetTypeTemplateVertical.vertical_id == v.id
            )
        ).all()
        total = universal_count + len(specific_tags)
        assert total > 0, f"Vertical '{v.code}' has no templates"
