from typing import Any

from app.services.report_context import is_technician_visible_field


def _field_is_required(f: dict[str, Any], answers: dict[str, Any]) -> bool:
    if f.get("required"):
        return True
    req_when = f.get("required_when")
    if not isinstance(req_when, dict):
        return False
    dep_field = req_when.get("field")
    values = req_when.get("values") or []
    if not dep_field:
        return False
    return answers.get(dep_field) in values


def validate_report_answers(schema: dict[str, Any], answers: dict[str, Any]) -> list[str]:
    """
    Comprehensive validation of report answers against the template schema.
    Returns a list of error messages.
    """
    errors: list[str] = []

    for sec in schema.get("sections", []):
        if sec.get("visible") is False:
            continue
        sec_title = sec.get("title", "Unknown Section")
        for f in sec.get("fields", []):
            fid = f.get("id")
            if not fid or not is_technician_visible_field(f):
                continue

            val = answers.get(fid)
            label = f.get("label", fid)

            if _field_is_required(f, answers) and (val in (None, "", [], {})):
                errors.append(f"Field '{label}' in {sec_title} is required.")
                continue

            if val in (None, "", [], {}):
                continue

            if f.get("type") == "number":
                try:
                    num_val = float(val)
                    if "min" in f and num_val < f["min"]:
                        errors.append(f"Field '{label}' must be at least {f['min']}.")
                    if "max" in f and num_val > f["max"]:
                        errors.append(f"Field '{label}' must be no more than {f['max']}.")
                except (ValueError, TypeError):
                    errors.append(f"Field '{label}' must be a valid number.")

            if f.get("type") == "photo":
                if not isinstance(val, list):
                    errors.append(f"Field '{label}' must be a list of photos.")
                else:
                    max_photos = f.get("max_photos")
                    if max_photos and len(val) > max_photos:
                        errors.append(f"Field '{label}' exceeds maximum allowed photos ({max_photos}).")

    return errors


def validate_required_fields(schema: dict[str, Any], answers: dict[str, Any]) -> list[str]:
    """Legacy support: only checks for missing required fields."""
    errors = validate_report_answers(schema, answers)
    return [e for e in errors if "is required" in e]
