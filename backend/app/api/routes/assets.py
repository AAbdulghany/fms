from typing import Annotated

from datetime import date, datetime, timezone, timedelta
from uuid import UUID



from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status

from sqlalchemy import select

from sqlalchemy.orm import Session, joinedload, selectinload



from app.api.deps import ensure_site_access, get_current_user, require_feature, require_roles

from app.database import get_db

from app.models import Asset, AssetLifecycleStatus, MaintenanceSchedule, Site, User, UserRole, UserSiteScope

from app.schemas import (

    AssetCreate,

    AssetImportPreview,

    AssetOut,

    AssetUpdate,

    MaintenanceCalendarEventOut,

    MaintenanceScheduleCreate,

    MaintenanceScheduleOut,

)

from app.services.asset_import import commit_import, preview_import

from app.services.asset_labels import generate_label_code, qr_payload_for_asset

from app.services.asset_lifecycle import get_lifecycle_timeline, reset_asset_lifecycle

from app.services.asset_metadata import expected_eol_date, read_asset_meta, write_asset_meta

from app.services.audit import write_audit

from app.services.maintenance_schedules import create_schedule

from app.services.maintenance_calendar import get_calendar_events

from app.services.pdf import render_asset_label_pdf



router = APIRouter(
    prefix="/assets",
    tags=["assets"],
    dependencies=[Depends(require_feature("assets"))],
)



_write = Depends(require_roles(UserRole.super_admin, UserRole.company_admin, UserRole.site_manager))





def _access_asset(db: Session, current: User, asset_id: UUID) -> Asset:

    asset = db.get(Asset, asset_id)

    if not asset or asset.tenant_id != current.tenant_id:

        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")

    if current.role == UserRole.site_manager:

        scoped = db.scalars(select(UserSiteScope.site_id).where(UserSiteScope.user_id == current.id)).all()

        if scoped and asset.site_id not in scoped:

            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")

    if current.role == UserRole.client_admin and current.client_id:

        site = db.get(Site, asset.site_id)

        if not site or site.client_id != current.client_id:

            raise HTTPException(status.HTTP_403_FORBIDDEN, detail="FORBIDDEN")

    return asset





def _asset_to_out(asset: Asset) -> AssetOut:

    next_due = None

    active_schedules = [s for s in (asset.schedules or []) if s.is_active]

    if active_schedules:

        next_due = min(s.next_due_at for s in active_schedules)

    meta = read_asset_meta(asset)

    site_name = None
    company_name = None
    site = getattr(asset, "site", None)
    if site is not None:
        site_name = site.name
        client = getattr(site, "client", None)
        if client is not None:
            company_name = client.legal_name

    return AssetOut(

        id=asset.id,

        site_id=asset.site_id,

        location_id=asset.location_id,

        name=asset.name,

        category=asset.category,

        model=asset.model,

        serial=asset.serial,

        installed_on=asset.installed_on,

        warranty_until=asset.warranty_until,

        max_repair_count=asset.max_repair_count,

        max_age_years=asset.max_age_years,

        current_repair_count=asset.current_repair_count,

        lifecycle_status=asset.lifecycle_status,

        label_code=asset.label_code,

        qr_payload=asset.qr_payload,

        next_due_at=next_due,

        floor=meta["floor"],

        room=meta["room"],

        smart_labels=meta["smart_labels"],

        criticality=meta["criticality"],

        last_maintenance_date=meta["last_maintenance_date"],

        schedules=[MaintenanceScheduleOut.model_validate(s) for s in active_schedules],

        company_name=company_name,

        site_name=site_name,

        expected_eol_date=expected_eol_date(asset),

        is_spare=meta["is_spare"],

        photo_url=meta.get("photo_url"),

    )





@router.get("", response_model=list[AssetOut])

