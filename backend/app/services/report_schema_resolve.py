"""Resolve effective report template schemas (category-specific observation checklists)."""

from __future__ import annotations

import copy
from typing import Any

OBSERVATIONS_SECTION_ID = "sec_observations"
DEFAULT_CATEGORY_KEY = "_default"


def default_observation_fields() -> list[dict[str, Any]]:
    return [
        {
            "id": "overall_condition",
            "type": "checklist",
            "label": "Overall condition",
            "options": ["Good", "Fair", "Poor", "Critical"],
            "required": True,
        },
        {
            "id": "findings_defects",
            "type": "textarea",
            "label": "Findings / defects",
            "rows": 5,
            "required": True,
        },
    ]


def get_observations_by_category(schema: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    stored = schema.get("observations_by_category")
    if isinstance(stored, dict) and stored:
        return {str(k): list(v) for k, v in stored.items() if isinstance(v, list)}

    for sec in schema.get("sections", []):
        if sec.get("id") == OBSERVATIONS_SECTION_ID:
            fields = sec.get("fields") or []
            if fields:
                return {DEFAULT_CATEGORY_KEY: list(fields)}
    return {DEFAULT_CATEGORY_KEY: default_observation_fields()}


def observation_fields_for_category(schema: dict[str, Any], asset_category: str | None) -> list[dict[str, Any]]:
    by_cat = get_observations_by_category(schema)
    key = (asset_category or "").strip()
    if key and key in by_cat:
        return copy.deepcopy(by_cat[key])
    return copy.deepcopy(by_cat.get(DEFAULT_CATEGORY_KEY) or default_observation_fields())


def resolve_effective_schema(schema: dict[str, Any], asset_category: str | None = None) -> dict[str, Any]:
    """Return a copy of the template schema with category-specific observation fields applied."""
    effective = copy.deepcopy(schema or {})
    fields = observation_fields_for_category(effective, asset_category)
    sections = effective.get("sections") or []
    for sec in sections:
        if sec.get("id") == OBSERVATIONS_SECTION_ID:
            sec["fields"] = fields
            break
    else:
        sections.append(
            {
                "id": OBSERVATIONS_SECTION_ID,
                "title": "Observations",
                "category_variant": True,
                "fields": fields,
            }
        )
        effective["sections"] = sections
    return effective


def set_category_observations(
    schema: dict[str, Any],
    category_key: str,
    fields: list[dict[str, Any]],
) -> dict[str, Any]:
    """Persist observation checklist fields for a category (mutates and returns schema)."""
    key = category_key.strip()
    if not key:
        raise ValueError("CATEGORY_KEY_REQUIRED")
    updated = copy.deepcopy(schema or {})
    by_cat = get_observations_by_category(updated)
    by_cat[key] = copy.deepcopy(fields)
    updated["observations_by_category"] = by_cat

    if key == DEFAULT_CATEGORY_KEY:
        for sec in updated.get("sections", []):
            if sec.get("id") == OBSERVATIONS_SECTION_ID:
                sec["fields"] = copy.deepcopy(fields)
                break
    return updated


def delete_category_observations(schema: dict[str, Any], category_key: str) -> dict[str, Any]:
    if category_key == DEFAULT_CATEGORY_KEY:
        raise ValueError("CANNOT_DELETE_DEFAULT")
    updated = copy.deepcopy(schema or {})
    by_cat = get_observations_by_category(updated)
    by_cat.pop(category_key, None)
    updated["observations_by_category"] = by_cat
    return updated
