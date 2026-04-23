# src/problem_evidence.py

import re

# Add / refine patterns as your controlled vocabulary grows
EVIDENCE_PATTERNS: dict[str, list[str]] = {
    "dolore_cronico": [
        r"\bdolore\b",
        r"\algia\b",
        r"\bnevralg",
        r"\bnrs\b",
        r"\bvas\b",
        r"\bscal[ae]\s*(?:nrs|vas)\b",
    ],
    "caduta": [
        r"\bcadut",
        r"\bscivolat",
        r"\btrauma\b",
        r"\bcontus",
    ],
    "scompenso_cardiaco": [
        r"\bscompenso\b",
        r"\binsufficienza\s+cardiaca\b",
        r"\bchf\b",
    ],
    "ipertensione": [
        r"\bipertens",
    ],
    "lesione_da_pressione": [
        r"\blesione\s+da\s+pressione\b",
        r"\bdecubit",
        r"\bpiaga\b",
        r"\bulcera\b",
    ],
    "malnutrizione": [
        r"\bmalnutriz",
        r"\bscarso\s+appetito\b",
        r"\bcalo\s+ponderale\b",
        r"\bappetito\s+scarso\b",
    ],
    "diabete_tipo_2": [
        r"\bdiabet",
        r"\bdm2\b",
        r"\bglicem",
    ],
    "scompenso_cardiaco": [
        r"\bscompenso\b",
        r"\binsufficienza\s+cardiaca\b",
        r"\bchf\b",
    ],
}

def has_evidence(label: str, text: str) -> bool:
    pats = EVIDENCE_PATTERNS.get(label, [])
    if not pats:
        # If we don't know the label, be conservative
        return False
    t = (text or "").lower()
    return any(re.search(p, t) for p in pats)