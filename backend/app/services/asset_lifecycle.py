"""Asset Lifecycle Management Service - P2-F2

Tracks asset repair counts and age, automatically creating replacement
work orders when lifecycle limits are reached.
"""

from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Asset, AssetLifecycleStatus, WorkOrder, WorkOrderSource


def check_lifecycle(db: Session, asset_id: UUID) -> AssetLifecycleStatus:
    """
    Evaluate asset lifecycle status based on repair count and age.
    
    Returns:
        AssetLifecycleStatus: active, warning, end_of_life, or replaced
    """
    asset = db.get(Asset, asset_id)
    if not asset:
        raise ValueError(f"Asset {asset_id} not found")
    
    # Check if already replaced
    if asset.lifecycle_status == AssetLifecycleStatus.replaced:
        return AssetLifecycleStatus.replaced
    
    at_repair_limit = False
    at_age_limit = False
    
    # Check repair count
    if asset.max_repair_count is not None:
        if asset.current_repair_count >= asset.max_repair_count:
            at_repair_limit = True
    
    # Check age
    if asset.max_age_years is not None and asset.installed_on:
        today = date.today()
        age_years = (today - asset.installed_on).days / 365.25
        if age_years >= asset.max_age_years:
            at_age_limit = True
    
    # Determine status
    if at_repair_limit or at_age_limit:
        new_status = AssetLifecycleStatus.end_of_life
    elif asset.max_repair_count and asset.current_repair_count >= asset.max_repair_count * 0.8:
        new_status = AssetLifecycleStatus.warning
    elif asset.max_age_years and asset.installed_on:
        today = date.today()
        age_years = (today - asset.installed_on).days / 365.25
        if age_years >= asset.max_age_years * 0.8:
            new_status = AssetLifecycleStatus.warning
        else:
            new_status = AssetLifecycleStatus.active
    else:
        new_status = AssetLifecycleStatus.active
    
    # Update if changed
    if new_status != asset.lifecycle_status:
        asset.lifecycle_status = new_status
        db.add(asset)
    
    return new_status


def trigger_replacement(db: Session, asset: Asset) -> WorkOrder:
    """
    Auto-create a replacement work order when asset reaches end of life.
    
    Returns:
        WorkOrder: The newly created replacement work order
    """
    # Check if replacement WO already exists
    existing = db.scalars(
        select(WorkOrder)
        .where(
            WorkOrder.tenant_id == asset.tenant_id,
            WorkOrder.asset_id == asset.id,
            WorkOrder.category == "replacement",
        )
        .order_by(WorkOrder.opened_at.desc())
        .limit(1)
    ).first()
    
    if existing:
        return existing
    
    # Create replacement work order
    reasons = []
    if asset.max_repair_count and asset.current_repair_count >= asset.max_repair_count:
        reasons.append(f"Max repair count reached ({asset.current_repair_count}/{asset.max_repair_count})")
    if asset.max_age_years and asset.installed_on:
        age_years = (date.today() - asset.installed_on).days / 365.25
        reasons.append(f"Max age reached ({age_years:.1f}/{asset.max_age_years} years)")
    
    description = f"Asset '{asset.name}' (ID: {asset.id}) has reached end of life.\n" + "\n".join(f"- {r}" for r in reasons)
    
    # Get client_id from the asset's site
    from app.models import Site
    site = db.get(Site, asset.site_id)
    if not site:
        raise ValueError(f"Site {asset.site_id} not found for asset {asset.id}")
    
    replacement_wo = WorkOrder(
        tenant_id=asset.tenant_id,
        client_id=site.client_id,
        site_id=asset.site_id,
        asset_id=asset.id,
        source=WorkOrderSource.corrective,
        category="replacement",
        urgency="normal",
        status="created",
        title=f"Replace Asset: {asset.name}",
        description=description,
        opened_at=datetime.now(timezone.utc),
    )
    
    db.add(replacement_wo)
    db.flush()  # Get the ID without committing
    
    return replacement_wo


def on_work_order_completed(db: Session, work_order: WorkOrder) -> None:
    """
    Hook to call when a work order is completed.
    Increments asset repair count and checks lifecycle.
    """
    if not work_order.asset_id:
        return
    
    asset = db.get(Asset, work_order.asset_id)
    if not asset:
        return
    
    # Skip if this is a replacement work order
    if work_order.category == "replacement":
        return
    
    # Increment repair count
    asset.current_repair_count += 1
    db.add(asset)
    
    # Check lifecycle
    status = check_lifecycle(db, asset.id)
    
    # If end of life, trigger replacement
    if status == AssetLifecycleStatus.end_of_life:
        trigger_replacement(db, asset)


def reset_asset_lifecycle(db: Session, asset_id: UUID) -> Asset:
    """
    Reset asset lifecycle when physical asset is replaced.
    Sets lifecycle_status to 'replaced' and resets counters.
    """
    asset = db.get(Asset, asset_id)
    if not asset:
        raise ValueError(f"Asset {asset_id} not found")
    
    asset.lifecycle_status = AssetLifecycleStatus.replaced
    asset.current_repair_count = 0
    db.add(asset)
    
    return asset


def get_lifecycle_timeline(db: Session, asset_id: UUID) -> dict:
    """
    Get asset lifecycle timeline data for visualization.
    
    Returns dict with:
    - repairs: current vs max
    - age: current vs max (in years)
    - status: lifecycle_status
    - warnings: list of warning messages
    - replacement_wo_id: ID of auto-created replacement WO (if any)
    """
    asset = db.get(Asset, asset_id)
    if not asset:
        raise ValueError(f"Asset {asset_id} not found")
    
    timeline = {
        "asset_id": str(asset.id),
        "name": asset.name,
        "lifecycle_status": asset.lifecycle_status.value,
        "repairs": {
            "current": asset.current_repair_count,
            "max": asset.max_repair_count,
            "percentage": (
                (asset.current_repair_count / asset.max_repair_count * 100)
                if asset.max_repair_count
                else None
            ),
        },
        "age": {
            "current_years": None,
            "max_years": asset.max_age_years,
            "percentage": None,
        },
        "warnings": [],
        "replacement_wo_id": None,
    }
    
    # Calculate age
    if asset.installed_on:
        age_years = (date.today() - asset.installed_on).days / 365.25
        timeline["age"]["current_years"] = round(age_years, 1)
        if asset.max_age_years:
            timeline["age"]["percentage"] = round(age_years / asset.max_age_years * 100, 1)
    
    # Check for warnings
    if asset.max_repair_count and asset.current_repair_count >= asset.max_repair_count * 0.8:
        timeline["warnings"].append(
            f"Approaching max repair count ({asset.current_repair_count}/{asset.max_repair_count})"
        )
    
    if asset.max_age_years and asset.installed_on:
        age_years = (date.today() - asset.installed_on).days / 365.25
        if age_years >= asset.max_age_years * 0.8:
            timeline["warnings"].append(
                f"Approaching max age ({age_years:.1f}/{asset.max_age_years} years)"
            )
    
    # Check for replacement WO
    if asset.lifecycle_status == AssetLifecycleStatus.end_of_life:
        replacement_wo = db.scalars(
            select(WorkOrder)
            .where(
                WorkOrder.tenant_id == asset.tenant_id,
                WorkOrder.asset_id == asset.id,
                WorkOrder.category == "replacement",
            )
            .order_by(WorkOrder.opened_at.desc())
            .limit(1)
        ).first()
        if replacement_wo:
            timeline["replacement_wo_id"] = str(replacement_wo.id)
    
    return timeline
