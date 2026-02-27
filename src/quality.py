# src/quality.py

MANDATORY_FIELDS = [
    "meta.visit_datetime",
    "meta.operator_role",
    "clinical.reason_for_visit",
    # NOTE: interventions is NOT mandatory (can be empty in real notes)
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

    # Mandatory fields check
    for path in MANDATORY_FIELDS:
        v = get_path(output, path)
        if v is None or v == "" or v == []:
            missing.append(path)

    # Soft warning if interventions empty
    interventions = output.get("clinical", {}).get("interventions", [])
    if interventions == []:
        warnings.append("No interventions extracted from note")

    # Vitals completeness warning
    vit = output.get("clinical", {}).get("vitals", {})
    if vit and all(vit.get(k) is None for k in [
        "blood_pressure_systolic",
        "blood_pressure_diastolic",
        "heart_rate",
        "temperature",
        "spo2",
    ]):
        warnings.append("No vital signs recorded in note")

    # Intervention-vitals consistency warning
    if "controllo_parametri_vitali" in interventions and vit:
        any_vital = any(vit.get(k) is not None for k in [
            "blood_pressure_systolic",
            "blood_pressure_diastolic",
            "heart_rate",
            "temperature",
            "spo2",
        ])
        if not any_vital:
            warnings.append("Vitals intervention present but no vitals extracted")

    return {"missing_mandatory_fields": missing, "warnings": warnings}