"""
src/schema.py
Type coercion for LLM output — ensures the pipeline always gets clean types.
"""
from __future__ import annotations

from typing import Any, Dict, List


def _str_or_none(x: Any) -> str | None:
    if isinstance(x, str):
        s = x.strip()
        return s if s else None
    return None


def _num_or_none(x: Any) -> int | float | None:
    if isinstance(x, (int, float)):
        return x
    if isinstance(x, str):
        try:
            return int(x) if "." not in x else float(x)
        except ValueError:
            pass
    return None


def _list_of_str(x: Any) -> List[str]:
    if not isinstance(x, list):
        return []
    return [str(i).strip() for i in x if str(i).strip()]


def coerce_llm_output(out: Any) -> Dict[str, Any]:
    """
    Coerce arbitrary parsed LLM JSON into the expected pipeline shape.
    Drops unknown keys, ensures nested structure, coerces types.
    """
    if not isinstance(out, dict):
        out = {}

    clinical = out.get("clinical") or {}
    coding = out.get("coding") or {}
    vitals = clinical.get("vitals") or {}

    if not isinstance(clinical, dict):
        clinical = {}
    if not isinstance(coding, dict):
        coding = {}
    if not isinstance(vitals, dict):
        vitals = {}

    return {
        "clinical": {
            "reason_for_visit": _str_or_none(clinical.get("reason_for_visit")),
            "follow_up": _str_or_none(clinical.get("follow_up")),
            "interventions": _list_of_str(clinical.get("interventions")),
            "vitals": {
                "blood_pressure_systolic": _num_or_none(vitals.get("blood_pressure_systolic")),
                "blood_pressure_diastolic": _num_or_none(vitals.get("blood_pressure_diastolic")),
                "heart_rate": _num_or_none(vitals.get("heart_rate")),
                "temperature": _num_or_none(vitals.get("temperature")),
                "spo2": _num_or_none(vitals.get("spo2")),
            },
        },
        "coding": {
            "problems_normalized": _list_of_str(coding.get("problems_normalized")),
        },
    }
