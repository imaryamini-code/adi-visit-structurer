"""Cross-validated learned baseline for the multi-label fields (interventions, problems).

Per label: TF-IDF word 1-2-grams of the cleaned note (digits removed) + logistic regression (C=10), threshold 0.5.
Labels with fewer than 2 positive training examples are never predicted. Configuration fixed in advance.
Every note is predicted by a model that never saw it (5-fold x 10 repeats). Rules scores come from stored predictions.

python3 -m tools.multilabel_cv --rules-pred experiments/full_01/rules/predictions
"""
from __future__ import annotations

import argparse
import json
import random
import re
import warnings
from pathlib import Path
from typing import Dict, List, Set

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RepeatedKFold

from src.normalize import normalize_interventions, normalize_problems
from tools.reason_variants import clean_note

warnings.filterwarnings("ignore")
ROOT = Path(__file__).resolve().parents[1]
REPEATS, FOLDS, SEED, BOOT = 10, 5, 20261116, 3000
FIELDS = {
    "interventions": lambda r: set(normalize_interventions(r["clinical"].get("interventions"))),
    "problems": lambda r: set(normalize_problems(r.get("coding", {}).get("problems_normalized", []))),
}


def prep(t: str) -> str:
    return re.sub(r"\d+", " ", clean_note(t).lower())


def counts(g: Set[str], p: Set[str]):
    return len(g & p), len(p - g), len(g - p)


def micro(tp, fp, fn):
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    return 2 * pr * rc / (pr + rc) if pr + rc else 0.0


def cv_counts(X: List[str], gold: List[Set[str]]) -> np.ndarray:
    """Per-note mean (tp, fp, fn) over repeats of out-of-fold predictions."""
    labels = sorted({l for g in gold for l in g})
    Y = np.array([[l in g for l in labels] for g in gold], dtype=int)
    acc = np.zeros((len(X), 3))
    n = np.zeros(len(X))
    Xa = np.array(X, dtype=object)
    for tr, te in RepeatedKFold(n_splits=FOLDS, n_repeats=REPEATS, random_state=SEED).split(Xa):
        vec = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True)
        A = vec.fit_transform(list(Xa[tr]))
        B = vec.transform(list(Xa[te]))
        pred = np.zeros((len(te), len(labels)), dtype=int)
        for j in range(len(labels)):
            y = Y[tr, j]
            if y.sum() < 2:
                continue
            if y.sum() == len(y):
                pred[:, j] = 1
                continue
            clf = LogisticRegression(C=10.0, max_iter=2000).fit(A, y)
            pred[:, j] = (clf.predict_proba(B)[:, 1] >= 0.5).astype(int)
        for row, i in enumerate(te):
            tp = int(((pred[row] == 1) & (Y[i] == 1)).sum())
            fp = int(((pred[row] == 1) & (Y[i] == 0)).sum())
            fn = int(((pred[row] == 0) & (Y[i] == 1)).sum())
            acc[i] += (tp, fp, fn)
            n[i] += 1
    return acc / n[:, None]


def boot(a: np.ndarray, b: np.ndarray | None = None):
    rng = random.Random(SEED)
    N = len(a)
    vals = []
    for _ in range(BOOT):
        idx = [rng.randrange(N) for _ in range(N)]
        fa = micro(*a[idx].sum(0))
        vals.append(fa - (micro(*b[idx].sum(0)) if b is not None else 0.0))
    vals.sort()
    return vals[int(0.025 * BOOT)], vals[int(0.975 * BOOT)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--rules-pred", type=Path, required=True)
    a = ap.parse_args()
    ids = sorted(p.stem for p in (ROOT / "data/synthetic/gold").glob("ADI-*.json"))
    X = [prep((ROOT / f"data/synthetic/raw/{i}.txt").read_text(encoding="utf-8")) for i in ids]
    rules = {i: json.loads((a.rules_pred / f"{i}.json").read_text(encoding="utf-8")) for i in ids}
    print("| field | reference | rules F1 | learned (CV) F1 [95% CI] | difference [95% CI] |")
    print("|---|---|---|---|---|")
    for gold_name in ("gold", "gold_reviewed_v1"):
        gold = {i: json.loads((ROOT / f"data/synthetic/{gold_name}/{i}.json").read_text(encoding="utf-8")) for i in ids}
        for field, fn in FIELDS.items():
            G = [fn(gold[i]) for i in ids]
            R = np.array([counts(g, fn(rules[i])) for g, i in zip(G, ids)], dtype=float)
            C = cv_counts(X, G)
            lo, hi = boot(C)
            dlo, dhi = boot(C, R)
            print(f"| {field} | {gold_name} | {micro(*R.sum(0)):.3f} | {micro(*C.sum(0)):.3f} [{lo:.3f}, {hi:.3f}] | "
                  f"{micro(*C.sum(0)) - micro(*R.sum(0)):+.3f} [{dlo:+.3f}, {dhi:+.3f}] |")


if __name__ == "__main__":
    main()
