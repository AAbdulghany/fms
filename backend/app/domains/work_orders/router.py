"""Work orders API — aggregates route modules by concern."""

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
