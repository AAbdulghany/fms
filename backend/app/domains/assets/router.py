from typing import Annotated

from datetime import date, datetime, timezone, timedelta
from uuid import UUID



from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile, status

from sqlalchemy import select

from sqlalchemy.orm import Session, joinedload, selectinload



from app.api.deps import ensure_site_access, get_current_user, require_feature, require_roles

from app.database import get_db

from app.models import (
    Asset,
    AssetLifecycleStatus,
    Client,
    MaintenanceSchedule,
    Site,
    User,
    UserRole,
    UserSiteScope,
    WorkOrder,
)

from app.schemas import (

    AssetCreate,

    AssetImportPreview,

    AssetOut,

    AssetUpdate,

    MaintenanceCalendarEventOut,

    MaintenanceScheduleCreate,

    MaintenanceScheduleOut,

    PaginatedMeta,

    PaginatedWorkOrders,

)

from app.services.asset_import import commit_import, preview_import

from app.services.asset_labels import generate_label_code, qr_payload_for_asset

from app.services.asset_lifecycle import get_lifecycle_timeline, reset_asset_lifecycle

from app.services.asset_metadata import expected_eol_date, read_asset_meta, write_asset_meta

from app.services.audit import write_audit
from app.services.asset_types import (
    apply_type_defaults,
    find_type_by_code,
    get_tenant_asset_type,
    resolve_asset_type_for_write,
)
from app.schemas.asset_types import AssetTypeRef

from app.services.maintenance_schedules import create_schedule, ensure_next_actions_for_tenant

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

    # Avoid lazy N+1 when list path deferred schedules
    _loaded = asset.__dict__.get("schedules")
    active_schedules = [s for s in (_loaded or []) if s.is_active] if _loaded is not None else []

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

        asset_type_id=asset.asset_type_id,

        asset_type=AssetTypeRef.model_validate(asset.asset_type) if asset.asset_type is not None else None,

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

    asset_type_id: UUID | None = Query(None),

    search: str | None = Query(None),

    view: str | None = Query(None),

    sort: str | None = Query(None),

    maintenance_filter: str | None = Query(None, alias="filter"),

    include_retired: bool = Query(False),

    page: int = Query(1, ge=1),

    page_size: int = Query(500, ge=1, le=1000),

) -> list[AssetOut]:

    _view = view if isinstance(view, str) else None
    _sort = sort if isinstance(sort, str) else None
    _filter = maintenance_filter if isinstance(maintenance_filter, str) else None
    need_schedules = _view == "maintenance" or _sort == "next_due" or bool(_filter)

    opts = [
        joinedload(Asset.site).joinedload(Site.client),
        joinedload(Asset.asset_type),
    ]
    if need_schedules:
        opts.insert(0, selectinload(Asset.schedules))

    q = select(Asset).where(Asset.tenant_id == current.tenant_id).options(*opts)

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

    if asset_type_id:

        q = q.where(Asset.asset_type_id == asset_type_id)

    if search:

        q = q.where(Asset.name.ilike(f"%{search}%"))



    # Soft page cap for register views; maintenance filter still pages after in-Python filter
    if not need_schedules:
        q = q.offset((page - 1) * page_size).limit(page_size)

    assets = list(db.scalars(q).unique().all())

    if need_schedules:

        now = datetime.now(timezone.utc)

        def _aware_dt(dt: datetime) -> datetime:
            if dt.tzinfo is None:
                return dt.replace(tzinfo=timezone.utc)
            return dt

        def _active_schedules(a: Asset):
            loaded = a.__dict__.get("schedules")
            return [s for s in (loaded or []) if s.is_active] if loaded is not None else []

        def _next_due(a: Asset):
            active = _active_schedules(a)
            if not active:
                return None
            return min(_aware_dt(s.next_due_at) for s in active)

        assets = [a for a in assets if _active_schedules(a)]

        if _filter == "overdue":
            assets = [
                a for a in assets
                if (due := _next_due(a)) is not None and due <= now
            ]
        elif _filter in ("due_week", "due_this_week"):
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
        start = (page - 1) * page_size
        assets = assets[start : start + page_size]



    return [_asset_to_out(a) for a in assets]





