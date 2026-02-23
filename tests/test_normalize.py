from src.normalize import normalize_problems

def test_normalize_exact_and_fuzzy():
    text = "Paziente con ipertensone arteriosa e dolore cronic. Riferisce diabete tipo 2."
    out = normalize_problems(text)
    assert "ipertensione" in out
    assert "dolore_cronico" in out
    assert "diabete_tipo_2" in out

def test_normalize_empty():
    assert normalize_problems("Nessuna problematica riferita.") == []