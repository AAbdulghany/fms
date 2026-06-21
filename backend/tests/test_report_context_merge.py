"""Auto-fill merge must always win over stale empty stored answers."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.core.security import hash_password
from app.models import Asset, Client, Site, Tenant, User, UserRole, WorkOrder, WorkOrderSource
from app.services.report_context import merge_report_answers


@pytest.fixture
def tenant(db_session):
    t = Tenant(id=uuid4(), name="T", status="active")
    db_session.add(t)
    db_session.commit()
    return t


@pytest.fixture
def ctx(db_session, tenant):
    client = Client(id=uuid4(), tenant_id=tenant.id, legal_name="Acme", code="AC")
    site = Site(
        id=uuid4(),
        tenant_id=tenant.id,
        client_id=client.id,
        name="Tower A",
        address_json={"address": "123 Main", "city": "Riyadh"},
    )
    asset = Asset(
        id=uuid4(),
        tenant_id=tenant.id,
        site_id=site.id,
        name="Chiller",
        label_code="CH-01",
    )
    tech = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email="tech@test.com",
        password_hash=hash_password("x"),
        full_name="Sara Tech",
        role=UserRole.technician,
        is_active=True,
    )
    wo = WorkOrder(
        id=uuid4(),
        tenant_id=tenant.id,
        client_id=client.id,
        site_id=site.id,
        asset_id=asset.id,
        assignee_user_id=tech.id,
        source=WorkOrderSource.preventive,
        title="PM01",
        opened_at=datetime(2026, 6, 22, 9, 0, tzinfo=timezone.utc),
    )
    db_session.add_all([client, site, asset, tech, wo])
    db_session.commit()
    db_session.refresh(wo)
    wo.assignee_user = tech
    wo.site = site
    wo.asset = asset
    return wo, tech


def test_merge_auto_fill_overrides_empty_stored_values(db_session, ctx):
    wo, tech = ctx
    stored = {
        "property_site_name": "",
        "property_full_address": "",
        "asset_unit_identification": "",
        "inspector_full_name": "",
        "inspection_date": "",
        "findings_defects": "مفيش",
    }
    merged = merge_report_answers(db_session, wo, tech, stored)
    assert merged["property_site_name"] == "Tower A"
    assert "123 Main" in merged["property_full_address"]
    assert merged["asset_unit_identification"] == "CH-01"
    assert merged["inspector_full_name"] == "Sara Tech"
    assert merged["inspection_date"] == "2026-06-22"
    assert merged["findings_defects"] == "مفيش"
