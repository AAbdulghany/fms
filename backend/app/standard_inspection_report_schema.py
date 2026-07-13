"""JSON schema for the Standard Inspection report template (form fields).

Technician-visible fields are minimal; auto_fill fields are merged by the backend
for PDF output and hidden from the data-entry UI.

Category-specific observation checklists live in ``observations_by_category`` and
are resolved at report time via ``report_schema_resolve.resolve_effective_schema``.
"""

from app.services.report_schema_resolve import default_observation_fields

_DEFAULT_OBS = default_observation_fields()

STANDARD_INSPECTION_SCHEMA: dict = {
    "version": 2,
    "observations_by_category": {
        "_default": _DEFAULT_OBS,
    },
    "sections": [
        {
            "id": "sec_auto",
            "title": "Report context (auto-filled)",
            "visible": False,
            "fields": [
                {
                    "id": "inspector_full_name",
                    "type": "header",
                    "label": "Inspector full name",
                    "auto_fill": True,
                },
                {
                    "id": "inspector_title",
                    "type": "header",
                    "label": "Inspector title / role",
                    "auto_fill": True,
                },
                {
                    "id": "inspector_contact",
                    "type": "header",
                    "label": "Inspector contact (phone / email)",
                    "auto_fill": True,
                },
                {
                    "id": "inspector_license",
                    "type": "header",
                    "label": "Accreditation or license number",
                    "auto_fill": True,
                },
                {
                    "id": "property_site_name",
                    "type": "header",
                    "label": "Property / site name",
                    "auto_fill": True,
                },
                {
                    "id": "property_full_address",
                    "type": "header",
                    "label": "Full site address",
                    "auto_fill": True,
                },
                {
                    "id": "asset_unit_identification",
                    "type": "header",
                    "label": "Specific asset or unit ID",
                    "auto_fill": True,
                },
                {
                    "id": "location_name",
                    "type": "header",
                    "label": "Location",
                    "auto_fill": True,
                },
                {
                    "id": "inspection_date",
                    "type": "header",
                    "label": "Inspection date",
                    "auto_fill": True,
                },
                {
                    "id": "inspection_start_time",
                    "type": "header",
                    "label": "Start time",
                    "auto_fill": True,
                },
                {
                    "id": "inspection_type",
                    "type": "header",
                    "label": "Inspection type",
                    "auto_fill": True,
                },
                {
                    "id": "scope_systems_list",
                    "type": "header",
                    "label": "Scope — systems examined",
                    "auto_fill": True,
                },
                {
                    "id": "reference_documents",
                    "type": "header",
                    "label": "Reference documents",
                    "auto_fill": True,
                },
                {
                    "id": "time_elapsed_hours",
                    "type": "header",
                    "label": "Time elapsed (hours)",
                    "auto_fill": True,
                },
            ],
        },
        {
            "id": "sec_visit",
            "title": "Site visit",
            "title_key": "report_section_sec_visit",
            "fields": [
                {
                    "id": "inspection_end_time",
                    "type": "time",
                    "label": "End time",
                    "label_key": "report_field_inspection_end_time",
                    "required": True,
                },
                {
                    "id": "environmental_factors",
                    "type": "textarea",
                    "label": "Environmental / site conditions (optional)",
                    "label_key": "report_field_environmental_factors",
                    "rows": 3,
                    "required": False,
                },
                {
                    "id": "tests_performed",
                    "type": "textarea",
                    "label": "Specific tests performed",
                    "label_key": "report_field_tests_performed",
                    "rows": 4,
                    "required": True,
                },
                {
                    "id": "areas_not_inspected",
                    "type": "textarea",
                    "label": "Areas not inspected or deemed unsafe",
                    "label_key": "report_field_areas_not_inspected",
                    "rows": 3,
                    "required": False,
                },
            ],
        },
        {
            "id": "sec_observations",
            "title": "Observations",
            "title_key": "report_section_sec_observations",
            "category_variant": True,
            "fields": _DEFAULT_OBS,
        },
        {
            "id": "sec_evidence",
            "title": "Supporting evidence",
            "title_key": "report_section_sec_evidence",
            "fields": [
                {
                    "id": "photo_documentation",
                    "type": "photo",
                    "label": "Photo documentation",
                    "label_key": "report_field_photo_documentation",
                    "max_photos": 12,
                    "required": False,
                    "required_when": {
                        "field": "overall_condition",
                        "values": ["Poor", "Critical"],
                    },
                },
            ],
        },
        {
            "id": "sec_resolution",
            "title": "Resolution",
            "title_key": "report_section_sec_resolution",
            "fields": [
                {
                    "id": "parts_used",
                    "type": "parts_used",
                    "label_key": "parts_used",
                    "required": False,
                },
                {
                    "id": "labor_log",
                    "type": "labor_log",
                    "label_key": "labor_hours",
                    "required": False,
                },
                {
                    "id": "recommended_actions",
                    "type": "textarea",
                    "label": "Recommended actions",
                    "label_key": "report_field_recommended_actions",
                    "rows": 4,
                    "required": False,
                },
            ],
        },
    ],
}
