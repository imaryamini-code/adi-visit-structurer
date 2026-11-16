from pathlib import Path

from src.evaluate import evaluate
from tools.stats import analyse, mcnemar_exact, metric, per_note

GOLD, PRED = Path("data/synthetic/gold"), Path("data/synthetic/pred")


def test_per_note_numbers_equal_the_official_evaluator():
    d = per_note(GOLD, PRED)
    e = evaluate(GOLD, PRED)
    full = list(range(len(d["reason"])))
    assert abs(metric(d, "reason", full) - e["reason_accuracy"]) < 1e-12
    assert abs(metric(d, "vitals", full) - e["vitals_exact_record_accuracy"]) < 1e-12
    assert abs(metric(d, "interventions", full) - e["interventions"]["micro_f1"]) < 1e-12
    assert abs(metric(d, "problems", full) - e["problems"]["micro_f1"]) < 1e-12


def test_mcnemar_exact_known_values():
    assert mcnemar_exact(0, 0) == 1.0
    assert abs(mcnemar_exact(18, 0) - 2 * 0.5 ** 18) < 1e-15
    assert mcnemar_exact(5, 5) == 1.0


def test_analysis_is_deterministic_and_handles_identical_conditions():
    d = per_note(GOLD, PRED)
    r1 = analyse({"a": d, "b": d}, [("a", "b")], boot=200)
    assert r1 == analyse({"a": d, "b": d}, [("a", "b")], boot=200)
    assert "+0.000" in r1 and "p = 1.0000" in r1
