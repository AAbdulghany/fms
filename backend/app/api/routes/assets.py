from typing import Annotated

from uuid import UUID



from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status

from sqlalchemy import select

from sqlalchemy.orm import Session, selectinload



from app.api.deps import ensure_site_access, get_current_user, require_feature, require_roles

from app.database import get_db

from app.models import Asset, MaintenanceSchedule, Site, User, UserRole, UserSiteScope

from app.schemas import (

    AssetCreate,

    AssetImportPreview,

    AssetOut,

    MaintenanceScheduleCreate,

    MaintenanceScheduleOut,

)

from app.services.asset_import import commit_import, preview_import

from app.services.asset_labels import generate_label_code, qr_payload_for_asset

from app.services.asset_lifecycle import get_lifecycle_timeline, reset_asset_lifecycle

from app.services.audit import write_audit

from app.services.maintenance_schedules import create_schedule

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

        schedules=[MaintenanceScheduleOut.model_validate(s) for s in active_schedules],

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

) -> list[AssetOut]:

    q = select(Asset).where(Asset.tenant_id == current.tenant_id).options(selectinload(Asset.schedules))



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



    if view == "maintenance" or sort == "next_due":

        from datetime import datetime, timezone



        now = datetime.now(timezone.utc)



        def _next_due(a: Asset):

            active = [s for s in a.schedules if s.is_active]

            if not active:

                return datetime.max.replace(tzinfo=timezone.utc)

            return min(s.next_due_at for s in active)



        if maintenance_filter == "overdue":

            assets = [a for a in assets if _next_due(a) <= now and a.schedules]

        elif maintenance_filter == "due_week":

            from datetime import timedelta



            week = now + timedelta(days=7)

            assets = [a for a in assets if now <= _next_due(a) <= week]

        elif maintenance_filter == "due_month":

            from datetime import timedelta



            month = now + timedelta(days=30)

            assets = [a for a in assets if now <= _next_due(a) <= month]



        assets.sort(key=_next_due)



    return [_asset_to_out(a) for a in assets]





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


