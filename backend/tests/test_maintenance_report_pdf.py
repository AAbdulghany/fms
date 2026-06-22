"""Maintenance report PDF/HTML rendering smoke tests."""

from app.services.maintenance_report_pdf import (
    build_report_view_model,
    render_maintenance_report_html,
    render_maintenance_report_pdf,
)
from app.services.pdf_brand import LOGO_SVG_PATH, PRIMARY_500


def test_logo_asset_exists():
    assert LOGO_SVG_PATH.is_file()


def test_html_template_renders_rtl():
    ctx = build_report_view_model(
        tenant_name="Orbit Demo Co",
        work_order_title="PM01",
        work_order_id="wo-123",
        answers={
            "property_site_name": "Tower A",
            "property_full_address": "123 Main, Riyadh",
            "asset_unit_identification": "CH-01",
            "inspection_date": "2026-06-22",
            "inspection_type": "Routine / periodic",
            "scope_systems_list": "hvac — general",
            "inspector_full_name": "Sara Tech",
            "inspector_title": "Technician",
            "inspector_contact": "+966 / tech@test.com",
            "inspection_start_time": "09:00",
            "inspection_end_time": "11:30",
            "time_elapsed_hours": 2.5,
            "overall_condition": "Good",
            "findings_defects": "Minor dust on coils.",
        },
        lang="ar",
    )
    html = render_maintenance_report_html(ctx)
    assert 'dir="rtl"' in html
    assert PRIMARY_500 in html
    assert "Orbit Demo Co" in html
    assert "تقرير صيانة" in html


def test_pdf_bytes_generated():
    pdf = render_maintenance_report_pdf(
        tenant_name="Demo",
        work_order_title="WO-1",
        work_order_id="uuid",
        answers={"overall_condition": "Fair", "findings_defects": "OK"},
    )
    assert pdf[:4] == b"%PDF"
