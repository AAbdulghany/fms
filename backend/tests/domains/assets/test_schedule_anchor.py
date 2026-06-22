"""Wave 4 Lane A — NT-P2-A02: Schedule anchor from install date.

Architect decision A1:
  - last_maintenance_date set  → base = last_maintenance_date + interval
  - last_maintenance_date null, installed_on set → base = installed_on + interval
  - Both null → base = today + interval
  - If computed next_due_at is in the past → leave overdue (do NOT skip to today+interval)

Key example: Install 2026-05-13, monthly (30 d), today 2026-06-20
    → next_due_at = 2026-06-12  (overdue, NOT 2026-07-20)
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.models import Asset, MaintenanceSchedule, ReportTemplate, Site, Tenant, TenantSubscription
from app.services.maintenance_schedules import create_schedule, compute_next_due
from app.services.platform_bootstrap import ensure_default_packages


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tenant_with_subscription(db_session):
    pkgs = ensure_default_packages(db_session)
    tenant = Tenant(name="Anchor Test Tenant", status="active")
    db_session.add(tenant)
    db_session.flush()
    db_session.add(
        TenantSubscription(tenant_id=tenant.id, package_id=pkgs["pro"].id, status="active")
    )
    db_session.flush()
    return tenant


@pytest.fixture
def report_template(db_session, tenant_with_subscription):
    tmpl = ReportTemplate(
        tenant_id=tenant_with_subscription.id,
        name="Anchor Test Template",
        code="ANCHOR-TEST",
        schema_json={"fields": []},
        version=1,
        is_active=True,
    )
    db_session.add(tmpl)
    db_session.flush()
    return tmpl


@pytest.fixture
def asset(db_session, tenant_with_subscription):
    """Asset without a site (schedules don't need a site to be created)."""
    from app.models import Client

    client = Client(
        tenant_id=tenant_with_subscription.id,
        legal_name="Anchor Client",
        code="ANC-001",
    )
    db_session.add(client)
    db_session.flush()

    site = Site(
        tenant_id=tenant_with_subscription.id,
        client_id=client.id,
        name="Anchor Site",
    )
    db_session.add(site)
    db_session.flush()

    a = Asset(
        tenant_id=tenant_with_subscription.id,
        site_id=site.id,
        name="Test HVAC",
        category="HVAC",
    )
    db_session.add(a)
    db_session.flush()
    return a


# ---------------------------------------------------------------------------
# Unit tests — compute_next_due
# ---------------------------------------------------------------------------


def test_compute_next_due_from_explicit_base():
    """compute_next_due uses the supplied from_dt, not today."""
    base = datetime(2026, 5, 13, tzinfo=timezone.utc)
    result = compute_next_due("monthly", from_dt=base)
    assert result == datetime(2026, 6, 12, tzinfo=timezone.utc)


def test_compute_next_due_weekly():
    base = datetime(2026, 5, 13, tzinfo=timezone.utc)
    result = compute_next_due("weekly", from_dt=base)
    assert result == datetime(2026, 5, 20, tzinfo=timezone.utc)


def test_compute_next_due_custom_days():
    base = datetime(2026, 5, 1, tzinfo=timezone.utc)
    result = compute_next_due("custom", custom_days=45, from_dt=base)
    assert result == datetime(2026, 6, 15, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Integration tests — create_schedule anchor priority
# ---------------------------------------------------------------------------


def test_schedule_anchor_installed_on_monthly(db_session, tenant_with_subscription, report_template, asset):
    """A1 core: May-13 install + monthly → June-12 due (overdue on June-20)."""
    installed = date(2026, 5, 13)
    sched = create_schedule(
        db_session,
        tenant_id=tenant_with_subscription.id,
        asset_id=asset.id,
        template_id=report_template.id,
        frequency="monthly",
        installed_on=installed,
    )
    expected = datetime(2026, 6, 12, tzinfo=timezone.utc)
    assert sched.next_due_at == expected, (
        f"Expected {expected} but got {sched.next_due_at}. "
        "Schedule must anchor to installed_on, not today."
    )


def test_schedule_anchor_overdue_not_bumped(db_session, tenant_with_subscription, report_template, asset):
    """A1 rule 2: if computed due date is in the past, leave it (do not skip to today+interval)."""
    today = datetime.now(timezone.utc).date()
    installed = today - timedelta(days=60)  # well in the past
    sched = create_schedule(
        db_session,
        tenant_id=tenant_with_subscription.id,
        asset_id=asset.id,
        template_id=report_template.id,
        frequency="monthly",
        installed_on=installed,
    )
    now = datetime.now(timezone.utc)
    assert sched.next_due_at < now, (
        "next_due_at should be in the past (overdue) when installed_on anchor is 60 days ago and interval is 30 days."
    )


def test_schedule_anchor_last_maintenance_takes_priority(db_session, tenant_with_subscription, report_template, asset):
    """last_maintenance_date beats installed_on when both provided."""
    installed = date(2026, 5, 13)
    last_maint = date(2026, 6, 1)
    sched = create_schedule(
        db_session,
        tenant_id=tenant_with_subscription.id,
        asset_id=asset.id,
        template_id=report_template.id,
        frequency="monthly",
        last_maintenance_date=last_maint,
        installed_on=installed,
    )
    # Should be anchored to last_maint (June 1), not installed (May 13)
    expected = datetime(2026, 7, 1, tzinfo=timezone.utc)
    assert sched.next_due_at == expected


def test_schedule_anchor_both_null_uses_today(db_session, tenant_with_subscription, report_template, asset):
    """When both last_maintenance_date and installed_on are null, anchor = today."""
    before = datetime.now(timezone.utc)
    sched = create_schedule(
        db_session,
        tenant_id=tenant_with_subscription.id,
        asset_id=asset.id,
        template_id=report_template.id,
        frequency="monthly",
    )
    after = datetime.now(timezone.utc)
    # next_due_at should be roughly today + 30 days
    lower = before + timedelta(days=29)
    upper = after + timedelta(days=31)
    assert lower <= sched.next_due_at <= upper, (
        f"Expected next_due_at between {lower} and {upper}, got {sched.next_due_at}"
    )


def test_schedule_anchor_installed_on_quarterly(db_session, tenant_with_subscription, report_template, asset):
    """Quarterly interval: Jan-1 install → Apr-1 first due."""
    installed = date(2026, 1, 1)
    sched = create_schedule(
        db_session,
        tenant_id=tenant_with_subscription.id,
        asset_id=asset.id,
        template_id=report_template.id,
        frequency="quarterly",
        installed_on=installed,
    )
    expected = datetime(2026, 4, 1, tzinfo=timezone.utc)
    assert sched.next_due_at == expected


def test_schedule_no_installed_on_no_last_maint_not_overdue(db_session, tenant_with_subscription, report_template, asset):
    """Baseline: no install date → next_due_at is in the future."""
    sched = create_schedule(
        db_session,
        tenant_id=tenant_with_subscription.id,
        asset_id=asset.id,
        template_id=report_template.id,
        frequency="weekly",
    )
    now = datetime.now(timezone.utc)
    assert sched.next_due_at > now
