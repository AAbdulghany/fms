"""In-memory WebSocket fan-out for Phase 3 real-time notifications (single-process MVP)."""

from __future__ import annotations

import logging
from typing import Any
from uuid import UUID

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """One user may have multiple tabs (multiple WebSocket connections)."""

    def __init__(self) -> None:
        self._connections: dict[UUID, list[WebSocket]] = {}

    async def connect(self, user_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, []).append(websocket)

    def disconnect(self, user_id: UUID, websocket: WebSocket) -> None:
        conns = self._connections.get(user_id)
        if not conns:
            return
        self._connections[user_id] = [c for c in conns if c is not websocket]
        if not self._connections[user_id]:
            del self._connections[user_id]

    async def send_to_user(self, user_id: UUID, message: dict[str, Any]) -> None:
        conns = self._connections.get(user_id)
        if not conns:
            return
        stale: list[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception as e:  # noqa: BLE001
                logger.debug("websocket send failed: %s", e)
                stale.append(ws)
        for ws in stale:
            self.disconnect(user_id, ws)


manager = ConnectionManager()
