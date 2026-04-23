#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


ID_RE = re.compile(r"^ADI-(\d{4})$")


# ---- What "schema" we expect (minimal, but consistent) ----
REQUIRED_TOP_KEYS = ["meta", "patient", "clinical", "coding", "quality"]

REQUIRED_META_KEYS = ["record_id", "template_type", "visit_datetime", "operator_role"]
REQUIRED_PATIENT_KEYS = ["patient_id", "age", "sex"]
REQUIRED_CLINICAL_KEYS = [
    "reason_for_visit",
    "anamnesis_brief",
    "vitals",
    "interventions",
    "critical_issues",
    "follow_up",
]
REQUIRED_CODING_KEYS = ["problems_normalized"]  # risk_flags optional
REQUIRED_QUALITY_KEYS = ["missing_mandatory_fields", "warnings"]

REQUIRED_VITAL_KEYS = [
    "blood_pressure_systolic",
    "blood_pressure_diastolic",
    "heart_rate",
    "temperature",
    "spo2",
]


# ---- Heuristics to catch common mistakes safely ----
SYMPTOM_ONLY_WORDS = [
    "stanchezza",
    "astenia",
    "scarso appetito",
    "inappetenza",
]
DIAGNOSIS_WORDS = [
    "malnutrizione",
    "disidratazione",
    "infezione",
]
FALL_WORDS = ["caduta", "caduto", "scivol"]


@dataclass
class FileCheck:
    record_id: str
    id_num: Optional[int]
    group: str  # manual / generated / unknown
    raw_path: Optional[str]
    gold_path: Optional[str]
    ok_pairing: bool
    ok_json_parse: bool
    schema_errors: List[str]
    schema_warnings: List[str]
    heuristic_warnings: List[str]


def parse_id_num(record_id: str) -> Optional[int]:
    m = ID_RE.match(record_id.strip())
    if not m:
        return None
    return int(m.group(1))


def group_from_id_num(id_num: Optional[int]) -> str:
    # Your current manual dataset is ADI-0001 .. ADI-0013
    if id_num is None:
        return "unknown"
    return "manual" if id_num <= 13 else "generated"


def safe_get(d: Dict[str, Any], key: str) -> Any:
    return d.get(key, None)


def check_required_keys(obj: Dict[str, Any], required: List[str], where: str) -> List[str]:
    errors = []
    for k in required:
        if k not in obj:
            errors.append(f"Missing key '{k}' in {where}")
    return errors


