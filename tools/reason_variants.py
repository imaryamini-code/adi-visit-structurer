"""Experimental: variants of the rules-based reason-for-visit extractor, scored on a dev/test split.

Split: notes with an odd id number are DEV, even are TEST. Variants are chosen on DEV only. TEST is scored
once, only when --test is passed, so that the reported number was not used to pick the variant.

python3 -m tools.reason_variants            # DEV only
python3 -m tools.reason_variants --test     # also score TEST (do this once, at the end)
"""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from typing import Callable, Dict, List, Optional

from src.extract_rules import _clean, _match_any, _sentences, extract_reason, _reason_from_keywords
from src.normalize import normalize_reason

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data/synthetic/gold"
RAW = ROOT / "data/synthetic/raw"


def clean_note(text: str) -> str:
    """Drop generator artefacts: a leading 'Ecco la nota ...:' line and any trailing 'Nota: ...' commentary."""
    text = re.sub(r"^\s*Ecco la nota[^\n:]*:\s*", "", text, flags=re.IGNORECASE)
    text = re.split(r"\n\s*(?:Nota|Note|N\.B\.)\s*:", text, maxsplit=1, flags=re.IGNORECASE)[0]
    text = re.split(r"\s{2,}(?:Nota|Note)\s*:", text, maxsplit=1, flags=re.IGNORECASE)[0]
    text = re.split(r"(?<=[.!?])\s+(?:Nota|Note)\s*:", text, maxsplit=1, flags=re.IGNORECASE)[0]
    return text


# --- specific tiers, in priority order (each returns a reason or None) ---------------------------------
SPECIFIC_ACTIONS = [
    ("medicazione e controllo lesione",
     ["lesione da pressione", "piaga da decubito", "lesione da decubito", "decubito", "cambio di medicazione",
      "cambio medicazione", "medicazione", "medicata", "ferita", "ulcera", "piaga", "lesione", "lesionale"]),
    ("controllo e gestione catetere", ["catetere vescicale", "catetere", "presidio urinario", "vescicale"]),
    ("controllo e gestione stomia", ["presidio stomale", "cute peristomale", "stomia", "colostomia", "ileostomia"]),
    ("controllo respiratorio e gestione ossigenoterapia",
     ["ossigenoterapia", "o2 terapia", "controllo respiratorio", "rivalutazione respiratoria"]),
    ("rivalutazione caduta recente", ["caduta recente", "post-caduta", "post caduta", "caduta", "scivolato", "trauma recente"]),
]
THERAPY = ["verifica della terapia", "verifica terapia", "monitoraggio della terapia", "somministrata", "somministrato",
           "somministrate", "somministrazione", "farmaci", "farmaco", "terapia farmacologica", "trattamento prescritto"]
SYMPTOMS = ["stanchezza", "debolezza generale", "scarso appetito", "ridotto appetito", "inappetenza", "astenia",
            "capogiro", "nausea"]
BREATH_SYMPTOM = ["dispnea", "affanno"]
PAIN = ["dolore cronico", "dolore al ginocchio", "dolore ginocchio", "sintomatologia algica", "dolore", "algia"]


def _first(t: str, table) -> Optional[str]:
    for reason, cues in table:
        if _match_any(t, cues):
            return reason
    return None


def v0(text: str) -> Optional[str]:
    return extract_reason(text)


def v1(text: str) -> Optional[str]:
    """Cleaned note, current logic."""
    return extract_reason(clean_note(text))


def v2(text: str) -> Optional[str]:
    """Cleaned note; specific actions anywhere in the note beat generic lead phrases; else current logic."""
    t = _clean(clean_note(text))
    hit = _first(t, SPECIFIC_ACTIONS)
    return hit or extract_reason(clean_note(text))


def v3(text: str) -> Optional[str]:
    """v2 plus: therapy given beats symptom mentions (pain, dyspnoea, general symptoms)."""
    t = _clean(clean_note(text))
    hit = _first(t, SPECIFIC_ACTIONS)
    if hit:
        return hit
    if _match_any(t, THERAPY):
        return "controllo terapia e somministrazione farmaco"
    return extract_reason(clean_note(text))


def v4(text: str) -> Optional[str]:
    """v3 plus: a symptom stated anywhere beats generic lead phrases (but never an action)."""
    t = _clean(clean_note(text))
    hit = _first(t, SPECIFIC_ACTIONS)
    if hit:
        return hit
    if _match_any(t, THERAPY):
        return "controllo terapia e somministrazione farmaco"
    if _match_any(t, SYMPTOMS):
        return "valutazione sintomi generali"
    if _match_any(t, BREATH_SYMPTOM):
        return "controllo respiratorio e gestione ossigenoterapia"
    if _match_any(t, PAIN):
        return "rivalutazione dolore"
    return extract_reason(clean_note(text))


VARIANTS: Dict[str, Callable[[str], Optional[str]]] = {"v0 current": v0, "v1 clean tail": v1, "v2 specific anywhere": v2,
                                                        "v3 +therapy over symptoms": v3, "v4 +symptoms anywhere": v4}


def load():
    gold, text = {}, {}
    for f in sorted(GOLD.glob("ADI-*.json")):
        rid = f.stem
        gold[rid] = normalize_reason(json.loads(f.read_text(encoding="utf-8"))["clinical"].get("reason_for_visit"))
        text[rid] = (RAW / f"{rid}.txt").read_text(encoding="utf-8")
    return gold, text


def split(ids: List[str]):
    dev = [i for i in ids if int(i.split("-")[1]) % 2 == 1]
    test = [i for i in ids if int(i.split("-")[1]) % 2 == 0]
    return dev, test


def score(fn, ids, gold, text):
    ok = [normalize_reason(fn(text[i])) == gold[i] for i in ids]
    return sum(ok) / len(ids), ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true", help="also score the held-out TEST half (do this once)")
    ap.add_argument("--show-errors", action="store_true")
    args = ap.parse_args()
    gold, text = load()
    dev, test = split(sorted(gold))
    print(f"DEV n={len(dev)}  TEST n={len(test)} ({'scored' if args.test else 'locked'})\n")
    print("| variant | DEV accuracy |" + (" TEST accuracy |" if args.test else ""))
    print("|---|---|" + ("---|" if args.test else ""))
    for name, fn in VARIANTS.items():
        d, ok = score(fn, dev, gold, text)
        row = f"| {name} | {d:.3f} ({sum(ok)}/{len(dev)}) |"
        if args.test:
            t, tok = score(fn, test, gold, text)
            row += f" {t:.3f} ({sum(tok)}/{len(test)}) |"
        print(row)
    if args.show_errors:
        for name, fn in list(VARIANTS.items())[-1:]:
            print(f"\nDEV errors of {name}:")
            for i in dev:
                p = normalize_reason(fn(text[i]))
                if p != gold[i]:
                    print(f"  {i} gold={gold[i]} pred={p}")


if __name__ == "__main__":
    main()
