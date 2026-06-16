"""WebSocket + REST notifications (Phase 3.1)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import decode_token
from app.database import SessionLocal, get_db
from app.models import User
from app.realtime import manager
from app.schemas import NotificationOut
from app.services.notification_service import list_notifications, mark_all_read, mark_read

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("", response_model=list[NotificationOut])
def get_notifications(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
    limit: int = Query(50, ge=1, le=100),
) -> list[NotificationOut]:
    rows = list_notifications(db, current.id, current.tenant_id, limit=limit)
    return [NotificationOut.from_model(r) for r in rows]


@router.patch("/{notification_id}/read", response_model=NotificationOut)
def read_notification(
    notification_id: UUID,
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> NotificationOut:
    row = mark_read(db, current.id, current.tenant_id, notification_id)
    if not row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="NOT_FOUND")
    db.commit()
    db.refresh(row)
    return NotificationOut.from_model(row)


@router.post("/read-all")
def read_all_notifications(
    db: Annotated[Session, Depends(get_db)],
    current: Annotated[User, Depends(get_current_user)],
) -> dict[str, int]:
    count = mark_all_read(db, current.id, current.tenant_id)
    db.commit()
    return {"updated": count}


@router.websocket("/ws")
async def notifications_ws(
    websocket: WebSocket,
    token: str = Query(""),
) -> None:
    payload = decode_token(token) if token else None
    if not payload or payload.get("type") != "access":
        await websocket.close(code=4401)
        return
    try:
        user_id = UUID(payload["sub"])
    except (KeyError, ValueError):
        await websocket.close(code=4401)
        return

    with SessionLocal() as db:
        user = db.get(User, user_id)
        if not user or not user.is_active:
            await websocket.close(code=4401)
            return
        token_tenant = payload.get("tenant_id")
        if token_tenant is not None and str(user.tenant_id) != str(token_tenant):
            await websocket.close(code=4401)
            return

    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(user_id, websocket)
