"""Opt-in v2 extractors: default unchanged, switch wired through every mode, tools and src agree."""
import json
from pathlib import Path

import pytest

import src.run_pipeline as rp
from src import extractors_v2 as v2
from tools import followup_variants as fv
from tools import reason_variants as rv
from tools.precision_rules import drop_generic_lesion as tool_drop

ROOT = Path(__file__).resolve().parents[1]
NOTES = sorted((ROOT / "data/synthetic/raw").glob("ADI-*.txt"))


def test_default_is_v1_and_unchanged():
    note = NOTES[4].read_text(encoding="utf-8")
    a = rp.process_note(note, "X", "rules")
    b = rp.process_note(note, "X", "rules", extractors="v1")
    assert a == b and "extractors" not in a["meta"]


def test_unknown_version_rejected():
    with pytest.raises(ValueError):
        rp.process_note("testo", "X", "rules", extractors="v9")


def test_src_and_tools_implementations_agree_on_all_notes():
    for p in NOTES:
        t = p.read_text(encoding="utf-8")
        assert v2.reason_v3(t) == rv.v3(t)
        assert v2.follow_up_v2(t) == fv.follow_up_v2(t)


def test_v2_rules_sets_flag_and_filters_generic_lesion():
    note = ("10/02/2026 ore 08:00. Visita domiciliare. Eseguito cambio di medicazione alla lesione. "
            "Prossimo controllo fra 3 giorni.")
    rec = rp.process_note(note, "X", "rules", extractors="v2")
    assert rec["meta"]["extractors"] == "v2"
    assert "lesione_da_pressione" not in rec["coding"]["problems_normalized"]
    assert rec["clinical"]["follow_up"] == {"type": "controllo", "timing_days": 3}  # type from the follow-up sentence
    wound = rp.process_note(note.replace("Prossimo controllo", "Prossimo controllo della lesione"), "X", "rules",
                            extractors="v2")
    assert wound["clinical"]["follow_up"] == {"type": "controllo_ferita", "timing_days": 3}
    explicit = rp.process_note(note.replace("alla lesione", "alla lesione da decubito"), "X", "rules", extractors="v2")
    assert "lesione_da_pressione" in explicit["coding"]["problems_normalized"]


def test_phrase_parser_understands_more_timings():
    assert v2.follow_up_phrase_v2("controllo fra 3 giorni")["timing_days"] == 3
    assert v2.follow_up_phrase_v2("nuovo controllo per i prossimi 2 giorni")["timing_days"] == 2
    assert v2.follow_up_phrase_v2("") is None and v2.follow_up_phrase_v2("tutto bene") is None


def test_llm_mode_uses_v2_canonical_follow_up_and_lesion_filter(monkeypatch):
    out = {"clinical": {"follow_up": "controllo fra 3 giorni", "vitals": {}}, "coding": {"problems_normalized": ["lesione_da_pressione", "dolore"]}}
    monkeypatch.setattr(rp, "call_llm", lambda text, model, context="": out)
    monkeypatch.setattr(rp, "llm_extract", object())
    rec = rp.process_note("10/02/2026 ore 08:00. Medicata la lesione.", "X", "llm", extractors="v2")
    assert rec["clinical"]["follow_up"]["timing_days"] == 3
    assert rec["coding"]["problems_normalized"] == ["dolore"]


def test_tool_and_src_lesion_rule_match():
    for text in ("Lesione da decubito.", "Medicata la lesione.", "Piaga sacrale."):
        assert tool_drop({"lesione_da_pressione"}, text) == set(v2.drop_generic_lesion(["lesione_da_pressione"], text))


def test_router_uses_v2_phrase_parser_when_given():
    from src.routing import RoutingConfig, resolve_escalations
    def fresh():
        return {"clinical": {"follow_up": None, "vitals": {}}, "coding": {"problems_normalized": []}}
    plan, llm = {"follow_up": "note mentions a follow-up but rules found none"}, {"clinical": {"follow_up": "controllo fra 3 giorni"}}
    rec = fresh()
    resolve_escalations("testo", rec, plan, llm, RoutingConfig(), follow_up_parser=v2.follow_up_phrase_v2)
    assert rec["clinical"]["follow_up"]["timing_days"] == 3
