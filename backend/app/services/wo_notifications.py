"""Background async hooks for work order WebSocket + email (Phase 3)."""

from __future__ import annotations

import asyncio
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import joinedload, Session

from app.database import SessionLocal
from app.models import User, WorkOrder
from app.realtime import manager
from app.services.email import send_work_order_assigned_email, send_work_order_status_email


async def notify_work_order_created(wo_id: UUID) -> None:
    db = SessionLocal()
    try:
        wo = db.execute(
            select(WorkOrder)
            .where(WorkOrder.id == wo_id)
            .options(joinedload(WorkOrder.assignee_user), joinedload(WorkOrder.creator_user))
        ).scalar_one_or_none()
        if not wo:
            return
        payload = {
            "type": "work_order.created",
            "work_order_id": str(wo.id),
            "title": wo.title or "Work order",
        }
        if wo.assignee_user_id:
            await manager.send_to_user(wo.assignee_user_id, payload)
        assignee = wo.assignee_user
        if assignee and assignee.email:
            await asyncio.to_thread(
                send_work_order_assigned_email,
                assignee.email,
                wo.title or "Work order",
                str(wo.id),
            )
    finally:
        db.close()


async def notify_work_order_assigned(wo_id: UUID) -> None:
    """Notify assignee when a work order is explicitly assigned (assign endpoint)."""
    db = SessionLocal()
    try:
        wo = db.execute(
            select(WorkOrder)
            .where(WorkOrder.id == wo_id)
            .options(joinedload(WorkOrder.assignee_user))
        ).scalar_one_or_none()
        if not wo or not wo.assignee_user_id:
            return
        await manager.send_to_user(
            wo.assignee_user_id,
            {
                "type": "work_order.assigned",
                "work_order_id": str(wo.id),
                "title": wo.title or "Work order",
            },
        )
        assignee = wo.assignee_user
        if assignee and assignee.email:
            await asyncio.to_thread(
                send_work_order_assigned_email,
                assignee.email,
                wo.title or "Work order",
                str(wo.id),
            )
    finally:
        db.close()


async def notify_work_order_requested(wo_id: UUID) -> None:
    """Notify all active company_admin users in the tenant when a WO request is submitted."""
    db = SessionLocal()
    try:
        wo = db.execute(
            select(WorkOrder)
            .where(WorkOrder.id == wo_id)
            .options(joinedload(WorkOrder.creator_user))
        ).scalar_one_or_none()
        if not wo:
            return
        payload = {
            "type": "work_order.requested",
            "work_order_id": str(wo.id),
            "title": wo.title or "Work order request",
        }
        admins = db.scalars(
            select(User).where(
                User.tenant_id == wo.tenant_id,
                User.is_active.is_(True),
                User.role.in_(["company_admin", "super_admin"]),
            )
        ).all()
        for admin in admins:
            await manager.send_to_user(admin.id, payload)
    finally:
        db.close()


async def notify_work_order_status_changed(
    wo_id: UUID,
    old_status: str,
    new_status: str,
) -> None:
    db = SessionLocal()
    try:
        wo = db.execute(
            select(WorkOrder)
            .where(WorkOrder.id == wo_id)
            .options(joinedload(WorkOrder.assignee_user), joinedload(WorkOrder.creator_user))
        ).scalar_one_or_none()
        if not wo:
            return
        payload = {
            "type": "work_order.status_changed",
            "work_order_id": str(wo.id),
            "title": wo.title or "Work order",
            "old_status": old_status,
            "new_status": new_status,
        }
        targets: set[UUID] = set()
        if wo.created_by_user_id:
            targets.add(wo.created_by_user_id)
        if wo.assignee_user_id:
            targets.add(wo.assignee_user_id)
        for uid in targets:
            await manager.send_to_user(uid, payload)

        # Email both parties if different users with emails
        for uid in targets:
            user = db.get(User, uid)
            if user and user.email:
                await asyncio.to_thread(
                    send_work_order_status_email,
                    user.email,
                    wo.title or "Work order",
                    old_status,
                    new_status,
                )
    finally:
        db.close()
