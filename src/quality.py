# src/quality.py

MANDATORY_FIELDS = [
    "meta.visit_datetime",
    "meta.operator_role",
    "clinical.reason_for_visit",
    "clinical.interventions"
]

def quality_check(output: dict) -> dict:
    missing = []
    warnings = []

    def get_path(d, path):
        cur = d
        for part in path.split("."):
            if not isinstance(cur, dict) or part not in cur:
                return None
            cur = cur[part]
        return cur

    for path in MANDATORY_FIELDS:
        v = get_path(output, path)
        if v is None or v == "" or v == []:
            missing.append(path)

    vit = output.get("clinical", {}).get("vitals", {})
    if (vit.get("blood_pressure_systolic") is None) != (vit.get("blood_pressure_diastolic") is None):
        warnings.append("BP incomplete: systolic/diastolic mismatch")

    return {"missing_mandatory_fields": missing, "warnings": warnings}