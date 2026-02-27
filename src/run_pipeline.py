# src/run_pipeline.py

import argparse
import json
import re
from pathlib import Path
from typing import Any, Dict, Callable, Optional

import src.preprocess as preprocess_mod
import src.extract_rules as rules_mod
from src.normalize import normalize_problems
from src.quality import quality_check

# LLM extractor (Ollama-based in src/llm_extract.py)
try:
    from src.llm_extract import llm_extract
except Exception:
    llm_extract = None


RAW_DIR = Path("data/synthetic/raw")
OUT_DIR = Path("reports/examples")


def _pick_callable(module, names: list[str]) -> Optional[Callable]:
    for n in names:
        fn = getattr(module, n, None)
        if callable(fn):
            return fn
    return None


def get_preprocess_fn() -> Callable[[str], str]:
    candidates = [
        "preprocess_text",
        "preprocess",
        "clean_text",
        "clean",
        "normalize_text",
        "prepare_text",
    ]
    fn = _pick_callable(preprocess_mod, candidates)
    if fn:
        return fn

    available = [x for x in dir(preprocess_mod) if not x.startswith("_")]
    raise ImportError(
        "Could not find a preprocess function in src/preprocess.py.\n"
        f"Tried: {candidates}\n"
        f"Available: {available}\n"
        "Fix: rename your preprocess function to 'preprocess_text' or add a wrapper."
    )


PREPROCESS = get_preprocess_fn()

# ---- Rule extractors (robust resolution) ----

EXTRACT_REASON = _pick_callable(
    rules_mod,
    ["extract_reason", "extract_reason_for_visit", "reason_for_visit", "get_reason"],
)
EXTRACT_FOLLOW_UP = _pick_callable(
    rules_mod,
    ["extract_follow_up", "extract_followup", "follow_up", "get_follow_up"],
)
EXTRACT_INTERVENTIONS = _pick_callable(
    rules_mod,
    ["extract_interventions", "extract_actions", "interventions", "get_interventions"],
)

EXTRACT_BP = _pick_callable(
    rules_mod,
    ["extract_blood_pressure", "extract_bp", "blood_pressure", "get_bp"],
)
EXTRACT_HR = _pick_callable(
    rules_mod,
    ["extract_heart_rate", "extract_hr", "heart_rate", "get_hr"],
)
EXTRACT_TEMP = _pick_callable(
    rules_mod,
    ["extract_temperature", "extract_temp", "temperature", "get_temp"],
)
EXTRACT_SPO2 = _pick_callable(
    rules_mod,
    ["extract_spo2", "extract_saturation", "spo2", "saturation", "get_spo2"],
)


def extract_vitals_wrapper(text: str) -> Dict[str, Any]:
    vitals = {
        "blood_pressure_systolic": None,
        "blood_pressure_diastolic": None,
        "heart_rate": None,
        "temperature": None,
        "spo2": None,
    }

    if EXTRACT_BP:
        bp = EXTRACT_BP(text)
        if isinstance(bp, dict):
            vitals["blood_pressure_systolic"] = bp.get("blood_pressure_systolic") or bp.get("systolic")
            vitals["blood_pressure_diastolic"] = bp.get("blood_pressure_diastolic") or bp.get("diastolic")
        elif isinstance(bp, (tuple, list)) and len(bp) >= 2:
            vitals["blood_pressure_systolic"] = bp[0]
            vitals["blood_pressure_diastolic"] = bp[1]

    if EXTRACT_HR:
        vitals["heart_rate"] = EXTRACT_HR(text)

    if EXTRACT_TEMP:
        vitals["temperature"] = EXTRACT_TEMP(text)

    if EXTRACT_SPO2:
        vitals["spo2"] = EXTRACT_SPO2(text)

    return vitals


def build_base_record(record_id: str) -> Dict[str, Any]:
    return {
        "meta": {
            "record_id": record_id,
            "template_type": ["diario_clinico", "presa_in_carico"],
            "visit_datetime": None,
            "operator_role": "infermiere",
        },
        "patient": {"patient_id": f"SYNTH-{record_id}", "age": None, "sex": None},
        "clinical": {
            "reason_for_visit": None,
            "anamnesis_brief": [],
            "vitals": {
                "blood_pressure_systolic": None,
                "blood_pressure_diastolic": None,
                "heart_rate": None,
                "temperature": None,
                "spo2": None,
            },
            "consciousness": None,
            "mobility": None,
            "interventions": [],
            "critical_issues": [],
            "follow_up": None,
        },
        "coding": {"problems_normalized": []},
        "quality": {"missing_mandatory_fields": [], "warnings": []},
    }


