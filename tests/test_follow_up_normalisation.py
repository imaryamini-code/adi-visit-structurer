import json

import src.run_pipeline as rp
from tools.rescore import normalised_copy


def test_phrases_become_structured_and_unknown_stay_none():
    assert rp.canonical_follow_up("nuovo controllo domiciliare entro tre giorni") == {"type": "controllo", "timing_days": 3}
    assert rp.canonical_follow_up("controllo domiciliare per la settimana prossima")["timing_days"] == 7
    assert rp.canonical_follow_up("prossima visita programmata") is None
    assert rp.canonical_follow_up("   ") is None and rp.canonical_follow_up(None) is None


def test_structured_values_pass_through_untouched():
    d = {"type": "controllo_ferita", "timing_days": 2}
    assert rp.canonical_follow_up(d) is d


def test_llm_mode_now_stores_structured_follow_up(monkeypatch):
    out = {"clinical": {"reason_for_visit": "x", "vitals": {}, "interventions": [],
                        "follow_up": "controllo entro 3 giorni", "critical_issues": []},
           "coding": {"problems_normalized": []}}
    monkeypatch.setattr(rp, "llm_extract", lambda **k: (out, "{}"))
    monkeypatch.setattr(rp, "LLM_CACHE_DIR", None)
    rec = rp.process_note("Nota di prova.", "ADI-0001", "llm", "m", require_llm=True)
    assert rec["clinical"]["follow_up"] == {"type": "controllo", "timing_days": 3}


def test_rescore_does_not_modify_the_original_predictions(tmp_path):
    f = tmp_path / "ADI-0001.json"
    rec = {"meta": {"record_id": "ADI-0001"}, "clinical": {"follow_up": "controllo entro 3 giorni"}}
    f.write_text(json.dumps(rec), encoding="utf-8")
    out = normalised_copy(tmp_path)
    assert json.loads(f.read_text(encoding="utf-8"))["clinical"]["follow_up"] == "controllo entro 3 giorni"
    assert json.loads((out / "ADI-0001.json").read_text(encoding="utf-8"))["clinical"]["follow_up"]["timing_days"] == 3
