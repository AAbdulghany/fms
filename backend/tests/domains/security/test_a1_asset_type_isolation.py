"""A1 U-X-03 — tenant isolation for asset types and client_id scoping."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Client, Tenant, User, UserRole
from app.models.asset_types import AssetType
from app.core.security import hash_password
from tests.api_helpers import auth_header


def _tenant_admin(db: Session, *, email: str, tenant_name: str) -> tuple[Tenant, User]:
    tenant = Tenant(id=uuid4(), name=tenant_name, status="active")
    db.add(tenant)
    db.flush()
    user = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email=email,
        password_hash=hash_password("pw"),
        full_name="Admin",
        role=UserRole.company_admin,
        is_active=True,
    )
    db.add(user)
    db.commit()
    return tenant, user


def test_cross_tenant_asset_type_get_is_404(api_client: TestClient, db_session: Session) -> None:
    t_a, admin_a = _tenant_admin(db_session, email="a@ex.com", tenant_name="TA")
    t_b, admin_b = _tenant_admin(db_session, email="b@ex.com", tenant_name="TB")
    now = datetime.now(timezone.utc)
    foreign = AssetType(
        tenant_id=t_a.id,
        code="secret_type",
        name_en="Secret",
        name_ar="Secret",
        origin="custom",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    db_session.add(foreign)
    db_session.commit()

    resp = api_client.get(
        f"/api/v1/asset-types/{foreign.id}",
        headers=auth_header(admin_b),
    )
    assert resp.status_code == 404


def test_cross_tenant_client_id_query_is_404(api_client: TestClient, db_session: Session) -> None:
    t_a, admin_a = _tenant_admin(db_session, email="a2@ex.com", tenant_name="TA2")
    t_b, admin_b = _tenant_admin(db_session, email="b2@ex.com", tenant_name="TB2")
    foreign_client = Client(
        id=uuid4(),
        tenant_id=t_a.id,
        legal_name="Foreign Hospital",
        code="FH",
        status="active",
        activity_type="hospital",
    )
    db_session.add(foreign_client)
    db_session.commit()

    resp = api_client.get(
        f"/api/v1/asset-types?client_id={foreign_client.id}",
        headers=auth_header(admin_b),
    )
    assert resp.status_code == 404
