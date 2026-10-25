"""A5: downtime windows, diagnostic codes, asset WO history."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
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
        email="a5-ca@test.com",
        password_hash=hash_password("pass"),
        full_name="A5 Company Admin",
        role=UserRole.company_admin,
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def asset_with_wo(db_session, sample_tenant, sample_client, sample_site, company_admin):
    asset = Asset(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        site_id=sample_site.id,
        name="A5 Chiller",
        category="HVAC",
    )
    wo = WorkOrder(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        client_id=sample_client.id,
        site_id=sample_site.id,
        asset_id=asset.id,
        source=WorkOrderSource.corrective,
        category="repair",
        urgency=Urgency.normal,
        status=WorkOrderStatus.in_progress,
        title="Chiller down",
        description="",
        created_by_user_id=company_admin.id,
    )
    db_session.add_all([asset, wo])
    db_session.commit()
    return asset, wo


def test_diagnostic_codes_seeded(api_client, company_admin):
    r = api_client.get(
        "/api/v1/work-orders/diagnostic-codes",
        headers=auth_header(company_admin),
    )
    assert r.status_code == 200
    data = r.json()
    kinds = {row["kind"] for row in data}
    assert "failure" in kinds
    assert "symptom" in kinds
    assert any(row["code"] == "MECH_FAIL" for row in data)


def test_patch_downtime_and_codes(api_client, company_admin, asset_with_wo):
    _, wo = asset_with_wo
    start = datetime.now(timezone.utc) - timedelta(hours=2)
    end = datetime.now(timezone.utc)
    r = api_client.patch(
        f"/api/v1/work-orders/{wo.id}",
        headers=auth_header(company_admin),
        json={
            "downtime_started_at": start.isoformat(),
            "downtime_ended_at": end.isoformat(),
            "failure_code": "mech_fail",
            "symptom_code": "no_cool",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["failure_code"] == "MECH_FAIL"
    assert body["symptom_code"] == "NO_COOL"
    assert body["downtime_started_at"] is not None
    assert body["downtime_ended_at"] is not None
    assert body["downtime_minutes"] is not None
    assert body["downtime_minutes"] >= 119


def test_invalid_downtime_window(api_client, company_admin, asset_with_wo):
    _, wo = asset_with_wo
    start = datetime.now(timezone.utc)
    end = start - timedelta(hours=1)
    r = api_client.patch(
        f"/api/v1/work-orders/{wo.id}",
        headers=auth_header(company_admin),
        json={
            "downtime_started_at": start.isoformat(),
            "downtime_ended_at": end.isoformat(),
        },
    )
    assert r.status_code == 400
    assert r.json()["detail"] == "INVALID_DOWNTIME_WINDOW"


def test_asset_work_order_history(api_client, company_admin, asset_with_wo):
    asset, wo = asset_with_wo
    r = api_client.get(
        f"/api/v1/assets/{asset.id}/work-order-history",
        headers=auth_header(company_admin),
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["meta"]["total"] >= 1
    ids = {row["id"] for row in body["data"]}
    assert str(wo.id) in ids
