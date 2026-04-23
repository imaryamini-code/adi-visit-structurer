# tests/test_pipeline_rules.py
from src.extract_rules import (
    extract_bp,
    extract_hr,
    extract_temp,
    extract_spo2,
    extract_datetime,
    extract_reason,
    extract_follow_up,
    extract_interventions,
    extract_vitals,
)


# ---------------------------------------------------------------------------
# Blood pressure
# ---------------------------------------------------------------------------

def test_bp_standard():
    sys_v, dia_v = extract_bp("PA 130/80 mmHg")
    assert sys_v == 130
    assert dia_v == 80


def test_bp_does_not_match_date():
    text = "Visita domiciliare 24/02/2026 ore 09:10. Pressione arteriosa 135/80 mmHg, FC=74."
    sys_v, dia_v = extract_bp(text)
    assert sys_v == 135
    assert dia_v == 80


def test_bp_verbose():
    text = "pressione arteriosa sistolica/diastolica 130/80 mmHg"
    sys_v, dia_v = extract_bp(text)
    assert sys_v == 130
    assert dia_v == 80


def test_bp_spoken():
    text = "La pressione è centotrenta su ottanta."
    sys_v, dia_v = extract_bp(text)
    assert sys_v == 130
    assert dia_v == 80


def test_bp_invalid_returns_none():
    sys_v, dia_v = extract_bp("Nessun dato pressione.")
    assert sys_v is None
    assert dia_v is None


# ---------------------------------------------------------------------------
# Heart rate
# ---------------------------------------------------------------------------

def test_hr_bpm():
    assert extract_hr("FC 72 bpm") == 72


def test_hr_spoken():
    assert extract_hr("frequenza cardiaca settantadue") == 72


def test_hr_out_of_range():
    assert extract_hr("FC 5 bpm") is None


# ---------------------------------------------------------------------------
# Temperature
# ---------------------------------------------------------------------------

def test_temp_decimal():
    assert extract_temp("temperatura corporea 36,7°C") == 36.7


def test_temp_dot():
    assert extract_temp("T: 37.1") == 37.1


def test_temp_out_of_range():
    assert extract_temp("temperatura 60°C") is None


# ---------------------------------------------------------------------------
# SpO2
# ---------------------------------------------------------------------------

def test_spo2_standard():
    assert extract_spo2("SpO2 97%") == 97


def test_spo2_saturazione():
    assert extract_spo2("saturazione 98") == 98


# ---------------------------------------------------------------------------
# Datetime
# ---------------------------------------------------------------------------

def test_datetime_standard():
    text = "15/02/2026 ore 10:30. Accesso domiciliare."
    assert extract_datetime(text) == "2026-02-15T10:30:00"


def test_datetime_none():
    assert extract_datetime("Nessuna data presente.") is None


# ---------------------------------------------------------------------------
# Vitals (unified)
# ---------------------------------------------------------------------------

def test_vitals_returns_numeric_types():
    text = "PA 130/80 mmHg, FC 72 bpm, temperatura 36.7°C, SpO2 97%."
    v = extract_vitals(text)
    assert v["blood_pressure_systolic"] == 130
    assert v["blood_pressure_diastolic"] == 80
    assert v["heart_rate"] == 72
    assert v["temperature"] == 36.7
    assert v["spo2"] == 97
    # All values should be numeric, not strings
    assert isinstance(v["blood_pressure_systolic"], int)
    assert isinstance(v["heart_rate"], int)
    assert isinstance(v["temperature"], float)


# ---------------------------------------------------------------------------
# Reason for visit
# ---------------------------------------------------------------------------

def test_reason_explicit_pattern():
    text = "Accesso domiciliare per medicazione e controllo della lesione."
    reason = extract_reason(text)
    assert reason == "medicazione e controllo lesione"


def test_reason_from_keywords():
    text = "Paziente in ossigenoterapia domiciliare, controllo respiratorio."
    reason = extract_reason(text)
    assert reason == "controllo respiratorio e gestione ossigenoterapia"


def test_reason_parametri():
    text = "Rilevati i parametri vitali: PA, FC, temperatura."
    reason = extract_reason(text)
    assert reason == "controllo parametri"


# ---------------------------------------------------------------------------
# Follow-up
# ---------------------------------------------------------------------------

def test_follow_up_days():
    text = "Programmato nuovo controllo domiciliare tra 7 giorni."
    fu = extract_follow_up(text)
    assert fu is not None
    assert fu["timing_days"] == 7
    assert fu["type"] == "controllo"


def test_follow_up_settimana():
    text = "Controllo previsto la prossima settimana."
    fu = extract_follow_up(text)
    assert fu is not None
    assert fu["timing_days"] == 7


def test_follow_up_ferita():
    text = "Controllo della lesione programmato tra 3 giorni."
    fu = extract_follow_up(text)
    assert fu is not None
    assert fu["type"] == "controllo_ferita"
    assert fu["timing_days"] == 3


def test_follow_up_phone_caregiver():
    text = "Previsto ricontatto telefonico con il caregiver."
    fu = extract_follow_up(text)
    assert fu is not None
    assert fu["type"] == "ricontatto_telefonico"
    assert fu["target"] == "caregiver"


def test_follow_up_none():
    assert extract_follow_up("Nessuna indicazione di follow-up.") is None


# ---------------------------------------------------------------------------
# Interventions
# ---------------------------------------------------------------------------

def test_interventions_vitals():
    v = {"blood_pressure_systolic": 130, "blood_pressure_diastolic": 80}
    interventions = extract_interventions("Rilevati i parametri vitali.", vitals=v)
    assert "monitoraggio_parametri_vitali" in interventions


def test_interventions_wound():
    interventions = extract_interventions("Eseguita medicazione della lesione.")
    assert "medicazione" in interventions


def test_interventions_fallback():
    # With no keywords, should fallback to valutazione_generale
    interventions = extract_interventions("Accesso di routine.")
    assert "valutazione_generale" in interventions
