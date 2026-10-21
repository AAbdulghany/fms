"""A1 adopt tests — U6-U13."""

from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.asset_types import AssetType, AssetTypeTemplate, AssetTypeVertical, Vertical
from app.services.asset_type_catalog import ensure_vertical_catalog
from app.services.asset_types_service import adopt_templates


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def seeded_db(db_session: Session, sample_tenant) -> Session:
    ensure_vertical_catalog(db_session)
    db_session.commit()
    return db_session


def _first_template(db: Session) -> AssetTypeTemplate:
    return db.scalar(
        select(AssetTypeTemplate).where(AssetTypeTemplate.is_active.is_(True))
    )


def _hvac_ahu_template(db: Session) -> AssetTypeTemplate:
    return db.scalar(
        select(AssetTypeTemplate).where(AssetTypeTemplate.code == "hvac_ahu")
    )


def _hvac_chiller_template(db: Session) -> AssetTypeTemplate:
    return db.scalar(
        select(AssetTypeTemplate).where(AssetTypeTemplate.code == "hvac_chiller")
    )


# ---------------------------------------------------------------------------
# U6 — adopting copies defaults, vertical tags, origin, source_template_id
# ---------------------------------------------------------------------------


def test_u6_adopt_copies_defaults(seeded_db: Session, sample_tenant) -> None:
    tmpl = _hvac_chiller_template(seeded_db)
    assert tmpl is not None

    result = adopt_templates(seeded_db, sample_tenant.id, [tmpl.id])
    seeded_db.commit()

    assert len(result["created"]) == 1
    at = result["created"][0]

    assert at.origin == "catalog"
    assert at.source_template_id == tmpl.id
    assert at.source_version == tmpl.version
    assert at.default_max_age_years == tmpl.default_max_age_years
    assert at.default_criticality == tmpl.default_criticality
    assert at.default_frequency == tmpl.default_frequency
    assert at.adopted_at is not None

    # Vertical tags should be copied
    vert_ids = seeded_db.scalars(
        select(AssetTypeVertical.vertical_id).where(AssetTypeVertical.asset_type_id == at.id)
    ).all()
    assert len(vert_ids) > 0  # chiller has multiple verticals


# ---------------------------------------------------------------------------
# U7 — adopting again returns skipped
# ---------------------------------------------------------------------------


def test_u7_adopt_idempotent(seeded_db: Session, sample_tenant) -> None:
    tmpl = _hvac_ahu_template(seeded_db)

    adopt_templates(seeded_db, sample_tenant.id, [tmpl.id])
    seeded_db.commit()

    result2 = adopt_templates(seeded_db, sample_tenant.id, [tmpl.id])
    seeded_db.commit()

    assert len(result2["created"]) == 0
    assert len(result2["skipped"]) == 1
    assert result2["skipped"][0]["reason"] == "already_adopted"


# ---------------------------------------------------------------------------
# U8 — legacy type with code HVAC_AHU gets linked when template code is hvac_ahu
# ---------------------------------------------------------------------------


