# src/run_pipeline.py
from pathlib import Path
import json

from src.preprocess import clean_text
from src.extract_rules import (
    extract_datetime,
    extract_bp,
    extract_hr,
    extract_temp,
    extract_spo2,
    extract_reason,
    extract_follow_up,
    extract_interventions,
)
from src.normalize import normalize_problems
from src.quality import quality_check


def process_dictation(text: str, record_id: str) -> dict:
    # Keep raw text for problem normalization (clean_text may remove useful anamnesis details)
    raw_text = text

    # Use cleaned text for rule-based field extraction
    text = clean_text(text)

    dt = extract_datetime(text)
    bp_sys, bp_dia = extract_bp(text)

    output = {
        "meta": {
            "record_id": record_id,
            "template_type": ["diario_clinico", "presa_in_carico"],
            "visit_datetime": dt,
            "operator_role": "infermiere",
        },
        "patient": {
            "patient_id": "SYNTH-" + record_id,
            "age": None,
            "sex": None,
        },
        "clinical": {
            "reason_for_visit": extract_reason(text),
            "anamnesis_brief": [],
            "vitals": {
                "blood_pressure_systolic": bp_sys,
                "blood_pressure_diastolic": bp_dia,
                "heart_rate": extract_hr(text),
                "temperature": extract_temp(text),
                "spo2": extract_spo2(text),
            },
            "consciousness": None,
            "mobility": None,
            "interventions": extract_interventions(text),
            "critical_issues": [],
            "follow_up": extract_follow_up(text),
        },
        "coding": {
            # Normalize problems on RAW text so we don't lose info removed by clean_text
            "problems_normalized": normalize_problems(raw_text),
        },
        "quality": {
            "missing_mandatory_fields": [],
            "warnings": [],
        },
    }

    output["quality"] = quality_check(output)
    return output


def main():
    raw_dir = Path("data/synthetic/raw")
    out_dir = Path("reports/examples")
    out_dir.mkdir(parents=True, exist_ok=True)

    for path in sorted(raw_dir.glob("*.txt")):
        record_id = path.stem
        text = path.read_text(encoding="utf-8")
        out = process_dictation(text, record_id)

        out_path = out_dir / f"{record_id}.json"
        out_path.write_text(
            json.dumps(out, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()