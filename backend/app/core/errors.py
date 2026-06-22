"""API error catalog — stable codes with bilingual user messages (NT-131).

Routes may raise HTTPException(detail="CODE") or detail={"code": "...", ...}.
The global handler expands string codes to { code, message_en, message_ar }.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

# code -> (message_en, message_ar)
ERROR_CATALOG: dict[str, tuple[str, str]] = {
    "NOT_FOUND": (
        "The requested item was not found.",
        "العنصر المطلوب غير موجود.",
    ),
    "FORBIDDEN": (
        "You don't have permission for this action.",
        "ليس لديك صلاحية لتنفيذ هذا الإجراء.",
    ),
    "FEATURE_NOT_AVAILABLE": (
        "This feature is not included in your subscription.",
        "هذه الميزة غير متوفرة في باقة اشتراكك.",
    ),
    "INVALID_CREDENTIALS": (
        "Invalid email or password.",
        "البريد أو كلمة المرور غير صحيحة.",
    ),
    "USER_INACTIVE": (
        "This account is inactive. Contact your administrator.",
        "الحساب غير نشط — تواصل مع المسؤول.",
    ),
    "INVALID_TOKEN": (
        "Your session has expired. Please sign in again.",
        "انتهت صلاحية الجلسة. يرجى تسجيل الدخول مرة أخرى.",
    ),
    "EMAIL_ALREADY_IN_USE": (
        "This email address is already registered.",
        "البريد الإلكتروني مسجّل مسبقاً.",
    ),
    "CODE_IN_USE": (
        "This company code is already in use.",
        "رمز الشركة مستخدم مسبقاً.",
    ),
    "INVALID_TRANSITION": (
        "This status change is not allowed.",
        "تغيير الحالة غير مسموح.",
    ),
    "INVALID_STATUS": (
        "The selected status is not valid.",
        "الحالة المحددة غير صالحة.",
    ),
    "ASSIGNEE_REQUIRED": (
        "Please assign a user before changing status to assigned.",
        "يرجى اختيار موظف قبل تعيين أمر العمل.",
    ),
    "HOLD_REASON_REQUIRED": (
        "Hold reason is required to place this work order on hold.",
        "سبب الإيقاف مطلوب لإيقاف أمر العمل مؤقتاً.",
    ),
    "REPORT_REQUIRED": (
        "The maintenance report must be submitted before marking as completed.",
        "يجب تقديم تقرير الصيانة قبل وضع علامة مكتمل.",
    ),
    "CANCELLATION_REASON_REQUIRED": (
        "Cancellation reason is required.",
        "سبب الإلغاء مطلوب.",
    ),
    "REPORT_NOT_ALLOWED_AT_THIS_STATUS": (
        "The report can be filled while the work order is in progress or on hold.",
        "يمكن ملء التقرير أثناء التنفيذ أو الإيقاف المؤقت فقط.",
    ),
    "REPORT_NOT_EDITABLE": (
        "This report can no longer be edited.",
        "لا يمكن تعديل هذا التقرير.",
    ),
    "REPORT_NOT_STARTED": (
        "No maintenance report exists for this work order yet.",
        "لا يوجد تقرير صيانة لهذا أمر العمل بعد.",
    ),
    "INVALID_ASSIGNEE": (
        "The selected user cannot be assigned to this work order.",
        "لا يمكن تعيين المستخدم المحدد على أمر العمل.",
    ),
    "INVALID_CLIENT_SITE": (
        "The selected company or site is not valid.",
        "الشركة أو الموقع المحدد غير صالح.",
    ),
    "INVALID_ASSET": (
        "The selected asset is not valid for this work order.",
        "الأصل المحدد غير صالح لأمر العمل.",
    ),
    "INVALID_LOCATION": (
        "The selected location is not valid.",
        "الموقع المحدد غير صالح.",
    ),
    "ASSET_RETIRED": (
        "This asset is retired and cannot be modified.",
        "الأصل مُستبدَل/متقاعد ولا يمكن تعديله.",
    ),
    "VALIDATION_ERROR": (
        "Please complete all required fields.",
        "يرجى إكمال جميع الحقول المطلوبة.",
    ),
    "VALIDATION_ERRORS": (
        "Some fields failed validation. Check your input and try again.",
        "فشل التحقق من بعض الحقول. راجع المدخلات وحاول مرة أخرى.",
    ),
    "WORK_ORDER_NOT_VERIFIED": (
        "Work order must be verified or closed before invoicing.",
        "يجب أن يكون أمر العمل في حالة verified أو closed قبل الفوترة.",
    ),
    "REPORT_NOT_APPROVED": (
        "The maintenance report must be submitted or approved before invoicing.",
        "يجب الموافقة على التقرير (أو تقديمه) قبل إنشاء الفاتورة.",
    ),
    "INVOICE_EXISTS": (
        "An invoice already exists for this work order.",
        "تم إنشاء فاتورة لهذا أمر العمل مسبقاً.",
    ),
    "NO_ACTIVE_CONTRACT": (
        "No active billing contract for this company.",
        "لا يوجد عقد فوترة نشط لهذه الشركة.",
    ),
    "PRICING_NOT_FOUND": (
        "Pricing profile linked to the contract was not found.",
        "ملف التسعير المرتبط بالعقد غير موجود.",
    ),
    "CANNOT_REMOVE_MEMBERS": (
        "You cannot remove members with this role.",
        "لا يمكنك إزالة أعضاء بهذا الدور.",
    ),
    "CANNOT_EDIT_CONTACT": (
        "You cannot edit this user's contact details.",
        "لا يمكنك تعديل بيانات اتصال هذا المستخدم.",
    ),
    "AI_SCHEDULING_NOT_AVAILABLE": (
        "AI maintenance scheduling is not available on your plan.",
        "جدولة الصيانة بالذكاء الاصطناعي غير متوفرة في باقتك.",
    ),
    "LICENSE_FROZEN": (
        "Your subscription is frozen. Contact support to restore access.",
        "اشتراكك مجمّد. تواصل مع الدعم لاستعادة الوصول.",
    ),
}


def expand_error_detail(detail: Any) -> Any:
    """Expand string or dict codes with bilingual messages."""
    if isinstance(detail, str):
        messages = ERROR_CATALOG.get(detail)
        if messages:
            en, ar = messages
            return {"code": detail, "message_en": en, "message_ar": ar}
        return detail

    if isinstance(detail, dict):
        code = detail.get("code")
        if isinstance(code, str) and code in ERROR_CATALOG and "message_en" not in detail:
            en, ar = ERROR_CATALOG[code]
            return {**detail, "message_en": en, "message_ar": ar}
        return detail

    return detail


def api_error(status_code: int, code: str, **extra: Any) -> HTTPException:
    """Raise HTTPException with catalog-backed detail."""
    en, ar = ERROR_CATALOG.get(code, (code.replace("_", " ").title(), code))
    payload: dict[str, Any] = {"code": code, "message_en": en, "message_ar": ar, **extra}
    return HTTPException(status_code=status_code, detail=payload)


async def http_exception_handler(_request: Request, exc: HTTPException) -> JSONResponse:
    detail = expand_error_detail(exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"detail": detail})
