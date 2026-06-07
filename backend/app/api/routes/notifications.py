"""WebSocket endpoint for Phase 3 real-time notifications."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.database import SessionLocal
from app.models import User
from app.realtime import manager

router = APIRouter(prefix="/notifications", tags=["notifications"])


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

    # SECURITY: verify user still exists, is active, and token tenant matches DB
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
