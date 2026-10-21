"""A1 — Pydantic schemas for verticals and asset type library."""

from __future__ import annotations

from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Verticals
# ---------------------------------------------------------------------------


class VerticalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name_en: str
    name_ar: str
    sort_order: int = 0


# ---------------------------------------------------------------------------
# Asset type template (platform catalog)
# ---------------------------------------------------------------------------


class AssetTypeTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name_en: str
    name_ar: str
    vertical_codes: list[str] = Field(default_factory=list)
    default_max_age_years: Optional[int] = None
    default_max_repair_count: Optional[int] = None
    default_criticality: Optional[str] = None
    default_frequency: Optional[str] = None
    version: int
    is_active: bool = True
    # Caller-specific: set by the router when the template is already adopted
    adopted: bool = False
    asset_type_id: Optional[UUID] = None


# ---------------------------------------------------------------------------
# Tenant asset type library
# ---------------------------------------------------------------------------


class AssetTypeRef(BaseModel):
    """Embedded in AssetOut; lightweight reference."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name_en: str
    name_ar: str


class AssetTypeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name_en: str
    name_ar: str
    origin: Literal["catalog", "custom", "legacy"]
    vertical_codes: list[str] = Field(default_factory=list)
    default_max_age_years: Optional[int] = None
    default_max_repair_count: Optional[int] = None
    default_criticality: Optional[str] = None
    default_frequency: Optional[str] = None
    default_report_template_id: Optional[UUID] = None
    source_template_id: Optional[UUID] = None
    source_version: Optional[int] = None
    is_active: bool = True
    recommended: bool = False
    asset_count: int = 0


class AssetTypeCreate(BaseModel):
    code: str = Field(
        ...,
        min_length=1,
        max_length=64,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9 _\-]*$",
    )
    name_en: str = Field(..., min_length=1, max_length=128)
    name_ar: str = Field(..., min_length=1, max_length=128)
    vertical_codes: list[str] = Field(default_factory=list)
    default_max_age_years: Optional[int] = Field(None, ge=1, le=100)
    default_max_repair_count: Optional[int] = Field(None, ge=0, le=1000)
    default_criticality: Optional[str] = Field(None, max_length=32)
    default_frequency: Optional[Literal["monthly", "quarterly", "yearly"]] = None
    default_report_template_id: Optional[UUID] = None


class AssetTypeUpdate(BaseModel):
    """All fields optional; ``code`` is absent (immutable)."""

    name_en: Optional[str] = Field(None, min_length=1, max_length=128)
    name_ar: Optional[str] = Field(None, min_length=1, max_length=128)
    vertical_codes: Optional[list[str]] = None
    default_max_age_years: Optional[int] = Field(None, ge=1, le=100)
    default_max_repair_count: Optional[int] = Field(None, ge=0, le=1000)
    default_criticality: Optional[str] = Field(None, max_length=32)
    default_frequency: Optional[Literal["monthly", "quarterly", "yearly"]] = None
    default_report_template_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    # Guard: reject if caller accidentally sends `code`
    # Do NOT mark exclude=True — we need to detect it in the router via model_fields_set
    code: Optional[Any] = None


class AssetTypeAdoptRequest(BaseModel):
    template_ids: list[UUID] = Field(..., min_length=1, max_length=100)


class AssetTypeAdoptSkipped(BaseModel):
    template_id: UUID
    asset_type_id: Optional[UUID] = None
    reason: str


class AssetTypeAdoptResponse(BaseModel):
    created: list[AssetTypeOut]
    skipped: list[AssetTypeAdoptSkipped]
