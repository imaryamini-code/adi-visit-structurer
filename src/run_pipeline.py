"""
src/run_pipeline.py
Batch pipeline: processes all raw ADI dictations and saves structured predictions.

Usage:
    python3 -m src.run_pipeline              # rules only
    python3 -m src.run_pipeline --hybrid     # rules + LLM
    python3 -m src.run_pipeline --use-llm    # LLM only
    python3 -m src.run_pipeline --hybrid --model mistral
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import src.preprocess as preprocess_mod
import src.extract_rules as rules_mod
from src.normalize import normalize_problems
from src.quality import quality_check
from src.schema import coerce_llm_output

try:
    from src.llm_extract import llm_extract
except Exception:
    llm_extract = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Paths and constants
# ---------------------------------------------------------------------------

RAW_DIR = Path("data/synthetic/raw")
PRED_DIR = Path("data/synthetic/pred")
REPORTS_DIR = Path("reports")
RUN_SUMMARY_PATH = REPORTS_DIR / "run_summary.json"

PIPELINE_VERSION = "1.0.0"

INTERVENTION_VOCAB = {
    "monitoraggio_parametri_vitali",
    "valutazione_generale",
    "medicazione",
    "somministrazione_farmaco",
    "monitoraggio_glicemia",
    "gestione_catetere",
    "gestione_stomia",
    "gestione_ossigenoterapia",
    "educazione_terapeutica",
}


# ---------------------------------------------------------------------------
# Module-level function resolution
# ---------------------------------------------------------------------------

def _pick(module: Any, names: List[str]) -> Optional[Callable]:
    for name in names:
        fn = getattr(module, name, None)
        if callable(fn):
            return fn
    return None


def _get_preprocess() -> Callable[[str], str]:
    fn = _pick(preprocess_mod, ["preprocess_text", "preprocess", "clean_text", "clean"])
    if fn:
        return fn
    raise ImportError("No preprocess function found in src/preprocess.py")


PREPROCESS = _get_preprocess()

EXTRACT_DATETIME = _pick(rules_mod, ["extract_datetime"])
EXTRACT_REASON = _pick(rules_mod, ["extract_reason", "extract_reason_for_visit"])
EXTRACT_FOLLOW_UP = _pick(rules_mod, ["extract_follow_up"])
EXTRACT_INTERVENTIONS = _pick(rules_mod, ["extract_interventions"])
EXTRACT_VITALS = _pick(rules_mod, ["extract_vitals"])
EXTRACT_BP = _pick(rules_mod, ["extract_bp", "extract_blood_pressure"])
EXTRACT_HR = _pick(rules_mod, ["extract_hr"])
EXTRACT_TEMP = _pick(rules_mod, ["extract_temp"])
EXTRACT_SPO2 = _pick(rules_mod, ["extract_spo2"])
EXTRACT_CRITICAL = _pick(rules_mod, ["extract_critical_issues"])


# ---------------------------------------------------------------------------
# Vitals wrapper
# ---------------------------------------------------------------------------

def _extract_vitals(text: str) -> Dict[str, Any]:
    if EXTRACT_VITALS:
        return EXTRACT_VITALS(text) or {}

    sys_v, dia_v = (EXTRACT_BP(text) if EXTRACT_BP else (None, None))
    return {
        "blood_pressure_systolic": sys_v,
        "blood_pressure_diastolic": dia_v,
        "heart_rate": EXTRACT_HR(text) if EXTRACT_HR else None,
        "temperature": EXTRACT_TEMP(text) if EXTRACT_TEMP else None,
        "spo2": EXTRACT_SPO2(text) if EXTRACT_SPO2 else None,
    }


# ---------------------------------------------------------------------------
# Record builder
# ---------------------------------------------------------------------------

def build_base_record(record_id: str, mode: str, model: str) -> Dict[str, Any]:
    return {
        "meta": {
            "record_id": record_id,
            "visit_datetime": None,
            "operator_role": "infermiere",
            "extraction_mode": mode,
            "llm_model": model if mode != "rules" else None,
            "pipeline_version": PIPELINE_VERSION,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
        "clinical": {
            "reason_for_visit": None,
            "vitals": {},
            "interventions": [],
            "follow_up": None,
            "critical_issues": [],
        },
        "coding": {"problems_normalized": []},
        "quality": {"missing_mandatory_fields": [], "warnings": []},
    }


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

def _normalize_interventions(
    interventions: List[str],
    vitals: Dict[str, Any],
    reason: Optional[str],
) -> List[str]:
    out = set(interventions or [])

    if any(v is not None for v in vitals.values()):
        out.add("monitoraggio_parametri_vitali")
    if reason and "lesione" in reason:
        out.add("medicazione")
    if reason and "farmaco" in reason:
        out.add("somministrazione_farmaco")
    if not out:
        out.add("valutazione_generale")

    return list(out & INTERVENTION_VOCAB)


# ---------------------------------------------------------------------------
# Extraction modes
# ---------------------------------------------------------------------------

def apply_rules(text: str, rec: Dict[str, Any]) -> None:
    vitals = _extract_vitals(text)

    rec["meta"]["visit_datetime"] = EXTRACT_DATETIME(text) if EXTRACT_DATETIME else None
    rec["clinical"]["reason_for_visit"] = EXTRACT_REASON(text) if EXTRACT_REASON else None
    rec["clinical"]["follow_up"] = EXTRACT_FOLLOW_UP(text) if EXTRACT_FOLLOW_UP else None
    rec["clinical"]["vitals"] = vitals

    interventions = EXTRACT_INTERVENTIONS(text, vitals=vitals) if EXTRACT_INTERVENTIONS else []
    rec["clinical"]["interventions"] = _normalize_interventions(
        interventions, vitals, rec["clinical"]["reason_for_visit"]
    )

    if EXTRACT_CRITICAL:
        rec["clinical"]["critical_issues"] = EXTRACT_CRITICAL(
            text, spo2=vitals.get("spo2")
        )

    rec["coding"]["problems_normalized"] = normalize_problems(text) or []


def apply_llm(text: str, rec: Dict[str, Any], model: str) -> None:
    if not llm_extract:
        raise RuntimeError("LLM extraction not available. Is Ollama installed?")

    out, _ = llm_extract(text=text, model=model, return_raw=True)
    out = coerce_llm_output(out)

    rec["meta"]["visit_datetime"] = None  # LLM doesn't extract datetime
    rec["clinical"] = out.get("clinical", {})
    rec["coding"] = out.get("coding", {})


def apply_hybrid(text: str, rec: Dict[str, Any], model: str) -> None:
    apply_rules(text, rec)

    if llm_extract:
        try:
            out, _ = llm_extract(text=text, model=model, return_raw=True)
            out = coerce_llm_output(out)

            # LLM fills gaps rules couldn't cover
            if not rec["clinical"]["reason_for_visit"]:
                rec["clinical"]["reason_for_visit"] = out["clinical"].get("reason_for_visit")

            rec["coding"]["problems_normalized"] = list(set(
                rec["coding"]["problems_normalized"]
                + out["coding"].get("problems_normalized", [])
            ))
        except RuntimeError:
            pass  # Ollama unavailable — rules result is still valid


# ---------------------------------------------------------------------------
# Save
# ---------------------------------------------------------------------------

def save_prediction(record_id: str, rec: Dict[str, Any]) -> Path:
    PRED_DIR.mkdir(parents=True, exist_ok=True)
    path = PRED_DIR / f"{record_id}.json"
    path.write_text(json.dumps(rec, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="ADI visit structurer — batch pipeline")
    parser.add_argument("--use-llm", action="store_true", help="Use LLM extraction only")
    parser.add_argument("--hybrid", action="store_true", help="Use hybrid extraction (rules + LLM)")
    parser.add_argument("--model", default="mistral", help="Ollama model name")
    args = parser.parse_args()

    mode = "hybrid" if args.hybrid else "llm" if args.use_llm else "rules"
    raw_files = sorted(RAW_DIR.glob("ADI-*.txt"))

    if not raw_files:
        print(f"No raw files found in {RAW_DIR}")
        return

    ok = 0
    failed = 0
    failures = []

    for txt in raw_files:
        record_id = txt.stem
        try:
            text = PREPROCESS(txt.read_text(encoding="utf-8"))
            rec = build_base_record(record_id, mode, args.model)

            if mode == "rules":
                apply_rules(text, rec)
            elif mode == "llm":
                apply_llm(text, rec, args.model)
            else:
                apply_hybrid(text, rec, args.model)

            rec["quality"] = quality_check(rec)
            save_prediction(record_id, rec)
            print(f"  [ok] {record_id}")
            ok += 1

        except Exception as e:
            print(f"  [fail] {record_id}: {e}")
            failed += 1
            failures.append({"record_id": record_id, "error": str(e)})

    # Write run summary
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    summary = {
        "run_timestamp": datetime.now().isoformat(timespec="seconds"),
        "mode": mode,
        "model": args.model if mode != "rules" else None,
        "pipeline_version": PIPELINE_VERSION,
        "records_total": len(raw_files),
        "records_ok": ok,
        "records_failed": failed,
        "failures": failures,
    }
    RUN_SUMMARY_PATH.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    print(f"\nDone: {ok} ok, {failed} failed")
    print(f"Summary: {RUN_SUMMARY_PATH}")


if __name__ == "__main__":
    main()
