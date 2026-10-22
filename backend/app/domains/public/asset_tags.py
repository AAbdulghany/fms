"""A2 — Public asset-tag resolve + anonymous report (rate-limited)."""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock
from typing import Annotated, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.database import get_db
from app.models import User, WorkOrder
from app.models._base import Urgency, WorkOrderSource, WorkOrderStatus
from app.services.asset_tags import resolve_tag

router = APIRouter(prefix="/public/asset-tags", tags=["public-asset-tags"])

_RATE: dict[tuple[str, str], list[float]] = defaultdict(list)
_RATE_LOCK = Lock()
_RATE_MAX = 5
_RATE_WINDOW_S = 3600


class PublicTagOut(BaseModel):
    token: str
    name: str
    client_name: Optional[str] = None
    site_name: str
    can_report: bool = True
    asset_id: Optional[UUID] = None
    has_history: bool = False


class PublicReportIn(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3, max_length=4000)
    contact: Optional[str] = Field(default=None, max_length=320)


def _optional_user(db: Session, request: Request) -> User | None:
    auth = request.headers.get("authorization") or ""
    if not auth.lower().startswith("bearer "):
        return None
    try:
        token = auth.split(" ", 1)[1].strip()
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return None
        user = db.get(User, UUID(payload["sub"]))
        if not user or not user.is_active:
            return None
        return user
    except Exception:
        return None


def reset_rate_limits() -> None:
    """Test helper — clear in-process rate buckets."""
    with _RATE_LOCK:
        _RATE.clear()


def _check_rate(ip: str, token: str) -> None:
    key = (ip or "unknown", token.upper())
    now = time.time()
    with _RATE_LOCK:
        stamps = [t for t in _RATE[key] if now - t < _RATE_WINDOW_S]
        if len(stamps) >= _RATE_MAX:
            _RATE[key] = stamps
            raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, detail="RATE_LIMITED")
        stamps.append(now)
        _RATE[key] = stamps


@router.get("/{token}", response_model=PublicTagOut)
def get_public_tag(
    token: str,
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> PublicTagOut:
    tag, asset, site, client = resolve_tag(db, token)
    user = _optional_user(db, request)
    if user is not None and user.tenant_id != tag.tenant_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="TAG_NOT_FOUND")
    out = PublicTagOut(
        token=tag.token,
        name=asset.name,
        client_name=client.legal_name if client else None,
        site_name=site.name,
        can_report=True,
    )
    if user is not None:
        out.asset_id = asset.id
        count = db.scalar(
            select(func.count())
            .select_from(WorkOrder)
            .where(WorkOrder.asset_id == asset.id, WorkOrder.tenant_id == tag.tenant_id)
        )
        out.has_history = bool(count and count > 0)
    return out


@router.post("/{token}/report", status_code=status.HTTP_201_CREATED)
def report_public_tag(
    token: str,
    body: PublicReportIn,
    db: Annotated[Session, Depends(get_db)],
    request: Request,
) -> dict[str, Any]:
    ip = request.client.host if request.client else "unknown"
    _check_rate(ip, token)
    tag, asset, site, _client = resolve_tag(db, token)
    if not site.client_id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail="INVALID_SITE")

    desc = body.description.strip()
    if body.contact:
        desc = f"{desc}\n\nContact: {body.contact.strip()}"

    wo = WorkOrder(
        tenant_id=tag.tenant_id,
        client_id=site.client_id,
        site_id=site.id,
        asset_id=asset.id,
        title=body.title.strip()[:200],
        description=desc[:4000],
        status=WorkOrderStatus.requested,
        source=WorkOrderSource.request,
        urgency=Urgency.normal,
        category=asset.category or "general",
        tags=[],
    )
    db.add(wo)
    db.commit()
    db.refresh(wo)
    status_val = wo.status.value if hasattr(wo.status, "value") else wo.status
    return {"id": str(wo.id), "status": status_val}