def list_assets(

    db: Annotated[Session, Depends(get_db)],

    current: Annotated[User, Depends(get_current_user)],

    site_id: UUID | None = Query(None),

    category: str | None = Query(None),

    search: str | None = Query(None),

    view: str | None = Query(None),

    sort: str | None = Query(None),

    maintenance_filter: str | None = Query(None, alias="filter"),

    include_retired: bool = Query(False),

) -> list[AssetOut]:

    q = select(Asset).where(Asset.tenant_id == current.tenant_id).options(
        selectinload(Asset.schedules),
        joinedload(Asset.site).joinedload(Site.client),
    )

    if not include_retired:
        q = q.where(Asset.lifecycle_status != AssetLifecycleStatus.replaced)



    if current.role == UserRole.site_manager:

        scoped = db.scalars(select(UserSiteScope.site_id).where(UserSiteScope.user_id == current.id)).all()

        if not scoped:

            return []

        q = q.where(Asset.site_id.in_(scoped))

    if current.role == UserRole.client_admin and current.client_id:

        site_rows = db.scalars(select(Site.id).where(Site.client_id == current.client_id)).all()

        if not site_rows:

            return []

        q = q.where(Asset.site_id.in_(site_rows))



    if site_id:

        q = q.where(Asset.site_id == site_id)

    if category:

        q = q.where(Asset.category == category)

    if search:

        q = q.where(Asset.name.ilike(f"%{search}%"))



    assets = list(db.scalars(q).all())

    _view = view if isinstance(view, str) else None
    _sort = sort if isinstance(sort, str) else None
    _filter = maintenance_filter if isinstance(maintenance_filter, str) else None

    if _view == "maintenance" or _sort == "next_due" or _filter:

        now = datetime.now(timezone.utc)



        def _active_schedules(a: Asset):
            return [s for s in (a.schedules or []) if s.is_active]

        def _next_due(a: Asset):
            active = _active_schedules(a)
            if not active:
                return None
            return min(s.next_due_at for s in active)



        if _view == "maintenance" or _sort == "next_due" or _filter:
            assets = [a for a in assets if _active_schedules(a)]

        if _filter == "overdue":
            assets = [
                a for a in assets
                if (due := _next_due(a)) is not None and due <= now
            ]
        elif _filter == "due_week":
            week = now + timedelta(days=7)
            assets = [
                a for a in assets
                if (due := _next_due(a)) is not None and now <= due <= week
            ]
        elif _filter == "due_month":
            month = now + timedelta(days=30)
            assets = [
                a for a in assets
                if (due := _next_due(a)) is not None and now <= due <= month
            ]

        assets.sort(key=lambda a: _next_due(a) or datetime.max.replace(tzinfo=timezone.utc))



    return [_asset_to_out(a) for a in assets]





@router.get("/maintenance-calendar", response_model=list[MaintenanceCalendarEventOut])
def maintenance_calendar(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    view: str = Query("quarterly"),
    year: int | None = Query(None),
    month: int | None = Query(None, ge=1, le=12),
    client_id: UUID | None = Query(None),
) -> list[MaintenanceCalendarEventOut]:
    events = get_calendar_events(
        db,
        tenant_id=current.tenant_id,
        current_user=current,
        view=view,
        year=year,
        month=month,
        client_id=client_id,
    )
    normalized = []
    y = year or datetime.now(timezone.utc).year
    view_mode = view if view in ("quarterly", "yearly", "monthly") else "quarterly"
    for e in events:
        bucket = e["bucket"]
        if isinstance(bucket, int):
            if view_mode == "quarterly":
                bucket = f"Q{bucket}"
            else:
                bucket = str(bucket)
        due = e["due_at"]
        if isinstance(due, str):
            due = datetime.fromisoformat(due.replace("Z", "+00:00"))
        normalized.append(
            {
                **e,
                "asset_id": UUID(e["asset_id"]) if isinstance(e["asset_id"], str) else e["asset_id"],
                "site_id": UUID(e["site_id"]) if isinstance(e["site_id"], str) else e["site_id"],
                "client_id": UUID(e["client_id"]) if isinstance(e["client_id"], str) else e["client_id"],
                "schedule_id": UUID(e["schedule_id"]) if isinstance(e["schedule_id"], str) else e["schedule_id"],
                "due_at": due,
                "bucket": str(bucket),
                "year": y,
                "view": view_mode,
            }
        )
    return [MaintenanceCalendarEventOut.model_validate(e) for e in normalized]





@router.post("", response_model=AssetOut)

