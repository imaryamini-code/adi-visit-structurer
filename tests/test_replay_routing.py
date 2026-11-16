import json
from pathlib import Path

import pytest

import src.run_pipeline as rp
from src.routing import RoutingConfig
from tools.replay_routing import cache_only_llm, replay_variant


def _first_notes(n=3):
    return sorted(Path("data/synthetic/raw").glob("ADI-*.txt"))[:n]


def _fake_answer():
    return {"clinical": {"reason_for_visit": "controllo generale", "vitals": {}, "interventions": [],
                         "follow_up": {"type": None, "timing_days": None}, "critical_issues": []},
            "coding": {"problems_normalized": []}}


def test_cache_miss_fails_loudly_and_never_calls_model(tmp_path, monkeypatch):
    monkeypatch.setattr(rp, "LLM_CACHE_DIR", tmp_path)
    monkeypatch.setattr(rp, "llm_extract", lambda **k: pytest.fail("model must not be called"))
    with pytest.raises(RuntimeError, match="not in cache"):
        replay_variant("m", RoutingConfig(), tmp_path, _first_notes())


def test_replay_uses_cached_answers_and_writes_records(tmp_path, monkeypatch):
    cache = tmp_path / "cache"
    monkeypatch.setattr(rp, "LLM_CACHE_DIR", cache)
    monkeypatch.setattr(rp, "llm_extract", lambda **k: pytest.fail("model must not be called"))
    notes = _first_notes()
    for p in notes:  # pre-fill the cache exactly as a real run would
        path = rp._cache_path(rp.PREPROCESS(p.read_text(encoding="utf-8")), "m")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"parsed": _fake_answer(), "raw": "{}"}), encoding="utf-8")
    out = tmp_path / "out"
    out.mkdir()
    stats = replay_variant("m", RoutingConfig(), out, notes)
    assert len(list(out.glob("ADI-*.json"))) == len(notes)
    assert set(stats) == {"llm_called", "notes_flagged"} and stats["llm_called"] <= len(notes)
    assert cache_only_llm("m")  # callable factory
