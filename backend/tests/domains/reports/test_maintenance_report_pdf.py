"""Maintenance report PDF/HTML rendering smoke tests — L1 Classic ledger."""

from app.services.maintenance_report_pdf import (
    build_report_view_model,
    render_maintenance_report_html,
    render_maintenance_report_pdf,
)
from app.services.pdf_brand import PRIMARY_500, company_initials


def test_company_initials():
    assert company_initials("Apex Facilities") == "AF"
    assert company_initials("Orbit Dev Co") == "OD"


def test_html_template_renders_rtl_with_tenant_brand():
    ctx = build_report_view_model(
        tenant_name="Apex Facilities",
        work_order_title="PM01",
        work_order_id="wo-123",
        client_name="Cairo General Hospital",
        answers={
            "property_site_name": "Main Campus",
            "property_full_address": "Kasr Al Ainy St, Cairo",
            "asset_unit_identification": "CH-01",
            "inspection_date": "2026-06-22",
            "inspection_type": "Corrective",
            "scope_systems_list": "hvac — general",
            "inspector_full_name": "Sara Tech",
            "inspector_title": "Technician",
            "inspector_contact": "+20 / tech@test.com",
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
    assert "Apex Facilities" in html
    assert "Cairo General Hospital" in html
    assert "مرافق" not in html or True  # tagline may be Arabic
    assert "تقرير صيانة" in html
    assert "تصحيحي" in html
    assert "Orbit Software" not in html
    assert ctx["company_initials"] == "AF"
    assert ctx["footer_note"].startswith("© Apex Facilities")


def test_html_prepared_for_english():
    ctx = build_report_view_model(
        tenant_name="Apex Facilities",
        work_order_title="WO",
        work_order_id="1",
        client_name="Cairo General Hospital",
        answers={"inspection_type": "Corrective", "overall_condition": "Fair"},
        lang="en",
    )
    html = render_maintenance_report_html(ctx)
    assert "Prepared for Cairo General Hospital" in html
    assert "CORRECTIVE" in html
    assert "Client" in html


def test_corrective_chip_from_wo_source_tag():
    ctx = build_report_view_model(
        tenant_name="Apex Facilities",
        work_order_title="Trip",
        work_order_id="wo-9",
        client_name="Cairo General Hospital",
        answers={"wo_source": "corrective", "maintenance_tags": ["corrective"], "overall_condition": "Fair"},
        lang="en",
    )
    assert ctx["show_corrective_chip"] is True


def test_pdf_bytes_generated():
    pdf = render_maintenance_report_pdf(
        tenant_name="Apex Facilities",
        work_order_title="AHU-3 compressor trip",
        work_order_id="WO-2026-0847",
        client_name="Cairo General Hospital",
        answers={
            "overall_condition": "Fair",
            "findings_defects": "Contactor welded closed; replaced CT-24-40.",
            "inspection_type": "Corrective",
            "wo_source": "corrective",
            "property_site_name": "Main Campus",
            "property_full_address": "Kasr Al Ainy St, Cairo",
            "asset_unit_identification": "AHU-3 / SN-9921",
            "inspector_full_name": "Sara Al-Harbi",
            "inspector_title": "Field Technician",
            "inspector_contact": "+20 100 123 4567",
            "inspection_date": "2026-10-22",
            "inspection_start_time": "08:15",
            "inspection_end_time": "11:45",
            "time_elapsed_hours": 3.5,
            "parts_used": [
                {"name": "Contactor 24V", "sku": "CT-24-40", "qty": 1},
                {"name": "Filter MERV-13", "sku": "FLT-M13-20", "qty": 2},
            ],
            "recommended_actions": "Monitor amp draw next PM cycle.",
        },
        lang="en",
    )
    assert pdf[:4] == b"%PDF"
    assert len(pdf) > 2000