def create_asset(

    body: AssetCreate,

    db: Annotated[Session, Depends(get_db)],

    current: Annotated[User, Depends(get_current_user)],

    _: Annotated[User, _write],

) -> AssetOut:

    ensure_site_access(db, current, body.site_id)

    if body.location_id:

        from app.models import Location



        loc = db.get(Location, body.location_id)

        if not loc or loc.tenant_id != current.tenant_id or loc.site_id != body.site_id:

            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_LOCATION")

    label = generate_label_code(

        db, tenant_id=current.tenant_id, site_id=body.site_id, category=body.category

    )

    a = Asset(

        tenant_id=current.tenant_id,

        site_id=body.site_id,

        location_id=body.location_id,

        parent_asset_id=body.parent_asset_id,

        name=body.name,

        category=body.category,

        model=body.model,

        serial=body.serial,

        installed_on=body.installed_on,

        warranty_until=body.warranty_until,

        max_repair_count=body.max_repair_count,

        max_age_years=body.max_age_years,

        label_code=label,

    )

    db.add(a)

    db.flush()

    write_asset_meta(
        a,
        floor=body.floor,
        room=body.room,
        smart_labels=body.smart_labels,
        criticality=body.criticality,
        last_maintenance_date=body.last_maintenance_date,
        is_spare=body.is_spare if body.is_spare else None,
    )

    a.qr_payload = qr_payload_for_asset(a.id)

    if body.schedule:

        try:

            create_schedule(

                db,

                tenant_id=current.tenant_id,

                asset_id=a.id,

                template_id=body.schedule.template_id,

                frequency=body.schedule.frequency,

                custom_days=body.schedule.custom_days,

                last_maintenance_date=body.last_maintenance_date,

                installed_on=body.installed_on,

            )

        except ValueError:

            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_SCHEDULE")

    write_audit(

        db,

        tenant_id=current.tenant_id,

        actor=current,

        action="create",

        entity_type="asset",

        entity_id=str(a.id),

        after={"name": body.name, "label_code": label},

    )

    db.commit()

    db.refresh(a)

    _ = a.schedules

    return _asset_to_out(a)







@router.get("/{asset_id}", response_model=AssetOut)

def get_asset(

    asset_id: UUID,

    db: Annotated[Session, Depends(get_db)],

    current: Annotated[User, Depends(get_current_user)],

) -> AssetOut:

    asset = _access_asset(db, current, asset_id)
    asset = db.execute(
        select(Asset)
        .where(Asset.id == asset.id)
        .options(
            selectinload(Asset.schedules),
            joinedload(Asset.site).joinedload(Site.client),
        )
    ).scalar_one()

    return _asset_to_out(asset)





@router.patch("/{asset_id}", response_model=AssetOut)
def update_asset(
    asset_id: UUID,
    body: AssetUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _write],
) -> AssetOut:
    asset = _access_asset(db, current, asset_id)
    if asset.lifecycle_status == AssetLifecycleStatus.replaced:
        if body.lifecycle_status != AssetLifecycleStatus.replaced:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="ASSET_RETIRED")

    if body.name is not None:
        asset.name = body.name.strip()
    if body.category is not None:
        asset.category = body.category.strip()
    if body.model is not None:
        asset.model = body.model
    if body.serial is not None:
        asset.serial = body.serial
    if body.installed_on is not None:
        asset.installed_on = body.installed_on
    if body.warranty_until is not None:
        asset.warranty_until = body.warranty_until
    if body.max_repair_count is not None:
        asset.max_repair_count = body.max_repair_count
    if body.max_age_years is not None:
        asset.max_age_years = body.max_age_years

    if body.lifecycle_status is not None:
        asset.lifecycle_status = body.lifecycle_status

    write_asset_meta(
        asset,
        floor=body.floor,
        room=body.room,
        smart_labels=body.smart_labels,
        criticality=body.criticality,
        last_maintenance_date=body.last_maintenance_date,
        is_spare=body.is_spare,
    )

    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="update",
        entity_type="asset",
        entity_id=str(asset.id),
        after={"name": asset.name},
    )
    db.commit()
    db.refresh(asset)
    _ = asset.schedules
    return _asset_to_out(asset)


@router.post("/{asset_id}/retire", response_model=AssetOut)
def retire_asset(
    asset_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _write],
) -> AssetOut:
    asset = _access_asset(db, current, asset_id)
    if asset.lifecycle_status == AssetLifecycleStatus.replaced:
        return _asset_to_out(asset)
    asset.lifecycle_status = AssetLifecycleStatus.replaced
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="retire",
        entity_type="asset",
        entity_id=str(asset.id),
        after={"lifecycle_status": asset.lifecycle_status.value},
    )
    db.commit()
    db.refresh(asset)
    _ = asset.schedules
    return _asset_to_out(asset)





@router.get("/{asset_id}/schedules", response_model=list[MaintenanceScheduleOut])

def list_schedules(

    asset_id: UUID,

    db: Annotated[Session, Depends(get_db)],

    current: Annotated[User, Depends(get_current_user)],

) -> list[MaintenanceScheduleOut]:

    asset = _access_asset(db, current, asset_id)

    rows = db.scalars(select(MaintenanceSchedule).where(MaintenanceSchedule.asset_id == asset.id)).all()

    return [MaintenanceScheduleOut.model_validate(r) for r in rows]