def apply_rules(text: str, rec: Dict[str, Any]) -> None:
    if EXTRACT_REASON:
        rec["clinical"]["reason_for_visit"] = EXTRACT_REASON(text)
    if EXTRACT_FOLLOW_UP:
        rec["clinical"]["follow_up"] = EXTRACT_FOLLOW_UP(text)
    if EXTRACT_INTERVENTIONS:
        rec["clinical"]["interventions"] = EXTRACT_INTERVENTIONS(text) or []
    rec["clinical"]["vitals"] = extract_vitals_wrapper(text)
    rec["coding"]["problems_normalized"] = normalize_problems(text)


def apply_llm(text: str, rec: Dict[str, Any], model: str) -> None:
    if llm_extract is None:
        raise RuntimeError("LLM extraction requested but src/llm_extract.py could not be imported.")

    out = llm_extract(text=text, model=model)

    rec["clinical"]["reason_for_visit"] = out["clinical"].get("reason_for_visit")
    rec["clinical"]["follow_up"] = out["clinical"].get("follow_up")
    rec["clinical"]["interventions"] = out["clinical"].get("interventions", [])
    rec["clinical"]["vitals"] = out["clinical"].get("vitals", rec["clinical"]["vitals"])
    rec["coding"]["problems_normalized"] = out["coding"].get("problems_normalized", [])


def apply_hybrid(text: str, rec: Dict[str, Any], model: str) -> None:
    if llm_extract is None:
        raise RuntimeError("Hybrid requested but src/llm_extract.py could not be imported.")

    out = llm_extract(text=text, model=model)

    # LLM for free-text fields
    rec["clinical"]["reason_for_visit"] = out["clinical"].get("reason_for_visit")
    rec["clinical"]["follow_up"] = out["clinical"].get("follow_up")
    rec["clinical"]["interventions"] = out["clinical"].get("interventions", [])

    # Rules-based vitals are more reliable than LLM vitals
    rec["clinical"]["vitals"] = extract_vitals_wrapper(text)

    # Merge problems (union)
    llm_probs = out["coding"].get("problems_normalized", [])
    rule_probs = normalize_problems(text)
    rec["coding"]["problems_normalized"] = sorted(set(llm_probs) | set(rule_probs))


# ---------------------------
# Normalization helpers
# ---------------------------

def normalize_reason(reason: Optional[str]) -> Optional[str]:
    if not reason:
        return None
    r = reason.strip().lower()

    # Normalize punctuation variants that break exact-match
    r = r.replace("+", " e ")
    r = re.sub(r"\s+", " ", r).strip()

    # Normalize common abbreviations
    r = re.sub(r"\bdx\b", "destro", r)
    r = re.sub(r"\bsx\b", "sinistro", r)

    # ✅ NEW: remove filler phrase that breaks exact match
    r = re.sub(r"\bda giorni\b", "", r).strip()
    r = re.sub(r"\s+", " ", r).strip()

    return r


def normalize_follow_up(fu: Optional[str]) -> Optional[str]:
    if fu is None:
        return None
    s = fu.strip().lower()
    s = re.sub(r"\s+", " ", s)

    # Canonical "programmato controllo tra X giorni"
    m = re.match(r"^(?:programmato controllo )?(?:tra )?(\d+)\s*giorni$", s)
    if m:
        n = m.group(1)
        return f"programmato controllo tra {n} giorni"

    # Canonical "programmato nuovo controllo"
    if s in {"nuovo controllo", "programmato nuovo controllo"}:
        return "programmato nuovo controllo"

    return s


# Controlled vocab for interventions (matches your gold labels)
INTERVENTION_VOCAB = {
    "controllo_parametri_vitali",
    "medicazione",
}

INTERVENTION_SYNONYMS = {
    "controllo parametri": "controllo_parametri_vitali",
    "controllo parametri vitali": "controllo_parametri_vitali",
    "rilevati parametri": "controllo_parametri_vitali",
    "rilevazione parametri": "controllo_parametri_vitali",
    "controllo generale": "controllo_parametri_vitali",

    "medicazione avanzata": "medicazione",
    "medicazione lesione": "medicazione",
    "medicazione piaga": "medicazione",
}


