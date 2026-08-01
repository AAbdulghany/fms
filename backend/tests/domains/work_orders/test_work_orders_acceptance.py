"""Wave 5 tests: asset_id filter on work orders list (NT-P5-A01)."""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.core.security import hash_password
from app.models import Asset, Urgency, User, UserRole, WorkOrder, WorkOrderSource, WorkOrderStatus
from tests.api_helpers import auth_header


@pytest.fixture
def company_admin(db_session, sample_tenant):
    user = User(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        email="ca@test.com",
        password_hash=hash_password("pass"),
        full_name="Company Admin",
        role=UserRole.company_admin,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def two_assets(db_session, sample_tenant, sample_client, sample_site):
    a1 = Asset(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        site_id=sample_site.id,
        name="Asset One",
        category="HVAC",
    )
    a2 = Asset(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        site_id=sample_site.id,
        name="Asset Two",
        category="Elevator",
    )
    db_session.add_all([a1, a2])
    db_session.commit()
    return a1, a2


@pytest.fixture
def work_orders_for_assets(db_session, sample_tenant, sample_client, sample_site, two_assets):
    a1, a2 = two_assets
    wo1 = WorkOrder(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        client_id=sample_client.id,
        site_id=sample_site.id,
        asset_id=a1.id,
        source=WorkOrderSource.preventive,
        category="maintenance",
        urgency=Urgency.normal,
        status=WorkOrderStatus.created,
        title="WO for asset one",
        description="",
    )
    wo2 = WorkOrder(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        client_id=sample_client.id,
        site_id=sample_site.id,
        asset_id=a2.id,
        source=WorkOrderSource.preventive,
        category="repair",
        urgency=Urgency.normal,
        status=WorkOrderStatus.in_progress,
        title="WO for asset two",
        description="",
    )
    wo3 = WorkOrder(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        client_id=sample_client.id,
        site_id=sample_site.id,
        asset_id=a1.id,
        source=WorkOrderSource.preventive,
        category="maintenance",
        urgency=Urgency.urgent,
        status=WorkOrderStatus.completed,
        title="Completed for asset one",
        description="",
    )
    db_session.add_all([wo1, wo2, wo3])
    db_session.commit()
    return wo1, wo2, wo3


def test_list_work_orders_filters_by_asset_id(
    api_client, company_admin, two_assets, work_orders_for_assets
):
    a1, _ = two_assets
    resp = api_client.get(
        f"/api/v1/work-orders?asset_id={a1.id}",
        headers=auth_header(company_admin),
    )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert len(data) == 2
    assert all(row["asset_id"] == str(a1.id) for row in data)


def test_list_work_orders_without_asset_id_returns_all(
    api_client, company_admin, work_orders_for_assets
):
    resp = api_client.get("/api/v1/work-orders", headers=auth_header(company_admin))
    assert resp.status_code == 200
    assert len(resp.json()["data"]) == 3
