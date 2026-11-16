"""Cross-validated learned baseline for the reason-for-visit field (no held-out set needed).

Every note is predicted by a model that never saw it. Configuration fixed in advance (not tuned on the data):
TF-IDF over word 1-2-grams of the cleaned note (digits removed), multinomial logistic regression, C=10.
C is also shown at 1 and 100 as a sensitivity check, NOT used to pick a winner.

python3 -m tools.reason_cv
"""
from __future__ import annotations

import random
import re
from typing import Dict, List

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import RepeatedKFold
from sklearn.pipeline import make_pipeline

from src.extract_rules import extract_reason
from src.normalize import normalize_reason
from tools.reason_variants import clean_note, load, v3

REPEATS, FOLDS, SEED, BOOT = 10, 5, 20261116, 5000


def prep(text: str) -> str:
    return re.sub(r"\d+", " ", clean_note(text).lower())


def oof_correct(ids: List[str], X: List[str], y: List[str], C: float) -> np.ndarray:
    """Per-note fraction of repeats in which the out-of-fold prediction was correct."""
    correct = np.zeros(len(ids))
    cnt = np.zeros(len(ids))
    rkf = RepeatedKFold(n_splits=FOLDS, n_repeats=REPEATS, random_state=SEED)
    X_arr, y_arr = np.array(X, dtype=object), np.array(y, dtype=object)
    for tr, te in rkf.split(X_arr):
        pipe = make_pipeline(TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=1),
                             LogisticRegression(C=C, max_iter=2000))
        pipe.fit(list(X_arr[tr]), list(y_arr[tr]))
        pred = pipe.predict(list(X_arr[te]))
        correct[te] += (pred == y_arr[te])
        cnt[te] += 1
    return correct / cnt


def boot_ci(a: np.ndarray, b: np.ndarray | None = None):
    rng = random.Random(SEED)
    n = len(a)
    vals = []
    for _ in range(BOOT):
        idx = [rng.randrange(n) for _ in range(n)]
        vals.append(float(np.mean([a[i] - (b[i] if b is not None else 0) for i in idx])))
    vals.sort()
    return vals[int(0.025 * BOOT)], vals[int(0.975 * BOOT)]


def main():
    gold, text = load()
    ids = sorted(gold)
    X = [prep(text[i]) for i in ids]
    y = [gold[i] for i in ids]
    rules0 = np.array([float(normalize_reason(extract_reason(text[i])) == gold[i]) for i in ids])
    rules3 = np.array([float(normalize_reason(v3(text[i])) == gold[i]) for i in ids])
    print(f"n={len(ids)} notes, {FOLDS}-fold x {REPEATS} repeats\n")
    print("| method | accuracy | 95% CI |")
    print("|---|---|---|")
    lo, hi = boot_ci(rules0)
    print(f"| rules, current (no fitting) | {rules0.mean():.3f} | [{rules0.mean() - (rules0.mean() - lo):.3f}, {hi:.3f}] |")
    res: Dict[float, np.ndarray] = {}
    for C in (10.0, 1.0, 100.0):
        res[C] = oof_correct(ids, X, y, C)
        lo, hi = boot_ci(res[C])
        tag = " (pre-declared)" if C == 10.0 else " (sensitivity)"
        print(f"| learned classifier, C={C:g}{tag} | {res[C].mean():.3f} | [{lo:.3f}, {hi:.3f}] |")
    print(f"| rules v3 (designed after seeing all notes; in-sample, optimistic) | {rules3.mean():.3f} | - |")
    d = res[10.0] - rules0
    lo, hi = boot_ci(res[10.0], rules0)
    print(f"\nPre-declared classifier minus current rules: {d.mean():+.3f}, 95% CI [{lo:+.3f}, {hi:+.3f}] (paired bootstrap over notes)")
    # per-class view
    from collections import Counter
    cls = Counter(y)
    print("\nPer gold class: n | rules accuracy | classifier accuracy (C=10)")
    for k, n in cls.most_common():
        m = np.array([g == k for g in y])
        print(f"  {k}: {n} | {rules0[m].mean():.2f} | {res[10.0][m].mean():.2f}")


if __name__ == "__main__":
    main()
