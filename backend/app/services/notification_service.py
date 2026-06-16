"""Persist and deliver user notifications (Phase 3.1)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Notification
from app.realtime import manager


def _ws_payload(row: Notification) -> dict:
    payload = dict(row.payload_json or {})
    return {
        "id": str(row.id),
        "type": row.type,
        "title": row.title,
        "work_order_id": payload.get("work_order_id"),
        "action": payload.get("action"),
        "old_status": payload.get("old_status"),
        "new_status": payload.get("new_status"),
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


def create_notification(
    db: Session,
    *,
    tenant_id: UUID,
    user_id: UUID,
    type: str,
    title: str,
    payload: dict | None = None,
) -> Notification:
    row = Notification(
        tenant_id=tenant_id,
        user_id=user_id,
        type=type,
        title=title,
        payload_json=payload or {},
    )
    db.add(row)
    db.flush()
    return row


async def persist_and_push(
    db: Session,
    *,
    tenant_id: UUID,
    user_id: UUID,
    type: str,
    title: str,
    payload: dict | None = None,
    commit: bool = True,
) -> Notification:
    row = create_notification(
        db,
        tenant_id=tenant_id,
        user_id=user_id,
        type=type,
        title=title,
        payload=payload,
    )
    if commit:
        db.commit()
        db.refresh(row)
    await manager.send_to_user(user_id, _ws_payload(row))
    return row


def list_notifications(db: Session, user_id: UUID, tenant_id: UUID, limit: int = 50) -> list[Notification]:
    return list(
        db.scalars(
            select(Notification)
            .where(Notification.user_id == user_id, Notification.tenant_id == tenant_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        ).all()
    )


def mark_read(db: Session, user_id: UUID, tenant_id: UUID, notification_id: UUID) -> Notification | None:
    row = db.get(Notification, notification_id)
    if not row or row.user_id != user_id or row.tenant_id != tenant_id:
        return None
    if row.read_at is None:
        row.read_at = datetime.now(timezone.utc)
    return row


def mark_all_read(db: Session, user_id: UUID, tenant_id: UUID) -> int:
    rows = db.scalars(
        select(Notification).where(
            Notification.user_id == user_id,
            Notification.tenant_id == tenant_id,
            Notification.read_at.is_(None),
        )
    ).all()
    now = datetime.now(timezone.utc)
    for row in rows:
        row.read_at = now
    return len(rows)
