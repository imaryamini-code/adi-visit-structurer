import json

import src.llm_extract as le
import src.run_pipeline as rp
from src.wiki_context import HEADER, KnowledgeLayer

NOTE_A = "Visita per controllo dopo caduta. Pressione arteriosa 130/80 mmHg, frequenza cardiaca 72 bpm."
NOTE_B = "Visita per medicazione ferita. Pressione arteriosa 120/70 mmHg, frequenza cardiaca 68 bpm."


def rec(rid, reason, vit):
    return {"meta": {"record_id": rid, "visit_datetime": "2026-02-15T10:00:00"},
            "clinical": {"reason_for_visit": reason, "vitals": vit, "interventions": [],
                         "follow_up": {"type": None, "timing_days": None}, "critical_issues": []},
            "coding": {"problems_normalized": []}}


V = lambda s, d, h: {"blood_pressure_systolic": s, "blood_pressure_diastolic": d, "heart_rate": h,
                     "temperature": None, "spo2": None}
REF = [(rec("ADI-0001", "controllo dopo caduta", V(130, 80, 72)), NOTE_A),
       (rec("ADI-0002", "medicazione ferita", V(120, 70, 68)), NOTE_B)]


def test_leave_one_out_never_shows_own_note():
    kl = KnowledgeLayer(REF, "wiki")
    ctx = kl.context(NOTE_A, exclude_id="ADI-0001")
    assert HEADER in ctx and "medicazione ferita" in ctx
    assert "130/80" not in ctx and "caduta" not in ctx.split("TEXT")[0].replace(HEADER, "")


def test_raw_kind_has_no_labels_and_excludes_self():
    ctx = KnowledgeLayer(REF, "raw").context(NOTE_A, "ADI-0001")
    assert "->" not in ctx and "120/70" in ctx and "130/80" not in ctx


def test_deterministic_and_empty_when_nothing_matches():
    kl = KnowledgeLayer(REF, "wiki")
    assert kl.context(NOTE_A, "ADI-0001") == kl.context(NOTE_A, "ADI-0001")
    assert kl.context("zzz qqq", "ADI-0001") == ""
    assert kl.fingerprint() == KnowledgeLayer(REF, "wiki").fingerprint()


def test_empty_context_keeps_prompt_and_cache_key(tmp_path, monkeypatch):
    seen = []
    monkeypatch.setattr(le, "_call_ollama", lambda prompt, **k: seen.append(prompt) or '{"clinical":{},"coding":{}}')
    le.llm_extract("NOTA", model="m")
    le.llm_extract("NOTA", model="m", context="CTX")
    assert seen[0] == f"{le.SYSTEM_PROMPT}\n\nTEXT:\nNOTA\n\nJSON ONLY:"
    assert "CTX" in seen[1] and seen[1].index("CTX") < seen[1].index("TEXT:")
    monkeypatch.setattr(rp, "LLM_CACHE_DIR", tmp_path)
    assert rp._cache_path("t", "m") != rp._cache_path("t", "m", "CTX")
    assert rp._cache_path("t", "m") == rp._cache_path("t", "m", "")


def test_context_reaches_the_llm_and_cache_separates_conditions(tmp_path, monkeypatch):
    calls = []

    def fake(text, model, base_url=None, timeout_s=0, return_raw=False, max_retries=1, context=""):
        calls.append(context)
        return ({"clinical": {"reason_for_visit": "x", "vitals": {}, "interventions": [],
                              "follow_up": {}, "critical_issues": []}, "coding": {"problems_normalized": []}}, "{}")

    monkeypatch.setattr(rp, "llm_extract", fake)
    monkeypatch.setattr(rp, "LLM_CACHE_DIR", tmp_path)
    rp.process_note(NOTE_A, "ADI-0001", "hybrid", "m", context="")
    rp.process_note(NOTE_A, "ADI-0001", "hybrid", "m", context="CTX")
    rp.process_note(NOTE_A, "ADI-0001", "hybrid", "m", context="CTX")  # cached
    assert calls == ["", "CTX"]


def test_context_is_capped_so_prompt_fits_model_window():
    big = [(rec(f"ADI-{i:04d}", "controllo", V(130, 80, 72)), NOTE_B.replace("medicazione", f"medicazione{i}"))
           for i in range(1, 60)]
    ctx = KnowledgeLayer(big, "raw", k=50, max_chars=400).context(NOTE_B, "ADI-9999")
    assert 0 < len(ctx) <= 400
