#!/usr/bin/env python3
"""Split work_orders router into concern modules (NT-CLEAN-21)."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "app" / "domains" / "work_orders"
MONOLITH_BACKUP = ROOT / "router.monolith.bak"

# Restore from backup if re-running
source = MONOLITH_BACKUP if MONOLITH_BACKUP.exists() else ROOT / "router.py"
if not MONOLITH_BACKUP.exists() and (ROOT / "router.py").exists():
    text = (ROOT / "router.py").read_text(encoding="utf-8")
    if "include_router" not in text and "def list_work_orders" in text:
        MONOLITH_BACKUP.write_text(text, encoding="utf-8")

all_lines = source.read_text(encoding="utf-8").splitlines(keepends=True)

COMMON_END = 303
CRUD_A = (305, 459)
REQUESTS = (461, 604)
CRUD_B = (607, 782)
REPORTS = (785, 903)
COLLAB = (906, 1144)


def slice_range(start: int, end: int) -> str:
    return "".join(all_lines[start - 1 : end])


COMMON_HEADER = '''"""Shared helpers and role dependencies for work order routes."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import require_roles
from app.models import (
    Tenant,
    User,
    UserRole,
    UserSiteScope,
    WorkOrder,
    WorkOrderDocument,
    WorkOrderStatus,
)
from app.schemas import UserBrief, WorkOrderOut
from app.services.report_context import merge_report_answers, resolve_report_inspector

'''

MODULE_HEADER = '''"""Work orders — {doc}."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy import false, func, select
from sqlalchemy.orm import Session, joinedload

from app.api.deps import ensure_client_access, ensure_site_access, get_current_user, require_roles
from app.database import get_db
from app.models import (
    AuditLog,
    Comment,
    MaintenanceReport,
    ReportStatus,
    ReportTemplate,
    Tenant,
    User,
    UserRole,
    UserSiteScope,
    WorkOrder,
    WorkOrderDocument,
    WorkOrderStatus,
)
from app.schemas import (
    AssignBody,
    AuditLogOut,
    CommentCreate,
    CommentOut,
    DeclineRequestBody,
    DocumentCreate,
    DocumentOut,
    MaintenanceReportOut,
    PaginatedMeta,
    PaginatedWorkOrders,
    ReportAnswersUpdate,
    UserBrief,
    WorkOrderCreate,
    WorkOrderOut,
    WorkOrderUpdate,
)
from app.services.asset_lifecycle import on_work_order_completed
from app.services.audit import write_audit
from app.services.report_context import merge_report_answers, resolve_report_inspector
from app.services.report_schema_resolve import resolve_effective_schema
from app.services.report_template_defaults import resolve_default_report_template
from app.services.report_validation import validate_required_fields
from app.services.wo_notifications import (
    notify_work_order_assigned,
    notify_work_order_created,
    notify_work_order_requested,
    notify_work_order_status_changed,
)
from app.services.work_order_fsm import (
    TransitionError,
    assert_mutable,
    can_transition,
    validate_status_transition,
)

from ._common import (
    REPORT_PDF_DOC_DESCRIPTION,
    REPORT_EDITABLE_STATUSES,
    _ASSIGN_ROLES,
    _access_wo,
    _approve_roles,
    _assignee_audit_label,
    _assert_patch_fields_allowed,
    _create_roles,
    _reload_wo_with_users,
    _request_roles,
    _sync_maintenance_report_pdf_export,
    _validate_assignee,
    _wo_load_options,
    _work_order_status_allows_report,
    _work_order_to_out,
    validate_tags,
)
from .router import router

'''


def main() -> None:
    common_body = slice_range(63, COMMON_END).replace(
        'router = APIRouter(prefix="/work-orders", tags=["work-orders"])\n\n', ""
    )
    (ROOT / "_common.py").write_text(COMMON_HEADER + common_body, encoding="utf-8")

    sections = [
        ("crud.py", "list, create, get, patch, assign", [CRUD_A, CRUD_B]),
        ("requests.py", "request / approve / decline flow", [REQUESTS]),
        ("reports.py", "maintenance report draft and submit", [REPORTS]),
        ("collaboration.py", "history, comments, documents", [COLLAB]),
    ]

    for fname, doc, ranges in sections:
        body = "".join(slice_range(s, e) for s, e in ranges)
        (ROOT / fname).write_text(MODULE_HEADER.format(doc=doc) + body, encoding="utf-8")

    aggregator = '''"""Work orders API — aggregates route modules by concern."""

from fastapi import APIRouter

router = APIRouter(prefix="/work-orders", tags=["work-orders"])

# Side-effect: register handlers on `router`
from . import collaboration, crud, reports, requests  # noqa: E402, F401

from ._common import (  # noqa: F401
    REPORT_PDF_DOC_DESCRIPTION,
    _reload_wo_with_users,
    _work_order_to_out,
    validate_tags,
)
from .collaboration import (  # noqa: F401
    create_work_order_comment,
    delete_work_order_document,
    download_work_order_document_file,
    get_work_order_comments,
    get_work_order_documents,
    get_work_order_history,
    upload_work_order_document,
)
from .crud import (  # noqa: F401
    assign_work_order,
    create_work_order,
    get_assignable_users,
    get_work_order,
    list_work_orders,
    patch_work_order,
)
from .reports import get_report, submit_report, upsert_report_draft  # noqa: F401
from .requests import (  # noqa: F401
    approve_work_order_request,
    decline_work_order_request,
    request_work_order,
)

__all__ = [
    "router",
    "list_work_orders",
    "create_work_order",
    "request_work_order",
    "approve_work_order_request",
    "decline_work_order_request",
    "get_work_order",
    "patch_work_order",
    "get_assignable_users",
    "assign_work_order",
    "get_report",
    "upsert_report_draft",
    "submit_report",
    "get_work_order_history",
    "get_work_order_comments",
    "create_work_order_comment",
    "get_work_order_documents",
    "download_work_order_document_file",
    "upload_work_order_document",
    "delete_work_order_document",
    "validate_tags",
    "_reload_wo_with_users",
    "_work_order_to_out",
    "REPORT_PDF_DOC_DESCRIPTION",
]
'''
    (ROOT / "router.py").write_text(aggregator, encoding="utf-8")

    if not MONOLITH_BACKUP.exists():
        MONOLITH_BACKUP.write_text("".join(all_lines), encoding="utf-8")

    print("split work_orders router OK")


if __name__ == "__main__":
    main()
