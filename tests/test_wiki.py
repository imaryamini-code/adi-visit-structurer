import json
from pathlib import Path

import pytest

from src.wiki import LAYOUTS, build_wiki, check_provenance, facts_from_record

TEXT = ("La visita è stata per il monitoraggio. Pressione arteriosa 130/80 mmHg, "
        "frequenza cardiaca 72 bpm. Nuovo controllo per la prossima settimana.")


def rec(rid, date="2026-02-15"):
    return {"meta": {"record_id": rid, "visit_datetime": date + "T10:30:00"},
            "clinical": {"reason_for_visit": "controllo parametri",
                         "vitals": {"blood_pressure_systolic": 130, "blood_pressure_diastolic": 80,
                                    "heart_rate": 72, "temperature": None, "spo2": None},
                         "interventions": ["monitoraggio_parametri_vitali"],
                         "follow_up": {"type": "controllo", "timing_days": 7},
                         "critical_issues": []},
            "coding": {"problems_normalized": []}}


def test_facts_have_evidence_from_note():
    f = {c: (t, e) for c, t, e in facts_from_record(rec("ADI-0001"), TEXT)}
    assert f["vitals"][0] == "PA 130/80 mmHg, FC 72 bpm"
    assert "130/80" in f["vitals"][1]


def test_missing_values_are_not_invented():
    r = rec("ADI-0001")
    r["clinical"]["vitals"] = {k: None for k in r["clinical"]["vitals"]}
    assert "vitals" not in {c for c, _, _ in facts_from_record(r, TEXT)}


@pytest.mark.parametrize("layout", LAYOUTS)
def test_every_layout_keeps_provenance(tmp_path, layout):
    recs = [(rec("ADI-0001"), TEXT), (rec("ADI-0002", "2026-02-16"), TEXT)]
    build_wiki(recs, layout, tmp_path, patients={"ADI-0001": "P1", "ADI-0002": "P1"})
    rep = check_provenance(tmp_path, ["ADI-0001", "ADI-0002"])
    assert rep["fact_lines"] > 0 and rep["untagged"] == 0 and rep["unknown_source"] == 0


def test_patient_layout_groups_visits(tmp_path):
    recs = [(rec("ADI-0001"), TEXT), (rec("ADI-0002", "2026-02-16"), TEXT)]
    build_wiki(recs, "patient", tmp_path, patients={"ADI-0001": "P1", "ADI-0002": "P1"})
    body = (tmp_path / "patients" / "P1.md").read_text(encoding="utf-8")
    assert body.count("## Visita") == 2


def test_unknown_source_is_detected(tmp_path):
    (tmp_path / "x.md").write_text("- fatto [source: ADI-9999]\n- senza fonte\n", encoding="utf-8")
    rep = check_provenance(tmp_path, ["ADI-0001"])
    assert rep == {"fact_lines": 2, "untagged": 1, "unknown_source": 1}


def test_build_is_deterministic(tmp_path):
    recs = [(rec("ADI-0001"), TEXT)]
    a, b = tmp_path / "a", tmp_path / "b"
    build_wiki(recs, "concept", a)
    build_wiki(recs, "concept", b)
    assert {p.name: p.read_bytes() for p in a.rglob("*.md")} == {p.name: p.read_bytes() for p in b.rglob("*.md")}


def test_evidence_matches_reworded_label_and_never_invents():
    from src.wiki import _evidence_by_stems
    t = "Oggi controlli dei parametri vitali. Segnalata caduta recente."
    assert "caduta" in _evidence_by_stems(t, "caduta_recente")
    assert _evidence_by_stems(t, "ulcera_sacrale") is None


def test_follow_up_given_as_free_text_is_kept():
    r = rec("ADI-0001")
    r["clinical"]["follow_up"] = "Programmato controllo tra 7 giorni"
    f = {c: t for c, t, _ in facts_from_record(r, TEXT)}
    assert f["follow_up"] == "Programmato controllo tra 7 giorni"
