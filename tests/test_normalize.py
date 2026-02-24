# tests/test_normalize.py
from src.normalize import normalize_problems


def test_normalize_empty_text():
    text = ""
    out = normalize_problems(text)
    assert out == []


def test_normalize_exact_terms_controlled_vocab():
    # Use phrases that are explicitly mapped in SYNONYM_MAP
    text = "Ipertensione arteriosa e dolore cronico. Riferisce diabete tipo 2."
    out = normalize_problems(text)

    # 'ipertensione arteriosa' -> ipertensione
    assert "ipertensione" in out

    # 'diabete tipo 2' -> diabete_tipo_2
    assert "diabete_tipo_2" in out

    # any 'dolore' triggers dolore_cronico rule in normalize.py
    assert "dolore_cronico" in out


def test_normalize_malnutrizione_from_appetite_and_fatigue():
    text = "Paziente riferisce stanchezza e scarso appetito."
    out = normalize_problems(text)
    assert "malnutrizione" in out


def test_normalize_caduta_and_risk():
    text = "Rivalutazione dopo caduta. Valutato rischio caduta."
    out = normalize_problems(text)
    assert "caduta" in out
    assert "rischio_caduta" in out


def test_normalize_disidratazione():
    text = "Consigliata idratazione: possibile disidratazione, beve poco."
    out = normalize_problems(text)
    assert "disidratazione" in out


def test_normalize_bpco():
    text = "Anamnesi: BPCO, dispnea a piccoli sforzi."
    out = normalize_problems(text)
    assert "bpco" in out


def test_normalize_lesione_da_pressione():
    text = "Medicazione piaga da decubito al tallone."
    out = normalize_problems(text)
    assert "lesione_da_pressione" in out


def test_fuzzy_ipertensione_typo():
    text = "Ipertensione arteriosaa."
    out = normalize_problems(text)
    assert "ipertensione" in out