"""Short fill profiles + PDF answer normalization."""

from datetime import datetime, timedelta, timezone

from app.models import WorkOrderSource
from app.services.report_fill_profiles import (
    fill_profile_for_source,
    normalize_answers_for_pdf,
    short_schema_for_source,
)
from app.services.report_schema_resolve import resolve_effective_schema


def test_profiles_split_by_source():
    assert fill_profile_for_source(WorkOrderSource.preventive) == "preventive_short"
    assert fill_profile_for_source(WorkOrderSource.corrective) == "corrective_short"
    assert fill_profile_for_source(WorkOrderSource.request) == "corrective_short"
    pm = short_schema_for_source("preventive")
    corr = short_schema_for_source("corrective")
    assert pm["fill_profile"] == "preventive_short"
    assert corr["fill_profile"] == "corrective_short"
    assert any(f.get("id") == "round_result" for s in pm["sections"] for f in s.get("fields") or [])
    assert any(f.get("id") == "symptom" for s in corr["sections"] for f in s.get("fields") or [])


def test_resolve_effective_uses_short_fill():
    schema = resolve_effective_schema({}, wo_source="preventive", use_short_fill=True)
    assert schema.get("fill_profile") == "preventive_short"


def test_normalize_corrective_maps_to_pdf_fields():
    out = normalize_answers_for_pdf(
        {
            "symptom": "Leak",
            "symptom_detail": "Drip at flange",
            "fix_action": "Tightened bolts",
            "replaced_parts": "Yes",
            "parts_note": "Gasket DN50",
            "overall_condition": "Fair",
        }
    )
    assert "Leak" in out["findings_defects"]
    assert "Tightened" in out["tests_performed"]
    assert out["parts_used"][0]["name"] == "Gasket DN50"


def test_normalize_keeps_catalog_parts_used():
    out = normalize_answers_for_pdf(
        {
            "replaced_parts": "Yes",
            "parts_used": [
                {"part_id": "abc", "name": "HEPA Filter", "sku": "FILT-01", "quantity": 2}
            ],
        }
    )
    assert out["parts_used"][0]["sku"] == "FILT-01"
    assert out["parts_used"][0]["quantity"] == 2


def test_corrective_short_requires_parts_when_yes():
    from app.services.report_validation import validate_required_fields

    schema = short_schema_for_source("corrective")
    missing = validate_required_fields(
        schema,
        {
            "symptom": "Leak",
            "fix_action": "Replaced gasket",
            "replaced_parts": "Yes",
            "overall_condition": "Fair",
        },
    )
    assert any("Parts used" in m for m in missing)
    ok = validate_required_fields(
        schema,
        {
            "symptom": "Leak",
            "fix_action": "Replaced gasket",
            "replaced_parts": "Yes",
            "parts_used": [{"part_id": "1", "name": "Gasket", "sku": "G1", "quantity": 1}],
            "overall_condition": "Fair",
        },
    )
    assert ok == []


def test_normalize_preventive_ok():
    out = normalize_answers_for_pdf({"round_result": "Done OK"})
    assert out["overall_condition"] == "Good"
    assert "OK" in out["tests_performed"]


def test_job_elapsed_hours():
    from types import SimpleNamespace

    from app.services.report_context import _job_elapsed_hours

    start = datetime(2026, 10, 25, 8, 0, tzinfo=timezone.utc)
    end = start + timedelta(hours=3, minutes=30)
    wo = SimpleNamespace(job_started_at=start, job_ended_at=end)
    assert _job_elapsed_hours(wo) == 3.5
