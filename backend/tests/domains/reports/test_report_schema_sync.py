"""Tests for report schema resolution and STD-INSP sync."""

from uuid import uuid4

import pytest

from app.models import Client, ReportTemplate, Site, Tenant
from app.services.report_schema_resolve import (
    DEFAULT_CATEGORY_KEY,
    observation_fields_for_category,
    resolve_effective_schema,
    set_category_observations,
)
from app.services.report_template_sync import sync_std_insp_for_tenant
from app.standard_inspection_report_schema import STANDARD_INSPECTION_SCHEMA


@pytest.fixture
def tenant(db_session):
    t = Tenant(id=uuid4(), name="Sync Tenant", status="active")
    db_session.add(t)
    db_session.commit()
    return t


def test_resolve_effective_schema_uses_category_override():
    schema = dict(STANDARD_INSPECTION_SCHEMA)
    hvac_fields = [
        {
            "id": "filter_condition",
            "type": "checklist",
            "label": "Filter condition",
            "options": ["Clean", "Dirty"],
            "required": True,
        }
    ]
    schema = set_category_observations(schema, "HVAC", hvac_fields)
    effective = resolve_effective_schema(schema, "HVAC")
    obs = next(s for s in effective["sections"] if s["id"] == "sec_observations")
    assert obs["fields"][0]["id"] == "filter_condition"

    default_effective = resolve_effective_schema(schema, "Elevators")
    obs_default = next(s for s in default_effective["sections"] if s["id"] == "sec_observations")
    assert obs_default["fields"][0]["id"] == "overall_condition"


def test_sync_std_insp_creates_and_upgrades(db_session, tenant):
    action, tmpl = sync_std_insp_for_tenant(db_session, tenant.id)
    assert action == "created"
    assert tmpl.code == "STD-INSP"
    assert tmpl.version == 2
    assert DEFAULT_CATEGORY_KEY in tmpl.schema_json.get("observations_by_category", {})

    tmpl.schema_json = {"version": 1, "sections": []}
    db_session.flush()
    action2, tmpl2 = sync_std_insp_for_tenant(db_session, tenant.id)
    assert action2 == "updated"
    assert tmpl2.schema_json.get("version") == 2
    assert observation_fields_for_category(tmpl2.schema_json, None)
