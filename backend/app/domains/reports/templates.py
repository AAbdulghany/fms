from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import distinct, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import Asset, ReportTemplate, User, UserRole
from app.schemas import (
    CategoryObservationsOut,
    CategoryObservationsUpdate,
    ObservationFieldDef,
    ReportTemplateCreate,
    ReportTemplateOut,
    TemplateSyncResult,
)
from app.services.audit import write_audit
from app.services.report_schema_resolve import (
    DEFAULT_CATEGORY_KEY,
    delete_category_observations,
    get_observations_by_category,
    resolve_effective_schema,
    set_category_observations,
)
from app.services.report_template_sync import sync_std_insp_all_tenants, sync_std_insp_for_tenant

router = APIRouter(prefix="/report-templates", tags=["report-templates"])

_admin = Depends(require_roles(UserRole.super_admin, UserRole.company_admin))

_ALLOWED_FIELD_TYPES = {"text", "textarea", "checklist"}


def _validate_observation_fields(fields: list[ObservationFieldDef]) -> list[dict]:
    if not fields:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="FIELDS_REQUIRED")
    seen: set[str] = set()
    out: list[dict] = []
    for f in fields:
        if f.type not in _ALLOWED_FIELD_TYPES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_FIELD_TYPE")
        if f.id in seen:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="DUPLICATE_FIELD_ID")
        seen.add(f.id)
        item = f.model_dump()
        if f.type != "checklist":
            item.pop("options", None)
        out.append(item)
    return out


def _get_tenant_template(db: Session, current: User, template_id: UUID) -> ReportTemplate:
    t = db.get(ReportTemplate, template_id)
    if not t or t.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    return t


@router.get("", response_model=list[ReportTemplateOut])
def list_templates(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[ReportTemplate]:
    return list(db.scalars(select(ReportTemplate).where(ReportTemplate.tenant_id == current.tenant_id)).all())


@router.post("/sync-standard", response_model=TemplateSyncResult)
def sync_standard_template(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> TemplateSyncResult:
    """Upgrade (or create) STD-INSP v2 for the current tenant."""
    action, tmpl = sync_std_insp_for_tenant(db, current.tenant_id)
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="sync_std_insp_template",
        entity_type="report_template",
        entity_id=str(tmpl.id),
        after={"result": action, "version": tmpl.version},
    )
    db.commit()
    return TemplateSyncResult(
        created=1 if action == "created" else 0,
        updated=1 if action == "updated" else 0,
        unchanged=1 if action == "unchanged" else 0,
    )


@router.get("/asset-categories", response_model=list[str])
def list_asset_categories(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[str]:
    rows = db.scalars(
        select(distinct(Asset.category))
        .where(Asset.tenant_id == current.tenant_id, Asset.category != "")
        .order_by(Asset.category)
    ).all()
    return [r for r in rows if r]


@router.post("", response_model=ReportTemplateOut)
def create_template(
    body: ReportTemplateCreate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> ReportTemplate:
    t = ReportTemplate(
        tenant_id=current.tenant_id,
        name=body.name,
        code=body.code,
        schema_json=body.definition,
        maintenance_types=body.maintenance_types,
        version=1,
    )
    db.add(t)
    write_audit(db, tenant_id=current.tenant_id, actor=current, action="create", entity_type="report_template")
    db.commit()
    db.refresh(t)
    return t


@router.get("/{template_id}", response_model=ReportTemplateOut)
def get_template(
    template_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    asset_category: str | None = Query(None),
) -> ReportTemplateOut:
    t = _get_tenant_template(db, current, template_id)
    if asset_category:
        effective = resolve_effective_schema(t.schema_json or {}, asset_category)
        return ReportTemplateOut(
            id=t.id,
            name=t.name,
            code=t.code,
            version=t.version,
            definition=effective,
            maintenance_types=t.maintenance_types or [],
            is_active=t.is_active,
        )
    return t


@router.get("/{template_id}/observations", response_model=CategoryObservationsOut)
def get_category_observations(
    template_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> CategoryObservationsOut:
    t = _get_tenant_template(db, current, template_id)
    raw = get_observations_by_category(t.schema_json or {})
    categories = {
        key: [ObservationFieldDef(**field) for field in fields]
        for key, fields in raw.items()
    }
    return CategoryObservationsOut(categories=categories)


@router.put("/{template_id}/observations/{category_key}", response_model=CategoryObservationsOut)
def put_category_observations(
    template_id: UUID,
    category_key: str,
    body: CategoryObservationsUpdate,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> CategoryObservationsOut:
    t = _get_tenant_template(db, current, template_id)
    key = category_key.strip()
    if not key:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="CATEGORY_KEY_REQUIRED")
    fields = _validate_observation_fields(body.fields)
    t.schema_json = set_category_observations(t.schema_json or {}, key, fields)
    t.version += 1
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="update_category_observations",
        entity_type="report_template",
        entity_id=str(t.id),
        after={"category": key, "field_count": len(fields), "version": t.version},
    )
    db.commit()
    db.refresh(t)
    raw = get_observations_by_category(t.schema_json or {})
    return CategoryObservationsOut(
        categories={
            k: [ObservationFieldDef(**field) for field in v]
            for k, v in raw.items()
        }
    )


@router.delete("/{template_id}/observations/{category_key}", response_model=CategoryObservationsOut)
def remove_category_observations(
    template_id: UUID,
    category_key: str,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> CategoryObservationsOut:
    if category_key == DEFAULT_CATEGORY_KEY:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="CANNOT_DELETE_DEFAULT")
    t = _get_tenant_template(db, current, template_id)
    try:
        t.schema_json = delete_category_observations(t.schema_json or {}, category_key)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    t.version += 1
    db.commit()
    db.refresh(t)
    raw = get_observations_by_category(t.schema_json or {})
    return CategoryObservationsOut(
        categories={
            k: [ObservationFieldDef(**field) for field in v]
            for k, v in raw.items()
        }
    )


@router.patch("/{template_id}/publish", response_model=ReportTemplateOut)
def publish_template(
    template_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> ReportTemplate:
    t = _get_tenant_template(db, current, template_id)
    t.version += 1
    write_audit(
        db,
        tenant_id=current.tenant_id,
        actor=current,
        action="publish_template",
        entity_type="report_template",
        entity_id=str(t.id),
        after={"version": t.version},
    )
    db.commit()
    db.refresh(t)
    return t
