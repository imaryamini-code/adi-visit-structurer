# src/normalize.py

from rapidfuzz import fuzz
from src.resources.problem_lexicon import PROBLEM_VOCAB, SYNONYM_MAP


FUZZY_THRESHOLD = 92  # high threshold = protects precision


def normalize_problems(text: str) -> list[str]:
    """
    Normalize clinical problems from raw Italian text using:
    - exact synonym matching (high precision)
    - fuzzy matching for near-typos (high threshold)
    - a few safe rule triggers
    """
    if not text:
        return []

    t = text.lower()
    found = set()

    # 1) Exact phrase mapping
    for phrase, norm in SYNONYM_MAP.items():
        if phrase in t:
            found.add(norm)

    # 2) Fuzzy matching (only for items not already found)
    # This helps with small typos like "ipertensione arteriosaa"
    for phrase, norm in SYNONYM_MAP.items():
        if norm in found:
            continue
        score = fuzz.partial_ratio(phrase, t)
        if score >= FUZZY_THRESHOLD:
            found.add(norm)

    # 3) Combined malnutrition rule
    appetite_signals = any(
        phrase in t
        for phrase in ["scarso appetito", "inappetenza", "ridotto appetito", "mangia poco", "non mangia"]
    )
    if "stanchezza" in t and appetite_signals:
        found.add("malnutrizione")

    # 4) Generic pain rule
    if "dolore" in t:
        found.add("dolore_cronico")

    # 5) Keep only valid vocabulary
    found = {label for label in found if label in PROBLEM_VOCAB}
    return sorted(found)