def normalize_text(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_one(record_id: str, raw_path: Optional[Path], gold_path: Optional[Path]) -> FileCheck:
    id_num = parse_id_num(record_id)
    group = group_from_id_num(id_num)

    ok_pairing = raw_path is not None and gold_path is not None
    ok_json_parse = False
    schema_errors: List[str] = []
    schema_warnings: List[str] = []
    heuristic_warnings: List[str] = []

    raw_text = ""
    if raw_path and raw_path.exists():
        raw_text = normalize_text(load_text(raw_path))

    gold: Dict[str, Any] = {}
    if gold_path and gold_path.exists():
        try:
            gold = load_json(gold_path)
            ok_json_parse = True
        except Exception as e:
            schema_errors.append(f"JSON parse error: {e}")
            ok_json_parse = False

    # If JSON didn't parse, stop here
    if not ok_json_parse:
        return FileCheck(
            record_id=record_id,
            id_num=id_num,
            group=group,
            raw_path=str(raw_path) if raw_path else None,
            gold_path=str(gold_path) if gold_path else None,
            ok_pairing=ok_pairing,
            ok_json_parse=ok_json_parse,
            schema_errors=schema_errors,
            schema_warnings=schema_warnings,
            heuristic_warnings=heuristic_warnings,
        )

    # ---- Schema checks ----
    # Top-level keys
    schema_errors += check_required_keys(gold, REQUIRED_TOP_KEYS, "root")

    # Sections
    meta = safe_get(gold, "meta") or {}
    patient = safe_get(gold, "patient") or {}
    clinical = safe_get(gold, "clinical") or {}
    coding = safe_get(gold, "coding") or {}
    quality = safe_get(gold, "quality") or {}

    if isinstance(meta, dict):
        schema_errors += check_required_keys(meta, REQUIRED_META_KEYS, "meta")
    else:
        schema_errors.append("meta is not an object")

    if isinstance(patient, dict):
        schema_errors += check_required_keys(patient, REQUIRED_PATIENT_KEYS, "patient")
    else:
        schema_errors.append("patient is not an object")

    if isinstance(clinical, dict):
        schema_errors += check_required_keys(clinical, REQUIRED_CLINICAL_KEYS, "clinical")
    else:
        schema_errors.append("clinical is not an object")

    if isinstance(coding, dict):
        schema_errors += check_required_keys(coding, REQUIRED_CODING_KEYS, "coding")
    else:
        schema_errors.append("coding is not an object")

    if isinstance(quality, dict):
        schema_errors += check_required_keys(quality, REQUIRED_QUALITY_KEYS, "quality")
    else:
        schema_errors.append("quality is not an object")

    # Vitals keys
    vitals = clinical.get("vitals") if isinstance(clinical, dict) else None
    if isinstance(vitals, dict):
        schema_errors += check_required_keys(vitals, REQUIRED_VITAL_KEYS, "clinical.vitals")
    else:
        schema_errors.append("clinical.vitals is not an object")

    # record_id consistency
    meta_record_id = meta.get("record_id") if isinstance(meta, dict) else None
    if meta_record_id and meta_record_id != record_id:
        schema_warnings.append(f"meta.record_id '{meta_record_id}' != filename id '{record_id}'")

    # ---- Heuristic checks to catch common “clinical NLP dataset” issues ----
    # 1) “presa_in_carico” should be rare: warn if included without signals
    template_type = meta.get("template_type") if isinstance(meta, dict) else None
    if isinstance(template_type, list) and "presa_in_carico" in template_type:
        # If raw doesn't contain intake signals, warn
        if "presa in carico" not in raw_text and "valutazione iniziale" not in raw_text and "prima visita" not in raw_text:
            heuristic_warnings.append("template_type includes 'presa_in_carico' but raw text has no intake signals")

    # 2) Fall events should surface in critical_issues or problems
    if any(w in raw_text for w in FALL_WORDS):
        probs = (coding.get("problems_normalized") if isinstance(coding, dict) else []) or []
        crit = (clinical.get("critical_issues") if isinstance(clinical, dict) else []) or []
        if "caduta" not in probs and not any("caduta" in str(x).lower() for x in crit):
            heuristic_warnings.append("Raw mentions fall/caduta but problems_normalized/critical_issues do not reflect it")

    # 3) Symptom-only text should not become a diagnosis (example: malnutrizione)
    probs = (coding.get("problems_normalized") if isinstance(coding, dict) else []) or []
    if isinstance(probs, list):
        probs_lower = [str(p).lower() for p in probs]
        if "malnutrizione" in probs_lower:
            # If raw does not explicitly say malnutrizione but has only appetite/fatigue symptoms, warn
            if "malnutrizione" not in raw_text and any(w in raw_text for w in SYMPTOM_ONLY_WORDS):
                heuristic_warnings.append("Gold labels 'malnutrizione' but raw text does not state it explicitly (consider symptom-level labels + risk_flag)")

    # 4) If raw includes 'SpO2' but gold spo2 is null, warn (and vice versa)
    if isinstance(vitals, dict):
        spo2_val = vitals.get("spo2")
        raw_has_spo2 = "spo2" in raw_text or "spo2%" in raw_text or "satur" in raw_text
        if raw_has_spo2 and spo2_val in (None, ""):
            heuristic_warnings.append("Raw mentions SpO2 but gold spo2 is null")
        if (not raw_has_spo2) and isinstance(spo2_val, (int, float)):
            heuristic_warnings.append("Gold has spo2 value but raw text does not mention SpO2")

    return FileCheck(
        record_id=record_id,
        id_num=id_num,
        group=group,
        raw_path=str(raw_path) if raw_path else None,
        gold_path=str(gold_path) if gold_path else None,
        ok_pairing=ok_pairing,
        ok_json_parse=ok_json_parse,
        schema_errors=schema_errors,
        schema_warnings=schema_warnings,
        heuristic_warnings=heuristic_warnings,
    )


def collect_pairs(raw_dir: Path, gold_dir: Path) -> List[Tuple[str, Optional[Path], Optional[Path]]]:
    raw_ids = {p.stem for p in raw_dir.glob("ADI-*.txt")}
    gold_ids = {p.stem for p in gold_dir.glob("ADI-*.json")}
    all_ids = sorted(raw_ids.union(gold_ids))

    pairs = []
    for rid in all_ids:
        pairs.append((
            rid,
            raw_dir / f"{rid}.txt" if rid in raw_ids else None,
            gold_dir / f"{rid}.json" if rid in gold_ids else None
        ))
    return pairs


def write_csv(report_path: Path, rows: List[FileCheck]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(asdict(rows[0]).keys()) if rows else []
    with report_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            d = asdict(r)
            # store lists as joined strings
            d["schema_errors"] = " | ".join(r.schema_errors)
            d["schema_warnings"] = " | ".join(r.schema_warnings)
            d["heuristic_warnings"] = " | ".join(r.heuristic_warnings)
            w.writerow(d)


def summarize(rows: List[FileCheck]) -> None:
    def stats(group: str) -> None:
        g = [r for r in rows if r.group == group]
        if not g:
            print(f"\n[{group}] No records")
            return

        n = len(g)
        n_pair_ok = sum(r.ok_pairing for r in g)
        n_json_ok = sum(r.ok_json_parse for r in g)
        n_schema_ok = sum((r.ok_json_parse and len(r.schema_errors) == 0) for r in g)
        n_heur_warn = sum(len(r.heuristic_warnings) > 0 for r in g)

        print(f"\n[{group}] Records: {n}")
        print(f"  Pairing OK: {n_pair_ok}/{n}")
        print(f"  JSON parse OK: {n_json_ok}/{n}")
        print(f"  Schema OK (no errors): {n_schema_ok}/{n}")
        print(f"  With heuristic warnings: {n_heur_warn}/{n}")

        # Top warning types
        warn_counts: Dict[str, int] = {}
        for r in g:
            for w in r.heuristic_warnings:
                warn_counts[w] = warn_counts.get(w, 0) + 1
        if warn_counts:
            top = sorted(warn_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            print("  Top heuristic warnings:")
            for w, c in top:
                print(f"   - {c}× {w}")

    print("\n=== DATASET SUMMARY ===")
    stats("manual")
    stats("generated")
    stats("unknown")

    # Print the worst offenders
    offenders = [r for r in rows if (r.schema_errors or r.heuristic_warnings or not r.ok_pairing)]
    offenders.sort(key=lambda r: (len(r.schema_errors), len(r.heuristic_warnings)), reverse=True)
    if offenders:
        print("\n=== TOP ISSUES (first 10) ===")
        for r in offenders[:10]:
            print(f"- {r.record_id}: errors={len(r.schema_errors)} heur_warnings={len(r.heuristic_warnings)} pairing_ok={r.ok_pairing}")
            for e in r.schema_errors[:3]:
                print(f"    ERROR: {e}")
            for w in r.heuristic_warnings[:3]:
                print(f"    WARN:  {w}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Validate synthetic ADI dataset (raw dictations + gold JSON).")
    ap.add_argument("--root", type=str, default="data/synthetic", help="Dataset root (default: data/synthetic)")
    ap.add_argument("--raw", type=str, default="raw", help="Raw dictations folder under root (default: raw)")
    ap.add_argument("--gold", type=str, default="gold", help="Gold JSON folder under root (default: gold)")
    ap.add_argument("--out", type=str, default="data/synthetic/validation_report.csv", help="CSV output path")
    args = ap.parse_args()

    root = Path(args.root)
    raw_dir = root / args.raw
    gold_dir = root / args.gold

    if not raw_dir.exists():
        print(f"ERROR: raw dir not found: {raw_dir}")
        return 2
    if not gold_dir.exists():
        print(f"ERROR: gold dir not found: {gold_dir}")
        return 2

    pairs = collect_pairs(raw_dir, gold_dir)
    rows: List[FileCheck] = []
    for rid, raw_path, gold_path in pairs:
        rows.append(validate_one(rid, raw_path, gold_path))

    summarize(rows)
    if rows:
        write_csv(Path(args.out), rows)
        print(f"\nSaved report to: {args.out}")

    # Exit code non-zero if any schema errors or pairing missing
    any_hard = any((not r.ok_pairing) or (r.ok_json_parse and len(r.schema_errors) > 0) or (not r.ok_json_parse) for r in rows)
    return 1 if any_hard else 0


if __name__ == "__main__":
    raise SystemExit(main())