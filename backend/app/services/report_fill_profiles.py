"""Short guided report profiles — preventive vs corrective (L1 fill redesign).

Technician-facing fields are minimal; PDF still consumes findings / condition /
labor / parts via ``normalize_answers_for_pdf``.
"""

from __future__ import annotations

from typing import Any

from app.models import WorkOrderSource

_AUTO_SECTION: dict[str, Any] = {
    "id": "sec_auto",
    "title": "Report context (auto-filled)",
    "visible": False,
    "fields": [
        {"id": "inspector_full_name", "type": "header", "label": "Inspector", "auto_fill": True},
        {"id": "inspector_title", "type": "header", "label": "Role", "auto_fill": True},
        {"id": "inspector_contact", "type": "header", "label": "Contact", "auto_fill": True},
        {"id": "inspector_license", "type": "header", "label": "License", "auto_fill": True},
        {"id": "client_legal_name", "type": "header", "label": "Client", "auto_fill": True},
        {"id": "property_site_name", "type": "header", "label": "Site", "auto_fill": True},
        {"id": "property_full_address", "type": "header", "label": "Address", "auto_fill": True},
        {"id": "asset_unit_identification", "type": "header", "label": "Asset", "auto_fill": True},
        {"id": "location_name", "type": "header", "label": "Location", "auto_fill": True},
        {"id": "inspection_date", "type": "header", "label": "Date", "auto_fill": True},
        {"id": "inspection_start_time", "type": "header", "label": "Start time", "auto_fill": True},
        {"id": "inspection_end_time", "type": "header", "label": "End time", "auto_fill": True},
        {"id": "inspection_type", "type": "header", "label": "Type", "auto_fill": True},
        {"id": "scope_systems_list", "type": "header", "label": "Scope", "auto_fill": True},
        {"id": "time_elapsed_hours", "type": "header", "label": "Hours", "auto_fill": True},
        {"id": "labor_log", "type": "header", "label": "Labor", "auto_fill": True},
    ],
}

CORRECTIVE_SHORT_SCHEMA: dict[str, Any] = {
    "version": 3,
    "fill_profile": "corrective_short",
    "observations_by_category": {"_default": []},
    "sections": [
        _AUTO_SECTION,
        {
            "id": "sec_symptom",
            "title": "What was wrong?",
            "fill_step": 1,
            "fields": [
                {
                    "id": "symptom",
                    "type": "checklist",
                    "label": "Symptom",
                    "label_key": "report_field_symptom",
                    "options": [
                        "No power / won't start",
                        "Overheating",
                        "Leak",
                        "Noise / vibration",
                        "Not cooling / heating",
                        "Alarm / trip",
                        "Other",
                    ],
                    "required": True,
                },
                {
                    "id": "symptom_detail",
                    "type": "text",
                    "label": "More detail (optional)",
                    "label_key": "report_field_symptom_detail",
                    "required": False,
                },
            ],
        },
        {
            "id": "sec_fix",
            "title": "What did you do?",
            "fill_step": 2,
            "fields": [
                {
                    "id": "fix_action",
                    "type": "textarea",
                    "label": "Action taken",
                    "label_key": "report_field_fix_action",
                    "rows": 3,
                    "required": True,
                },
                {
                    "id": "replaced_parts",
                    "type": "checklist",
                    "label": "Replaced parts?",
                    "label_key": "report_field_replaced_parts",
                    "options": ["No", "Yes"],
                    "required": True,
                },
                {
                    "id": "parts_used",
                    "type": "parts_used",
                    "label": "Parts used",
                    "label_key": "report_field_parts_note",
                    "required": False,
                    "required_when": {"field": "replaced_parts", "values": ["Yes"]},
                },
            ],
        },
        {
            "id": "sec_close",
            "title": "Close out",
            "fill_step": 3,
            "fields": [
                {
                    "id": "overall_condition",
                    "type": "checklist",
                    "label": "Overall condition",
                    "label_key": "report_field_overall_condition",
                    "options": ["Good", "Fair", "Poor", "Critical"],
                    "required": True,
                },
                {
                    "id": "photo_documentation",
                    "type": "photo",
                    "label": "Photos",
                    "label_key": "report_field_photo_documentation",
                    "max_photos": 8,
                    "required": False,
                    "required_when": {
                        "field": "overall_condition",
                        "values": ["Poor", "Critical"],
                    },
                },
            ],
        },
    ],
}

