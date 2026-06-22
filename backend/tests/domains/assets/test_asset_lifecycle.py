"""
Asset Lifecycle Tests - P2-F2

Tests for automatic asset lifecycle tracking and replacement work order creation.
"""

from datetime import date, timedelta
from uuid import uuid4

from app.services.asset_lifecycle import (
    check_lifecycle,
    on_work_order_completed,
    trigger_replacement,
    get_lifecycle_timeline,
)
from app.models import Asset, AssetLifecycleStatus, WorkOrder, WorkOrderStatus, WorkOrderSource


def test_lifecycle_repair_count_triggers_replacement(db_session, sample_tenant, sample_site):
    """Test that reaching max repair count creates a replacement WO."""
    # 1. Create asset with max_repair_count = 2
    asset = Asset(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        site_id=sample_site.id,
        name="AC Unit",
        category="hvac",
        max_repair_count=2,
        current_repair_count=1,
        lifecycle_status=AssetLifecycleStatus.active,
    )
    db_session.add(asset)
    db_session.commit()

    # 2. Create and complete a work order
    wo = WorkOrder(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        client_id=sample_site.client_id,
        site_id=sample_site.id,
        asset_id=asset.id,
        status=WorkOrderStatus.completed,
        source=WorkOrderSource.corrective,
        category="repair",
        title="Repair AC",
        urgency="normal",
    )
    db_session.add(wo)
    db_session.commit()

    # 3. Trigger lifecycle check
    on_work_order_completed(db_session, wo)
    db_session.commit()

    # 4. Verify asset status is now 'end_of_life'
    db_session.refresh(asset)
    assert asset.current_repair_count == 2
    assert asset.lifecycle_status == AssetLifecycleStatus.end_of_life

    # 5. Verify a replacement Work Order was auto-created
    replacement_wo = db_session.query(WorkOrder).filter(
        WorkOrder.category == "replacement",
        WorkOrder.asset_id == asset.id,
    ).first()
    assert replacement_wo is not None
    assert replacement_wo.source == WorkOrderSource.corrective
    assert "end of life" in replacement_wo.description.lower()


def test_lifecycle_age_triggers_end_of_life(db_session, sample_tenant, sample_site):
    """Test that reaching max age sets lifecycle status to end_of_life."""
    # 1. Create asset installed 6 years ago with max_age_years = 5
    asset = Asset(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        site_id=sample_site.id,
        name="Old Chiller",
        category="hvac",
        installed_on=date.today() - timedelta(days=365 * 6),
        max_age_years=5,
        lifecycle_status=AssetLifecycleStatus.active,
    )
    db_session.add(asset)
    db_session.commit()

    # 2. Check lifecycle
    status = check_lifecycle(db_session, asset.id)
    db_session.commit()

    # 3. Verify status is end_of_life
    assert status == AssetLifecycleStatus.end_of_life
    db_session.refresh(asset)
    assert asset.lifecycle_status == AssetLifecycleStatus.end_of_life


def test_lifecycle_warning_at_80_percent(db_session, sample_tenant, sample_site):
    """Test that warning status is set at 80% of limits."""
    # Asset at 80% of max repairs
    asset = Asset(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        site_id=sample_site.id,
        name="Pump",
        category="plumbing",
        max_repair_count=5,
        current_repair_count=4,  # 80%
        lifecycle_status=AssetLifecycleStatus.active,
    )
    db_session.add(asset)
    db_session.commit()

    status = check_lifecycle(db_session, asset.id)
    assert status == AssetLifecycleStatus.warning


def test_get_lifecycle_timeline(db_session, sample_tenant, sample_site):
    """Test lifecycle timeline data retrieval."""
    asset = Asset(
        id=uuid4(),
        tenant_id=sample_tenant.id,
        site_id=sample_site.id,
        name="Fire Alarm",
        category="safety",
        max_repair_count=3,
        current_repair_count=2,
        max_age_years=10,
        installed_on=date.today() - timedelta(days=365 * 3),
        lifecycle_status=AssetLifecycleStatus.active,
    )
    db_session.add(asset)
    db_session.commit()

    timeline = get_lifecycle_timeline(db_session, asset.id)
    
    assert timeline["asset_id"] == str(asset.id)
    assert timeline["name"] == "Fire Alarm"
    assert timeline["lifecycle_status"] == "active"
    assert timeline["repairs"]["current"] == 2
    assert timeline["repairs"]["max"] == 3
    assert timeline["age"]["max_years"] == 10
    assert timeline["age"]["current_years"] is not None