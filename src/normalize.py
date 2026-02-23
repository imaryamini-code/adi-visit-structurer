# src/normalize.py

PROBLEM_VOCAB = {
    "ipertensione",
    "diabete_tipo_2",
    "lesione_da_pressione",
    "dolore_cronico",
    "scompenso_cardiaco",
    "bpco",
    "caduta",
    "rischio_caduta",
    "disidratazione",
    "malnutrizione",
}

SYNONYM_MAP = {
    "ipertensione arteriosa": "ipertensione",
    "pressione alta": "ipertensione",
    "diabete tipo 2": "diabete_tipo_2",
    "diabete mellito tipo 2": "diabete_tipo_2",
    "lesione da pressione": "lesione_da_pressione",
    "piaga da decubito": "lesione_da_pressione",
    "ulcera da pressione": "lesione_da_pressione",
    "dolore cronico": "dolore_cronico",
    "bpco": "bpco",
    "bronchite cronica": "bpco",
}

def normalize_problems(text: str) -> list[str]:
    t = text.lower()
    found = set()

    for phrase, norm in SYNONYM_MAP.items():
        if phrase in t:
            found.add(norm)

    # (Optional safety) ensure outputs are only from the controlled vocab
    found = {p for p in found if p in PROBLEM_VOCAB}

    return sorted(found)
