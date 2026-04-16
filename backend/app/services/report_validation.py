from typing import Any


def validate_required_fields(schema: dict[str, Any], answers: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for sec in schema.get("sections", []):
        for f in sec.get("fields", []):
            fid = f.get("id")
            if not fid:
                continue
            if f.get("required") and (fid not in answers or answers[fid] in (None, "", [])):
                missing.append(str(fid))
    return missing
