import json
import sys
from pathlib import Path

import src.llm_extract as le
import tools.compare_models as cm

REPO = Path(__file__).resolve().parents[1]


def test_reuse_cache_starts_a_fresh_run_and_refuses_an_existing_one(tmp_path, monkeypatch):
    for d in ("data", "src", "tools"):  # the run manifest hashes these files relative to cwd
        (tmp_path / d).symlink_to(REPO / d)
    old = tmp_path / "old_cache" / "mistral"
    old.mkdir(parents=True)
    (old / "marker.json").write_text("{}", encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(le, "_call_ollama", lambda *a, **k: json.dumps(
        {"clinical": {"reason_for_visit": "x", "vitals": {}, "interventions": [],
                      "follow_up": {"type": None, "timing_days": None}, "critical_issues": []},
         "coding": {"problems_normalized": []}}))
    monkeypatch.setattr(cm, "ollama_info", lambda m: {"fake": True})
    argv = ["x", "--run-id", "r1", "--models", "mistral", "--modes", "hybrid", "--limit", "2",
            "--reuse-cache", str(tmp_path / "old_cache")]
    monkeypatch.setattr(sys, "argv", argv)
    cm.main()  # used to crash with FileExistsError before the fix
    assert (tmp_path / "experiments" / "r1" / "llm_cache" / "mistral" / "marker.json").exists()
    monkeypatch.setattr(sys, "argv", argv)
    try:
        cm.main()
        raised = False
    except FileExistsError:
        raised = True
    assert raised  # an existing run is never overwritten
