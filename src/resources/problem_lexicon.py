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
    # cardio
    "ipertensione arteriosa": "ipertensione",
    "pressione alta": "ipertensione",

    # diabetes
    "diabete tipo 2": "diabete_tipo_2",
    "diabete mellito tipo 2": "diabete_tipo_2",

    # wounds
    "lesione da pressione": "lesione_da_pressione",
    "piaga da decubito": "lesione_da_pressione",
    "ulcera da pressione": "lesione_da_pressione",

    # respiratory
    "bpco": "bpco",
    "bronchite cronica": "bpco",

    # falls
    "caduta": "caduta",
    "rischio caduta": "rischio_caduta",

    # hydration / nutrition
    "scarso appetito": "malnutrizione",
    "inappetenza": "malnutrizione",
    "ridotto appetito": "malnutrizione",
    "mangia poco": "malnutrizione",
    "non mangia": "malnutrizione",
    "disidratazione": "disidratazione",
    "poca idratazione": "disidratazione",
}