PREVENTIVE_SHORT_SCHEMA: dict[str, Any] = {
    "version": 3,
    "fill_profile": "preventive_short",
    "observations_by_category": {"_default": []},
    "sections": [
        _AUTO_SECTION,
        {
            "id": "sec_round",
            "title": "Round result",
            "fill_step": 1,
            "fields": [
                {
                    "id": "round_result",
                    "type": "checklist",
                    "label": "Round result",
                    "label_key": "report_field_round_result",
                    "options": ["Done OK", "Done with issues"],
                    "required": True,
                },
            ],
        },
        {
            "id": "sec_issues",
            "title": "Issues",
            "fill_step": 2,
            "fields": [
                {
                    "id": "issue_notes",
                    "type": "textarea",
                    "label": "What needs attention",
                    "label_key": "report_field_issue_notes",
                    "rows": 3,
                    "required": False,
                    "required_when": {
                        "field": "round_result",
                        "values": ["Done with issues"],
                    },
                },
                {
                    "id": "overall_condition",
                    "type": "checklist",
                    "label": "Overall condition",
                    "label_key": "report_field_overall_condition",
                    "options": ["Good", "Fair", "Poor", "Critical"],
                    "required": True,
                },
                {
                    "id": "photo_documentation",
                    "type": "photo",
                    "label": "Photos",
                    "label_key": "report_field_photo_documentation",
                    "max_photos": 8,
                    "required": False,
                    "required_when": {
                        "field": "overall_condition",
                        "values": ["Poor", "Critical"],
                    },
                },
            ],
        },
    ],
}


def fill_profile_for_source(source: WorkOrderSource | str | None) -> str:
    raw = source.value if isinstance(source, WorkOrderSource) else str(source or "")
    if raw == WorkOrderSource.preventive.value:
        return "preventive_short"
    return "corrective_short"


def short_schema_for_source(source: WorkOrderSource | str | None) -> dict[str, Any]:
    import copy

    profile = fill_profile_for_source(source)
    if profile == "preventive_short":
        return copy.deepcopy(PREVENTIVE_SHORT_SCHEMA)
    return copy.deepcopy(CORRECTIVE_SHORT_SCHEMA)


def normalize_answers_for_pdf(answers: dict[str, Any] | None) -> dict[str, Any]:
    """Map short-form answers onto classic PDF fields (findings, tests, parts)."""
    a = dict(answers or {})
    findings_bits: list[str] = []

    symptom = str(a.get("symptom") or "").strip()
    detail = str(a.get("symptom_detail") or "").strip()
    fix = str(a.get("fix_action") or "").strip()
    round_result = str(a.get("round_result") or "").strip()
    issue_notes = str(a.get("issue_notes") or "").strip()

    if symptom:
        findings_bits.append(f"Symptom: {symptom}")
    if detail:
        findings_bits.append(detail)
    if fix:
        findings_bits.append(f"Action: {fix}")
    if round_result:
        findings_bits.append(f"Round: {round_result}")
    if issue_notes:
        findings_bits.append(issue_notes)

    if findings_bits and not str(a.get("findings_defects") or "").strip():
        a["findings_defects"] = "\n".join(findings_bits)

    if fix and not str(a.get("tests_performed") or "").strip():
        a["tests_performed"] = fix
    elif round_result and not str(a.get("tests_performed") or "").strip():
        a["tests_performed"] = (
            "Preventive round completed with issues."
            if round_result == "Done with issues"
            else "Preventive round completed — OK."
        )

    if round_result == "Done OK" and not str(a.get("overall_condition") or "").strip():
        a["overall_condition"] = "Good"

    parts_note = str(a.get("parts_note") or "").strip()
    raw_parts = a.get("parts_used")
    if isinstance(raw_parts, list) and raw_parts:
        cleaned: list[dict[str, Any]] = []
        for row in raw_parts:
            if not isinstance(row, dict):
                continue
            name = str(row.get("name") or row.get("part_name") or "").strip()
            sku = str(row.get("sku") or row.get("part_sku") or "").strip()
            qty = row.get("quantity", row.get("qty", 1))
            if not name and not sku:
                continue
            cleaned.append(
                {
                    "part_id": str(row.get("part_id") or "").strip() or None,
                    "name": name or sku,
                    "sku": sku or "—",
                    "quantity": qty,
                }
            )
        if cleaned:
            a["parts_used"] = cleaned
    elif a.get("replaced_parts") == "Yes" and parts_note:
        a["parts_used"] = [{"name": parts_note, "sku": "", "quantity": 1}]

    return a
