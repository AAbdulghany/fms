"""A1 — /asset-types CRUD, adopt, and archive endpoints."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import ensure_client_access, get_current_user, require_feature, require_roles
from app.database import get_db
from app.models import Client, Site, User, UserRole
from app.models.asset_types import AssetType, AssetTypeVertical, Vertical
from app.schemas.asset_types import (
    AssetTypeAdoptRequest,
    AssetTypeAdoptResponse,
    AssetTypeAdoptSkipped,
    AssetTypeCreate,
    AssetTypeOut,
    AssetTypeUpdate,
)
from app.services.asset_types_service import (
    adopt_templates,
    count_assets_for_type,
    create_asset_type,
    get_asset_type_or_404,
    update_asset_type,
)
from app.services.audit import write_audit

router = APIRouter(
    prefix="/asset-types",
    tags=["asset-types"],
    dependencies=[Depends(require_feature("assets"))],
)

# write guard: company_admin + super_admin only (not client_admin — locked A1 decision)
_write = Depends(require_roles(UserRole.super_admin, UserRole.company_admin))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _asset_type_to_out(
    db: Session,
    at: AssetType,
    *,
    recommended: bool = False,
    include_count: bool = True,
) -> AssetTypeOut:
    vert_codes = [
        tv.vertical.code
        for tv in at.asset_type_verticals
        if tv.vertical and tv.vertical.is_active
    ]
    asset_count = count_assets_for_type(db, at.id) if include_count else 0
    return AssetTypeOut(
        id=at.id,
        code=at.code,
        name_en=at.name_en,
        name_ar=at.name_ar,
        origin=at.origin,  # type: ignore[arg-type]
        vertical_codes=vert_codes,
        default_max_age_years=at.default_max_age_years,
        default_max_repair_count=at.default_max_repair_count,
        default_criticality=at.default_criticality,
        default_frequency=at.default_frequency,
        default_report_template_id=at.default_report_template_id,
        source_template_id=at.source_template_id,
        source_version=at.source_version,
        is_active=at.is_active,
        recommended=recommended,
        asset_count=asset_count,
    )


def _vertical_codes_for_client(db: Session, client_id: UUID) -> set[str]:
    """Return the vertical codes associated with the client's vertical."""
    client = db.get(Client, client_id)
    if not client or not client.vertical_id:
        # Fall back to activity_type alias
        if client and client.activity_type:
            from app.services.verticals import resolve_vertical
            v = resolve_vertical(db, client.activity_type)
            if v:
                return {v.code}
        return set()
    v = db.get(Vertical, client.vertical_id)
    return {v.code} if v else set()


# ---------------------------------------------------------------------------
# POST /asset-types/adopt — must come before /{id} routes
# ---------------------------------------------------------------------------


@router.post("/adopt", response_model=AssetTypeAdoptResponse)
def adopt_asset_types(
    body: AssetTypeAdoptRequest,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _write],
) -> AssetTypeAdoptResponse:
    result = adopt_templates(db, current.tenant_id, body.template_ids)

    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="adopt_asset_types",
        entity_type="asset_type",
        after={
            "created_count": len(result["created"]),
            "skipped_count": len(result["skipped"]),
        },
    )
    db.commit()

    created_out = [_asset_type_to_out(db, at, include_count=False) for at in result["created"]]
    skipped_out = [
        AssetTypeAdoptSkipped(
            template_id=s["template_id"],
            asset_type_id=s.get("asset_type_id"),
            reason=s["reason"],
        )
        for s in result["skipped"]
    ]
    return AssetTypeAdoptResponse(created=created_out, skipped=skipped_out)


# ---------------------------------------------------------------------------
# GET /asset-types
# ---------------------------------------------------------------------------


@router.get("", response_model=list[AssetTypeOut])
def list_asset_types(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    client_id: UUID | None = Query(None),
    vertical: str | None = Query(None),
    include_inactive: bool = Query(False),
    asset_type_id: UUID | None = Query(None),
    match_vertical: bool = Query(
        False,
        description=(
            "When true with client_id or vertical, return only types tagged for that "
            "vertical (plus untagged/universal types). Recommended always true for matches."
        ),
    ),
) -> list[AssetTypeOut]:
    # client_id scope check
    if client_id:
        ensure_client_access(db, current, client_id)

    q = select(AssetType).where(AssetType.tenant_id == current.tenant_id)
    if not include_inactive:
        q = q.where(AssetType.is_active.is_(True))
    if asset_type_id:
        q = q.where(AssetType.id == asset_type_id)

    rows = list(db.scalars(q).all())

    # Determine recommended vertical codes
    recommended_codes: set[str] = set()
    if client_id:
        recommended_codes = _vertical_codes_for_client(db, client_id)
    elif vertical:
        recommended_codes = {vertical}

    def _type_codes(at: AssetType) -> set[str]:
        return {tv.vertical.code for tv in at.asset_type_verticals if tv.vertical}

    def _is_recommended(at: AssetType) -> bool:
        if not recommended_codes:
            return False
        codes = _type_codes(at)
        # Untagged types are treated as universal (usable for any vertical)
        return (not codes) or bool(codes & recommended_codes)

    if match_vertical and recommended_codes:
        rows = [at for at in rows if _is_recommended(at)]

    # Sort: recommended first, then by name_en
    rows.sort(key=lambda at: (not _is_recommended(at), at.name_en))

    return [
        _asset_type_to_out(db, at, recommended=_is_recommended(at)) for at in rows
    ]


# ---------------------------------------------------------------------------
# POST /asset-types
# ---------------------------------------------------------------------------


