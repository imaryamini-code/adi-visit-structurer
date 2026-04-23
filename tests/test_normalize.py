# tests/test_normalize.py
from src.normalize import normalize_problems, normalize_reason, normalize_interventions


# ---------------------------------------------------------------------------
# normalize_problems
# ---------------------------------------------------------------------------

def test_empty_text():
    assert normalize_problems("") == []


def test_exact_terms():
    text = "Ipertensione arteriosa e dolore cronico. Riferisce diabete tipo 2."
    out = normalize_problems(text)
    assert "ipertensione" in out
    assert "diabete_tipo_2" in out
    assert "dolore" in out


def test_malnutrizione_from_appetite_and_fatigue():
    text = "Paziente riferisce stanchezza e scarso appetito."
    out = normalize_problems(text)
    # inappetenza maps to "inappetenza", astenia to "astenia"
    assert "inappetenza" in out or "astenia" in out


def test_caduta():
    text = "Rivalutazione dopo caduta recente."
    out = normalize_problems(text)
    # gold vocab uses "caduta" not "caduta_recente"
    assert "caduta" in out


def test_disidratazione():
    text = "Consigliata idratazione: possibile disidratazione, beve poco."
    out = normalize_problems(text)
    assert "disidratazione" in out


def test_bpco():
    text = "Anamnesi: BPCO, dispnea a piccoli sforzi."
    out = normalize_problems(text)
    assert "bpco" in out


def test_lesione_da_pressione():
    text = "Medicazione piaga da decubito al tallone."
    out = normalize_problems(text)
    # gold vocab uses "lesione_da_pressione"
    assert "lesione_da_pressione" in out


def test_normalize_list_input():
    items = ["lesione_cutanea", "caduta_recente", "dolore_generico"]
    out = normalize_problems(items)
    assert "lesione_da_pressione" in out
    assert "caduta" in out
    assert "dolore" in out


def test_no_duplicates():
    text = "Caduta recente dopo caduta domestica."
    out = normalize_problems(text)
    assert out.count("caduta") == 1


# ---------------------------------------------------------------------------
# normalize_reason
# ---------------------------------------------------------------------------

def test_reason_medicazione():
    assert normalize_reason("medicazione e controllo lesione") == "medicazione e controllo lesione"


def test_reason_alias():
    assert normalize_reason("medicazione/controllo lesione") == "medicazione e controllo lesione"


def test_reason_caduta():
    result = normalize_reason("controllo post-caduta")
    assert result == "rivalutazione caduta recente"


def test_reason_fallback_wound():
    result = normalize_reason("cambio medicazione lesione")
    assert result == "medicazione e controllo lesione"


def test_reason_none():
    assert normalize_reason(None) is None
    assert normalize_reason("") is None


# ---------------------------------------------------------------------------
# normalize_interventions
# ---------------------------------------------------------------------------

def test_interventions_dedup():
    items = ["monitoraggio parametri vitali", "monitoraggio_parametri_vitali"]
    out = normalize_interventions(items)
    assert out.count("monitoraggio_parametri_vitali") == 1


def test_interventions_mapping():
    items = ["somministrazione terapia", "medicazione lesione"]
    out = normalize_interventions(items)
    assert "somministrazione_farmaco" in out
    assert "medicazione" in out
