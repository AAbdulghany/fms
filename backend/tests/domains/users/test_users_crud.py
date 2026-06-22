"""User CRUD tests — Phase 3 MVP.

Test plan IDs: US-01 … US-04
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.security import hash_password, verify_password
from app.models import Client, Tenant, User, UserRole
from app.schemas import UserCreateBody, UserPatchBody, UserPatchMe


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tenant(db_session):
    t = Tenant(id=uuid4(), name="CRUD Tenant", status="active")
    db_session.add(t)
    db_session.commit()
    db_session.refresh(t)
    return t


@pytest.fixture
def super_admin(db_session, tenant):
    u = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email="super@crud.test",
        password_hash=hash_password("adminpass"),
        full_name="Super Admin",
        role=UserRole.super_admin,
        is_active=True,
        is_platform_admin=False,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def company_admin(db_session, tenant):
    u = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email="companyadmin@crud.test",
        password_hash=hash_password("adminpass"),
        full_name="Company Admin",
        role=UserRole.company_admin,
        is_active=True,
        is_platform_admin=False,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


@pytest.fixture
def technician(db_session, tenant):
    u = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email="tech@crud.test",
        password_hash=hash_password("techpass"),
        full_name="Tech User",
        role=UserRole.technician,
        is_active=True,
        is_platform_admin=False,
    )
    db_session.add(u)
    db_session.commit()
    db_session.refresh(u)
    return u


# ---------------------------------------------------------------------------
# US-01: super_admin lists users — 200, tenant-scoped
# ---------------------------------------------------------------------------


def test_us01_super_admin_lists_users(db_session, tenant, super_admin, technician):
    """super_admin gets all users in tenant; cannot see other-tenant users."""
    from app.api.routes.users import list_users

    other_tenant = Tenant(id=uuid4(), name="Other Tenant", status="active")
    db_session.add(other_tenant)
    other_user = User(
        id=uuid4(),
        tenant_id=other_tenant.id,
        email="other@other.test",
        password_hash=hash_password("pass"),
        full_name="Other",
        role=UserRole.technician,
        is_active=True,
    )
    db_session.add(other_user)
    db_session.commit()

    results = list_users(db_session, super_admin, super_admin)
    returned_ids = {u.id for u in results}

    assert super_admin.id in returned_ids
    assert technician.id in returned_ids
    assert other_user.id not in returned_ids


def test_us01_company_admin_lists_users(db_session, tenant, company_admin, technician):
    """company_admin can also list users (Phase 3 expansion)."""
    from app.api.routes.users import list_users

    results = list_users(db_session, company_admin, company_admin)
    returned_ids = {u.id for u in results}

    assert company_admin.id in returned_ids
    assert technician.id in returned_ids


def test_us01_technician_cannot_list_users(db_session, tenant, technician):
    """technician is blocked from list_users endpoint."""
    from app.api.deps import require_roles

    dep = require_roles(UserRole.super_admin, UserRole.company_admin)

    with pytest.raises(HTTPException) as exc:
        dep(technician)

    assert exc.value.status_code == 403


# ---------------------------------------------------------------------------
# US-02: company_admin creates technician — 201
# ---------------------------------------------------------------------------


def test_us02_company_admin_creates_technician(db_session, company_admin):
    """company_admin can create a technician."""
    from app.api.routes.users import create_user

    body = UserCreateBody(
        email="newtech@crud.test",
        full_name="New Technician",
        role=UserRole.technician,
        password="secure123",
    )

    result = create_user(body, db_session, company_admin, company_admin)
    new_user = result.user

    assert new_user.email == "newtech@crud.test"
    assert new_user.role == UserRole.technician
    assert new_user.tenant_id == company_admin.tenant_id
    assert new_user.is_active is True


def test_us02_company_admin_creates_site_manager(db_session, company_admin):
    """company_admin can create a site_manager."""
    from app.api.routes.users import create_user

    body = UserCreateBody(
        email="newsmgr@crud.test",
        full_name="New Site Manager",
        role=UserRole.site_manager,
        password="secure123",
    )

    result = create_user(body, db_session, company_admin, company_admin)
    assert result.user.role == UserRole.site_manager


def test_us02_company_admin_cannot_create_super_admin(db_session, company_admin):
    """company_admin cannot create super_admin — 403."""
    from app.api.routes.users import create_user

    body = UserCreateBody(
        email="badsuper@crud.test",
        full_name="Bad Super",
        role=UserRole.super_admin,
        password="secure123",
    )

    with pytest.raises(HTTPException) as exc:
        create_user(body, db_session, company_admin, company_admin)

    assert exc.value.status_code == 403


def test_us02_company_admin_cannot_create_company_admin(db_session, company_admin):
    """company_admin cannot create another company_admin — 403."""
    from app.api.routes.users import create_user

    body = UserCreateBody(
        email="badca@crud.test",
        full_name="Bad CA",
        role=UserRole.company_admin,
        password="secure123",
    )

    with pytest.raises(HTTPException) as exc:
        create_user(body, db_session, company_admin, company_admin)

    assert exc.value.status_code == 403


def test_us02_super_admin_can_create_company_admin(db_session, super_admin):
    """super_admin can create company_admin."""
    from app.api.routes.users import create_user

    body = UserCreateBody(
        email="newca@crud.test",
        full_name="New CA",
        role=UserRole.company_admin,
        password="secure123",
    )

    result = create_user(body, db_session, super_admin, super_admin)
    assert result.user.role == UserRole.company_admin


def test_us02_duplicate_email_rejected(db_session, super_admin, technician):
    """Creating a user with existing email returns 400."""
    from app.api.routes.users import create_user

    body = UserCreateBody(
        email=technician.email,
        full_name="Duplicate",
        role=UserRole.technician,
        password="secure123",
    )

    with pytest.raises(HTTPException) as exc:
        create_user(body, db_session, super_admin, super_admin)

    assert exc.value.status_code == 400
    assert "EMAIL_ALREADY_IN_USE" in exc.value.detail


# ---------------------------------------------------------------------------
# US-03: PATCH /users/me — full_name + password change; username unchanged
# ---------------------------------------------------------------------------


def test_us03_patch_me_full_name(db_session, technician):
    """User can update their full_name."""
    from app.api.routes.users import patch_me

    original_username = technician.username

    body = UserPatchMe(full_name="Updated Name")
    updated = patch_me(body, db_session, technician)

    assert updated.full_name == "Updated Name"
    assert updated.username == original_username  # username unchanged


def test_us03_patch_me_password(db_session, technician):
    """User can update their password; new hash verifies correctly."""
    from app.api.routes.users import patch_me

    body = UserPatchMe(password="newpassword99")
    patch_me(body, db_session, technician)

    db_session.refresh(technician)
    assert verify_password("newpassword99", technician.password_hash)


def test_us03_patch_me_both_fields(db_session, technician):
    """User can update full_name and password in one request."""
    from app.api.routes.users import patch_me

    body = UserPatchMe(full_name="New Full Name", password="anotherpass42")
    updated = patch_me(body, db_session, technician)

    assert updated.full_name == "New Full Name"
    db_session.refresh(technician)
    assert verify_password("anotherpass42", technician.password_hash)


def test_us03_patch_me_empty_body_is_noop(db_session, technician):
    """PATCH /me with empty body changes nothing."""
    from app.api.routes.users import patch_me

    original_name = technician.full_name
    original_hash = technician.password_hash

    body = UserPatchMe()
    updated = patch_me(body, db_session, technician)

    assert updated.full_name == original_name
    db_session.refresh(technician)
    assert technician.password_hash == original_hash


# ---------------------------------------------------------------------------
# US-04: PATCH username is NOT allowed via /users/me
# ---------------------------------------------------------------------------


def test_us04_patch_me_schema_has_no_username_field():
    """UserPatchMe must not expose a username field."""
    fields = UserPatchMe.model_fields
    assert "username" not in fields, "username must not be patchable via /users/me"


def test_us04_patch_user_by_admin(db_session, super_admin, technician):
    """super_admin can patch user full_name and is_active."""
    from app.api.routes.users import patch_user

    body = UserPatchBody(full_name="Admin Updated", is_active=False)
    updated = patch_user(technician.id, body, db_session, super_admin, super_admin)

    assert updated.full_name == "Admin Updated"
    assert updated.is_active is False


def test_us04_patch_user_company_admin_cannot_edit_super_admin(
    db_session, company_admin, super_admin
):
    """company_admin cannot edit a super_admin user."""
    from app.api.routes.users import patch_user

    body = UserPatchBody(full_name="Hacked")

    with pytest.raises(HTTPException) as exc:
        patch_user(super_admin.id, body, db_session, company_admin, company_admin)

    assert exc.value.status_code == 403


def test_us04_patch_user_not_found(db_session, super_admin):
    """Patching a non-existent user returns 404."""
    from app.api.routes.users import patch_user

    body = UserPatchBody(full_name="Ghost")

    with pytest.raises(HTTPException) as exc:
        patch_user(uuid4(), body, db_session, super_admin, super_admin)

    assert exc.value.status_code == 404
