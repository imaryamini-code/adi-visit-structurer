"""Confidence intervals and paired tests for a finished run (no model needed).

    python3 -m tools.stats --run experiments/full_01 [--gold-dir data/synthetic/gold]

* 95% bootstrap CIs (resampling NOTES; the same resamples are used for every condition, so they are paired).
* Paired comparison of two conditions: for accuracy-type metrics the counts of notes only A / only B got right
  plus an exact McNemar p-value; for micro-F1 the paired-bootstrap CI of the difference.
* Follow-up phrases are normalised with the project's rules parser, like tools/rescore.py.
Many comparisons are listed: p-values are NOT corrected for multiple testing, so read them as descriptive,
except for the one comparison you decide in advance is the primary one.
Writes <run>/stats.md.
"""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

from src.evaluate import VITALS, follow_up_key
from src.normalize import normalize_interventions, normalize_problems, normalize_reason
from src.run_pipeline import canonical_follow_up

ACC = ("reason", "follow_up", "vitals")
LAB = ("interventions", "problems")


def per_note(gold_dir: Path, pred_dir: Path) -> Dict[str, list]:
    """Per-note correctness (bools) and label counts (tp, fp, fn), in sorted note order."""
    out: Dict[str, list] = {k: [] for k in ACC + LAB}
    for gf in sorted(Path(gold_dir).glob("ADI-*.json")):
        g = json.loads(gf.read_text(encoding="utf-8"))
        p = json.loads((Path(pred_dir) / gf.name).read_text(encoding="utf-8"))
        gc, pc = g["clinical"], p["clinical"]
        out["reason"].append(normalize_reason(gc.get("reason_for_visit")) == normalize_reason(pc.get("reason_for_visit")))
        out["follow_up"].append(follow_up_key(gc.get("follow_up")) ==
                                follow_up_key(canonical_follow_up(pc.get("follow_up"))))
        gv, pv = gc.get("vitals") or {}, pc.get("vitals") or {}
        out["vitals"].append(all(gv.get(k) == pv.get(k) for k in VITALS))
        for name, gs, ps in (
            ("interventions", set(normalize_interventions(gc.get("interventions"))),
             set(normalize_interventions(pc.get("interventions")))),
            ("problems", set(normalize_problems(g.get("coding", {}).get("problems_normalized", []))),
             set(normalize_problems(p.get("coding", {}).get("problems_normalized", [])))),
        ):
            out[name].append((len(gs & ps), len(ps - gs), len(gs - ps)))
    return out


def f1(counts: Sequence[Tuple[int, int, int]], idx: Sequence[int]) -> float:
    tp = sum(counts[i][0] for i in idx)
    fp = sum(counts[i][1] for i in idx)
    fn = sum(counts[i][2] for i in idx)
    pr = tp / (tp + fp) if tp + fp else 0.0
    rc = tp / (tp + fn) if tp + fn else 0.0
    return 2 * pr * rc / (pr + rc) if pr + rc else 0.0


def metric(data: Dict[str, list], name: str, idx: Sequence[int]) -> float:
    if name in ACC:
        return sum(data[name][i] for i in idx) / len(idx)
    return f1(data[name], idx)


def mcnemar_exact(only_a: int, only_b: int) -> float:
    n = only_a + only_b
    if n == 0:
        return 1.0
    k = min(only_a, only_b)
    return min(1.0, 2 * sum(math.comb(n, i) for i in range(k + 1)) * 0.5 ** n)


def percentile(vals: List[float], q: float) -> float:
    s = sorted(vals)
    return s[min(len(s) - 1, max(0, int(round(q * (len(s) - 1)))))]


def analyse(conds: Dict[str, Dict[str, list]], pairs: Sequence[Tuple[str, str]], boot: int = 5000, seed: int = 20261116) -> str:
    n = len(next(iter(conds.values()))["reason"])
    rng = random.Random(seed)
    draws = [[rng.randrange(n) for _ in range(n)] for _ in range(boot)]
    metrics = ACC + LAB
    full = list(range(n))
    lines = [f"Bootstrap: {boot} resamples of {n} notes, seed {seed}. 95% percentile intervals.", "",
             "## Each condition (point estimate [95% CI])", "",
             "| condition | reason | follow-up | vitals | interventions F1 | problems F1 |", "|---|---|---|---|---|---|"]
    for c, d in conds.items():
        cells = []
        for m in metrics:
            vals = [metric(d, m, ix) for ix in draws]
            cells.append(f"{metric(d, m, full):.3f} [{percentile(vals, .025):.2f}, {percentile(vals, .975):.2f}]")
        lines.append(f"| {c} | " + " | ".join(cells) + " |")
    lines += ["", "## Paired comparisons (B minus A)", "",
              "Accuracy metrics: notes only A right / only B right and exact McNemar p. F1: difference and its paired 95% CI.",
              "p-values are uncorrected for multiple comparisons: descriptive, not confirmatory.", "",
              "| A | B | metric | A | B | difference | only A right / only B right | p (McNemar) or 95% CI of diff |",
              "|---|---|---|---|---|---|---|---|"]
    for a, b in pairs:
        for m in metrics:
            ma, mb = metric(conds[a], m, full), metric(conds[b], m, full)
            if m in ACC:
                oa = sum(x and not y for x, y in zip(conds[a][m], conds[b][m]))
                ob = sum(y and not x for x, y in zip(conds[a][m], conds[b][m]))
                lines.append(f"| {a} | {b} | {m} | {ma:.3f} | {mb:.3f} | {mb - ma:+.3f} | {oa} / {ob} | p = {mcnemar_exact(oa, ob):.4f} |")
            else:
                diffs = [metric(conds[b], m, ix) - metric(conds[a], m, ix) for ix in draws]
                lines.append(f"| {a} | {b} | {m} F1 | {ma:.3f} | {mb:.3f} | {mb - ma:+.3f} | - | [{percentile(diffs, .025):+.3f}, {percentile(diffs, .975):+.3f}] |")
    return "\n".join(lines)


def default_pairs(names: Sequence[str]) -> List[Tuple[str, str]]:
    pairs = [("rules", n) for n in names if n != "rules" and "+" not in n]
    for n in names:
        if "+" in n:
            base = n.replace("+wiki", "").replace("+raw", "")
            if base in names:
                pairs.append((base, n))
    return pairs


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, required=True)
    ap.add_argument("--gold-dir", type=Path, default=Path("data/synthetic/gold"))
    ap.add_argument("--boot", type=int, default=5000)
    a = ap.parse_args()
    names = sorted((p.name for p in a.run.iterdir() if (p / "predictions").is_dir()), key=lambda c: (c != "rules", c))
    conds = {c: per_note(a.gold_dir, a.run / c / "predictions") for c in names}
    report = f"# Statistics for {a.run} (gold: {a.gold_dir})\n\n" + analyse(conds, default_pairs(names), a.boot)
    (a.run / "stats.md").write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
