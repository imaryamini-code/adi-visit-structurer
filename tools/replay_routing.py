"""Replay adaptive-routing variants from a finished run's saved LLM answers (no Ollama needed).

    python3 -m tools.replay_routing --run experiments/full_01 --models mistral llama3.1:8b

Every variant re-runs rules + routing on the raw notes and takes LLM answers ONLY from
<run>/llm_cache. A note whose answer is not in the cache raises an error: the replay can
never call the model or silently fall back. Scores are given against the original gold and,
if present, gold_reviewed_v1 (the latter is exploratory; see docs/ANNOTATION_AUDIT.md).
Writes <run>/replay.md next to the run's manifest.
"""
from __future__ import annotations

import argparse
import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Optional

import src.run_pipeline as pipeline
from src.evaluate import evaluate
from src.routing import RoutingConfig

RAW = Path("data/synthetic/raw")
GOLDS = {"original": Path("data/synthetic/gold"), "reviewed_v1": Path("data/synthetic/gold_reviewed_v1")}

_VITALS_ONLY = dict(escalate_missing_reason=False, escalate_generic_reason=False,
                    escalate_missing_follow_up=False, escalate_fallback_interventions=False,
                    escalate_empty_problems=False)

VARIANTS: Dict[str, RoutingConfig] = {
    "default (flag generic reason)": RoutingConfig(),
    "prefer_llm for generic reason": RoutingConfig(generic_reason_policy="prefer_llm"),
    "no escalation for empty problems": RoutingConfig(escalate_empty_problems=False),
    "no grounding check": RoutingConfig(require_grounding=False),
    "vitals only (all else rules)": RoutingConfig(**_VITALS_ONLY),
}


def cache_only_llm(model: str):
    """LLM function that reads the run's cache and fails loudly on a miss."""
    def fn(text: str):
        path = pipeline._cache_path(text, model)
        if path is None or not path.exists():
            raise RuntimeError(f"not in cache (replay never calls the model): {path}")
        return pipeline.coerce_llm_output(json.loads(path.read_text(encoding="utf-8"))["parsed"])
    return fn


def replay_variant(model: str, cfg: RoutingConfig, out_dir: Path, raw_files) -> Dict[str, int]:
    llm_fn = cache_only_llm(model)
    called = flagged = 0
    for p in raw_files:
        text = pipeline.PREPROCESS(p.read_text(encoding="utf-8"))
        rec = pipeline.build_base_record(p.stem, "adaptive", model)
        pipeline.apply_adaptive(text, rec, model, require_llm=True, cfg=cfg, llm_fn=llm_fn)
        rec["quality"] = pipeline.quality_check(rec)
        called += rec["meta"]["llm_status"] == "called"
        flagged += bool((rec.get("routing") or {}).get("needs_review"))
        (out_dir / f"{p.stem}.json").write_text(json.dumps(rec, ensure_ascii=False), encoding="utf-8")
    return {"llm_called": called, "notes_flagged": flagged}


def replay(run: Path, models, variants: Optional[Dict[str, RoutingConfig]] = None,
           golds: Optional[Dict[str, Path]] = None, raw_dir: Path = RAW) -> str:
    variants = variants or VARIANTS
    golds = {k: v for k, v in (golds or GOLDS).items() if v.is_dir()}
    raw_files = sorted(raw_dir.glob("ADI-*.txt"))
    if not raw_files:
        raise SystemExit(f"no raw notes in {raw_dir}")
    pipeline.LLM_CACHE_DIR = Path(run) / "llm_cache"
    lines = [f"# Routing replay of {run}", "",
             "LLM answers come only from the run's saved cache; no model was called. "
             "Scores: reason / follow-up / vitals accuracy, micro-F1 interventions / problems.", ""]
    for model in models:
        for gname, gdir in golds.items():
            lines += [f"## {model}, scored against {gname}"
                      + (" (exploratory)" if gname != "original" else ""), "",
                      "| variant | reason | follow-up | vitals | int F1 | prob F1 | LLM-called notes | flagged notes |",
                      "|---|---|---|---|---|---|---|---|"]
            for name, cfg in variants.items():
                tmp = Path(tempfile.mkdtemp())
                try:
                    stats = replay_variant(model, cfg, tmp, raw_files)
                    m = evaluate(gdir, tmp)
                finally:
                    shutil.rmtree(tmp, ignore_errors=True)
                lines.append(f"| {name} | {m['reason_accuracy']:.3f} | {m['follow_up_type_timing_accuracy']:.3f} | "
                             f"{m['vitals_exact_record_accuracy']:.3f} | {m['interventions']['micro_f1']:.3f} | "
                             f"{m['problems']['micro_f1']:.3f} | {stats['llm_called']} | {stats['notes_flagged']} |")
            lines.append("")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--run", type=Path, required=True, help="finished run directory, e.g. experiments/full_01")
    ap.add_argument("--models", nargs="+", default=["mistral", "llama3.1:8b"])
    a = ap.parse_args()
    if not (a.run / "llm_cache").is_dir():
        ap.error(f"{a.run}/llm_cache not found (was the run made with the cache version?)")
    report = replay(a.run, a.models)
    (a.run / "replay.md").write_text(report + "\n", encoding="utf-8")
    print(report)
    print(f"\nWritten to {a.run / 'replay.md'}")


if __name__ == "__main__":
    main()
