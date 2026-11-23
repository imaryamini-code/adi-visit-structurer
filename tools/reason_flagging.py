"""Flag uncertain reasons for review: do rules/classifier/LLM disagreements point at the wrong reasons?

    python3 -m tools.reason_flagging --run experiments/full_01

The rules' reason is wrong on about a quarter of the notes and routing alone flags only a few of them.
This tool asks whether a review flag raised when two independent readers disagree catches more.
Nothing is tuned: every signal below is declared in advance and all are reported, so there is no
winner picked from the data. Needs no model call: LLM answers are read from the run's saved predictions.

Signals (flag a note when ...):
  classifier  the rules' reason differs from a TF-IDF + logistic regression (C=10) prediction made
              by a model that never saw that note (5-fold, fixed seed)
  confident   the same, but only when the classifier's own probability is at least GATE (0.3), which
              cuts the review load; GATE was picked on the DEV notes and scored once on TEST
  llm         the rules' reason differs from the LLM-only reason of the model (needs --llm-runs)
  routing     the adaptive pipeline already flagged the reason (needs --adaptive-runs)
Reported: notes flagged, wrong reasons caught, precision, and the accuracy of the notes that are NOT
flagged (what is left if a person checks every flagged note), overall and on the DEV (odd) and
TEST (even) halves. Stability over 10 different fold splits is shown for the classifier signal.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import KFold
from sklearn.pipeline import make_pipeline

from src.normalize import normalize_reason
from tools.reason_cv import prep
from tools.reason_variants import load

SEED, C = 20261116, 10.0
GATE = 0.3  # chosen on the DEV (odd) notes only, from {0, .2, .3, .4, .5, .6, .7}; TEST scored once


def predictions(run: Path, cond: str, ids: List[str]) -> Dict[str, str]:
    out = {}
    for i in ids:
        rec = json.loads((run / cond / "predictions" / f"{i}.json").read_text(encoding="utf-8"))
        out[i] = normalize_reason(rec["clinical"].get("reason_for_visit"))
    return out


def routing_flags(run: Path, cond: str, ids: List[str]) -> np.ndarray:
    return np.array([json.loads((run / cond / "predictions" / f"{i}.json").read_text(encoding="utf-8"))
                     ["routing"]["fields"]["reason_for_visit"]["status"] == "flagged" for i in ids])


def classifier_oof(X, y, ids, seed: int, with_confidence: bool = False):
    out, conf = {}, {}
    for tr, te in KFold(5, shuffle=True, random_state=seed).split(X):
        m = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True),
                          LogisticRegression(C=C, max_iter=2000))
        m.fit(list(X[tr]), list(y[tr]))
        proba, classes = m.predict_proba(list(X[te])), list(m.classes_)
        for k, j in enumerate(te):
            out[ids[j]], conf[ids[j]] = classes[int(proba[k].argmax())], float(proba[k].max())
    return (out, conf) if with_confidence else out


def row(name: str, flag: np.ndarray, wrong: np.ndarray, odd: np.ndarray) -> str:
    n, c = int(flag.sum()), int((flag & wrong).sum())
    left, left_wrong = int((~flag).sum()), int((~flag & wrong).sum())
    d = f"{int((flag & wrong & odd).sum())}/{int((wrong & odd).sum())}"
    t = f"{int((flag & wrong & ~odd).sum())}/{int((wrong & ~odd).sum())}"
    return (f"| {name} | {n} | {c}/{int(wrong.sum())} | {c / n:.2f} | {1 - left_wrong / left:.3f} | {d} | {t} |"
            if n else f"| {name} | 0 | 0/{int(wrong.sum())} | - | {1 - left_wrong / left:.3f} | {d} | {t} |")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--rules", default="rules", help="condition folder with the rules' predictions")
    ap.add_argument("--llm-runs", nargs="*", default=[], metavar="RUN:COND",
                    help="e.g. experiments/wiki_02_llm:llm_mistral (LLM-only predictions)")
    ap.add_argument("--adaptive-runs", nargs="*", default=[], metavar="COND",
                    help="adaptive condition folders in --run, e.g. adaptive_mistral")
    a = ap.parse_args()
    gold, text = load()
    ids = sorted(gold)
    rules = predictions(a.run, a.rules, ids)
    wrong = np.array([rules[i] != gold[i] for i in ids])
    odd = np.array([int(re.findall(r"\d+", i)[0]) % 2 == 1 for i in ids])
    X = np.array([prep(text[i]) for i in ids], dtype=object)
    y = np.array([gold[i] for i in ids], dtype=object)
    clf, conf = classifier_oof(X, y, ids, SEED, with_confidence=True)
    sig = {"classifier disagrees with rules": np.array([rules[i] != clf[i] for i in ids]),
           f"classifier disagrees and is confident (p >= {GATE})":
               np.array([rules[i] != clf[i] and conf[i] >= GATE for i in ids])}
    for spec in a.llm_runs:
        r, cond = spec.split(":")
        p = predictions(Path(r), cond, ids)
        sig[f"{cond} disagrees with rules"] = np.array([rules[i] != p[i] for i in ids])
    cur = {c: routing_flags(a.run, c, ids) for c in a.adaptive_runs}
    print(f"# Review flags for the reason field, {a.run}\n")
    print(f"Rules wrong on {int(wrong.sum())} of {len(ids)} notes (DEV {int((wrong & odd).sum())}, TEST {int((wrong & ~odd).sum())}). "
          f"If every note were flagged, precision would be {wrong.mean():.2f}.\n")
    print("| flag | notes flagged | wrong caught | precision | accuracy of unflagged notes | DEV caught | TEST caught |")
    print("|---|---|---|---|---|---|---|")
    print(row("none (rules as they are)", np.zeros(len(ids), bool), wrong, odd))
    for c, f in cur.items():
        print(row(f"{c}: routing flags today", f, wrong, odd))
    for k, f in sig.items():
        print(row(k, f, wrong, odd))
    for c, f in cur.items():
        print(row(f"{c} routing + classifier", f | sig["classifier disagrees with rules"], wrong, odd))
        print(row(f"{c} routing + confident classifier", f | sig[f"classifier disagrees and is confident (p >= {GATE})"], wrong, odd))
    reps = []
    for r in range(10):
        p, cf = classifier_oof(X, y, ids, 1000 + r, with_confidence=True)
        f = np.array([rules[i] != p[i] for i in ids])
        g = np.array([rules[i] != p[i] and cf[i] >= GATE for i in ids])
        reps.append((int(f.sum()), int((f & wrong).sum()), int(g.sum()), int((g & wrong).sum())))
    reps = np.array(reps)
    print(f"\nStability over 10 fold splits: classifier signal flagged {reps[:, 0].min()}-{reps[:, 0].max()}, "
          f"wrong caught {reps[:, 1].min()}-{reps[:, 1].max()} of {int(wrong.sum())}; "
          f"confident signal flagged {reps[:, 2].min()}-{reps[:, 2].max()}, caught {reps[:, 3].min()}-{reps[:, 3].max()}.")


if __name__ == "__main__":
    main()
