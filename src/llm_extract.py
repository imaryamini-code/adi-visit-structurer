# src/llm_extract.py

import json
import os
from typing import Any, Dict

import requests


DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_MODEL = "llama3.1:8b"


SYSTEM_PROMPT = (
    "You extract structured clinical data from Italian ADI home-visit notes.\n"
    "Return ONLY valid JSON with this structure:\n"
    '{ "clinical": { "reason_for_visit": null|string, "follow_up": null|string, '
    '"interventions": [], "vitals": { "blood_pressure_systolic": null|number, '
    '"blood_pressure_diastolic": null|number, "heart_rate": null|number, '
    '"temperature": null|number, "spo2": null|number } }, '
    '"coding": { "problems_normalized": [] } }\n'
    "Rules:\n"
    "- Do NOT invent data.\n"
    "- Do NOT confuse dates with blood pressure.\n"
    "- Use null if missing.\n"
    "- Output must be strict JSON (no commentary, no markdown).\n"
)


def llm_extract(
    text: str,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_OLLAMA_URL,
) -> Dict[str, Any]:
    """
    Local LLM extraction using Ollama.
    Requires Ollama running (usually already) and model pulled (e.g., llama3.1:8b).
    """
    prompt = f"{SYSTEM_PROMPT}\n\nTEXT:\n{text}\n\nJSON ONLY:"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1},
    }

    try:
        r = requests.post(f"{base_url}/api/generate", json=payload, timeout=90)
    except requests.RequestException as e:
        raise RuntimeError(
            f"Could not reach Ollama at {base_url}. "
            "Make sure Ollama is running.\n"
            f"Error: {e}"
        )

    if r.status_code != 200:
        raise RuntimeError(f"Ollama error {r.status_code}: {r.text}")

    data = r.json()
    out_text = (data.get("response") or "").strip()

    # Best-effort extract JSON object if the model adds extra text
    if "{" in out_text and "}" in out_text:
        out_text = out_text[out_text.find("{") : out_text.rfind("}") + 1]

    try:
        return json.loads(out_text)
    except json.JSONDecodeError as e:
        os.makedirs("reports", exist_ok=True)
        with open("reports/llm_raw_output.txt", "w", encoding="utf-8") as f:
            f.write(out_text)
        raise RuntimeError(
            "Local LLM returned invalid JSON. Raw output saved to reports/llm_raw_output.txt.\n"
            f"JSON error: {e}"
        )