@router.post("/{asset_id}/ai-scheduling/stub", status_code=status.HTTP_501_NOT_IMPLEMENTED)
def ai_scheduling_stub(
    asset_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, Depends(require_feature("ai_maintenance"))],
) -> None:
    """Placeholder for future AI scheduling — never calls external services (NT-116)."""
    _access_asset(db, current, asset_id)
    raise HTTPException(
        status.HTTP_501_NOT_IMPLEMENTED,
        detail="AI_SCHEDULING_NOT_AVAILABLE",
    )





@router.post("/{asset_id}/schedules", response_model=MaintenanceScheduleOut)

def add_schedule(

    asset_id: UUID,

    body: MaintenanceScheduleCreate,

    db: Annotated[Session, Depends(get_db)],

    current: Annotated[User, Depends(get_current_user)],

    _: Annotated[User, _write],

) -> MaintenanceScheduleOut:

    asset = _access_asset(db, current, asset_id)

    ensure_site_access(db, current, asset.site_id)

    try:

        sched = create_schedule(

            db,

            tenant_id=current.tenant_id,

            asset_id=asset.id,

            template_id=body.template_id,

            frequency=body.frequency,

            custom_days=body.custom_days,

        )

    except ValueError:

        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_SCHEDULE")

    db.commit()

    db.refresh(sched)

    return MaintenanceScheduleOut.model_validate(sched)





@router.get("/{asset_id}/label-sheet")

def asset_label_sheet(

    asset_id: UUID,

    db: Annotated[Session, Depends(get_db)],

    current: Annotated[User, Depends(get_current_user)],

) -> Response:

    asset = _access_asset(db, current, asset_id)

    db.refresh(asset)

    _ = asset.schedules

    pdf = render_asset_label_pdf(asset)

    return Response(

        content=pdf,

        media_type="application/pdf",

        headers={"Content-Disposition": f'inline; filename="label-{asset.label_code or asset.id}.pdf"'},

    )





@router.post("/import/preview", response_model=AssetImportPreview)

async def import_preview(

    db: Annotated[Session, Depends(get_db)],

    current: Annotated[User, Depends(get_current_user)],

    _: Annotated[User, _write],

    __: Annotated[User, Depends(require_feature("csv_import"))],

    file: UploadFile = File(...),

) -> AssetImportPreview:

    content = (await file.read()).decode("utf-8-sig", errors="replace")

    result = preview_import(db, current.tenant_id, content)

    return AssetImportPreview.model_validate(result)





@router.post("/import")

async def import_commit(

    db: Annotated[Session, Depends(get_db)],

    current: Annotated[User, Depends(get_current_user)],

    _: Annotated[User, _write],

    __: Annotated[User, Depends(require_feature("csv_import"))],

    file: UploadFile = File(...),

) -> dict[str, int]:

    content = (await file.read()).decode("utf-8-sig", errors="replace")

    try:

        result = commit_import(db, current.tenant_id, content)

    except ValueError:

        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="VALIDATION_ERRORS")

    db.commit()

    return result





@router.get("/{asset_id}/lifecycle")

def get_asset_lifecycle(

    asset_id: UUID,

    db: Annotated[Session, Depends(get_db)],

    current: Annotated[User, Depends(get_current_user)],

) -> dict:

    """Get asset lifecycle timeline and status (P2-F2)."""

    asset = _access_asset(db, current, asset_id)



    try:

        timeline = get_lifecycle_timeline(db, asset_id)

        return timeline

    except ValueError as e:

        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))





@router.post("/{asset_id}/reset-lifecycle", response_model=AssetOut)

def reset_lifecycle(

    asset_id: UUID,

    db: Annotated[Session, Depends(get_db)],

    current: Annotated[User, Depends(get_current_user)],

    _: Annotated[User, _write],

) -> AssetOut:

    """Reset asset lifecycle when physical asset is replaced (P2-F2)."""

    asset = db.get(Asset, asset_id)

    if not asset or asset.tenant_id != current.tenant_id:

        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")



    ensure_site_access(db, current, asset.site_id)



    try:

        reset_asset = reset_asset_lifecycle(db, asset_id)

        write_audit(

            db,

            tenant_id=current.tenant_id,

            actor=current,

            action="reset_lifecycle",

            entity_type="asset",

            entity_id=str(asset_id),

        )

        db.commit()

        db.refresh(reset_asset)

        _ = reset_asset.schedules

        return _asset_to_out(reset_asset)

    except ValueError as e:

        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(e))