@router.post("/archive-all")
def archive_all_types(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _write],
) -> dict:
    """Soft-archive every active tenant asset type (library reset).

    Intended for local/dev wipe only — blocked when APP_ENV is production.
    """
    from app.config import settings
    from app.services.asset_types_service import archive_all_asset_types

    env = str(getattr(settings, "app_env", "") or "").lower()
    if env in ("production", "pilot"):
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail="ARCHIVE_ALL_DEV_ONLY")

    n = archive_all_asset_types(db, current.tenant_id)
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="archive_all",
        entity_type="asset_type",
        entity_id=str(current.tenant_id),
        after={"archived": n},
    )
    db.commit()
    return {"archived": n}


@router.post("", response_model=AssetTypeOut, status_code=status.HTTP_201_CREATED)
def create_asset_type_endpoint(
    body: AssetTypeCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _write],
) -> AssetTypeOut:
    at = create_asset_type(
        db,
        tenant_id=current.tenant_id,
        code=body.code,
        name_en=body.name_en,
        name_ar=body.name_ar,
        vertical_codes=body.vertical_codes,
        default_max_age_years=body.default_max_age_years,
        default_max_repair_count=body.default_max_repair_count,
        default_criticality=body.default_criticality,
        default_frequency=body.default_frequency,
        default_report_template_id=body.default_report_template_id,
    )
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="create",
        entity_type="asset_type",
        entity_id=str(at.id),
        after={"code": at.code, "name_en": at.name_en},
    )
    db.commit()
    db.refresh(at)
    return _asset_type_to_out(db, at)


# ---------------------------------------------------------------------------
# GET /asset-types/{id}
# ---------------------------------------------------------------------------


@router.get("/{asset_type_id}", response_model=AssetTypeOut)
def get_asset_type(
    asset_type_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> AssetTypeOut:
    at = get_asset_type_or_404(db, current.tenant_id, asset_type_id)
    return _asset_type_to_out(db, at)


# ---------------------------------------------------------------------------
# PATCH /asset-types/{id}
# ---------------------------------------------------------------------------


@router.post("/{asset_type_id}/apply-pm-schedules")
def apply_pm_schedules(
    asset_type_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _write],
    only_missing: bool = Query(
        False,
        description="If true, only create schedules for assets that have none.",
    ),
) -> dict:
    """Push AssetType default_frequency + template onto all assets of this type."""
    at = get_asset_type_or_404(db, current.tenant_id, asset_type_id)
    from app.services.asset_type_pm import apply_type_pm_to_assets

    result = apply_type_pm_to_assets(
        db, tenant_id=current.tenant_id, asset_type=at, only_missing=only_missing
    )
    if not result.get("ok"):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail=result.get("reason") or "APPLY_PM_FAILED",
        )
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="apply_pm_schedules",
        entity_type="asset_type",
        entity_id=str(at.id),
        after=result,
    )
    db.commit()
    return result


@router.patch("/{asset_type_id}", response_model=AssetTypeOut)
def update_asset_type_endpoint(
    asset_type_id: UUID,
    body: AssetTypeUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _write],
    apply_schedules: bool = Query(
        False,
        description="After saving PM defaults, sync MaintenanceSchedule on linked assets.",
    ),
) -> AssetTypeOut:
    # Guard: code in body → immutable (check model_fields_set, not dump, to catch explicit code)
    raw = body.model_dump(exclude_unset=True)
    if "code" in body.model_fields_set:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="ASSET_TYPE_CODE_IMMUTABLE")

    at = get_asset_type_or_404(db, current.tenant_id, asset_type_id)

    # Apply only the fields that were explicitly sent
    if "name_en" in raw and raw["name_en"] is not None:
        at.name_en = raw["name_en"]
    if "name_ar" in raw and raw["name_ar"] is not None:
        at.name_ar = raw["name_ar"]
    if "is_active" in raw:
        at.is_active = raw["is_active"]
    if "default_max_age_years" in raw:
        at.default_max_age_years = raw["default_max_age_years"]
    if "default_max_repair_count" in raw:
        at.default_max_repair_count = raw["default_max_repair_count"]
    if "default_criticality" in raw:
        at.default_criticality = raw["default_criticality"]
    if "default_frequency" in raw:
        from app.services.asset_types_service import ALLOWED_FREQUENCIES
        freq = raw["default_frequency"]
        if freq is not None and freq not in ALLOWED_FREQUENCIES:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="INVALID_FREQUENCY")
        at.default_frequency = freq
    if "default_report_template_id" in raw:
        from app.services.asset_types_service import _resolve_report_template
        _resolve_report_template(db, current.tenant_id, raw["default_report_template_id"])
        at.default_report_template_id = raw["default_report_template_id"]
    if "vertical_codes" in raw:
        from app.services.asset_types_service import _set_vertical_tags
        _set_vertical_tags(db, at, raw["vertical_codes"])
    from datetime import datetime, timezone
    at.updated_at = datetime.now(timezone.utc)
    db.flush()

    pm_result = None
    if apply_schedules and (
        "default_frequency" in raw or "default_report_template_id" in raw
    ):
        from app.services.asset_type_pm import apply_type_pm_to_assets

        pm_result = apply_type_pm_to_assets(
            db, tenant_id=current.tenant_id, asset_type=at, only_missing=False
        )

    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="update",
        entity_type="asset_type",
        entity_id=str(at.id),
        after={"code": at.code, "pm_apply": pm_result},
    )
    db.commit()
    db.refresh(at)
    return _asset_type_to_out(db, at)
