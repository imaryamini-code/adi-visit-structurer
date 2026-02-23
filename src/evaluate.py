# src/evaluate.py
from __future__ import annotations

from pathlib import Path
import json
from typing import Any


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def get_path(d: dict[str, Any], path: str) -> Any:
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def normalize_text(x: Any) -> Any:
    if x is None:
        return None
    if isinstance(x, str):
        return " ".join(x.strip().lower().split())
    return x


def f1_for_lists(gold_list: list[str], pred_list: list[str]) -> dict[str, float]:
    gold_set = set(gold_list or [])
    pred_set = set(pred_list or [])

    # If both are empty, it's a perfect match
    if not gold_set and not pred_set:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}

    tp = len(gold_set & pred_set)
    fp = len(pred_set - gold_set)
    fn = len(gold_set - pred_set)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return {"precision": precision, "recall": recall, "f1": f1}


def exact_match_vitals(g: dict[str, Any], p: dict[str, Any]) -> bool:
    keys = ["blood_pressure_systolic", "blood_pressure_diastolic", "heart_rate", "temperature", "spo2"]
    gv = g.get("clinical", {}).get("vitals", {}) or {}
    pv = p.get("clinical", {}).get("vitals", {}) or {}
    return all(gv.get(k) == pv.get(k) for k in keys)


def main():
    gold_dir = Path("data/synthetic/gold")
    pred_dir = Path("reports/examples")
    out_path = Path("reports/metrics.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fields_text = [
        "clinical.reason_for_visit",
        "clinical.follow_up",
    ]
    fields_list = [
        "clinical.interventions",
        "coding.problems_normalized",
    ]

    per_record = {}
    totals = {
        "n_records": 0,
        "text_field_accuracy": {f: {"correct": 0, "total": 0} for f in fields_text},
        "vitals_exact_match": {"correct": 0, "total": 0},
        "list_f1_sum": {f: {"precision": 0.0, "recall": 0.0, "f1": 0.0, "total": 0} for f in fields_list},
    }

    for gold_path in sorted(gold_dir.glob("*.json")):
        record_id = gold_path.stem
        pred_path = pred_dir / f"{record_id}.json"
        if not pred_path.exists():
            continue

        g = load_json(gold_path)
        p = load_json(pred_path)

        rec = {"text_fields": {}, "lists": {}, "vitals_exact_match": None}
        totals["n_records"] += 1

        # Text fields: exact match after normalization
        for f in fields_text:
            gv = normalize_text(get_path(g, f))
            pv = normalize_text(get_path(p, f))
            ok = (gv == pv)
            rec["text_fields"][f] = {"gold": gv, "pred": pv, "correct": ok}

            totals["text_field_accuracy"][f]["total"] += 1
            if ok:
                totals["text_field_accuracy"][f]["correct"] += 1

        # Vitals exact match
        vem = exact_match_vitals(g, p)
        rec["vitals_exact_match"] = vem
        totals["vitals_exact_match"]["total"] += 1
        if vem:
            totals["vitals_exact_match"]["correct"] += 1

        # List F1
        for f in fields_list:
            gl = get_path(g, f) or []
            pl = get_path(p, f) or []
            scores = f1_for_lists(gl, pl)
            rec["lists"][f] = {"gold": gl, "pred": pl, **scores}

            totals["list_f1_sum"][f]["total"] += 1
            totals["list_f1_sum"][f]["precision"] += scores["precision"]
            totals["list_f1_sum"][f]["recall"] += scores["recall"]
            totals["list_f1_sum"][f]["f1"] += scores["f1"]

        per_record[record_id] = rec

    # Aggregate
    summary = {"n_records": totals["n_records"]}

    summary["text_field_accuracy"] = {}
    for f, v in totals["text_field_accuracy"].items():
        total = v["total"]
        correct = v["correct"]
        summary["text_field_accuracy"][f] = (correct / total) if total else 0.0

    vtot = totals["vitals_exact_match"]["total"]
    vcor = totals["vitals_exact_match"]["correct"]
    summary["vitals_exact_match_rate"] = (vcor / vtot) if vtot else 0.0

    summary["list_f1_macro"] = {}
    for f, v in totals["list_f1_sum"].items():
        n = v["total"]
        summary["list_f1_macro"][f] = {
            "precision": (v["precision"] / n) if n else 0.0,
            "recall": (v["recall"] / n) if n else 0.0,
            "f1": (v["f1"] / n) if n else 0.0,
        }

    metrics = {"summary": summary, "per_record": per_record}
    out_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
