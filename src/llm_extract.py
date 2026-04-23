"""
src/llm_extract.py
Local LLM extraction using Ollama.

Features:
- Strict JSON output with schema enforcement
- JSON extraction if model adds preamble
- One retry with repair prompt on parse failure
- Optional raw output return for debugging
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional, Tuple

import requests

DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "mistral")

SYSTEM_PROMPT = (
    "You are a clinical NLP assistant specializing in Italian ADI (Assistenza Domiciliare Integrata) home-care notes.\n"
    "Your task: extract structured clinical information and return it as strict JSON.\n\n"
    "OUTPUT FORMAT — return exactly this structure, nothing else:\n"
    '{\n'
    '  "clinical": {\n'
    '    "reason_for_visit": null,\n'
    '    "follow_up": null,\n'
    '    "interventions": [],\n'
    '    "vitals": {\n'
    '      "blood_pressure_systolic": null,\n'
    '      "blood_pressure_diastolic": null,\n'
    '      "heart_rate": null,\n'
    '      "temperature": null,\n'
    '      "spo2": null\n'
    '    }\n'
    '  },\n'
    '  "coding": {\n'
    '    "problems_normalized": []\n'
    '  }\n'
    '}\n\n'
    "EXTRACTION RULES:\n"
    "1. reason_for_visit: short Italian clinical phrase describing WHY the visit occurred.\n"
    "   Examples: controllo parametri vitali, medicazione e controllo lesione, rivalutazione dolore\n"
    "2. follow_up: next planned action. Examples: controllo tra 7 giorni, ricontatto telefonico con caregiver\n"
    "3. interventions: list of actions performed. Use underscore_format.\n"
    "   Valid values: monitoraggio_parametri_vitali, valutazione_generale, medicazione,\n"
    "   somministrazione_farmaco, gestione_catetere, gestione_stomia, gestione_ossigenoterapia,\n"
    "   educazione_terapeutica, monitoraggio_glicemia\n"
    "4. vitals: extract as separate numbers. blood_pressure MUST be split into systolic and diastolic.\n"
    "   IMPORTANT: dates like 15/02/2026 are NOT blood pressure. Only extract BP if explicitly mentioned.\n"
    "5. problems_normalized: clinical problems found. Examples: dolore, lesione_da_pressione, caduta,\n"
    "   ipertensione, dispnea, febbre, diabete_tipo_2, bpco\n"
    "6. Use null for any field not mentioned in the note. Do NOT invent data.\n"
    "7. Output ONLY the JSON object. No explanation, no markdown, no code fences.\n"
)

REPAIR_PROMPT = (
    "You returned INVALID JSON. Fix it.\n"
    "Return ONLY strict JSON with the exact required structure.\n"
    "Do not add any text outside the JSON object.\n"
)


def _extract_json_object(text: str) -> str:
    """Best-effort extraction of a JSON object if the model adds extra text."""
    t = (text or "").strip()
    if "{" in t and "}" in t:
        t = t[t.find("{") : t.rfind("}") + 1]
    return t.strip()


def _call_ollama(prompt: str, model: str, base_url: str, timeout_s: int) -> str:
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0},
    }
    try:
        r = requests.post(f"{base_url}/api/generate", json=payload, timeout=timeout_s)
    except requests.RequestException as e:
        raise RuntimeError(
            f"Could not reach Ollama at {base_url}.\n"
            "Make sure Ollama is running: ollama serve\n"
            f"Error: {e}"
        )

    if r.status_code != 200:
        if "model" in r.text.lower() and "not" in r.text.lower():
            raise RuntimeError(
                f"Ollama returned {r.status_code}: {r.text}\n"
                f"Model '{model}' may not be installed.\n"
                f"Run: ollama pull {model}"
            )
        raise RuntimeError(f"Ollama error {r.status_code}: {r.text}")

    return (r.json().get("response") or "").strip()


def llm_extract(
    text: str,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_OLLAMA_URL,
    timeout_s: int = 90,
    return_raw: bool = False,
    max_retries: int = 1,
) -> Dict[str, Any] | Tuple[Dict[str, Any], str]:
    """
    Extract structured clinical data using a local LLM via Ollama.

    Args:
        text: Preprocessed clinical note.
        model: Ollama model name.
        base_url: Ollama server URL.
        timeout_s: Request timeout in seconds.
        return_raw: If True, return (parsed_dict, raw_string) tuple.
        max_retries: Number of repair attempts on invalid JSON.

    Returns:
        Parsed dict, or (dict, raw_str) if return_raw=True.

    Raises:
        RuntimeError: If Ollama is unreachable or JSON cannot be parsed after retries.
    """
    prompt = f"{SYSTEM_PROMPT}\n\nTEXT:\n{text}\n\nJSON ONLY:"
    raw = _call_ollama(prompt=prompt, model=model, base_url=base_url, timeout_s=timeout_s)
    candidate = _extract_json_object(raw)

    def _try_parse(s: str) -> Optional[Dict[str, Any]]:
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return None

    parsed = _try_parse(candidate)

    for _ in range(max_retries):
        if parsed is not None:
            break
        repair = (
            f"{REPAIR_PROMPT}\n"
            f"Required structure:\n{SYSTEM_PROMPT}\n\n"
            f"TEXT:\n{text}\n\n"
            f"Your invalid output:\n{raw}\n\n"
            "JSON ONLY:"
        )
        raw = _call_ollama(prompt=repair, model=model, base_url=base_url, timeout_s=timeout_s)
        candidate = _extract_json_object(raw)
        parsed = _try_parse(candidate)

    if parsed is None:
        os.makedirs("reports", exist_ok=True)
        with open("reports/llm_raw_output_last.txt", "w", encoding="utf-8") as f:
            f.write(raw)
        raise RuntimeError(
            "Local LLM returned invalid JSON after retries. "
            "Raw output saved to reports/llm_raw_output_last.txt."
        )

    return (parsed, raw) if return_raw else parsed
