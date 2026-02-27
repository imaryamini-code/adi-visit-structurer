# tests/test_pipeline_rules.py
from src.extract_rules import extract_bp, extract_follow_up, extract_reason
from src.normalize import normalize_problems


def test_bp_does_not_match_date():
    text = "Visita domiciliare 24/02/2026 09:10\nPressione 135-80, FC=74."
    sys, dia = extract_bp(text)
    assert sys == 135
    assert dia == 80


def test_follow_up_followup_colon():
    text = "Follow up: controllo la prossima settimana."
    fu = extract_follow_up(text)
    assert fu == "controllo la prossima settimana"


def test_reason_from_motivo():
    text = "Motivo: monitoraggio segni vitali + verifica terapia."
    reason = extract_reason(text)
    assert reason == "monitoraggio segni vitali + verifica terapia"


def test_reason_from_riferisce():
    text = "Paziente riferisce stanchezza e scarso appetito."
    reason = extract_reason(text)
    assert reason == "stanchezza e scarso appetito"


def test_normalize_malnutrizione_from_appetite_and_fatigue():
    text = "Paziente riferisce stanchezza e scarso appetito."
    probs = normalize_problems(text)
    assert "malnutrizione" in probs