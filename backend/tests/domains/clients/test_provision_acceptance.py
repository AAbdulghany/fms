"""Wave 5 provision tests (NT-P5-C01-BE, NT-P5-S01, NT-P5-S02, NT-P5-B4, NT-P5-C06-BE)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.security import hash_password
from app.models import Client, Site, User, UserRole, UserSiteScope
from tests.api_helpers import auth_header, assert_api_error


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def super_admin(db_session, sample_tenant):
    user = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="sadmin_w5@test.com",
        password_hash=hash_password("pass"),
        full_name="Super Admin",
        role=UserRole.super_admin,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def company_admin_w5(db_session, sample_tenant):
    user = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="cadmin_w5@test.com",
        password_hash=hash_password("pass"),
        full_name="Company Admin W5",
        role=UserRole.company_admin,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


# ---------------------------------------------------------------------------
# NT-P5-C01-BE: provision endpoint creates exactly 1 site
# ---------------------------------------------------------------------------


def test_provision_creates_exactly_one_site(api_client, super_admin, db_session):
    """POST /clients/provision must insert exactly one Site row (RC-1 fix)."""
    resp = api_client.post(
        "/api/v1/clients/provision",
        json={
            "legal_name": "Acme Corp",
            "manager_full_name": "Ali Hassan",
            "site_name": "Main HQ",
            "city": "Cairo",
            "country": "Egypt",
            "timezone": "Africa/Cairo",
        },
        headers=auth_header(super_admin),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    company_id = data["company_id"]

    # Count sites in DB for this client
    from uuid import UUID as _UUID
    from sqlalchemy import select, func
    count = db_session.scalar(
        select(func.count()).select_from(Site).where(Site.client_id == _UUID(company_id))
    )
    assert count == 1, f"Expected exactly 1 site, got {count}"


def test_provision_response_has_credentials(api_client, super_admin):
    """Provision response must include manager credentials."""
    resp = api_client.post(
        "/api/v1/clients/provision",
        json={
            "legal_name": "Beta Ltd",
            "manager_full_name": "Sara Nour",
            "site_name": "Branch A",
            "city": "Alexandria",
            "country": "Egypt",
            "timezone": "Africa/Cairo",
        },
        headers=auth_header(super_admin),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["manager_username"]
    assert data["initial_password"]
    assert data["manager_email"]


# ---------------------------------------------------------------------------
# NT-P5-B4: GET /clients returns aggregates
# ---------------------------------------------------------------------------


def test_list_clients_returns_aggregates(api_client, super_admin, db_session, sample_tenant, sample_client):
    """GET /clients returns sites_count and active_wo_count fields."""
    resp = api_client.get("/api/v1/clients", headers=auth_header(super_admin))
    assert resp.status_code == 200, resp.text
    rows = resp.json()
    assert len(rows) >= 1
    row = next(r for r in rows if r["id"] == str(sample_client.id))
    assert "sites_count" in row
    assert "active_wo_count" in row
    assert "primary_contact_email" in row
    assert "primary_contact_phone" in row
    assert isinstance(row["sites_count"], int)
    assert isinstance(row["active_wo_count"], int)


# ---------------------------------------------------------------------------
# NT-P5-S01: PATCH /sites/{site_id}
# ---------------------------------------------------------------------------


def test_patch_site_updates_name(api_client, super_admin, sample_site, db_session):
    """PATCH /sites/{site_id} updates the site name."""
    resp = api_client.patch(
        f"/api/v1/sites/{sample_site.id}",
        json={"name": "Updated Site Name"},
        headers=auth_header(super_admin),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "Updated Site Name"


def test_patch_site_updates_city(api_client, super_admin, sample_site):
    """PATCH /sites/{site_id} updates city in address_json."""
    resp = api_client.patch(
        f"/api/v1/sites/{sample_site.id}",
        json={"city": "Riyadh", "country": "SA"},
        headers=auth_header(super_admin),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["city"] == "Riyadh"
    assert data["country"] == "SA"


def test_patch_site_updates_status(api_client, super_admin, sample_site):
    """PATCH /sites/{site_id} can update status."""
    resp = api_client.patch(
        f"/api/v1/sites/{sample_site.id}",
        json={"status": "inactive"},
        headers=auth_header(super_admin),
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "inactive"


def test_patch_site_404_for_unknown(api_client, super_admin):
    """PATCH /sites/{unknown} returns 404."""
    resp = api_client.patch(
        f"/api/v1/sites/{uuid4()}",
        json={"name": "Ghost"},
        headers=auth_header(super_admin),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# NT-P5-S02: POST /sites/{site_id}/assign-manager
# ---------------------------------------------------------------------------


def test_assign_manager_to_existing_site(api_client, super_admin, sample_site, db_session):
    """POST /sites/{site_id}/assign-manager creates site_manager + UserSiteScope."""
    resp = api_client.post(
        f"/api/v1/sites/{sample_site.id}/assign-manager",
        json={"manager_full_name": "Mohamed Salah"},
        headers=auth_header(super_admin),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["manager_username"]
    assert data["initial_password"]
    assert data["manager_email"]

    # Verify UserSiteScope created
    from sqlalchemy import select
    mgr = db_session.scalar(
        select(User).where(User.username == data["manager_username"])
    )
    assert mgr is not None
    assert mgr.role == UserRole.site_manager
    scope = db_session.get(UserSiteScope, {"user_id": mgr.id, "site_id": sample_site.id})
    assert scope is not None


def test_assign_manager_does_not_create_new_site(api_client, super_admin, sample_site, db_session):
    """assign-manager must NOT create a duplicate site."""
    from sqlalchemy import select, func
    count_before = db_session.scalar(
        select(func.count()).select_from(Site).where(
            Site.client_id == sample_site.client_id
        )
    )
    api_client.post(
        f"/api/v1/sites/{sample_site.id}/assign-manager",
        json={"manager_full_name": "Fatima Zahra"},
        headers=auth_header(super_admin),
    )
    count_after = db_session.scalar(
        select(func.count()).select_from(Site).where(
            Site.client_id == sample_site.client_id
        )
    )
    assert count_after == count_before, "assign-manager must not create extra sites"


# ---------------------------------------------------------------------------
# NT-P5-C06-BE: PATCH /users/{id} phone/email for tenant admins
# ---------------------------------------------------------------------------


@pytest.fixture
def client_admin_user(db_session, sample_tenant, sample_client):
    user = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        client_id=sample_client.id,
        email="clientadmin_w5@test.com",
        password_hash=hash_password("pass"),
        full_name="Client Admin",
        role=UserRole.client_admin,
        is_active=True,
        phone=None,
    )
    db_session.add(user)
    db_session.commit()
    return user


def test_patch_user_phone_email_by_super_admin(
    api_client, super_admin, client_admin_user
):
    """super_admin can patch phone/email of client_admin users."""
    resp = api_client.patch(
        f"/api/v1/users/{client_admin_user.id}",
        json={"phone": "+966500000001", "email": "new_ca@test.com"},
        headers=auth_header(super_admin),
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["email"] == "new_ca@test.com"


def test_patch_user_phone_by_company_admin(
    api_client, company_admin_w5, client_admin_user
):
    """company_admin can patch phone of client_admin users."""
    resp = api_client.patch(
        f"/api/v1/users/{client_admin_user.id}",
        json={"phone": "+966500000002"},
        headers=auth_header(company_admin_w5),
    )
    assert resp.status_code == 200, resp.text


def test_patch_user_phone_forbidden_for_peer(
    api_client, client_admin_user, db_session, sample_tenant, sample_client
):
    """client_admin cannot patch phone of another client_admin (not a tenant admin)."""
    other = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        client_id=sample_client.id,
        email="other_ca@test.com",
        password_hash=hash_password("pass"),
        full_name="Other CA",
        role=UserRole.client_admin,
        is_active=True,
    )
    db_session.add(other)
    db_session.commit()
    resp = api_client.patch(
        f"/api/v1/users/{other.id}",
        json={"phone": "+966500000003"},
        headers=auth_header(client_admin_user),
    )
    assert resp.status_code == 403


def test_patch_user_email_duplicate_rejected(
    api_client, super_admin, client_admin_user, db_session, sample_tenant, sample_client
):
    """Changing email to an existing email returns 400."""
    other = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        client_id=sample_client.id,
        email="taken@test.com",
        password_hash=hash_password("pass"),
        full_name="Taken Email User",
        role=UserRole.site_manager,
        is_active=True,
    )
    db_session.add(other)
    db_session.commit()

    resp = api_client.patch(
        f"/api/v1/users/{client_admin_user.id}",
        json={"email": "taken@test.com"},
        headers=auth_header(super_admin),
    )
    assert_api_error(resp, status=400, code="EMAIL_ALREADY_IN_USE")
