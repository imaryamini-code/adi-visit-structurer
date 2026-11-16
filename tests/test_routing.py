"""Tests for adaptive field-level routing (src/routing.py). No Ollama needed: the LLM is stubbed."""
import pytest

from src.routing import (
    ACCEPTED, ESCALATED_ACCEPTED, FLAGGED, NOT_MENTIONED,
    RoutingConfig, plan_escalations, route_record,
)


def make_rec(**clinical):
    base = {
        "reason_for_visit": "medicazione e controllo lesione",
        "vitals": {
            "blood_pressure_systolic": 140, "blood_pressure_diastolic": 90,
            "heart_rate": 80, "temperature": 37.2, "spo2": 97,
        },
        "interventions": ["medicazione"],
        "follow_up": {"type": "controllo", "timing_days": 3},
        "critical_issues": [],
    }
    base.update(clinical)
    return {"clinical": base, "coding": {"problems_normalized": ["lesione_da_pressione"]}}


def llm_returning(clinical=None, coding=None):
    calls = []

    def fn(text):
        calls.append(text)
        return {"clinical": clinical or {}, "coding": coding or {}}

    fn.calls = calls
    return fn


def never_called(text):
    raise AssertionError("LLM must not be called for this note")


# --- no escalation -----------------------------------------------------------------

def test_clean_rules_result_never_calls_llm():
    rec = make_rec()
    res = route_record("PA 140/90, FC 80, 37,2°C, SpO2 97%. Medicazione eseguita.", rec, never_called)
    assert not res.llm_called
    assert res.needs_review == []
    assert res.decisions["blood_pressure"].status == ACCEPTED
    assert rec["routing"]["llm_called"] is False


def test_vital_not_mentioned_is_not_escalated():
    rec = make_rec()
    rec["clinical"]["vitals"]["spo2"] = None
    res = route_record("PA 140/90, FC 80, 37,2°C. Medicazione.", rec, never_called)
    assert res.decisions["spo2"].status == NOT_MENTIONED


def test_spo2_mentioned_but_not_measured_is_not_escalated():
    rec = make_rec()
    rec["clinical"]["vitals"]["spo2"] = None
    plan = plan_escalations("Saturazione non rilevata durante la visita.", rec, RoutingConfig())
    assert "spo2" not in plan


# --- escalation + verification -----------------------------------------------------

def test_missing_spo2_with_value_in_note_escalates_and_accepts_grounded_value():
    rec = make_rec()
    rec["clinical"]["vitals"]["spo2"] = None
    llm = llm_returning({"vitals": {"spo2": 99}})
    res = route_record("Ossigenazione ematica saturo 99%. PA 140/90.", rec, llm)
    assert res.llm_called and len(llm.calls) == 1
    assert rec["clinical"]["vitals"]["spo2"] == 99
    assert res.decisions["spo2"].status == ESCALATED_ACCEPTED


def test_hallucinated_number_not_in_note_is_flagged_not_used():
    rec = make_rec()
    rec["clinical"]["vitals"]["spo2"] = None
    llm = llm_returning({"vitals": {"spo2": 94}})  # 94 is not in the note
    res = route_record("Ossigenazione ematica saturo 99%.", rec, llm)
    assert rec["clinical"]["vitals"]["spo2"] is None
    assert res.decisions["spo2"].status == FLAGGED
    assert res.decisions["spo2"].llm_suggestion == 94
    assert "spo2" in res.needs_review


def test_implausible_rules_value_is_removed_and_flagged_when_llm_cannot_fix():
    rec = make_rec()
    rec["clinical"]["vitals"]["heart_rate"] = 400
    res = route_record("FC 400 bpm.", rec, llm_returning({"vitals": {}}))
    assert rec["clinical"]["vitals"]["heart_rate"] is None
    assert res.decisions["heart_rate"].status == FLAGGED


def test_blood_pressure_pair_requires_systolic_above_diastolic():
    rec = make_rec()
    rec["clinical"]["vitals"].update(blood_pressure_systolic=None, blood_pressure_diastolic=None)
    llm = llm_returning({"vitals": {"blood_pressure_systolic": 80, "blood_pressure_diastolic": 120}})
    res = route_record("Pressione arteriosa 80/120 mmHg.", rec, llm)
    assert res.decisions["blood_pressure"].status == FLAGGED


# --- reason ------------------------------------------------------------------------

def test_generic_reason_flags_when_llm_disagrees_by_default():
    rec = make_rec(reason_for_visit="controllo generale")
    llm = llm_returning({"reason_for_visit": "rivalutazione del dolore"})
    res = route_record("Accesso per dolore al ginocchio.", rec, llm)
    assert rec["clinical"]["reason_for_visit"] == "controllo generale"  # kept
    assert res.decisions["reason_for_visit"].status == FLAGGED


def test_generic_reason_prefer_llm_policy():
    rec = make_rec(reason_for_visit="controllo generale")
    llm = llm_returning({"reason_for_visit": "rivalutazione del dolore"})
    cfg = RoutingConfig(generic_reason_policy="prefer_llm")
    res = route_record("Accesso per dolore al ginocchio.", rec, llm, cfg)
    assert rec["clinical"]["reason_for_visit"] == "rivalutazione dolore"
    assert res.decisions["reason_for_visit"].status == ESCALATED_ACCEPTED