@router.post("/maintenance-schedules/ensure-next-actions")
def ensure_next_maintenance_actions(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Seed missing next-event preventive WOs for all active schedules (no dummy reminders)."""
    created = ensure_next_actions_for_tenant(db, current.tenant_id)
    db.commit()
    return {"created": created}


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

    resolved = resolve_asset_type_for_write(
        db,
        tenant_id=current.tenant_id,
        asset_type_id=body.asset_type_id,
        category=body.category,
        asset_type_name=getattr(body, "asset_type_name", None),
    )
    defaults = apply_type_defaults(
        resolved.asset_type,
        max_age_years=body.max_age_years,
        max_repair_count=body.max_repair_count,
        criticality=body.criticality,
    )

    label = generate_label_code(

        db, tenant_id=current.tenant_id, site_id=body.site_id, category=resolved.category

    )

    a = Asset(

        tenant_id=current.tenant_id,

        site_id=body.site_id,

        location_id=body.location_id,

        parent_asset_id=body.parent_asset_id,

        name=body.name,

        category=resolved.category,

        asset_type_id=resolved.asset_type.id if resolved.asset_type else None,

        model=body.model,

        serial=body.serial,

        installed_on=body.installed_on,

        warranty_until=body.warranty_until,

        max_repair_count=defaults["max_repair_count"],

        max_age_years=defaults["max_age_years"],

        label_code=label,

    )

    db.add(a)

    db.flush()

    write_asset_meta(
        a,
        floor=body.floor,
        room=body.room,
        smart_labels=body.smart_labels,
        criticality=defaults["criticality"],
        last_maintenance_date=body.last_maintenance_date,
        is_spare=body.is_spare if body.is_spare else None,
    )

    from app.services.asset_tags import ensure_active_tag

    ensure_active_tag(db, a)

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

        after={
            "name": body.name,
            "label_code": label,
            "category": resolved.category,
            "asset_type_id": str(a.asset_type_id) if a.asset_type_id else None,
        },

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
            joinedload(Asset.asset_type),
        )
    ).scalar_one()

    return _asset_to_out(asset)


@router.get("/{asset_id}/work-order-history", response_model=PaginatedWorkOrders)
def get_asset_work_order_history(
    asset_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> PaginatedWorkOrders:
    """A5 — solid chronological WO history for an asset (gap matrix P0 / AI foundation)."""
    from sqlalchemy import func

    from app.domains.work_orders._common import _wo_load_options, _work_order_to_out

    asset = _access_asset(db, current, asset_id)
    q = select(WorkOrder).where(
        WorkOrder.tenant_id == current.tenant_id,
        WorkOrder.asset_id == asset.id,
    )
    if current.role == UserRole.technician:
        q = q.where(WorkOrder.assignee_user_id == current.id)
    if current.role == UserRole.client_admin and current.client_id:
        q = q.where(WorkOrder.client_id == current.client_id)
    if current.role == UserRole.site_manager:
        scoped = db.scalars(
            select(UserSiteScope.site_id).where(UserSiteScope.user_id == current.id)
        ).all()
        if scoped:
            q = q.where(WorkOrder.site_id.in_(scoped))
        else:
            from sqlalchemy import false

            q = q.where(false())

    total = db.scalar(select(func.count()).select_from(q.subquery()))
    rows = list(
        db.scalars(
            q.options(*_wo_load_options())
            .order_by(WorkOrder.opened_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
    )
    return PaginatedWorkOrders(
        data=[_work_order_to_out(r) for r in rows],
        meta=PaginatedMeta(page=page, page_size=page_size, total=int(total or 0)),
    )


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
    type_before = {
        "asset_type_id": str(asset.asset_type_id) if asset.asset_type_id else None,
        "category": asset.category,
    }
    if body.asset_type_id is not None:
        new_type = get_tenant_asset_type(db, current.tenant_id, body.asset_type_id)
        if new_type is None:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_ASSET_TYPE")
        if body.category is not None and body.category.strip() != new_type.code:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="ASSET_TYPE_CATEGORY_MISMATCH")
        if new_type.id != asset.asset_type_id:
            if not new_type.is_active:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="ASSET_TYPE_ARCHIVED")
            # I1: category mirrors the type code. label_code is NOT regenerated (physical sticker).
            asset.asset_type_id = new_type.id
            asset.category = new_type.code
    elif body.category is not None:
        new_category = body.category.strip()
        if asset.asset_type_id is not None:
            current_type = get_tenant_asset_type(db, current.tenant_id, asset.asset_type_id)
            if current_type is not None and new_category != current_type.code:
                raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="ASSET_TYPE_CATEGORY_MISMATCH")
        else:
            asset.category = new_category
            linked = find_type_by_code(db, current.tenant_id, new_category)
            if linked is not None:
                asset.asset_type_id = linked.id
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
        before=type_before if type_before["asset_type_id"] != (str(asset.asset_type_id) if asset.asset_type_id else None) else None,
        after={
            "name": asset.name,
            "asset_type_id": str(asset.asset_type_id) if asset.asset_type_id else None,
            "category": asset.category,
        },
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
    request: Request,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    size_mm: float | None = Query(
        default=None,
        ge=40,
        le=120,
        description="Primary size in mm: side for Design A, width for Design C.",
    ),
    design: str | None = Query(
        default=None,
        description="Sticker design: a (docked square) or c (field tag).",
    ),
    format: str | None = Query(
        default="pdf",
        description="Response format: pdf (print) or png (WYSIWYG on-screen preview).",
    ),
) -> Response:
    asset = _access_asset(db, current, asset_id)
    db.refresh(asset)
    _ = asset.schedules

    import os

    from app.config import get_settings
    from app.services.asset_label_sticker import (
        DESIGN_A,
        LABEL_SIZE_MM_DEFAULT,
        clamp_label_size_mm,
        normalize_label_design,
        sticker_pdf_to_png,
    )
    from app.services.asset_tags import absolute_qr_payload, ensure_active_tag

    ensure_active_tag(db, asset)
    db.flush()

    client_name = None
    site = db.get(Site, asset.site_id)
    if site:
        client = db.get(Client, site.client_id) if site.client_id else None
        if client:
            client_name = client.legal_name

    settings = get_settings()
    sticker_design = normalize_label_design(
        design if design is not None else getattr(settings, "asset_label_design", DESIGN_A)
    )
    default_mm = getattr(settings, "asset_label_size_mm", LABEL_SIZE_MM_DEFAULT)
    sticker_mm = clamp_label_size_mm(
        size_mm if size_mm is not None else default_mm,
        design=sticker_design,
    )

    # Same absolute URL the Vite preview encodes (PUBLIC_APP_URL or browser Origin)
    app_base = (os.environ.get("PUBLIC_APP_URL") or "").rstrip("/")
    if not app_base:
        app_base = (request.headers.get("origin") or "").rstrip("/")
    if not app_base:
        referer = request.headers.get("referer") or ""
        if referer.startswith("http"):
            from urllib.parse import urlsplit

            parts = urlsplit(referer)
            app_base = f"{parts.scheme}://{parts.netloc}"
    qr_abs = absolute_qr_payload(asset.qr_payload, app_base=app_base or None)

    pdf = render_asset_label_pdf(
        asset,
        client_name=client_name,
        size_mm=sticker_mm,
        design=sticker_design,
        qr_payload=qr_abs,
    )
    db.commit()

    fmt = (format or "pdf").strip().lower()
    no_cache = {
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache",
    }
    stem = asset.label_code or str(asset.id)
    if fmt in ("png", "image", "preview"):
        return Response(
            content=sticker_pdf_to_png(pdf),
            media_type="image/png",
            headers={
                **no_cache,
                "Content-Disposition": f'inline; filename="label-{stem}.png"',
            },
        )

    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={
            **no_cache,
            "Content-Disposition": f'inline; filename="label-{stem}.pdf"',
        },
    )


@router.post("/{asset_id}/qr/rotate")
def rotate_asset_qr(
    asset_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[
        User,
        Depends(require_roles(UserRole.super_admin, UserRole.company_admin)),
    ],
) -> dict:
    """Revoke active tag and mint a new opaque token (compromised label)."""
    asset = _access_asset(db, current, asset_id)
    from app.services.asset_tags import public_tag_url, revoke_and_mint

    tag = revoke_and_mint(db, asset)
    db.commit()
    db.refresh(asset)
    return {
        "token": tag.token,
        "qr_payload": asset.qr_payload or public_tag_url(tag.token),
        "status": tag.status,
    }





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

