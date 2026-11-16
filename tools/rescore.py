"""Re-score a finished run with the LLM follow-up phrases normalised by the project's rules parser.

    python3 -m tools.rescore --run experiments/full_01

The original scorer parses free-text follow-up phrases with a narrow pattern, which understates
LLM-only conditions. Here every stored prediction's follow-up is first passed through
canonical_follow_up() (the same parser the router uses), then scored with the unchanged evaluator.
No model is called. Writes <run>/rescore.md.
"""
from __future__ import annotations

import argparse
import copy
import json
import shutil
import tempfile
from pathlib import Path

from src.evaluate import evaluate
from src.run_pipeline import canonical_follow_up

GOLDS = {"original": Path("data/synthetic/gold"), "reviewed_v1 (exploratory)": Path("data/synthetic/gold_reviewed_v1")}


def normalised_copy(pred_dir: Path) -> Path:
    out = Path(tempfile.mkdtemp())
    for f in sorted(pred_dir.glob("ADI-*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        rec = copy.deepcopy(rec)
        rec["clinical"]["follow_up"] = canonical_follow_up(rec["clinical"].get("follow_up"))
        (out / f.name).write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
    return out


def rescore(run: Path) -> str:
    conds = sorted(p.name for p in Path(run).iterdir() if (p / "predictions").is_dir())
    conds.sort(key=lambda c: (c != "rules", c))
    lines = [f"# Re-score of {run} with normalised follow-up", "",
             "Follow-up is scored twice: as stored (scorer's own string parser) and after the phrase is "
             "parsed by the project's rules parser (same for every condition). Other metrics are unchanged.", ""]
    for gname, gdir in GOLDS.items():
        if not gdir.is_dir():
            continue
        lines += [f"## Scored against {gname}", "",
                  "| condition | reason | follow-up as stored | follow-up normalised | vitals | int F1 | prob F1 |",
                  "|---|---|---|---|---|---|---|"]
        for c in conds:
            pdir = Path(run) / c / "predictions"
            a = evaluate(gdir, pdir)
            tmp = normalised_copy(pdir)
            try:
                b = evaluate(gdir, tmp)
            finally:
                shutil.rmtree(tmp, ignore_errors=True)
            lines.append(f"| {c} | {a['reason_accuracy']:.3f} | {a['follow_up_type_timing_accuracy']:.3f} | "
                         f"{b['follow_up_type_timing_accuracy']:.3f} | {a['vitals_exact_record_accuracy']:.3f} | "
                         f"{a['interventions']['micro_f1']:.3f} | {a['problems']['micro_f1']:.3f} |")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, required=True)
    a = ap.parse_args()
    report = rescore(a.run)
    (a.run / "rescore.md").write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
