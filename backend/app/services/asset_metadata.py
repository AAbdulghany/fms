"""Asset metadata_json helpers for extended registration fields."""

from __future__ import annotations

from datetime import date
from typing import Any

from app.models import Asset


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        return date.fromisoformat(value)
    return None


def read_asset_meta(asset: Asset) -> dict[str, Any]:
    meta = dict(asset.metadata_json or {})
    return {
        "floor": meta.get("floor"),
        "room": meta.get("room"),
        "smart_labels": list(meta.get("smart_labels") or []),
        "criticality": meta.get("criticality"),
        "last_maintenance_date": _parse_date(meta.get("last_maintenance_date")),
        "is_spare": bool(meta.get("is_spare", False)),
        "photo_url": meta.get("photo_url"),
    }


def write_asset_meta(
    asset: Asset,
    *,
    floor: str | None = None,
    room: str | None = None,
    smart_labels: list[str] | None = None,
    criticality: str | None = None,
    last_maintenance_date: date | None = None,
    clear_last_maintenance: bool = False,
    is_spare: bool | None = None,
    photo_url: str | None = None,
) -> None:
    meta = dict(asset.metadata_json or {})
    if floor is not None:
        meta["floor"] = floor.strip() if floor else None
    if room is not None:
        meta["room"] = room.strip() if room else None
    if smart_labels is not None:
        meta["smart_labels"] = [s.strip() for s in smart_labels if s and s.strip()]
    if criticality is not None:
        meta["criticality"] = criticality.strip() if criticality else None
    if clear_last_maintenance:
        meta.pop("last_maintenance_date", None)
    elif last_maintenance_date is not None:
        meta["last_maintenance_date"] = last_maintenance_date.isoformat()
    if is_spare is not None:
        meta["is_spare"] = is_spare
    if photo_url is not None:
        meta["photo_url"] = photo_url.strip() if photo_url else None
    asset.metadata_json = meta


def expected_eol_date(asset: Asset) -> date | None:
    if not asset.installed_on or not asset.max_age_years:
        return None
    try:
        return date(
            asset.installed_on.year + asset.max_age_years,
            asset.installed_on.month,
            asset.installed_on.day,
        )
    except ValueError:
        return date(
            asset.installed_on.year + asset.max_age_years,
            asset.installed_on.month,
            28,
        )
