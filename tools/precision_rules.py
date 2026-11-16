"""Post-hoc precision rules tested on stored rules predictions, dev (odd) vs locked TEST (even) notes.

problems: keep `lesione_da_pressione` only when the note says decubito / da pressione / piaga   (ADOPT: holds on TEST)
interventions: drop monitoraggio / valutazione_generale by predicted reason                     (NOT ADOPTED: fitted on DEV, fails on TEST)

python3 -m tools.precision_rules --rules-pred experiments/full_01/rules/predictions
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from src.normalize import normalize_interventions, normalize_problems, normalize_reason
from tools.reason_variants import clean_note, split, v3

ROOT = Path(__file__).resolve().parents[1]
EXPLICIT_PRESSURE = re.compile(r"decubito|da pressione|piaga")
TREAT = {"medicazione e controllo lesione", "controllo terapia e somministrazione farmaco", "valutazione sintomi generali"}


def drop_generic_lesion(problems: set, text: str) -> set:
    p = set(problems)
    if not EXPLICIT_PRESSURE.search(clean_note(text).lower()):
        p.discard("lesione_da_pressione")
    return p


def suppress_interventions(interv: set, text: str) -> set:
    p, r = set(interv), normalize_reason(v3(text))
    if r in TREAT:
        p.discard("monitoraggio_parametri_vitali")
    if r in {"controllo terapia e somministrazione farmaco", "controllo parametri"}:
        p.discard("valutazione_generale")
    return p


def micro_f1(pairs):
    tp = sum(len(g & p) for g, p in pairs)
    fp = sum(len(p - g) for g, p in pairs)
    fn = sum(len(g - p) for g, p in pairs)
    pr, rc = (tp / (tp + fp) if tp + fp else 0.0), (tp / (tp + fn) if tp + fn else 0.0)
    return 2 * pr * rc / (pr + rc) if pr + rc else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules-pred", type=Path, required=True)
    a = ap.parse_args()
    ids = sorted(p.stem for p in (ROOT / "data/synthetic/gold").glob("ADI-*.json"))
    dev, test = split(ids)
    load = lambda d, i: json.loads((d / f"{i}.json").read_text(encoding="utf-8"))
    text = {i: (ROOT / f"data/synthetic/raw/{i}.txt").read_text(encoding="utf-8") for i in ids}
    rules = {i: load(a.rules_pred, i) for i in ids}
    print("| field | reference | split | current | with rule |\n|---|---|---|---|---|")
    for gname in ("gold", "gold_reviewed_v1"):
        gold = {i: load(ROOT / "data/synthetic" / gname, i) for i in ids}
        for field in ("interventions", "problems"):
            for sname, s in (("dev", dev), ("TEST", test)):
                base, new = [], []
                for i in s:
                    if field == "problems":
                        g = set(normalize_problems(gold[i].get("coding", {}).get("problems_normalized", [])))
                        p = set(normalize_problems(rules[i].get("coding", {}).get("problems_normalized", [])))
                        q = drop_generic_lesion(p, text[i])
                    else:
                        g = set(normalize_interventions(gold[i]["clinical"].get("interventions")))
                        p = set(normalize_interventions(rules[i]["clinical"].get("interventions")))
                        q = suppress_interventions(p, text[i])
                    base.append((g, p)); new.append((g, q))
                print(f"| {field} | {gname} | {sname} | {micro_f1(base):.3f} | {micro_f1(new):.3f} |")


if __name__ == "__main__":
    main()
