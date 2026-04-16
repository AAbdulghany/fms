from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database import get_db
from app.models import ReportTemplate, User, UserRole
from app.schemas import ReportTemplateCreate, ReportTemplateOut
from app.services.audit import write_audit

router = APIRouter(prefix="/report-templates", tags=["report-templates"])

_admin = Depends(require_roles(UserRole.super_admin, UserRole.company_admin))


@router.get("", response_model=list[ReportTemplateOut])
def list_templates(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> list[ReportTemplate]:
    return list(db.scalars(select(ReportTemplate).where(ReportTemplate.tenant_id == current.tenant_id)).all())


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
) -> ReportTemplate:
    t = db.get(ReportTemplate, template_id)
    if not t or t.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    return t


@router.patch("/{template_id}/publish", response_model=ReportTemplateOut)
def publish_template(
    template_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    _: Annotated[User, _admin],
) -> ReportTemplate:
    t = db.get(ReportTemplate, template_id)
    if not t or t.tenant_id != current.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
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
