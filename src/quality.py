"""
src/quality.py
Quality checks for structured ADI output records.
"""
from __future__ import annotations

from typing import Any, Dict, List

MANDATORY_FIELDS = [
    "meta.visit_datetime",
    "meta.operator_role",
    "clinical.reason_for_visit",
]


def _get_path(d: Dict, path: str) -> Any:
    cur = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _has_value(v: Any) -> bool:
    return v not in (None, "", [], {})


def _normalize_vitals(vitals: Dict) -> Dict:
    """Unify both combined and split BP representations for checks."""
    vitals = vitals or {}
    systolic = vitals.get("blood_pressure_systolic")
    diastolic = vitals.get("blood_pressure_diastolic")
    combined = vitals.get("blood_pressure")

    if (not _has_value(systolic) or not _has_value(diastolic)) and isinstance(combined, str) and "/" in combined:
        left, right = combined.split("/", 1)
        systolic = systolic if _has_value(systolic) else left.strip() or None
        diastolic = diastolic if _has_value(diastolic) else right.strip() or None

    if not _has_value(combined) and _has_value(systolic) and _has_value(diastolic):
        combined = f"{systolic}/{diastolic}"

    return {
        "blood_pressure": combined,
        "blood_pressure_systolic": systolic,
        "blood_pressure_diastolic": diastolic,
        "heart_rate": vitals.get("heart_rate"),
        "temperature": vitals.get("temperature"),
        "spo2": vitals.get("spo2"),
    }


def quality_check(output: Dict) -> Dict[str, List[str]]:
    """
    Run quality checks on a structured ADI record.
    Returns {"missing_mandatory_fields": [...], "warnings": [...]}.
    """
    missing: List[str] = []
    warnings: List[str] = []

    # Mandatory field presence
    for path in MANDATORY_FIELDS:
        v = _get_path(output, path)
        if not _has_value(v):
            missing.append(path)

    clinical = output.get("clinical", {}) or {}
    interventions = clinical.get("interventions", []) or []
    vitals = _normalize_vitals(clinical.get("vitals", {}) or {})
    follow_up = clinical.get("follow_up")
    reason = clinical.get("reason_for_visit")

    any_vital = any(
        _has_value(vitals.get(k))
        for k in ("blood_pressure", "blood_pressure_systolic", "blood_pressure_diastolic",
                  "heart_rate", "temperature", "spo2")
    )

    if not interventions:
        warnings.append("No interventions extracted")

    if not any_vital:
        warnings.append("No vital signs extracted")

    if "monitoraggio_parametri_vitali" in interventions and not any_vital:
        warnings.append("Vitals monitoring intervention present but no vitals extracted")

    if reason == "controllo parametri":
        if not _has_value(vitals.get("blood_pressure")):
            warnings.append("Reason suggests parameter monitoring but blood pressure is missing")
        if not _has_value(vitals.get("heart_rate")):
            warnings.append("Reason suggests parameter monitoring but heart rate is missing")

    if not _has_value(follow_up):
        warnings.append("Follow-up not specified")

    return {"missing_mandatory_fields": missing, "warnings": warnings}