def normalize_interventions(interventions: list[str], text: str, reason: Optional[str]) -> list[str]:
    t = (text or "").lower()
    r = (reason or "").lower()

    out = []

    # map LLM outputs to controlled vocab
    for it in interventions or []:
        low = str(it).strip().lower()
        mapped = INTERVENTION_SYNONYMS.get(low, low)
        if mapped in INTERVENTION_VOCAB:
            out.append(mapped)

    # infer medicazione from text/reason keywords
    if ("medicazione" in t) or ("medicazione" in r) or ("piaga" in t) or ("lesione" in t) or ("decubito" in t):
        out.append("medicazione")

    # unique + stable order
    out = list(dict.fromkeys(out))

    # final filter to vocab
    return [x for x in out if x in INTERVENTION_VOCAB]


def postprocess_record(rec: Dict[str, Any], text: str) -> None:
    # Normalize text fields to canonical forms
    rec["clinical"]["reason_for_visit"] = normalize_reason(rec["clinical"].get("reason_for_visit"))
    rec["clinical"]["follow_up"] = normalize_follow_up(rec["clinical"].get("follow_up"))

    # If LLM returned None for reason, fallback to rules
    if rec["clinical"]["reason_for_visit"] is None and EXTRACT_REASON:
        rec["clinical"]["reason_for_visit"] = normalize_reason(EXTRACT_REASON(text))

    # ✅ NEW: If follow_up is None but note mentions "nuovo controllo"
    if rec["clinical"]["follow_up"] is None and "nuovo controllo" in (text or "").lower():
        rec["clinical"]["follow_up"] = "programmato nuovo controllo"

    # Normalize interventions into controlled vocab + infer medicazione when appropriate
    rec["clinical"]["interventions"] = normalize_interventions(
        rec["clinical"].get("interventions", []),
        text=text,
        reason=rec["clinical"].get("reason_for_visit"),
    )

    # Infer controllo_parametri_vitali when vitals exist
    vitals = rec.get("clinical", {}).get("vitals", {}) or {}
    has_any_vital = any(
        vitals.get(k) is not None
        for k in ["blood_pressure_systolic", "blood_pressure_diastolic", "heart_rate", "temperature", "spo2"]
    )

    # ✅ NEW: If reason is still None but vitals exist, set standard reason
    if rec["clinical"]["reason_for_visit"] is None and has_any_vital:
        rec["clinical"]["reason_for_visit"] = "controllo parametri"

    if has_any_vital and "controllo_parametri_vitali" not in rec["clinical"]["interventions"]:
        rec["clinical"]["interventions"].insert(0, "controllo_parametri_vitali")


def run_quality_check(rec: Dict[str, Any], text: str) -> Dict[str, Any]:
    """
    Call quality_check() safely regardless of its signature.
    Supports:
      - quality_check(rec, text)
      - quality_check(rec)
    """
    try:
        return quality_check(rec, text)  # type: ignore
    except TypeError:
        return quality_check(rec)  # type: ignore


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--use-llm", action="store_true", help="Use LLM extraction only")
    parser.add_argument("--hybrid", action="store_true", help="Use hybrid extraction (recommended)")
    parser.add_argument("--model", default="llama3.1:8b", help="LLM model name (Ollama)")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    Path("reports").mkdir(parents=True, exist_ok=True)

    for txt_path in sorted(RAW_DIR.glob("ADI-*.txt")):
        record_id = txt_path.stem
        raw = txt_path.read_text(encoding="utf-8")
        text = PREPROCESS(raw)

        rec = build_base_record(record_id)

        if args.hybrid:
            apply_hybrid(text, rec, args.model)
        elif args.use_llm:
            apply_llm(text, rec, args.model)
        else:
            apply_rules(text, rec)

        # ✅ postprocessing before quality checks
        postprocess_record(rec, text)

        q = run_quality_check(rec, text)
        rec["quality"]["missing_mandatory_fields"] = q.get("missing_fields", [])
        rec["quality"]["warnings"] = q.get("warnings", [])

        out_path = OUT_DIR / f"{record_id}.json"
        out_path.write_text(json.dumps(rec, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {out_path}")

    (Path("reports") / "llm_mode.json").write_text(
        json.dumps(
            {"use_llm": args.use_llm, "hybrid": args.hybrid, "model": args.model},
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()