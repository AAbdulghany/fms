"""A1 asset create/update with asset_type_id — U21-U35."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Asset, User, UserRole
from app.models.asset_types import AssetType
from app.services.asset_type_catalog import ensure_vertical_catalog
from app.services.asset_types_service import adopt_templates
from tests.api_helpers import auth_header as _auth
from datetime import datetime, timezone
from uuid import uuid4


def _detail_code(resp) -> str:
    """Extract the error code from a response, handling both string and bilingual detail."""
    detail = resp.json()["detail"]
    if isinstance(detail, str):
        return detail
    return detail.get("code", str(detail))


def _make_asset_type(
    db: Session,
    tenant_id,
    code: str = "hvac_ahu",
    is_active: bool = True,
    age: int | None = 15,
    criticality: str | None = "high",
    repair: int | None = None,
) -> AssetType:
    now = datetime.now(timezone.utc)
    at = AssetType(
        tenant_id=tenant_id,
        code=code,
        name_en=code.upper(),
        name_ar=code,
        origin="custom",
        default_max_age_years=age,
        default_criticality=criticality,
        default_max_repair_count=repair,
        is_active=is_active,
        created_at=now,
        updated_at=now,
    )
    db.add(at)
    db.flush()
    return at


@pytest.fixture
def seeded_db(db_session: Session, sample_tenant) -> Session:
    ensure_vertical_catalog(db_session)
    db_session.commit()
    return db_session


@pytest.fixture
def admin_user(db_session: Session, sample_tenant) -> User:
    from app.core.security import hash_password

    u = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="admin_asset@test.com",
        password_hash=hash_password("pw"),
        full_name="Admin",
        role=UserRole.company_admin,
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    return u


# ---------------------------------------------------------------------------
# U21 — Create with asset_type_id sets category = type.code
# ---------------------------------------------------------------------------


def test_u21_create_sets_category(
    api_client: TestClient, db_session: Session, admin_user, sample_site
) -> None:
    at = _make_asset_type(db_session, admin_user.tenant_id, code="test_type_a1")
    db_session.commit()

    resp = api_client.post(
        "/api/v1/assets",
        json={
            "site_id": str(sample_site.id),
            "name": "Test Asset U21",
            "asset_type_id": str(at.id),
        },
        headers=_auth(admin_user),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["category"] == "test_type_a1"
    assert data["asset_type_id"] == str(at.id)


# ---------------------------------------------------------------------------
# U22 — Create with asset_type_id applies type defaults for None fields
# ---------------------------------------------------------------------------


def test_u22_defaults_applied(
    api_client: TestClient, db_session: Session, admin_user, sample_site
) -> None:
    at = _make_asset_type(db_session, admin_user.tenant_id, code="type_defaults", age=20, criticality="critical")
    db_session.commit()

    resp = api_client.post(
        "/api/v1/assets",
        json={
            "site_id": str(sample_site.id),
            "name": "Defaults Test",
            "asset_type_id": str(at.id),
        },
        headers=_auth(admin_user),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["max_age_years"] == 20
    assert data["criticality"] == "critical"


# ---------------------------------------------------------------------------
# U23 — Create with asset_type_id and explicit max_age_years keeps explicit value
# ---------------------------------------------------------------------------


def test_u23_explicit_value_wins(
    api_client: TestClient, db_session: Session, admin_user, sample_site
) -> None:
    at = _make_asset_type(db_session, admin_user.tenant_id, code="type_explicit", age=20)
    db_session.commit()

    resp = api_client.post(
        "/api/v1/assets",
        json={
            "site_id": str(sample_site.id),
            "name": "Explicit Test",
            "asset_type_id": str(at.id),
            "max_age_years": 3,
        },
        headers=_auth(admin_user),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["max_age_years"] == 3


# ---------------------------------------------------------------------------
# U24 — Create with archived type gives 400 ASSET_TYPE_ARCHIVED
# ---------------------------------------------------------------------------


def test_u24_archived_type_rejected(
    api_client: TestClient, db_session: Session, admin_user, sample_site
) -> None:
    at = _make_asset_type(db_session, admin_user.tenant_id, code="archived_type", is_active=False)
    db_session.commit()

    resp = api_client.post(
        "/api/v1/assets",
        json={
            "site_id": str(sample_site.id),
            "name": "Archived Test",
            "asset_type_id": str(at.id),
        },
        headers=_auth(admin_user),
    )
    assert resp.status_code == 400
    assert _detail_code(resp) == "ASSET_TYPE_ARCHIVED"


# ---------------------------------------------------------------------------
# U25 — Create with another tenant's type gives 400/404
# ---------------------------------------------------------------------------


def test_u25_cross_tenant_type_rejected(
    api_client: TestClient, db_session: Session, admin_user, sample_site
) -> None:
    from app.models import Tenant

    other = Tenant(id=uuid4(), name="Other", status="active")
    db_session.add(other)
    db_session.flush()
    at = _make_asset_type(db_session, other.id, code="other_type")
    db_session.commit()

    resp = api_client.post(
        "/api/v1/assets",
        json={
            "site_id": str(sample_site.id),
            "name": "Cross-tenant Test",
            "asset_type_id": str(at.id),
        },
        headers=_auth(admin_user),
    )
    assert resp.status_code in (400, 404)


# ---------------------------------------------------------------------------
# U26 — Create with asset_type_id and different category gives 400
# ---------------------------------------------------------------------------


def test_u26_category_mismatch(
    api_client: TestClient, db_session: Session, admin_user, sample_site
) -> None:
    at = _make_asset_type(db_session, admin_user.tenant_id, code="real_code")
    db_session.commit()

    resp = api_client.post(
        "/api/v1/assets",
        json={
            "site_id": str(sample_site.id),
            "name": "Mismatch",
            "asset_type_id": str(at.id),
            "category": "different_code",
        },
        headers=_auth(admin_user),
    )
    assert resp.status_code == 400
    assert _detail_code(resp) == "ASSET_TYPE_CATEGORY_MISMATCH"


# ---------------------------------------------------------------------------
# U27 — Create with only category links existing type
# ---------------------------------------------------------------------------


def test_u27_category_links_existing_type(
    api_client: TestClient, db_session: Session, admin_user, sample_site
) -> None:
    at = _make_asset_type(db_session, admin_user.tenant_id, code="known_cat")
    db_session.commit()

    resp = api_client.post(
        "/api/v1/assets",
        json={
            "site_id": str(sample_site.id),
            "name": "Category Link",
            "category": "known_cat",
        },
        headers=_auth(admin_user),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["asset_type_id"] == str(at.id)


# ---------------------------------------------------------------------------
# U28 — Create with only category and no matching type leaves asset_type_id null
# ---------------------------------------------------------------------------


def test_u28_unknown_category_no_type(
    api_client: TestClient, db_session: Session, admin_user, sample_site
) -> None:
    resp = api_client.post(
        "/api/v1/assets",
        json={
            "site_id": str(sample_site.id),
            "name": "Unknown Cat",
            "category": "totally_unknown_xyz",
        },
        headers=_auth(admin_user),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["asset_type_id"] is None


# ---------------------------------------------------------------------------
# U29 — Create with asset_type_id does NOT create a schedule unless schedule is in body
# ---------------------------------------------------------------------------


def test_u29_no_auto_schedule(
    api_client: TestClient, db_session: Session, admin_user, sample_site
) -> None:
    at = _make_asset_type(db_session, admin_user.tenant_id, code="no_schedule_type")
    db_session.commit()

    resp = api_client.post(
        "/api/v1/assets",
        json={
            "site_id": str(sample_site.id),
            "name": "No Schedule",
            "asset_type_id": str(at.id),
        },
        headers=_auth(admin_user),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["schedules"] == []


# ---------------------------------------------------------------------------
# U30 — PATCH asset_type_id changes category, does not change label_code
# ---------------------------------------------------------------------------


def test_u30_update_type_changes_category_not_label(
    api_client: TestClient, db_session: Session, admin_user, sample_site
) -> None:
    at1 = _make_asset_type(db_session, admin_user.tenant_id, code="type_one")
    at2 = _make_asset_type(db_session, admin_user.tenant_id, code="type_two")
    db_session.commit()

    create_resp = api_client.post(
        "/api/v1/assets",
        json={"site_id": str(sample_site.id), "name": "Update Type", "asset_type_id": str(at1.id)},
        headers=_auth(admin_user),
    )
    assert create_resp.status_code == 200
    asset_id = create_resp.json()["id"]
    label_code_before = create_resp.json()["label_code"]

    patch_resp = api_client.patch(
        f"/api/v1/assets/{asset_id}",
        json={"asset_type_id": str(at2.id)},
        headers=_auth(admin_user),
    )
    assert patch_resp.status_code == 200, patch_resp.text
    data = patch_resp.json()
    assert data["category"] == "type_two"
    assert data["label_code"] == label_code_before  # not regenerated


# ---------------------------------------------------------------------------
# U31 — PATCH category on a typed asset with a different value gives 400
# ---------------------------------------------------------------------------


def test_u31_update_category_on_typed_asset_rejected(
    api_client: TestClient, db_session: Session, admin_user, sample_site
) -> None:
    at = _make_asset_type(db_session, admin_user.tenant_id, code="typed_code")
    db_session.commit()

    create_resp = api_client.post(
        "/api/v1/assets",
        json={"site_id": str(sample_site.id), "name": "Typed Asset", "asset_type_id": str(at.id)},
        headers=_auth(admin_user),
    )
    asset_id = create_resp.json()["id"]

    patch_resp = api_client.patch(
        f"/api/v1/assets/{asset_id}",
        json={"category": "something_else"},
        headers=_auth(admin_user),
    )
    assert patch_resp.status_code == 400
    assert _detail_code(patch_resp) == "ASSET_TYPE_CATEGORY_MISMATCH"


# ---------------------------------------------------------------------------
# U32 — AssetOut.asset_type holds id, code, names; null for untyped asset
# ---------------------------------------------------------------------------


def test_u32_asset_out_asset_type_field(
    api_client: TestClient, db_session: Session, admin_user, sample_site
) -> None:
    at = _make_asset_type(db_session, admin_user.tenant_id, code="ref_type")
    db_session.commit()

    resp = api_client.post(
        "/api/v1/assets",
        json={"site_id": str(sample_site.id), "name": "Typed", "asset_type_id": str(at.id)},
        headers=_auth(admin_user),
    )
    data = resp.json()
    assert data["asset_type"] is not None
    assert data["asset_type"]["code"] == "ref_type"

    # Untyped
    resp2 = api_client.post(
        "/api/v1/assets",
        json={"site_id": str(sample_site.id), "name": "Untyped"},
        headers=_auth(admin_user),
    )
    assert resp2.json()["asset_type"] is None


# ---------------------------------------------------------------------------
# U33 — GET /assets?asset_type_id= returns only matching assets
# ---------------------------------------------------------------------------


def test_u33_filter_by_asset_type_id(
    api_client: TestClient, db_session: Session, admin_user, sample_site
) -> None:
    at = _make_asset_type(db_session, admin_user.tenant_id, code="filtered_type")
    db_session.commit()

    api_client.post(
        "/api/v1/assets",
        json={"site_id": str(sample_site.id), "name": "Typed A", "asset_type_id": str(at.id)},
        headers=_auth(admin_user),
    )
    api_client.post(
        "/api/v1/assets",
        json={"site_id": str(sample_site.id), "name": "Untyped B"},
        headers=_auth(admin_user),
    )

    resp = api_client.get(
        f"/api/v1/assets?asset_type_id={at.id}",
        headers=_auth(admin_user),
    )
    results = resp.json()
    assert all(r["asset_type_id"] == str(at.id) for r in results)
    assert len(results) == 1


# ---------------------------------------------------------------------------
# U34 — Invariant: asset.category == asset.asset_type.code after create/update
# ---------------------------------------------------------------------------


def test_u34_invariant_category_equals_type_code(
    api_client: TestClient, db_session: Session, admin_user, sample_site
) -> None:
    at = _make_asset_type(db_session, admin_user.tenant_id, code="invariant_code")
    db_session.commit()

    resp = api_client.post(
        "/api/v1/assets",
        json={"site_id": str(sample_site.id), "name": "Invariant", "asset_type_id": str(at.id)},
        headers=_auth(admin_user),
    )
    data = resp.json()
    assert data["category"] == data["asset_type"]["code"]


# ---------------------------------------------------------------------------
# U35 — CSV import with matching category links the type
# ---------------------------------------------------------------------------


def test_u35_csv_import_links_type(
    db_session: Session, sample_tenant, sample_site
) -> None:
    from app.services.asset_import import commit_import

    at = _make_asset_type(db_session, sample_tenant.id, code="HVAC")
    db_session.commit()

    csv_content = "site_code,name,category\n"
    csv_content += f"{sample_site.name},CSV Asset,HVAC\n"

    commit_import(db_session, sample_tenant.id, csv_content)
    db_session.commit()

    asset = db_session.scalar(
        select(Asset).where(
            Asset.tenant_id == sample_tenant.id,
            Asset.category == "HVAC",
        )
    )
    assert asset is not None
    assert asset.asset_type_id == at.id
