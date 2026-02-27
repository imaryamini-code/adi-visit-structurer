# src/llm_extract.py

import json
import os
from typing import Any, Dict, Optional

import requests

DEFAULT_OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")  # safer default than llama3.1:8b


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
    timeout_s: int = 90,
) -> Dict[str, Any]:
    """
    Local LLM extraction using Ollama.
    Requires:
      - Ollama running on base_url (default http://localhost:11434)
      - Model pulled locally (e.g. `ollama pull llama3.1`)
    """
    prompt = f"{SYSTEM_PROMPT}\n\nTEXT:\n{text}\n\nJSON ONLY:"

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1},
    }

    try:
        r = requests.post(f"{base_url}/api/generate", json=payload, timeout=timeout_s)
    except requests.RequestException as e:
        raise RuntimeError(
            f"Could not reach Ollama at {base_url}.\n"
            "Make sure Ollama is running (e.g. `ollama serve`).\n"
            f"Error: {e}"
        )

    if r.status_code != 200:
        # Common case: model not found locally
        if "model" in r.text.lower() and "not" in r.text.lower():
            raise RuntimeError(
                f"Ollama returned {r.status_code}: {r.text}\n"
                f"Model '{model}' may not be installed.\n"
                f"Try: ollama pull {model}\n"
                "Or set OLLAMA_MODEL to a model you have."
            )
        raise RuntimeError(f"Ollama error {r.status_code}: {r.text}")

    data = r.json()
    out_text = (data.get("response") or "").strip()

    # Best-effort: extract JSON object if the model adds extra text
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