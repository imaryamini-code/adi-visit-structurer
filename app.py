"""
app.py
ADI Assistant — Flask web application.

Accepts voice or text clinical notes and returns structured ADI report drafts.
Uses the same pipeline modules as the batch runner (src/run_pipeline.py).
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from flask import Flask, jsonify, render_template, request

from src.preprocess import preprocess_text
from src.extract_rules import (
    extract_vitals,
    extract_reason,
    extract_anamnesis,
    extract_follow_up,
    extract_interventions,
    extract_critical_issues,
)
from src.normalize import normalize_problems, normalize_reason, normalize_interventions
from src.voice_input import transcribe_audio

app = Flask(__name__)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

OLLAMA_MODEL = "mistral"
OLLAMA_URL = "http://localhost:11434/api/generate"

# Smart mode: only call LLM when rules don't produce enough
SMART_LLM_MODE = False  # mistral is fast — always run for best accuracy
RULE_ONLY_MODE = False


# ---------------------------------------------------------------------------
# LLM extraction (optional — falls back gracefully if Ollama is unavailable)
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> Dict[str, Any]:
    """Extract first JSON object from model output."""
    text = text.strip()
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    import re
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if m:
        try:
            obj = json.loads(m.group(0))
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

    return {}


def _call_llm(text: str) -> Dict[str, Any]:
    """Call local Ollama LLM for flexible clinical extraction."""
    prompt = (
        "You are a clinical NLP assistant for Italian ADI home-care notes.\n"
        "Extract structured information and return ONLY valid JSON — no markdown, no explanation.\n\n"
        "Return this exact structure:\n"
        '{"reason_for_visit":null,"anamnesis_brief":null,'
        '"vitals":{"blood_pressure_systolic":null,"blood_pressure_diastolic":null,'
        '"heart_rate":null,"temperature":null,"spo2":null},'
        '"follow_up":null,"interventions":[],"critical_issues":[]}\n\n'
        "Rules:\n"
        "- reason_for_visit: short Italian phrase (e.g. controllo parametri vitali, medicazione e controllo lesione)\n"
        "- vitals: split BP into systolic/diastolic integers. Dates like 15/02 are NOT blood pressure.\n"
        "- interventions: use underscore_format (monitoraggio_parametri_vitali, medicazione, etc.)\n"
        "- follow_up: next planned action in Italian (e.g. controllo tra 7 giorni)\n"
        "- Use null for anything not mentioned. Do not invent data.\n\n"
        f"Note:\n{text}"
    )

    try:
        r = requests.post(
            OLLAMA_URL,
            json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False,
                  "options": {"temperature": 0, "num_predict": 150}},
            timeout=30,
        )
        r.raise_for_status()
        raw = r.json().get("response", "")
    except Exception as e:
        return {"_llm_error": str(e)}

    parsed = _extract_json(raw)
    if not parsed:
        return {"_llm_error": "Model output could not be parsed as JSON."}

    def safe_str(v: Any) -> Optional[str]:
        if v is None:
            return None
        s = str(v).strip()
        return s if s else None

    vitals = parsed.get("vitals") or {}
    interventions = parsed.get("interventions") or []
    if not isinstance(interventions, list):
        interventions = [str(interventions)] if interventions else []

    critical = parsed.get("critical_issues") or []
    if not isinstance(critical, list):
        critical = [str(critical)] if critical else []

    return {
        "reason_for_visit": normalize_reason(safe_str(parsed.get("reason_for_visit"))),
        "anamnesis_brief": safe_str(parsed.get("anamnesis_brief")),
        "vitals_llm": {
            "blood_pressure": safe_str(vitals.get("blood_pressure")),
            "heart_rate": safe_str(vitals.get("heart_rate")),
            "temperature": safe_str(vitals.get("temperature")),
            "spo2": safe_str(vitals.get("spo2")),
        },
        "follow_up": safe_str(parsed.get("follow_up")),
        "interventions": normalize_interventions(
            [str(x).strip() for x in interventions if str(x).strip()]
        ),
        "critical_issues": list(dict.fromkeys(
            str(x).strip() for x in critical if str(x).strip()
        )),
        "_llm_error": None,
    }


def _should_call_llm(rule_vitals: Dict, reason: Optional[str], interventions: List) -> bool:
    if RULE_ONLY_MODE:
        return False
    if not SMART_LLM_MODE:
        return True
    enough_vitals = sum(1 for v in rule_vitals.values() if v is not None) >= 1
    return not (reason and enough_vitals and interventions)


# ---------------------------------------------------------------------------
# Hybrid extraction (rules-first, LLM fills gaps)
# ---------------------------------------------------------------------------

def hybrid_extract(text: str) -> Dict[str, Any]:
    """
    Run rule-based extraction first.
    Only call LLM when rules don't produce sufficient output.
    Rules are the single source of truth for numeric values.
    """
    vitals = extract_vitals(text)
    reason = extract_reason(text)
    anamnesis = extract_anamnesis(text)
    follow_up = extract_follow_up(text)
    interventions = extract_interventions(text, vitals=vitals, reason=reason)
    critical = extract_critical_issues(text, spo2=vitals.get("spo2"))
    problems = normalize_problems(text)
    llm_error = None

    if _should_call_llm(vitals, reason, interventions):
        llm = _call_llm(text)
        llm_error = llm.get("_llm_error")

        if not reason:
            reason = llm.get("reason_for_visit")
        if not follow_up:
            raw_fu = llm.get("follow_up")
            if raw_fu:
                follow_up = raw_fu  # string from LLM, kept as-is

        # LLM interventions supplement but don't override rules
        llm_interventions = llm.get("interventions", []) or []
        interventions = normalize_interventions(list(set(interventions + llm_interventions)))

    if not reason:
        reason = "valutazione generale"
    reason = normalize_reason(reason) or reason

    return {
        "reason_for_visit": reason,
        "anamnesis_brief": anamnesis,
        "vitals": vitals,
        "follow_up": follow_up,
        "interventions": interventions,
        "critical_issues": critical,
        "problems_normalized": problems,
        "_llm_error": llm_error,
    }


# ---------------------------------------------------------------------------
# Output builder
# ---------------------------------------------------------------------------

def build_output(extracted: Dict[str, Any]) -> Dict[str, Any]:
    warnings: List[str] = []
    missing: List[str] = []

    if not extracted.get("reason_for_visit"):
        missing.append("clinical.reason_for_visit")

    vitals = extracted.get("vitals", {}) or {}
    present = [k for k, v in vitals.items() if v is not None]

    if not present:
        warnings.append("No vital signs recorded in note")
    elif len(present) < 2:
        warnings.append(f"Only partial vital signs detected: {', '.join(present)}")

    if not extracted.get("interventions"):
        warnings.append("No interventions detected")



    # Convert follow_up dict to human-readable string for web display
    follow_up = extracted.get("follow_up")
    if isinstance(follow_up, dict):
        ftype = follow_up.get("type", "")
        days = follow_up.get("timing_days")
        target = follow_up.get("target")
        if ftype == "controllo_ferita":
            follow_up = f"Controllo ferita tra {days} giorni." if days else "Controllo ferita programmato."
        elif ftype == "ricontatto_telefonico":
            follow_up = f"Ricontatto telefonico con {target}." if target else "Ricontatto telefonico previsto."
        elif ftype == "controllo":
            follow_up = f"Nuovo controllo tra {days} giorni." if days else "Controllo programmato."
        else:
            follow_up = str(ftype).replace("_", " ") if ftype else None

    return {
        "meta": {
            "visit_datetime": datetime.now().isoformat(timespec="seconds"),
            "operator_role": "infermiere",
            "model": OLLAMA_MODEL if not RULE_ONLY_MODE else None,
            "extraction_mode": "rule-only" if RULE_ONLY_MODE else "fast-hybrid",
        },
        "clinical": {
            "reason_for_visit": extracted.get("reason_for_visit"),
            "anamnesis_brief": extracted.get("anamnesis_brief"),
            "vitals": {
                "blood_pressure": (
                    f"{vitals['blood_pressure_systolic']}/{vitals['blood_pressure_diastolic']}"
                    if vitals.get("blood_pressure_systolic") and vitals.get("blood_pressure_diastolic")
                    else None
                ),
                "heart_rate": vitals.get("heart_rate"),
                "temperature": vitals.get("temperature"),
                "spo2": vitals.get("spo2"),
            },
            "follow_up": follow_up,
            "interventions": extracted.get("interventions", []),
            "critical_issues": extracted.get("critical_issues", []),
        },
        "coding": {
            "problems_normalized": extracted.get("problems_normalized", []),
        },
        "quality": {
            "missing_mandatory_fields": missing,
            "warnings": warnings,
        },
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def home():
    return render_template("login.html")


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/assistant")
def assistant():
    return render_template("index.html")


@app.route("/quiz")
def quiz():
    return render_template("quiz.html")


@app.route("/process_text", methods=["POST"])
def process_text():
    data = request.get_json(silent=True) or {}
    raw_text = (data.get("text") or "").strip()

    if not raw_text:
        return jsonify({"error": "No text provided"}), 400

    text = preprocess_text(raw_text)
    extracted = hybrid_extract(text)
    output = build_output(extracted)

    return jsonify({"transcript": raw_text, "result": output})


@app.route("/process_audio", methods=["POST"])
def process_audio():
    if "audio" not in request.files:
        return jsonify({"error": "No audio file provided"}), 400

    audio_file = request.files["audio"]
    if not audio_file.filename:
        return jsonify({"error": "Empty filename"}), 400

    save_path = UPLOAD_DIR / audio_file.filename
    audio_file.save(save_path)

    try:
        raw_transcript = transcribe_audio(str(save_path))
    except Exception as e:
        return jsonify({"error": f"Audio transcription failed: {e}"}), 500
    finally:
        try:
            save_path.unlink(missing_ok=True)
        except Exception:
            pass

    text = preprocess_text(raw_transcript)
    extracted = hybrid_extract(text)
    output = build_output(extracted)

    return jsonify({"transcript": raw_transcript, "result": output})


if __name__ == "__main__":
    app.run(debug=True, port=5001)
