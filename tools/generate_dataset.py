import json
import random
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

MODEL = "llama3.1:8b"

OUT_RAW = Path("data/synthetic/raw")
OUT_GOLD = Path("data/synthetic/gold")

TARGET_TOTAL = 100
DEFAULT_START_DATE = datetime(2026, 2, 10, 8, 0)

random.seed(11)

SEXES = ["F", "M", None]
ROLES = ["infermiere", "infermiere", "infermiere", "medico"]
MOBILITY_VALUES = [None, "autonoma", "con aiuto", "ridotta"]
CONSCIOUSNESS_VALUES = [None, "vigile", "vigile e orientato", "collaborante"]

VITAL_OPTIONS = {
    "blood_pressure_systolic": [105, 110, 115, 120, 125, 130, 135, 140, 150],
    "blood_pressure_diastolic": [65, 70, 75, 80, 85, 90],
    "heart_rate": [60, 64, 68, 72, 76, 80, 88, 96],
    "temperature": [36.1, 36.4, 36.5, 36.7, 36.8, 37.0, 37.4, 37.8],
    "spo2": [94, 95, 96, 97, 98, 99],
    "respiratory_rate": [16, 18, 20, 22],
}

SCENARIO_WEIGHTS = [
    ("routine", 20),
    ("symptoms_no_vitals", 10),
    ("fall", 7),
    ("wound", 16),
    ("medication", 12),
    ("pain_reassessment", 8),
    ("catheter", 7),
    ("stomia", 5),
    ("caregiver_education", 6),
    ("oxygen_therapy", 5),
    ("incomplete_dictation", 4),
]

ANAMNESIS_MAP = {
    "routine": [],
    "symptoms_no_vitals": ["riferita sintomatologia aspecifica nelle ultime 24 ore"],
    "fall": ["caduta recente riferita dal caregiver", "nessuna perdita di coscienza segnalata"],
    "wound": ["lesione cutanea già nota in monitoraggio domiciliare"],
    "medication": ["terapia domiciliare in corso"],
    "pain_reassessment": ["dolore già noto in sede riferita dal paziente"],
    "catheter": ["presenza di catetere vescicale"],
    "stomia": ["presenza di stomia in gestione domiciliare"],
    "caregiver_education": ["caregiver presente durante l'accesso"],
    "oxygen_therapy": ["ossigenoterapia domiciliare in corso"],
    "incomplete_dictation": [],
}


def ensure_dirs() -> None:
    OUT_RAW.mkdir(parents=True, exist_ok=True)
    OUT_GOLD.mkdir(parents=True, exist_ok=True)


