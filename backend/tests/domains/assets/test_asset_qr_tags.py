"""A2 — AssetTag mint / resolve / PDF / rate-limit (U-QR-01..07) + A1-C2."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.models import (
    Asset,
    SubscriptionPackage,
    Tenant,
    TenantSubscription,
    User,
    UserRole,
)
from app.models.asset_tags import AssetTag
from app.domains.public.asset_tags import reset_rate_limits
from app.services.asset_tags import ensure_active_tag
from app.services.pdf import render_asset_label_pdf
from tests.api_helpers import assert_api_error, auth_header


@pytest.fixture(autouse=True)
def _clear_rate():
    reset_rate_limits()
    yield
    reset_rate_limits()


@pytest.fixture
def admin_user(db_session: Session, sample_tenant) -> User:
    u = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="qr_admin@test.com",
        password_hash=hash_password("pw"),
        full_name="QR Admin",
        role=UserRole.company_admin,
        is_active=True,
    )
    db_session.add(u)
    db_session.commit()
    return u


def _make_asset(db: Session, tenant_id, site_id, name: str = "QR Asset") -> Asset:
    a = Asset(
        id=uuid4(),
        tenant_id=tenant_id,
        site_id=site_id,
        name=name,
        category="hvac",
        label_code="TST-HVAC-001",
    )
    db.add(a)
    db.flush()
    return a


# ---------------------------------------------------------------------------
# U-QR-01 — create mints tag + qr_payload
# ---------------------------------------------------------------------------


def test_u_qr_01_create_mints_tag(
    api_client: TestClient, db_session: Session, admin_user, sample_site, monkeypatch
) -> None:
    monkeypatch.setenv("PUBLIC_APP_URL", "https://app.example.com")
    resp = api_client.post(
        "/api/v1/assets",
        json={"site_id": str(sample_site.id), "name": "Minted Asset", "category": "hvac"},
        headers=auth_header(admin_user),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "/a/" in (data.get("qr_payload") or "")
    assert data["qr_payload"].startswith("https://app.example.com/a/")
    token = data["qr_payload"].rsplit("/", 1)[-1]
    tag = db_session.scalar(select(AssetTag).where(AssetTag.token == token))
    assert tag is not None
    assert tag.status == "active"
    assert str(tag.asset_id) == data["id"]


# ---------------------------------------------------------------------------
# U-QR-02 — rotate revokes old
# ---------------------------------------------------------------------------


def test_u_qr_02_rotate_revokes(
    api_client: TestClient, db_session: Session, admin_user, sample_site
) -> None:
    asset = _make_asset(db_session, admin_user.tenant_id, sample_site.id)
    old = ensure_active_tag(db_session, asset)
    db_session.commit()
    old_token = old.token

    resp = api_client.post(
        f"/api/v1/assets/{asset.id}/qr/rotate",
        headers=auth_header(admin_user),
    )
    assert resp.status_code == 200, resp.text
    new_token = resp.json()["token"]
    assert new_token != old_token

    db_session.expire_all()
    old_row = db_session.scalar(select(AssetTag).where(AssetTag.token == old_token))
    assert old_row is not None
    assert old_row.status == "revoked"

    gone = api_client.get(f"/api/v1/public/asset-tags/{old_token}")
    assert gone.status_code == 404


# ---------------------------------------------------------------------------
# U-QR-03 — anon resolve redacted
# ---------------------------------------------------------------------------


def test_u_qr_03_anon_resolve(api_client: TestClient, db_session: Session, sample_tenant, sample_site, sample_client) -> None:
    asset = _make_asset(db_session, sample_tenant.id, sample_site.id, name="Pump A")
    tag = ensure_active_tag(db_session, asset)
    db_session.commit()

    resp = api_client.get(f"/api/v1/public/asset-tags/{tag.token}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["name"] == "Pump A"
    assert data["site_name"] == sample_site.name
    assert data["client_name"] == sample_client.legal_name
    assert data["can_report"] is True
    assert data.get("asset_id") is None
    assert data.get("has_history") is False


# ---------------------------------------------------------------------------
# U-QR-04 — same-tenant auth gets asset_id
# ---------------------------------------------------------------------------


def test_u_qr_04_auth_resolve(
    api_client: TestClient, db_session: Session, admin_user, sample_site
) -> None:
    asset = _make_asset(db_session, admin_user.tenant_id, sample_site.id)
    tag = ensure_active_tag(db_session, asset)
    db_session.commit()

    resp = api_client.get(
        f"/api/v1/public/asset-tags/{tag.token}",
        headers=auth_header(admin_user),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["asset_id"] == str(asset.id)


# ---------------------------------------------------------------------------
# U-QR-05 — cross-tenant auth → 404
# ---------------------------------------------------------------------------


def test_u_qr_05_cross_tenant(
    api_client: TestClient, db_session: Session, admin_user, sample_site
) -> None:
    asset = _make_asset(db_session, admin_user.tenant_id, sample_site.id)
    tag = ensure_active_tag(db_session, asset)

    other_tenant = Tenant(id=uuid4(), name="Other", status="active")
    db_session.add(other_tenant)
    other_user = User(
        id=uuid4(),
        tenant_id=other_tenant.id,
        email="other@test.com",
        password_hash=hash_password("pw"),
        full_name="Other",
        role=UserRole.company_admin,
        is_active=True,
    )
    db_session.add(other_user)
    db_session.commit()

    resp = api_client.get(
        f"/api/v1/public/asset-tags/{tag.token}",
        headers=auth_header(other_user),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# U-QR-06 — PDF embeds PNG
# ---------------------------------------------------------------------------


def test_u_qr_06_pdf_has_qr_image(db_session: Session, sample_tenant, sample_site) -> None:
    asset = _make_asset(db_session, sample_tenant.id, sample_site.id)
    ensure_active_tag(db_session, asset)
    db_session.commit()
    pdf = render_asset_label_pdf(asset, client_name="Test Client Corp", size_mm=50)
    assert pdf[:4] == b"%PDF"
    # ReportLab embeds the QR as an XObject image (may Flate-compress PNG bytes)
    assert b"/Image" in pdf or b"\x89PNG" in pdf
    assert len(pdf) > 2000  # text-only label is ~1KB; QR image pushes it larger


def test_u_qr_06b_label_size_clamped(db_session: Session, sample_tenant, sample_site) -> None:
    from app.services.asset_label_sticker import clamp_label_size_mm

    assert clamp_label_size_mm(70) == 70
    assert clamp_label_size_mm(10) == 40
    assert clamp_label_size_mm(200) == 120
    asset = _make_asset(db_session, sample_tenant.id, sample_site.id)
    ensure_active_tag(db_session, asset)
    db_session.commit()
    small = render_asset_label_pdf(asset, client_name="Co", size_mm=40, design="a")
    large = render_asset_label_pdf(asset, client_name="Co", size_mm=60, design="a")
    assert small[:4] == b"%PDF" and large[:4] == b"%PDF"
    assert len(large) >= len(small) * 0.8


def test_u_qr_06c_field_tag_design(db_session: Session, sample_tenant, sample_site) -> None:
    asset = _make_asset(db_session, sample_tenant.id, sample_site.id, name="Long Asset Name Unit")
    ensure_active_tag(db_session, asset)
    db_session.commit()
    pdf = render_asset_label_pdf(asset, client_name="Test Client Corp", size_mm=60, design="c")
    assert pdf[:4] == b"%PDF"
    assert b"/Image" in pdf or b"\x89PNG" in pdf
    assert len(pdf) > 1500


# ---------------------------------------------------------------------------
# U-QR-07 — rate limit
# ---------------------------------------------------------------------------


def test_u_qr_07_rate_limit(
    api_client: TestClient, db_session: Session, sample_tenant, sample_site
) -> None:
    asset = _make_asset(db_session, sample_tenant.id, sample_site.id)
    tag = ensure_active_tag(db_session, asset)
    db_session.commit()

    body = {"title": "Leak", "description": "Water on floor near unit"}
    for i in range(5):
        r = api_client.post(f"/api/v1/public/asset-tags/{tag.token}/report", json=body)
        assert r.status_code == 201, f"attempt {i}: {r.text}"

    blocked = api_client.post(f"/api/v1/public/asset-tags/{tag.token}/report", json=body)
    assert_api_error(blocked, status=429, code="RATE_LIMITED")


# ---------------------------------------------------------------------------
# A1-C2 — /asset-types feature gate
# ---------------------------------------------------------------------------


def test_a1_c2_asset_types_feature_gate(
    api_client: TestClient, db_session: Session, sample_tenant, monkeypatch
) -> None:
    monkeypatch.setenv("APP_ENV", "production")
    from app.config import get_settings

    get_settings.cache_clear()

    user = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="nofeat_at@test.com",
        password_hash=hash_password("pass123"),
        full_name="No Feat",
        role=UserRole.company_admin,
        is_active=True,
    )
    empty_pkg = SubscriptionPackage(
        code="empty_a1c2",
        name="Empty",
        features_json=[],
        limits_json={"max_users": 5},
        is_active=True,
    )
    db_session.add(empty_pkg)
    db_session.add(user)
    db_session.flush()
    db_session.add(
        TenantSubscription(
            tenant_id=sample_tenant.id,
            package_id=empty_pkg.id,
            status="active",
        )
    )
    db_session.commit()

    res = api_client.get("/api/v1/asset-types", headers=auth_header(user))
    assert_api_error(res, status=403, code="FEATURE_NOT_AVAILABLE")
    get_settings.cache_clear()