def test_missing_reason_unmappable_llm_text_is_flagged():
    rec = make_rec(reason_for_visit=None)
    res = route_record("Visita.", rec, llm_returning({"reason_for_visit": "xyz sconosciuto"}))
    assert rec["clinical"]["reason_for_visit"] is None
    assert res.decisions["reason_for_visit"].status == FLAGGED


# --- follow-up ---------------------------------------------------------------------

def test_follow_up_llm_phrase_is_parsed_by_rules_into_structured_form():
    rec = make_rec(follow_up=None)
    llm = llm_returning({"follow_up": "controllo tra 7 giorni"})
    res = route_record("Si programma il prossimo controllo.", rec, llm)
    assert rec["clinical"]["follow_up"]["timing_days"] == 7
    assert res.decisions["follow_up"].status == ESCALATED_ACCEPTED


# --- robustness / cost -------------------------------------------------------------

def test_llm_called_at_most_once_even_with_many_escalated_fields():
    rec = make_rec(reason_for_visit=None, follow_up=None, interventions=["valutazione_generale"])
    rec["clinical"]["vitals"].update(spo2=None, heart_rate=None)
    rec["coding"]["problems_normalized"] = []
    llm = llm_returning({})
    route_record("Frequenza cardiaca 72 bpm, saturazione 98%. Prossimo controllo previsto.", rec, llm)
    assert len(llm.calls) == 1


def test_llm_unavailable_flags_fields_instead_of_crashing():
    rec = make_rec()
    rec["clinical"]["vitals"]["spo2"] = None

    def down(text):
        raise RuntimeError("Could not reach Ollama at http://localhost:11434.\nmore")

    res = route_record("Saturazione 98%.", rec, down)
    assert not res.llm_called
    assert res.llm_error.startswith("Could not reach Ollama")
    assert res.decisions["spo2"].status == FLAGGED
    assert rec["routing"]["needs_review"] == ["spo2"]


def test_no_llm_configured_flags_instead_of_crashing():
    rec = make_rec()
    rec["clinical"]["vitals"]["spo2"] = None
    res = route_record("Saturazione 98%.", rec, None)
    assert res.decisions["spo2"].status == FLAGGED


def test_ablation_switches_disable_escalation():
    rec = make_rec()
    rec["clinical"]["vitals"]["spo2"] = None
    cfg = RoutingConfig(escalate_missing_vitals=False)
    assert "spo2" not in plan_escalations("Saturazione 98%.", rec, cfg)


def test_interventions_fallback_escalates_and_filters_to_vocabulary():
    rec = make_rec(interventions=["valutazione_generale"])
    llm = llm_returning({"interventions": ["medicazione", "inventato_dal_modello"]})
    route_record("Cambio medicazione eseguito.", rec, llm)
    assert rec["clinical"]["interventions"] == ["medicazione"]


def test_routing_log_is_json_serialisable():
    import json
    rec = make_rec()
    route_record("PA 140/90.", rec, never_called)
    json.dumps(rec["routing"])


# --- process_note integration (the entry point used by batch runs and compare_models) ---------

from pathlib import Path  # noqa: E402

import src.run_pipeline as rp  # noqa: E402

RAW_DIR = Path("data/synthetic/raw")


def _first_note(needs_llm: bool):
    """Find a real synthetic note that does / does not need the LLM under the default policy."""
    for f in sorted(RAW_DIR.glob("ADI-*.txt")):
        text = rp.PREPROCESS(f.read_text(encoding="utf-8"))
        rec = rp.build_base_record(f.stem, "adaptive", "mistral")
        rp.apply_rules(text, rec)
        if bool(plan_escalations(text, rec, RoutingConfig())) == needs_llm:
            return f
    pytest.skip("no suitable synthetic note found")


def test_process_note_adaptive_without_need_does_not_call_llm(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("LLM must not be called")
    monkeypatch.setattr(rp, "llm_extract", boom)
    f = _first_note(needs_llm=False)
    rec = rp.process_note(f.read_text(encoding="utf-8"), f.stem, "adaptive", "mistral", require_llm=True)
    assert rec["meta"]["llm_status"] == "not_needed"
    assert rec["routing"]["llm_called"] is False


def test_process_note_adaptive_calls_llm_once_when_needed(monkeypatch):
    calls = []

    def stub(text, model, **k):
        calls.append(model)
        return {"clinical": {}, "coding": {}}
    monkeypatch.setattr(rp, "llm_extract", stub)
    f = _first_note(needs_llm=True)
    rec = rp.process_note(f.read_text(encoding="utf-8"), f.stem, "adaptive", "llama3.1:8b")
    assert calls == ["llama3.1:8b"]
    assert rec["meta"]["llm_status"] == "called"


def test_process_note_adaptive_require_llm_raises_if_needed_but_unavailable(monkeypatch):
    def down(*a, **k):
        raise RuntimeError("Could not reach Ollama")
    monkeypatch.setattr(rp, "llm_extract", down)
    f = _first_note(needs_llm=True)
    with pytest.raises(RuntimeError, match="needs the LLM"):
        rp.process_note(f.read_text(encoding="utf-8"), f.stem, "adaptive", "mistral", require_llm=True)
    # Without require_llm (interactive use) it degrades gracefully and flags instead.
    rec = rp.process_note(f.read_text(encoding="utf-8"), f.stem, "adaptive", "mistral")
    assert rec["meta"]["llm_status"] == "unavailable"
    assert rec["routing"]["needs_review"]