def test_u8_legacy_code_merge(seeded_db: Session, sample_tenant) -> None:
    from datetime import datetime, timezone

    # Create a legacy type with a different case
    legacy = AssetType(
        tenant_id=sample_tenant.id,
        code="HVAC_AHU",  # different case from template "hvac_ahu"
        name_en="Legacy AHU",
        name_ar="وحدة قديمة",
        origin="legacy",
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    seeded_db.add(legacy)
    seeded_db.flush()

    tmpl = _hvac_ahu_template(seeded_db)
    result = adopt_templates(seeded_db, sample_tenant.id, [tmpl.id])
    seeded_db.commit()

    assert len(result["created"]) == 0
    skipped = result["skipped"]
    assert len(skipped) == 1
    assert skipped[0]["reason"] == "merged_with_existing_code"
    assert skipped[0]["asset_type_id"] == legacy.id

    # The legacy row now has provenance
    seeded_db.refresh(legacy)
    assert legacy.source_template_id == tmpl.id
    assert legacy.source_version == tmpl.version
    assert legacy.adopted_at is not None
    # Original code preserved (I2)
    assert legacy.code == "HVAC_AHU"
    # Original names preserved (tenant values not overwritten)
    assert legacy.name_en == "Legacy AHU"


# ---------------------------------------------------------------------------
# U9 — default_report_template_code resolves to tenant's template
# ---------------------------------------------------------------------------


def test_u9_resolves_report_template(seeded_db: Session, sample_tenant) -> None:
    from app.models import ReportTemplate
    from datetime import datetime, timezone

    rt = ReportTemplate(
        tenant_id=sample_tenant.id,
        code="STD-INSP",
        name="Standard Inspection",
        schema_json={},
    )
    seeded_db.add(rt)
    seeded_db.flush()

    tmpl = _hvac_ahu_template(seeded_db)
    result = adopt_templates(seeded_db, sample_tenant.id, [tmpl.id])
    seeded_db.commit()

    assert len(result["created"]) == 1
    at = result["created"][0]
    assert at.default_report_template_id == rt.id


# ---------------------------------------------------------------------------
# U10 — unresolved template code gives null, no error
# ---------------------------------------------------------------------------


def test_u10_unresolved_template_code_no_error(seeded_db: Session, sample_tenant) -> None:
    tmpl = _hvac_ahu_template(seeded_db)
    # No STD-INSP report template in this tenant
    result = adopt_templates(seeded_db, sample_tenant.id, [tmpl.id])
    seeded_db.commit()

    assert len(result["created"]) == 1
    at = result["created"][0]
    assert at.default_report_template_id is None  # not found, no error


# ---------------------------------------------------------------------------
# U11 — another tenant's template code is not resolved
# ---------------------------------------------------------------------------


def test_u11_cross_tenant_template_not_resolved(seeded_db: Session, sample_tenant) -> None:
    from app.models import ReportTemplate, Tenant
    from uuid import uuid4
    from datetime import datetime, timezone

    # Other tenant
    other_tenant = Tenant(id=uuid4(), name="Other Tenant", status="active")
    seeded_db.add(other_tenant)
    seeded_db.flush()

    rt = ReportTemplate(
        tenant_id=other_tenant.id,
        code="STD-INSP",
        name="Other Standard",
        schema_json={},
    )
    seeded_db.add(rt)
    seeded_db.flush()

    tmpl = _hvac_ahu_template(seeded_db)
    result = adopt_templates(seeded_db, sample_tenant.id, [tmpl.id])
    seeded_db.commit()

    at = result["created"][0]
    assert at.default_report_template_id is None  # belongs to other tenant


# ---------------------------------------------------------------------------
# U12 — inactive template goes to skipped
# ---------------------------------------------------------------------------


def test_u12_inactive_template_skipped(seeded_db: Session, sample_tenant) -> None:
    tmpl = _hvac_ahu_template(seeded_db)
    tmpl.is_active = False
    seeded_db.flush()

    result = adopt_templates(seeded_db, sample_tenant.id, [tmpl.id])
    seeded_db.commit()

    assert len(result["created"]) == 0
    assert len(result["skipped"]) == 1
    assert result["skipped"][0]["reason"] == "inactive_template"


# ---------------------------------------------------------------------------
# U13 — editing the tenant copy does not change the catalog; catalog bump does not change copy
# ---------------------------------------------------------------------------


def test_u13_copy_independence(seeded_db: Session, sample_tenant) -> None:
    tmpl = _hvac_chiller_template(seeded_db)

    result = adopt_templates(seeded_db, sample_tenant.id, [tmpl.id])
    seeded_db.commit()
    at = result["created"][0]

    # Edit the tenant copy
    at.default_max_age_years = 99
    seeded_db.flush()

    # Simulate a catalog version bump
    tmpl.name_en = "Super Chiller"
    tmpl.version += 1
    seeded_db.flush()

    # Catalog change does not affect the tenant copy
    seeded_db.expire(at)
    seeded_db.refresh(at)
    assert at.default_max_age_years == 99  # tenant value preserved
    assert at.name_en != "Super Chiller"  # catalog change did not propagate
