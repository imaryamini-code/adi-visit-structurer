# src/normalize.py
from __future__ import annotations

import re
from rapidfuzz import fuzz

PROBLEM_VOCAB = {
    "ipertensione",
    "diabete_tipo_2",
    "lesione_da_pressione",
    "dolore_cronico",
    "scompenso_cardiaco",
    "bpco",
    "caduta",
    "rischio_caduta",
    "disidratazione",
    "malnutrizione",
}

SYNONYM_MAP = {
    # Hypertension (including common typos)
    "ipertensione arteriosa": "ipertensione",
    "ipertensione": "ipertensione",
    "pressione alta": "ipertensione",
    "ipertensone": "ipertensione",
    "ipertensone arteriosa": "ipertensione",

    # Diabetes
    "diabete tipo 2": "diabete_tipo_2",
    "diabete mellito tipo 2": "diabete_tipo_2",
    "diabete tipo2": "diabete_tipo_2",

    # Pressure injury
    "lesione da pressione": "lesione_da_pressione",
    "piaga da decubito": "lesione_da_pressione",
    "ulcera da pressione": "lesione_da_pressione",

    # Chronic pain
    "dolore cronico": "dolore_cronico",

    # Respiratory
    "bpco": "bpco",
    "bronchite cronica": "bpco",
}

FUZZY_ENABLED = True
FUZZY_THRESHOLD = 88  # slightly lower to catch more typos safely


def _normalize_text(text: str) -> str:
    t = text.lower()
    t = re.sub(r"[^a-zàèéìòù0-9\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalize_problems(text: str) -> list[str]:
    t = _normalize_text(text)
    found: set[str] = set()

    # 1) Exact matching
    for phrase, norm in SYNONYM_MAP.items():
        if phrase in t:
            found.add(norm)

    # 2) Regex fallback for “ipertens...” family (ipertensone, ipertensione, ipertensiva...)
    if re.search(r"\bipertens\w*\b", t):
        found.add("ipertensione")

    # 3) Fuzzy matching as safety net
    if FUZZY_ENABLED:
        for phrase, norm in SYNONYM_MAP.items():
            if norm in found:
                continue
            if len(phrase) < 6:
                continue
            if fuzz.partial_ratio(phrase, t) >= FUZZY_THRESHOLD:
                found.add(norm)

    # Safety: only controlled vocab
    found = {p for p in found if p in PROBLEM_VOCAB}
    return sorted(found)