def iso_dt(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%dT%H:%M:%S")


def existing_record_numbers() -> list[int]:
    numbers = []
    for path in OUT_GOLD.glob("ADI-*.json"):
        m = re.match(r"ADI-(\d{4})\.json$", path.name)
        if m:
            numbers.append(int(m.group(1)))
    return sorted(numbers)


def get_generation_plan(target_total: int = TARGET_TOTAL) -> tuple[int, int]:
    existing = existing_record_numbers()
    current_total = len(existing)
    if current_total >= target_total:
        return 0, (max(existing) + 1 if existing else 1)

    next_id = (max(existing) + 1) if existing else 1
    n_new = target_total - current_total
    return n_new, next_id


def weighted_scenarios(n: int) -> list[str]:
    bag = []
    for name, weight in SCENARIO_WEIGHTS:
        bag.extend([name] * weight)
    random.shuffle(bag)

    out = []
    while len(out) < n:
        out.extend(bag)
        random.shuffle(out)

    return out[:n]


def pick_patient_age() -> int | None:
    return random.choice([None, random.randint(67, 92), random.randint(70, 88)])


def make_vitals(include_all: bool = True, include_spo2_probability: float = 0.8) -> dict:
    if not include_all:
        return {
            "blood_pressure_systolic": None,
            "blood_pressure_diastolic": None,
            "heart_rate": None,
            "temperature": None,
            "spo2": None,
            "respiratory_rate": None,
        }

    return {
        "blood_pressure_systolic": random.choice(VITAL_OPTIONS["blood_pressure_systolic"]),
        "blood_pressure_diastolic": random.choice(VITAL_OPTIONS["blood_pressure_diastolic"]),
        "heart_rate": random.choice(VITAL_OPTIONS["heart_rate"]),
        "temperature": random.choice(VITAL_OPTIONS["temperature"]),
        "spo2": random.choice(VITAL_OPTIONS["spo2"]) if random.random() < include_spo2_probability else None,
        "respiratory_rate": random.choice(VITAL_OPTIONS["respiratory_rate"]) if random.random() < 0.35 else None,
    }


def scenario_to_reason(scenario: str) -> str | None:
    mapping = {
        "routine": "controllo parametri",
        "symptoms_no_vitals": "riferiti sintomi generali",
        "fall": "rivalutazione caduta recente",
        "wound": "medicazione e controllo lesione",
        "medication": "controllo terapia e somministrazione farmaco",
        "pain_reassessment": "rivalutazione dolore",
        "catheter": "controllo e gestione catetere",
        "stomia": "controllo e gestione stomia",
        "caregiver_education": "educazione caregiver e controllo generale",
        "oxygen_therapy": "controllo respiratorio e gestione ossigenoterapia",
        "incomplete_dictation": random.choice(
            ["controllo generale", "accesso domiciliare di rivalutazione", None]
        ),
    }
    return mapping.get(scenario, "controllo generale")


def make_follow_up_struct(kind: str, days: int | None = None, target: str | None = None) -> dict:
    if kind == "controllo":
        return {"type": "controllo", "timing_days": days}
    if kind == "ricontatto_telefonico":
        return {"type": "ricontatto_telefonico", "target": target, "timing_days": days}
    if kind == "controllo_ferita":
        return {"type": "controllo_ferita", "timing_days": days}
    return {"type": kind, "timing_days": days}


def build_gold(record_id: str, dt: datetime, scenario: str) -> dict:
    age = pick_patient_age()
    sex = random.choice(SEXES)
    operator_role = random.choice(ROLES)
    vitals = make_vitals(include_all=scenario not in {"symptoms_no_vitals", "incomplete_dictation"})
    problems: list[str] = []
    interventions: list[str] = []
    critical_issues: list[str] = []
    warnings: list[str] = []
    missing: list[str] = []
    follow_up = None
    mobility = random.choice(MOBILITY_VALUES)
    consciousness = random.choice(CONSCIOUSNESS_VALUES)
    caregiver_present = scenario in {"caregiver_education", "fall"} or random.random() < 0.2
    oxygen_therapy = scenario == "oxygen_therapy"

    if scenario == "routine":
        interventions = ["monitoraggio_parametri_vitali", "valutazione_generale"]
        follow_up = make_follow_up_struct("controllo", random.choice([3, 7, 14]))

    elif scenario == "symptoms_no_vitals":
        vitals = make_vitals(include_all=False)
        problems = random.sample(["astenia", "inappetenza", "capogiro", "insonnia", "nausea"], k=2)
        interventions = [
            "valutazione_generale",
            random.choice(["educazione_alimentare", "educazione_terapeutica"]),
        ]
        follow_up = make_follow_up_struct("ricontatto_telefonico", None, "caregiver")
        warnings.extend(["Nessun parametro vitale riportato", "Follow-up senza tempistica"])

    elif scenario == "fall":
        problems = ["caduta"]
        interventions = ["monitoraggio_parametri_vitali", "valutazione_generale"]
        critical_issues = ["caduta_recente"]
        follow_up = make_follow_up_struct("controllo", None)
        warnings.append("Follow-up senza tempistica")

    elif scenario == "wound":
        problems = random.choice([[], ["dolore"]])
        interventions = ["medicazione", "valutazione_generale"]
        if any(v is not None for v in vitals.values()):
            interventions.insert(0, "monitoraggio_parametri_vitali")
        follow_up = make_follow_up_struct("controllo_ferita", random.choice([2, 3, 7]))

    elif scenario == "medication":
        problems = random.sample(["dolore", "febbre", "dispnea"], k=1)
        interventions = ["somministrazione_farmaco", "educazione_terapeutica"]
        if any(v is not None for v in vitals.values()):
            interventions.insert(0, "monitoraggio_parametri_vitali")
        follow_up = make_follow_up_struct("controllo", random.choice([2, 7]))

    elif scenario == "pain_reassessment":
        problems = ["dolore"]
        interventions = ["valutazione_generale"]
        if any(v is not None for v in vitals.values()):
            interventions.insert(0, "monitoraggio_parametri_vitali")
        follow_up = make_follow_up_struct("controllo", random.choice([2, 3, 7]))

    elif scenario == "catheter":
        interventions = ["gestione_catetere", "valutazione_generale"]
        if any(v is not None for v in vitals.values()):
            interventions.insert(0, "monitoraggio_parametri_vitali")
        follow_up = make_follow_up_struct("controllo", random.choice([3, 7]))

    elif scenario == "stomia":
        interventions = ["gestione_stomia", "educazione_terapeutica"]
        if any(v is not None for v in vitals.values()):
            interventions.insert(0, "monitoraggio_parametri_vitali")
        follow_up = make_follow_up_struct("controllo", random.choice([3, 7]))

    elif scenario == "caregiver_education":
        problems = random.choice([[], ["astenia"]])
        interventions = ["valutazione_generale", "educazione_terapeutica"]
        if any(v is not None for v in vitals.values()):
            interventions.insert(0, "monitoraggio_parametri_vitali")
        follow_up = make_follow_up_struct("ricontatto_telefonico", None, "caregiver")
        warnings.append("Follow-up senza tempistica")

    elif scenario == "oxygen_therapy":
        problems = random.choice([["dispnea"], ["dispnea", "astenia"], []])
        interventions = [
            "monitoraggio_parametri_vitali",
            "valutazione_generale",
            "gestione_ossigenoterapia",
        ]
        follow_up = make_follow_up_struct("controllo", random.choice([2, 3, 7]))

    elif scenario == "incomplete_dictation":
        vitals = {
            "blood_pressure_systolic": random.choice([None, 120, 130]),
            "blood_pressure_diastolic": random.choice([None, 80]),
            "heart_rate": None,
            "temperature": None,
            "spo2": None,
            "respiratory_rate": None,
        }
        problems = random.choice([[], ["astenia"], ["dolore"]])
        interventions = random.choice([[], ["valutazione_generale"], ["monitoraggio_parametri_vitali"]])
        follow_up = random.choice([None, make_follow_up_struct("controllo", None)])
        if scenario_to_reason(scenario) is None:
            missing.append("clinical.reason_for_visit")
        warnings.extend(["Dettatura incompleta o sintetica", "Possibili informazioni cliniche mancanti"])

    if vitals["spo2"] is None and oxygen_therapy:
        vitals["spo2"] = random.choice([94, 95, 96])

    if vitals["spo2"] is None and scenario not in {"symptoms_no_vitals", "incomplete_dictation"}:
        warnings.append("SpO2 non menzionata")

    risk_flags = ["rischio_malnutrizione"] if "inappetenza" in problems else []

    return {
        "meta": {
            "record_id": record_id,
            "template_type": ["diario_clinico"],
            "visit_datetime": iso_dt(dt),
            "operator_role": operator_role,
        },
        "patient": {
            "patient_id": f"SYNTH-{record_id}",
            "age": age,
            "sex": sex,
        },
        "clinical": {
            "reason_for_visit": scenario_to_reason(scenario),
            "anamnesis_brief": ANAMNESIS_MAP.get(scenario, []),
            "vitals": vitals,
            "consciousness": consciousness,
            "mobility": mobility,
            "interventions": list(dict.fromkeys(interventions)),
            "critical_issues": critical_issues,
            "follow_up": follow_up,
            "caregiver_present": caregiver_present,
            "oxygen_therapy": oxygen_therapy,
        },
        "coding": {
            "problems_normalized": problems,
            "risk_flags": risk_flags,
        },
        "quality": {
            "missing_mandatory_fields": missing,
            "warnings": sorted(list(dict.fromkeys(warnings))),
        },
    }


def build_reason_line(gold: dict) -> str:
    reason = gold["clinical"]["reason_for_visit"]
    mapping = {
        "controllo parametri": [
            "Accesso domiciliare per controllo parametri vitali.",
            "Visita ADI per monitoraggio dei parametri.",
            "Accesso per rilevazione dei parametri vitali e valutazione generale.",
        ],
        "riferiti sintomi generali": [
            "Accesso domiciliare per riferita sintomatologia generale.",
            "Visita richiesta per comparsa di sintomi aspecifici.",
            "Accesso per rivalutazione clinica dopo sintomi riferiti dal paziente.",
        ],
        "rivalutazione caduta recente": [
            "Accesso domiciliare per rivalutazione post-caduta recente.",
            "Visita per controllo dopo caduta riferita dal caregiver.",
            "Accesso per rivalutazione clinica in seguito a recente caduta.",
        ],
        "medicazione e controllo lesione": [
            "Accesso domiciliare per medicazione e controllo della lesione.",
            "Visita per medicazione della ferita e rivalutazione locale.",
            "Accesso per controllo della lesione cutanea e cambio medicazione.",
        ],
        "controllo terapia e somministrazione farmaco": [
            "Accesso domiciliare per controllo terapia e somministrazione del farmaco.",
            "Visita per verifica della terapia in corso e somministrazione prescritta.",
            "Accesso per monitoraggio terapia domiciliare e somministrazione farmacologica.",
        ],
        "rivalutazione dolore": [
            "Accesso domiciliare per rivalutazione del dolore riferito.",
            "Visita per controllo della sintomatologia algica.",
            "Accesso per rivalutazione del dolore e delle condizioni generali.",
        ],
        "controllo e gestione catetere": [
            "Accesso domiciliare per controllo e gestione del catetere vescicale.",
            "Visita per verifica del presidio urinario e gestione del catetere.",
            "Accesso per controllo catetere e valutazione generale.",
        ],
        "controllo e gestione stomia": [
            "Accesso domiciliare per controllo e gestione della stomia.",
            "Visita per verifica del presidio stomale e istruzione del paziente.",
            "Accesso per controllo stomia e condizioni locali.",
        ],
        "educazione caregiver e controllo generale": [
            "Accesso domiciliare per educazione del caregiver e controllo generale.",
            "Visita per istruzione del caregiver e rivalutazione clinica.",
            "Accesso per supporto al caregiver e verifica delle condizioni generali.",
        ],
        "controllo respiratorio e gestione ossigenoterapia": [
            "Accesso domiciliare per controllo respiratorio e gestione dell'ossigenoterapia.",
            "Visita per rivalutazione respiratoria in paziente in O2 terapia.",
            "Accesso per monitoraggio respiratorio e verifica dell'ossigenoterapia domiciliare.",
        ],
        "controllo generale": [
            "Accesso domiciliare di controllo generale.",
            "Visita ADI di rivalutazione clinica.",
            "Accesso per valutazione delle condizioni generali.",
        ],
        None: [
            "Accesso domiciliare di rivalutazione.",
        ],
    }
    return random.choice(mapping.get(reason, ["Accesso domiciliare di controllo generale."]))


def vitals_sentence(vitals: dict) -> str | None:
    parts = []
    if vitals.get("blood_pressure_systolic") and vitals.get("blood_pressure_diastolic"):
        parts.append(f"PA {vitals['blood_pressure_systolic']}/{vitals['blood_pressure_diastolic']} mmHg")
    if vitals.get("heart_rate"):
        parts.append(f"FC {vitals['heart_rate']} bpm")
    if vitals.get("temperature") is not None:
        parts.append(f"T {str(vitals['temperature']).replace('.', ',')}°C")
    if vitals.get("spo2") is not None:
        parts.append(f"SpO2 {vitals['spo2']}%")
    if vitals.get("respiratory_rate") is not None:
        parts.append(f"FR {vitals['respiratory_rate']} atti/min")
    if not parts:
        return None

    starters = [
        "Rilevati parametri vitali:",
        "Parametri rilevati:",
        "Si rilevano i seguenti parametri:",
    ]
    return f"{random.choice(starters)} " + ", ".join(parts) + "."


def problem_sentence(gold: dict) -> str | None:
    problems = gold["coding"]["problems_normalized"] or []
    scenario_reason = gold["clinical"]["reason_for_visit"] or ""

    custom_map = {
        "dolore": [
            "Il paziente riferisce dolore in sede già nota.",
            "Persistenza di dolore riferito, in monitoraggio.",
        ],
        "astenia": [
            "Riferita astenia.",
            "Paziente riferisce senso di debolezza generale.",
        ],
        "inappetenza": [
            "Riferita inappetenza.",
            "Ridotto appetito nelle ultime 24 ore.",
        ],
        "capogiro": [
            "Riferiti episodi di capogiro.",
        ],
        "nausea": [
            "Paziente riferisce nausea.",
        ],
        "dispnea": [
            "Riferita lieve dispnea.",
            "Quadro respiratorio in osservazione.",
        ],
        "caduta": [
            "Caduta recente riferita dal caregiver, senza traumi maggiori evidenti.",
        ],
    }

    sentences = []
    for p in problems:
        if p in custom_map:
            sentences.append(random.choice(custom_map[p]))

    if "lesione" in scenario_reason:
        sentences.append(random.choice([
            "Lesione già nota, in trattamento domiciliare.",
            "Cute in sede di lesione da rivalutare e medicare.",
        ]))
    if "catetere" in scenario_reason:
        sentences.append(random.choice([
            "Catetere in sede, da controllare il corretto funzionamento.",
            "Presidio urinario presente, senza criticità immediate riferite.",
        ]))
    if "stomia" in scenario_reason:
        sentences.append(random.choice([
            "Stomia in sede, cute peristomale da controllare.",
            "Presidio stomale in valutazione durante l'accesso.",
        ]))

    if not sentences:
        return random.choice([
            "Paziente in condizioni generali discrete.",
            "Condizioni generali nel complesso stabili.",
            "Paziente vigile e collaborante durante l'accesso.",
        ])

    return " ".join(sentences[:2])


def intervention_sentence(gold: dict) -> str | None:
    interventions = gold["clinical"]["interventions"] or []
    phrases = []

    mapping = {
        "monitoraggio_parametri_vitali": [
            "Eseguito monitoraggio dei parametri vitali.",
            "Effettuata rilevazione dei parametri.",
        ],
        "valutazione_generale": [
            "Effettuata valutazione generale del paziente.",
            "Eseguita rivalutazione clinica generale.",
        ],
        "medicazione": [
            "Eseguita medicazione della lesione secondo indicazione.",
            "Effettuato cambio medicazione con rivalutazione locale.",
        ],
        "somministrazione_farmaco": [
            "Somministrata terapia come da prescrizione.",
            "Eseguita somministrazione farmacologica prevista.",
        ],
        "gestione_catetere": [
            "Effettuato controllo del catetere vescicale.",
            "Gestito presidio urinario con verifica del corretto funzionamento.",
        ],
        "gestione_stomia": [
            "Effettuato controllo del presidio stomale.",
            "Gestita stomia con verifica della cute peristomale.",
        ],
        "educazione_terapeutica": [
            "Fornite indicazioni terapeutiche al paziente/caregiver.",
            "Eseguita educazione sanitaria durante l'accesso.",
        ],
        "gestione_ossigenoterapia": [
            "Verificata corretta O2 terapia domiciliare.",
            "Controllata ossigenoterapia in corso.",
        ],
    }

    for item in interventions:
        if item in mapping:
            phrases.append(random.choice(mapping[item]))

    if not phrases:
        return None
    return " ".join(phrases[:2])


def follow_up_sentence(gold: dict) -> str | None:
    follow = gold.get("clinical", {}).get("follow_up")

    if not follow:
        return None

    if isinstance(follow, str):
        f = follow.lower().strip()
        if "ferita" in f or "lesione" in f:
            return "Programmato controllo della lesione."
        if "telefon" in f:
            return "Previsto ricontatto telefonico."
        if "controllo" in f or "rivalutazione" in f:
            return "Programmato nuovo controllo domiciliare."
        return None

    if not isinstance(follow, dict):
        return None

    ftype = follow.get("type")
    days = follow.get("timing_days")
    target = follow.get("target")

    if ftype == "controllo_ferita":
        if days:
            return f"Programmato controllo della lesione tra {days} giorni."
        return "Programmato controllo della lesione."

    if ftype == "ricontatto_telefonico":
        if days and target:
            return f"Previsto ricontatto telefonico con {target} tra {days} giorni."
        if target:
            return f"Previsto ricontatto telefonico con {target}."
        return "Previsto ricontatto telefonico."

    if ftype == "controllo":
        if days:
            return f"Programmato nuovo controllo domiciliare tra {days} giorni."
        return "Programmato nuovo controllo domiciliare."

    return None


def caregiver_sentence(gold: dict) -> str | None:
    if gold["clinical"].get("caregiver_present"):
        return random.choice([
            "Caregiver presente durante l'accesso.",
            "Familiare presente e informato sulle indicazioni fornite.",
        ])
    return None


def build_dictation_from_gold(gold: dict) -> str:
    visit_dt = gold.get("meta", {}).get("visit_datetime")

    if isinstance(visit_dt, str):
        dt = datetime.fromisoformat(visit_dt)
    elif isinstance(visit_dt, datetime):
        dt = visit_dt
    else:
        dt = DEFAULT_START_DATE

    header = f"{dt.strftime('%d/%m/%Y')} ore {dt.strftime('%H:%M')}."

    reason = build_reason_line(gold)
    problem = problem_sentence(gold)
    vitals = vitals_sentence(gold.get("clinical", {}).get("vitals", {}))
    intervention = intervention_sentence(gold)
    caregiver = caregiver_sentence(gold)
    follow = follow_up_sentence(gold)

    lines = [header, reason, problem, vitals, intervention, caregiver, follow]
    lines = [l for l in lines if l]

    text = " ".join(lines)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def ollama_polish_dictation(base_text: str, gold: dict) -> str:
    prompt = f"""
Riscrivi questa breve nota clinica domiciliare ADI in italiano rendendola più naturale e professionale, ma senza cambiare i dati clinici.

Regole:
- Mantieni lo stesso significato clinico.
- Non inventare parametri o farmaci.
- Stile breve, realistico, da cartella domiciliare.
- 4-7 frasi massimo.
- Non aggiungere titoli o elenchi.
- Conserva data e ora all'inizio.
- Usa linguaggio tipico ADI/infermieristico.

Nota di partenza:
{base_text}

JSON di riferimento:
{json.dumps(gold, ensure_ascii=False)}
""".strip()

    result = subprocess.run(
        ["ollama", "run", MODEL],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return result.stdout.decode("utf-8").strip()


def save_pair(record_id: str, dictation: str, gold: dict) -> None:
    raw_path = OUT_RAW / f"{record_id}.txt"
    gold_path = OUT_GOLD / f"{record_id}.json"

    raw_path.write_text(dictation + "\n", encoding="utf-8")
    gold_path.write_text(json.dumps(gold, ensure_ascii=False, indent=2), encoding="utf-8")


def main(target_total: int = TARGET_TOTAL, regenerate_existing: bool = False) -> None:
    ensure_dirs()

    if regenerate_existing:
        existing = existing_record_numbers()
        print(f"Regenerating raw text for {len(existing)} existing records...")
        for rec_num in existing:
            record_id = f"ADI-{rec_num:04d}"
            gold_path = OUT_GOLD / f"{record_id}.json"
            if not gold_path.exists():
                continue

            gold = json.loads(gold_path.read_text(encoding="utf-8"))
            base_text = build_dictation_from_gold(gold)

            try:
                dictation = ollama_polish_dictation(base_text, gold)
            except Exception:
                dictation = base_text

            save_pair(record_id, dictation, gold)
            print(f"Regenerated {record_id}")

        print("Done.")
        return

    n_new, start_id = get_generation_plan(target_total=target_total)
    if n_new <= 0:
        print(f"Dataset already has at least {target_total} examples. Nothing to generate.")
        return

    scenarios = weighted_scenarios(n_new)

    print(f"Current total: {len(existing_record_numbers())}")
    print(f"Generating {n_new} new examples...")
    print(f"Record IDs: ADI-{start_id:04d} to ADI-{start_id + n_new - 1:04d}")

    for i in range(n_new):
        rec_num = start_id + i
        record_id = f"ADI-{rec_num:04d}"
        dt = DEFAULT_START_DATE + timedelta(
            days=random.randint(0, 45),
            hours=random.randint(0, 10),
            minutes=random.choice([0, 10, 20, 30, 40, 50]),
        )

        scenario = scenarios[i]
        gold = build_gold(record_id, dt, scenario)
        base_text = build_dictation_from_gold(gold)

        try:
            dictation = ollama_polish_dictation(base_text, gold)
        except Exception:
            dictation = base_text

        save_pair(record_id, dictation, gold)
        print(f"Generated {record_id} ({scenario})")

    print("Done.")


if __name__ == "__main__":
    main(target_total=100, regenerate_existing=False)