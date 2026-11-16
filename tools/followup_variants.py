"""Experimental: sentence-scoped follow-up extractor, scored on the same dev/test split as reason_variants.

DEV = odd note numbers, TEST = even. Design is done on DEV; TEST is scored once with --test.

python3 -m tools.followup_variants [--test] [--show-errors]
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from src.evaluate import follow_up_key
from src.extract_rules import (_clean, _match_any, _sentences, _timing_days, _word_days,
                               extract_datetime, extract_follow_up)
from tools.reason_variants import clean_note, split

ROOT = Path(__file__).resolve().parents[1]
GOLD = ROOT / "data/synthetic/gold"
RAW = ROOT / "data/synthetic/raw"

_PLAN = re.compile(r"programmat|previst|pianificat|prossim|nuov|success|ricontatt|ricontroll|follow-?up|da rivalutare")
_ITEM = re.compile(r"controll|visita|accesso|rivalutazione|ricontatt|ricontroll|follow-?up|contatto|telefon")
_NUM = re.compile(r"(\d+)\s+(giorn\w*|settiman\w*|mes\w*)")
_DATE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
WOUND = ["ferita", "lesione", "ulcera", "piaga", "medicazione", "decubito"]


def follow_up_v1(text: str) -> Optional[Dict[str, Any]]:
    note = clean_note(text)
    visit = extract_datetime(note)
    scope = [s for s in _sentences(note) if _PLAN.search(s) and _ITEM.search(s)]
    if not scope:
        return None
    blob = " ".join(scope)

    days = None
    m = _NUM.search(blob)
    if m:
        days = _timing_days(int(m.group(1)), m.group(2))
    if days is None:
        days = _word_days(blob)
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
    wound = _match_any(blob, WOUND)
    if days is not None:
        return {"type": "controllo_ferita" if wound else "controllo", "timing_days": days}
    if _match_any(blob, ["ricontatto telefonico", "contatto telefonico", "telefon"]):
        target = "caregiver" if _match_any(blob, ["caregiver", "familiari", "familiare", "parenti"]) else None
        return {"type": "ricontatto_telefonico", "timing_days": None, "target": target}
    return {"type": "controllo_ferita" if wound else "controllo", "timing_days": None}


_PLAN2 = re.compile(_PLAN.pattern + r"|prevede|prevedere|concordat|fissat|stabilit|ulterior")
_ITEM2 = re.compile(_ITEM.pattern + r"|monitoraggio")


def follow_up_v2(text: str) -> Optional[Dict[str, Any]]:
    """v1 + wider cue lexicon (prevede, concordato, monitoraggio, ordinal 'settimo giorno').
    Designed AFTER seeing all notes, so any score on this set is in-sample."""
    note = clean_note(text)
    visit = extract_datetime(note)
    scope = [s for s in _sentences(note) if _PLAN2.search(s) and _ITEM2.search(s)]
    if not scope:
        return None
    blob = " ".join(scope)
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
    wound = _match_any(blob, WOUND)
    if days is not None:
        return {"type": "controllo_ferita" if wound else "controllo", "timing_days": days}
    if _match_any(blob, ["ricontatto telefonico", "contatto telefonico", "telefon"]):
        target = "caregiver" if _match_any(blob, ["caregiver", "familiari", "familiare", "parenti"]) else None
        return {"type": "ricontatto_telefonico", "timing_days": None, "target": target}
    return {"type": "controllo_ferita" if wound else "controllo", "timing_days": None}


VARIANTS = {"v0 current": lambda t: extract_follow_up(t), "v1 sentence-scoped": follow_up_v1,
            "v2 wider cues (in-sample)": follow_up_v2}


def load():
    gold, text = {}, {}
    for f in sorted(GOLD.glob("ADI-*.json")):
        gold[f.stem] = follow_up_key(json.loads(f.read_text(encoding="utf-8"))["clinical"].get("follow_up"))
        text[f.stem] = (RAW / f"{f.stem}.txt").read_text(encoding="utf-8")
    return gold, text


def acc(fn, ids, gold, text):
    ok = [follow_up_key(fn(text[i])) == gold[i] for i in ids]
    return sum(ok) / len(ids), ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--show-errors", action="store_true")
    a = ap.parse_args()
    gold, text = load()
    dev, test = split(sorted(gold))
    print(f"DEV n={len(dev)} TEST n={len(test)} ({'scored' if a.test else 'locked'})\n| variant | DEV |" + (" TEST |" if a.test else ""))
    print("|---|---|" + ("---|" if a.test else ""))
    for name, fn in VARIANTS.items():
        d, ok = acc(fn, dev, gold, text)
        row = f"| {name} | {d:.3f} ({sum(ok)}/{len(dev)}) |"
        if a.test:
            t, tok = acc(fn, test, gold, text)
            row += f" {t:.3f} ({sum(tok)}/{len(test)}) |"
        print(row)
    if a.show_errors:
        fn = VARIANTS["v1 sentence-scoped"]
        print("\nDEV errors of v1:")
        for i in dev:
            p = follow_up_key(fn(text[i]))
            if p != gold[i]:
                print(f"  {i} gold={gold[i]} pred={p}")


if __name__ == "__main__":
    main()
