"""Version-2 rule extractors (opt-in: `process_note(..., extractors="v2")` / `compare_models --extractors v2`).

What changed relative to v1 and why (evidence: docs, tools/*_variants.py, project note error-analysis-2026-11-16):

* clean_note: drop generator artefacts ("Ecco la nota ...:" lead, trailing "Nota: ..." commentary).
* reason_v3: specific actions (wound, catheter, ostomy, respiratory therapy, fall) anywhere in the note beat a generic
  lead phrase; therapy given beats symptom mentions. Held-out gain was small (+2 of 50 notes); known weakness: a fall
  note that mentions possible lesions can be read as wound care.
* follow_up_v2: only sentences that plan a follow-up count; timing from digits/words/"settimo giorno"/"prossima
  settimana"/a calendar date relative to the visit; type taken from the follow-up sentence. Held-out gain +3 of 50 notes
  (design version) and further gap-filling afterwards (in-sample).
* drop_generic_lesion: `lesione_da_pressione` only when the note says decubito / da pressione / piaga
  (held-out problems F1 0.706 -> 0.833). Applied to every mode so conditions stay comparable.

v1 behaviour is untouched. Nothing here reads the gold files.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, Optional, Set

from src.extract_rules import (_clean, _match_any, _sentences, _timing_days, _word_days,
                               extract_datetime, extract_reason)


# --- note cleaning -----------------------------------------------------------------------------------------
def clean_note(text: str) -> str:
    text = re.sub(r"^\s*Ecco la nota[^\n:]*:\s*", "", text, flags=re.IGNORECASE)
    text = re.split(r"\n\s*(?:Nota|Note|N\.B\.)\s*:", text, maxsplit=1, flags=re.IGNORECASE)[0]
    text = re.split(r"\s{2,}(?:Nota|Note)\s*:", text, maxsplit=1, flags=re.IGNORECASE)[0]
    text = re.split(r"(?<=[.!?])\s+(?:Nota|Note)\s*:", text, maxsplit=1, flags=re.IGNORECASE)[0]
    return text


# --- reason ------------------------------------------------------------------------------------------------
_SPECIFIC_ACTIONS = [
    ("medicazione e controllo lesione",
     ["lesione da pressione", "piaga da decubito", "lesione da decubito", "decubito", "cambio di medicazione",
      "cambio medicazione", "medicazione", "medicata", "ferita", "ulcera", "piaga", "lesione", "lesionale"]),
    ("controllo e gestione catetere", ["catetere vescicale", "catetere", "presidio urinario", "vescicale"]),
    ("controllo e gestione stomia", ["presidio stomale", "cute peristomale", "stomia", "colostomia", "ileostomia"]),
    ("controllo respiratorio e gestione ossigenoterapia",
     ["ossigenoterapia", "o2 terapia", "controllo respiratorio", "rivalutazione respiratoria"]),
    ("rivalutazione caduta recente",
     ["caduta recente", "post-caduta", "post caduta", "caduta", "scivolato", "trauma recente"]),
]
_THERAPY = ["verifica della terapia", "verifica terapia", "monitoraggio della terapia", "somministrata",
            "somministrato", "somministrate", "somministrazione", "farmaci", "farmaco", "terapia farmacologica",
            "trattamento prescritto"]


def reason_v3(text: str) -> Optional[str]:
    note = clean_note(text)
    t = _clean(note)
    for reason, cues in _SPECIFIC_ACTIONS:
        if _match_any(t, cues):
            return reason
    if _match_any(t, _THERAPY):
        return "controllo terapia e somministrazione farmaco"
    return extract_reason(note)


# --- follow-up ---------------------------------------------------------------------------------------------
_PLAN = re.compile(r"programmat|previst|pianificat|prossim|nuov|success|ricontatt|ricontroll|follow-?up|da rivalutare"
                   r"|prevede|prevedere|concordat|fissat|stabilit|ulterior")
_ITEM = re.compile(r"controll|visita|accesso|rivalutazione|ricontatt|ricontroll|follow-?up|contatto|telefon|monitoraggio")
_NUM = re.compile(r"(\d+)\s+(giorn\w*|settiman\w*|mes\w*)")
_DATE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
_WOUND = ["ferita", "lesione", "ulcera", "piaga", "medicazione", "decubito"]


def _follow_up_from_blob(blob: str, visit: Optional[str]) -> Dict[str, Any]:
    days = None
    m = _NUM.search(blob)
    if m:
        days = _timing_days(int(m.group(1)), m.group(2))
    if days is None:
        days = _word_days(blob)
    if days is None and re.search(r"\bsettimo\s+giorno\b", blob):
        days = 7
    if days is None and ("prossima settimana" in blob or "settimana prossima" in blob):
        days = 7
    if days is None and visit:
        m = _DATE.search(blob)
        if m:
            try:
                d = datetime(int(m.group(3)), int(m.group(2)), int(m.group(1)))
                delta = (d - datetime.fromisoformat(visit).replace(hour=0, minute=0)).days
                if delta > 0:
                    days = delta
            except ValueError:
                pass
    wound = _match_any(blob, _WOUND)
    if days is not None:
        return {"type": "controllo_ferita" if wound else "controllo", "timing_days": days}
    if _match_any(blob, ["ricontatto telefonico", "contatto telefonico", "telefon"]):
        target = "caregiver" if _match_any(blob, ["caregiver", "familiari", "familiare", "parenti"]) else None
        return {"type": "ricontatto_telefonico", "timing_days": None, "target": target}
    return {"type": "controllo_ferita" if wound else "controllo", "timing_days": None}


def follow_up_v2(text: str) -> Optional[Dict[str, Any]]:
    """Follow-up from a whole note: only sentences that plan a follow-up are read."""
    note = clean_note(text)
    scope = [s for s in _sentences(note) if _PLAN.search(s) and _ITEM.search(s)]
    if not scope:
        return None
    return _follow_up_from_blob(" ".join(scope), extract_datetime(note))


def follow_up_phrase_v2(phrase: str) -> Optional[Dict[str, Any]]:
    """Free-text follow-up phrase (typically an LLM answer) -> structured form, understanding more timings."""
    if not isinstance(phrase, str) or not phrase.strip():
        return None
    t = _clean(phrase)
    if not _ITEM.search(t):
        return None
    return _follow_up_from_blob(t, None)


# --- problems ----------------------------------------------------------------------------------------------
_EXPLICIT_PRESSURE = re.compile(r"decubito|da pressione|piaga")


def drop_generic_lesion(problems, text: str):
    """Keep `lesione_da_pressione` only when the note states a pressure/decubitus lesion."""
    out = list(problems)
    if not _EXPLICIT_PRESSURE.search(clean_note(text).lower()):
        out = [p for p in out if p != "lesione_da_pressione"]
    return out
