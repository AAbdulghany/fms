from typing import Any

def validate_report_answers(schema: dict[str, Any], answers: dict[str, Any]) -> list[str]:
    """
    Comprehensive validation of report answers against the template schema.
    Returns a list of error messages.
    """
    errors: list[str] = []

    for sec in schema.get("sections", []):
        sec_title = sec.get("title", "Unknown Section")
        for f in sec.get("fields", []):
            fid = f.get("id")
            if not fid:
                continue

            val = answers.get(fid)
            label = f.get("label", fid)

            # 1. Required Check
            if f.get("required") and (val in (None, "", [], {})):
                errors.append(f"Field '{label}' in {sec_title} is required.")
                continue # Skip further validation for empty required field

            if val in (None, "", [], {}):
                continue

            # 2. Type and Range Validation for numeric fields
            if f.get("type") == "number":
                try:
                    num_val = float(val)
                    # Min check
                    if "min" in f and num_val < f["min"]:
                        errors.append(f"Field '{label}' must be at least {f['min']}.")
                    # Max check
                    if "max" in f and num_val > f["max"]:
                        errors.append(f"Field '{label}' must be no more than {f['max']}.")
                except (ValueError, TypeError):
                    errors.append(f"Field '{label}' must be a valid number.")

            # 3. Photo count validation
            if f.get("type") == "photo":
                # Expecting answers[fid] to be a list of photo objects/paths
                if not isinstance(val, list):
                    errors.append(f"Field '{label}' must be a list of photos.")
                else:
                    max_photos = f.get("max_photos")
                    if max_photos and len(val) > max_photos:
                        errors.append(f"Field '{label}' exceeds maximum allowed photos ({max_photos}).")

    return errors

def validate_required_fields(schema: dict[str, Any], answers: dict[str, Any]) -> list[str]:
    """
    Legacy support: only checks for missing required fields.
    """
    errors = validate_report_answers(schema, answers)
    # Filter to only include 'required' messages for backward compatibility if needed
    return [e for e in errors if "is required" in e]
