"""A5 — tenant failure / symptom code catalog + downtime helpers."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import DiagnosticCode

DEFAULT_FAILURE_CODES: list[tuple[str, str, str]] = [
    ("MECH_FAIL", "Mechanical failure", "عطل ميكانيكي"),
    ("ELEC_FAIL", "Electrical failure", "عطل كهربائي"),
    ("SENSOR_FAIL", "Sensor / control failure", "عطل حساس / تحكم"),
    ("LEAK", "Leak", "تسريب"),
    ("OVERHEAT", "Overheating", "ارتفاع حرارة"),
    ("NO_POWER", "No power / won't start", "لا يعمل / لا طاقة"),
    ("SOFTWARE", "Software / firmware", "برمجيات / برنامج ثابت"),
    ("OTHER", "Other", "أخرى"),
]

DEFAULT_SYMPTOM_CODES: list[tuple[str, str, str]] = [
    ("NOISE", "Unusual noise", "ضوضاء غير طبيعية"),
    ("VIBRATION", "Vibration", "اهتزاز"),
    ("NO_COOL", "No cooling", "لا تبريد"),
    ("NO_HEAT", "No heating", "لا تدفئة"),
    ("ERROR_CODE", "Error code displayed", "رمز خطأ ظاهر"),
    ("INTERMITTENT", "Intermittent fault", "عطل متقطع"),
    ("LEAKING", "Leaking", "يتسرب"),
    ("WONT_START", "Won't start", "لا يبدأ"),
    ("OTHER", "Other", "أخرى"),
]


def downtime_minutes(started: datetime | None, ended: datetime | None) -> int | None:
    if not started or not ended:
        return None
    delta = ended - started
    secs = int(delta.total_seconds())
    if secs < 0:
        return None
    return secs // 60


def ensure_default_codes(db: Session, tenant_id: UUID) -> None:
    existing = db.scalar(
        select(DiagnosticCode.id).where(DiagnosticCode.tenant_id == tenant_id).limit(1)
    )
    if existing:
        return
    rows: list[DiagnosticCode] = []
    for code, en, ar in DEFAULT_FAILURE_CODES:
        rows.append(
            DiagnosticCode(
                tenant_id=tenant_id,
                kind="failure",
                code=code,
                name_en=en,
                name_ar=ar,
                is_active=True,
            )
        )
    for code, en, ar in DEFAULT_SYMPTOM_CODES:
        rows.append(
            DiagnosticCode(
                tenant_id=tenant_id,
                kind="symptom",
                code=code,
                name_en=en,
                name_ar=ar,
                is_active=True,
            )
        )
    db.add_all(rows)
    db.commit()


def list_codes(
    db: Session,
    tenant_id: UUID,
    *,
    kind: str | None = None,
    active_only: bool = True,
) -> list[DiagnosticCode]:
    ensure_default_codes(db, tenant_id)
    q = select(DiagnosticCode).where(DiagnosticCode.tenant_id == tenant_id)
    if kind:
        q = q.where(DiagnosticCode.kind == kind)
    if active_only:
        q = q.where(DiagnosticCode.is_active.is_(True))
    q = q.order_by(DiagnosticCode.kind, DiagnosticCode.code)
    return list(db.scalars(q).all())
