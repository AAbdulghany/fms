"""A1 library CRUD tests — U14-U20."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import AuditLog, User, UserRole
from app.models.asset_types import AssetType, Vertical
from app.services.asset_type_catalog import ensure_vertical_catalog
from tests.api_helpers import auth_header as _auth_header


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------



@pytest.fixture
def seeded_db(db_session: Session, sample_tenant) -> Session:
    ensure_vertical_catalog(db_session)
    db_session.commit()
    return db_session


@pytest.fixture
def admin_user(db_session: Session, sample_tenant) -> User:
    from uuid import uuid4
    from app.core.security import hash_password

    user = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="admin_types@test.com",
        password_hash=hash_password("pw"),
        full_name="Admin",
        role=UserRole.company_admin,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def client_user(db_session: Session, sample_tenant) -> User:
    """client_admin user — should be blocked from write endpoints."""
    from uuid import uuid4
    from app.core.security import hash_password

    user = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="cadmin_types@test.com",
        password_hash=hash_password("pw"),
        full_name="Client Admin",
        role=UserRole.client_admin,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


# ---------------------------------------------------------------------------
# U14 — POST /asset-types creates a custom type
# ---------------------------------------------------------------------------


def test_u14_create_custom_type(api_client: TestClient, seeded_db, admin_user) -> None:
    resp = api_client.post(
        "/api/v1/asset-types",
        json={"code": "custom_pump", "name_en": "Custom Pump", "name_ar": "مضخة مخصصة"},
        headers=_auth_header(admin_user),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["origin"] == "custom"
    assert data["code"] == "custom_pump"


# ---------------------------------------------------------------------------
# U15 — duplicate code (different case) gives 409
# ---------------------------------------------------------------------------


def test_u15_duplicate_code_conflict(api_client: TestClient, seeded_db, admin_user) -> None:
    api_client.post(
        "/api/v1/asset-types",
        json={"code": "pump_x", "name_en": "Pump X", "name_ar": "مضخة"},
        headers=_auth_header(admin_user),
    )
    resp = api_client.post(
        "/api/v1/asset-types",
        json={"code": "PUMP_X", "name_en": "Pump X Upper", "name_ar": "مضخة"},
        headers=_auth_header(admin_user),
    )
    assert resp.status_code == 409
    assert resp.json()["detail"] == "ASSET_TYPE_CODE_EXISTS"


# ---------------------------------------------------------------------------
# U16 — PATCH with code gives 400
# ---------------------------------------------------------------------------


def test_u16_patch_code_immutable(api_client: TestClient, seeded_db, admin_user) -> None:
    resp = api_client.post(
        "/api/v1/asset-types",
        json={"code": "immutable_type", "name_en": "Immutable", "name_ar": "ثابت"},
        headers=_auth_header(admin_user),
    )
    type_id = resp.json()["id"]
    patch_resp = api_client.patch(
        f"/api/v1/asset-types/{type_id}",
        json={"code": "new_code"},
        headers=_auth_header(admin_user),
    )
    assert patch_resp.status_code == 400
    detail = patch_resp.json()["detail"]
    detail_code = detail if isinstance(detail, str) else detail.get("code", detail)
    assert detail_code == "ASSET_TYPE_CODE_IMMUTABLE"


# ---------------------------------------------------------------------------
# U17 — archive hides from default list; include_inactive shows it; restore restores
# ---------------------------------------------------------------------------


def test_u17_archive_and_restore(api_client: TestClient, seeded_db, admin_user) -> None:
    resp = api_client.post(
        "/api/v1/asset-types",
        json={"code": "archivable", "name_en": "Archivable", "name_ar": "قابل للأرشفة"},
        headers=_auth_header(admin_user),
    )
    type_id = resp.json()["id"]

    # Archive
    api_client.patch(
        f"/api/v1/asset-types/{type_id}",
        json={"is_active": False},
        headers=_auth_header(admin_user),
    )

    # Not in default list
    list_resp = api_client.get(
        "/api/v1/asset-types",
        headers=_auth_header(admin_user),
    )
    ids = [t["id"] for t in list_resp.json()]
    assert type_id not in ids

    # Visible with include_inactive
    list_resp2 = api_client.get(
        "/api/v1/asset-types?include_inactive=true",
        headers=_auth_header(admin_user),
    )
    ids2 = [t["id"] for t in list_resp2.json()]
    assert type_id in ids2

    # Restore
    api_client.patch(
        f"/api/v1/asset-types/{type_id}",
        json={"is_active": True},
        headers=_auth_header(admin_user),
    )
    list_resp3 = api_client.get(
        "/api/v1/asset-types",
        headers=_auth_header(admin_user),
    )
    ids3 = [t["id"] for t in list_resp3.json()]
    assert type_id in ids3


# ---------------------------------------------------------------------------
# U18 — GET /asset-types?client_id marks recommended types first
# ---------------------------------------------------------------------------


def test_u18_recommended_for_client(
    api_client: TestClient, seeded_db: Session, admin_user, sample_client
) -> None:
    # Give the sample client a hospital vertical
    hospital_v = seeded_db.scalar(
        __import__("sqlalchemy").select(Vertical).where(Vertical.code == "hospital")
    )
    sample_client.vertical_id = hospital_v.id
    seeded_db.commit()

    # Adopt a hospital-only type
    from app.models.asset_types import AssetTypeTemplate
    from app.services.asset_types_service import adopt_templates
    medical_gas = seeded_db.scalar(
        __import__("sqlalchemy").select(AssetTypeTemplate).where(
            AssetTypeTemplate.code == "medical_gas"
        )
    )
    adopt_templates(seeded_db, admin_user.tenant_id, [medical_gas.id])
    seeded_db.commit()

    resp = api_client.get(
        f"/api/v1/asset-types?client_id={sample_client.id}",
        headers=_auth_header(admin_user),
    )
    assert resp.status_code == 200, resp.text
    types = resp.json()
    # At least one recommended type should exist
    recommended = [t for t in types if t["recommended"]]
    assert len(recommended) > 0
    # Recommended types should sort first
    first_recommended_idx = next(
        (i for i, t in enumerate(types) if t["recommended"]), None
    )
    first_not_recommended_idx = next(
        (i for i, t in enumerate(types) if not t["recommended"]), None
    )
    if first_recommended_idx is not None and first_not_recommended_idx is not None:
        assert first_recommended_idx < first_not_recommended_idx


# ---------------------------------------------------------------------------
# U19 — invalid default_frequency gives 422
# ---------------------------------------------------------------------------


def test_u19_invalid_frequency(api_client: TestClient, seeded_db, admin_user) -> None:
    resp = api_client.post(
        "/api/v1/asset-types",
        json={
            "code": "freq_test",
            "name_en": "Freq Test",
            "name_ar": "اختبار",
            "default_frequency": "daily",  # not in {monthly, quarterly, yearly}
        },
        headers=_auth_header(admin_user),
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# U20 — every write creates an audit row
# ---------------------------------------------------------------------------


def test_u20_write_creates_audit(
    api_client: TestClient, seeded_db, admin_user, db_session: Session
) -> None:
    resp = api_client.post(
        "/api/v1/asset-types",
        json={"code": "audit_type", "name_en": "Audit Type", "name_ar": "نوع للتدقيق"},
        headers=_auth_header(admin_user),
    )
    assert resp.status_code == 201

    from sqlalchemy import select

    audit_rows = db_session.scalars(
        select(AuditLog).where(
            AuditLog.entity_type == "asset_type",
            AuditLog.action == "create",
        )
    ).all()
    assert len(audit_rows) >= 1
