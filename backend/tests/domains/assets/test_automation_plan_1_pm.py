"""Automation Plan #1 — PM calendar series + next-action WO chain."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.models import (
    Asset,
    Client,
    MaintenanceSchedule,
    ReportTemplate,
    Site,
    Tenant,
    TenantSubscription,
    WorkOrder,
    WorkOrderSource,
    WorkOrderStatus,
)
from app.services.asset_lifecycle import on_work_order_completed
from app.services.maintenance_calendar import get_calendar_events
from app.services.maintenance_schedules import (
    create_schedule,
    frequency_interval_days,
    iter_projected_dues,
    normalize_frequency,
)
from app.services.platform_bootstrap import ensure_default_packages


@pytest.fixture
def tenant_bundle(db_session):
    pkgs = ensure_default_packages(db_session)
    tenant = Tenant(name="AP1 Tenant", status="active")
    db_session.add(tenant)
    db_session.flush()
    db_session.add(
        TenantSubscription(tenant_id=tenant.id, package_id=pkgs["pro"].id, status="active")
    )
    client = Client(tenant_id=tenant.id, legal_name="AP1 Client", code="AP1")
    db_session.add(client)
    db_session.flush()
    site = Site(tenant_id=tenant.id, client_id=client.id, name="AP1 Site")
    db_session.add(site)
    db_session.flush()
    tmpl = ReportTemplate(
        tenant_id=tenant.id,
        name="PM Template",
        code="PM-AP1",
        schema_json={"fields": []},
        version=1,
        is_active=True,
    )
    db_session.add(tmpl)
    db_session.flush()
    return tenant, client, site, tmpl


def test_normalize_semi_annual_and_annually():
    assert normalize_frequency("semi-annual") == "semi_annual"
    assert normalize_frequency("annually") == "yearly"
    assert frequency_interval_days("semi_annual") == 182
    assert frequency_interval_days("yearly") == 365


def test_create_schedule_seeds_next_action_wo(db_session, tenant_bundle):
    tenant, _client, site, tmpl = tenant_bundle
    asset = Asset(
        tenant_id=tenant.id,
        site_id=site.id,
        name="Pump",
        category="mech",
        installed_on=date(2026, 1, 1),
        max_age_years=2,
    )
    db_session.add(asset)
    db_session.flush()

    sched = create_schedule(
        db_session,
        tenant_id=tenant.id,
        asset_id=asset.id,
        template_id=tmpl.id,
        frequency="quarterly",
        installed_on=asset.installed_on,
    )
    db_session.flush()

    wos = list(
        db_session.query(WorkOrder).filter(
            WorkOrder.asset_id == asset.id,
            WorkOrder.source == WorkOrderSource.preventive,
        )
    )
    assert len(wos) == 1
    assert wos[0].status == WorkOrderStatus.created
    assert wos[0].template_id == tmpl.id
    assert sched.next_due_at.date() == date(2026, 4, 1)


def test_projected_dues_stop_at_eol(db_session, tenant_bundle):
    tenant, _client, site, tmpl = tenant_bundle
    asset = Asset(
        tenant_id=tenant.id,
        site_id=site.id,
        name="Fan",
        category="hvac",
        installed_on=date(2026, 1, 1),
        max_age_years=1,  # EOL 2027-01-01
    )
    db_session.add(asset)
    db_session.flush()
    sched = MaintenanceSchedule(
        tenant_id=tenant.id,
        asset_id=asset.id,
        template_id=tmpl.id,
        frequency="monthly",
        next_due_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        is_active=True,
    )
    db_session.add(sched)
    db_session.flush()

    dues = list(
        iter_projected_dues(
            sched,
            range_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            range_end=datetime(2027, 12, 31, tzinfo=timezone.utc),
            asset=asset,
        )
    )
    assert dues
    # install 2026-01-01 + 30d → first due 2026-01-31 (not walked back before that)
    assert dues[0].date() == date(2026, 1, 31)
    assert all(d.date() >= date(2026, 1, 31) for d in dues)
    assert all(d.date() <= date(2027, 1, 1) for d in dues)
    assert 11 <= len(dues) <= 13


def test_projected_dues_never_before_install():
    """Forward-only: dues must not precede (installed_on + interval)."""
    from types import SimpleNamespace

    from app.services.maintenance_schedules import _series_first_due

    asset = SimpleNamespace(
        installed_on=date(2026, 6, 15),
        max_age_years=5,
        metadata_json={},
    )
    sched = SimpleNamespace(
        frequency="monthly",
        next_due_at=datetime(2026, 7, 15, tzinfo=timezone.utc),
    )
    first = _series_first_due(sched, asset)  # type: ignore[arg-type]
    assert first.date() == date(2026, 7, 15)

    dues = list(
        iter_projected_dues(
            sched,  # type: ignore[arg-type]
            range_start=datetime(2026, 1, 1, tzinfo=timezone.utc),
            range_end=datetime(2026, 12, 31, tzinfo=timezone.utc),
            asset=asset,  # type: ignore[arg-type]
        )
    )
    assert dues[0].date() == date(2026, 7, 15)
    assert all(d.date() >= date(2026, 7, 15) for d in dues)


def test_completing_pm_creates_next_action(db_session, tenant_bundle):
    tenant, _client, site, tmpl = tenant_bundle
    asset = Asset(
        tenant_id=tenant.id,
        site_id=site.id,
        name="Chiller",
        category="hvac",
        installed_on=date.today() - timedelta(days=30),
        max_age_years=10,
    )
    db_session.add(asset)
    db_session.flush()
    sched = create_schedule(
        db_session,
        tenant_id=tenant.id,
        asset_id=asset.id,
        template_id=tmpl.id,
        frequency="monthly",
        installed_on=asset.installed_on,
    )
    first = (
        db_session.query(WorkOrder)
        .filter(WorkOrder.asset_id == asset.id, WorkOrder.source == WorkOrderSource.preventive)
        .one()
    )
    first.status = WorkOrderStatus.completed
    db_session.flush()

    on_work_order_completed(db_session, first)
    db_session.flush()

    open_wos = (
        db_session.query(WorkOrder)
        .filter(
            WorkOrder.asset_id == asset.id,
            WorkOrder.source == WorkOrderSource.preventive,
            WorkOrder.status == WorkOrderStatus.created,
        )
        .all()
    )
    assert len(open_wos) == 1
    assert open_wos[0].id != first.id
    db_session.refresh(sched)
    assert sched.is_active is True
    assert sched.next_due_at is not None


def test_calendar_expands_year(db_session, tenant_bundle):
    tenant, client, site, tmpl = tenant_bundle
    from app.models import User, UserRole

    admin = User(
        id=uuid4(),
        tenant_id=tenant.id,
        email="ap1-admin@example.com",
        full_name="AP1 Admin",
        role=UserRole.company_admin,
        password_hash="x",
        is_active=True,
    )
    db_session.add(admin)
    asset = Asset(
        tenant_id=tenant.id,
        site_id=site.id,
        name="Boiler",
        category="mech",
        installed_on=date(2026, 1, 15),
        max_age_years=5,
    )
    db_session.add(asset)
    db_session.flush()
    create_schedule(
        db_session,
        tenant_id=tenant.id,
        asset_id=asset.id,
        template_id=tmpl.id,
        frequency="quarterly",
        installed_on=asset.installed_on,
        seed_next_action=False,
    )
    db_session.flush()

    events = get_calendar_events(
        db_session,
        tenant_id=tenant.id,
        current_user=admin,
        view="yearly",
        year=2026,
        client_id=client.id,
    )
    # quarterly from ~Apr 2026 → Apr, Jul, Oct (+ Jan 2027 out of year)
    assert len(events) >= 3
    assert all(e["asset_name"] == "Boiler" for e in events)
