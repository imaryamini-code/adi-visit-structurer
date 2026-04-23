import json
from pathlib import Path

GOLD_DIR = Path("data/synthetic/gold")
PRED_DIR = Path("data/synthetic/pred")
REPORTS_DIR = Path("reports")


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def safe_get(dct, *keys, default=None):
    cur = dct
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


def canonical_reason(label: str | None) -> str | None:
    if not label:
        return None

    t = str(label).strip().lower()

    mapping = {
        # parameter monitoring
        "controllo parametri": "controllo_parametri",
        "monitoraggio parametri vitali": "controllo_parametri",
        "controllo parametri vitali": "controllo_parametri",
        # therapy
        "monitoraggio segni vitali e verifica terapia": "controllo_terapia",
        "controllo pressione e rivalutazione terapia": "controllo_terapia",
        "controllo terapia e somministrazione farmaco": "controllo_terapia",
        "controllo terapia/somministrazione farmaco": "controllo_terapia",
        "somministrazione terapia": "controllo_terapia",
        # wounds
        "medicazione lesione da pressione": "medicazione_lesione",
        "medicazione piaga da decubito": "medicazione_lesione",
        "medicazione/controllo lesione": "medicazione_lesione",
        "medicazione e controllo lesione": "medicazione_lesione",
        # pain
        "valutazione dolore cronico": "rivalutazione_dolore",
        "valutazione dolore e controllo parametri": "rivalutazione_dolore",
        "rivalutazione dolore": "rivalutazione_dolore",
        "dolore al ginocchio destro": "rivalutazione_dolore",
        "dolore al ginocchio": "rivalutazione_dolore",
        "dolore cronico": "rivalutazione_dolore",
        "dolore articolare": "rivalutazione_dolore",
        "dolore toracico": "rivalutazione_dolore",
        "dolore lombare": "rivalutazione_dolore",
        "dolore addominale": "rivalutazione_dolore",
        # devices
        "controllo e gestione catetere": "controllo_catetere",
        "controllo e gestione stomia": "controllo_stomia",
        # respiratory
        "controllo respiratorio e gestione ossigenoterapia": "controllo_respiratorio",
        "controllo respiratorio": "controllo_respiratorio",
        "dispnea": "controllo_respiratorio",
        "tosse, febbre e lieve dispnea": "controllo_respiratorio",
        # symptoms
        "riferiti sintomi generali": "sintomi_generali",
        "valutazione sintomi generali": "sintomi_generali",
        "stanchezza e scarso appetito": "sintomi_generali",
        "febbre": "sintomi_generali",
        # general / caregiver
        "educazione caregiver e controllo generale": "controllo_generale",
        "controllo generale": "controllo_generale",
        "valutazione generale": "controllo_generale",
        "valutazione delle condizioni generali": "controllo_generale",
        # falls
        "rivalutazione caduta recente": "caduta",
        "controllo post-caduta": "caduta",
    }

    if t in mapping:
        return mapping[t]

    if "lesione" in t or "ferita" in t or "medicazione" in t or "decubito" in t:
        return "medicazione_lesione"
    if "dolore" in t or "algia" in t:
        return "rivalutazione_dolore"
    if "catetere" in t:
        return "controllo_catetere"
    if "stomia" in t:
        return "controllo_stomia"
    if "ossigenoterapia" in t or "respiratorio" in t or "dispnea" in t or "affanno" in t or "tosse" in t:
        return "controllo_respiratorio"
    if "caduta" in t:
        return "caduta"
    if "terapia" in t or "farmaco" in t:
        return "controllo_terapia"
    if "parametri" in t or "segni vitali" in t or "pressione" in t:
        return "controllo_parametri"
    if "astenia" in t or "inappetenza" in t or "nausea" in t or "capogiro" in t or "appetito" in t or "stanchezza" in t or "febbre" in t:
        return "sintomi_generali"
    if "generali" in t or "controllo generale" in t or "rivalutazione clinica" in t or "valutazione generale" in t:
        return "controllo_generale"

    return t


def canonical_problem(label: str | None) -> str | None:
    if not label:
        return None

    t = str(label).strip().lower()

    mapping = {
        # pain - gold uses "dolore" not "dolore_cronico"
        "dolore": "dolore",
        "dolore_generico": "dolore",
        "dolore generico": "dolore",
        "dolore_cronico": "dolore",
        "dolore cronico": "dolore",
        "dolore cronico": "dolore",
        # wounds - gold uses "lesione_da_pressione"
        "lesione": "lesione_da_pressione",
        "lesione_cutanea": "lesione_da_pressione",
        "lesione cutanea": "lesione_da_pressione",
        "lesione_da_pressione": "lesione_da_pressione",
        "lesione da pressione": "lesione_da_pressione",
        "piaga da decubito": "lesione_da_pressione",
        "decubito": "lesione_da_pressione",
        "ferita": "lesione_da_pressione",
        "ulcera": "lesione_da_pressione",
        # falls - gold uses "caduta" not "caduta_recente"
        "caduta": "caduta",
        "caduta_recente": "caduta",
        "caduta recente": "caduta",
        "rischio_caduta": "rischio_caduta",
        # chronic conditions
        "ipertensione": "ipertensione",
        "bpco": "bpco",
        "scompenso_cardiaco": "scompenso_cardiaco",
        "scompenso cardiaco": "scompenso_cardiaco",
        "diabete_tipo_2": "diabete_tipo_2",
        "diabete tipo 2": "diabete_tipo_2",
        # symptoms
        "febbre": "febbre",
        "dispnea": "dispnea",
        "malnutrizione": "malnutrizione",
        "inappetenza": "inappetenza",
        "disidratazione": "disidratazione",
        "astenia": "astenia",
        "nausea": "nausea",
        "capogiro": "capogiro",
        "insonnia": "insonnia",
    }

    if t in mapping:
        return mapping[t]

    if "dolore" in t:
        return "dolore"
    if "lesione" in t or "ferita" in t or "ulcera" in t or "decubito" in t:
        return "lesione_da_pressione"
    if "caduta" in t:
        return "caduta"
    if "pressione" in t or "ipertension" in t:
        return "ipertensione"
    if "dispnea" in t or "bpco" in t:
        return "bpco"
    if "scompenso" in t:
        return "scompenso_cardiaco"
    if "diabete" in t or "glicemia" in t:
        return "diabete_tipo_2"
    if "inappetenza" in t or "appetito" in t:
        return "inappetenza"
    if "malnutrizione" in t:
        return "malnutrizione"
    if "disidrat" in t:
        return "disidratazione"
    if "astenia" in t or "stanchezza" in t or "debolezza" in t:
        return "astenia"
    if "nausea" in t:
        return "nausea"
    if "capogiro" in t or "vertigin" in t:
        return "capogiro"
    if "insonnia" in t:
        return "insonnia"
    if "febbre" in t:
        return "febbre"

    return t


def canonicalize_problem_list(items):
    out = []
    for item in items or []:
        c = canonical_problem(item)
        if c:
            out.append(c)
    return sorted(set(out))


def normalize_follow_up(fu):
    if fu is None:
        return None

    if isinstance(fu, str):
        s = fu.strip().lower()
        if "telefon" in s:
            return {"type": "ricontatto_telefonico", "timing_days": None, "target": None}
        if "ferita" in s or "lesione" in s:
            return {"type": "controllo_ferita", "timing_days": None}
        if "controllo" in s or "rivalutazione" in s or "monitoraggio" in s:
            return {"type": "controllo", "timing_days": None}
        return {"type": s, "timing_days": None}

    if isinstance(fu, dict):
        out = {"type": fu.get("type"), "timing_days": fu.get("timing_days")}
        if "target" in fu:
            out["target"] = fu.get("target")
        return out

    return None


def follow_up_equal(gold_fu, pred_fu):
    g = normalize_follow_up(gold_fu)
    p = normalize_follow_up(pred_fu)
    return g == p


def normalize_vitals_for_compare(vitals):
    vitals = vitals or {}

    systolic = vitals.get("blood_pressure_systolic")
    diastolic = vitals.get("blood_pressure_diastolic")

    if systolic is None or diastolic is None:
        bp = vitals.get("blood_pressure")
        if isinstance(bp, str) and "/" in bp:
            left, right = bp.split("/", 1)
            left = left.strip()
            right = right.strip()
            systolic = systolic if systolic is not None else left
            diastolic = diastolic if diastolic is not None else right

    return {
        "blood_pressure_systolic": None if systolic in ("", None) else str(systolic),
        "blood_pressure_diastolic": None if diastolic in ("", None) else str(diastolic),
        "heart_rate": None if vitals.get("heart_rate") in ("", None) else str(vitals.get("heart_rate")),
        "temperature": None if vitals.get("temperature") in ("", None) else str(vitals.get("temperature")),
        "spo2": None if vitals.get("spo2") in ("", None) else str(vitals.get("spo2")),
    }


def vitals_equal(gold_v, pred_v):
    keys = [
        "blood_pressure_systolic",
        "blood_pressure_diastolic",
        "heart_rate",
        "temperature",
        "spo2",
    ]
    gold_v = normalize_vitals_for_compare(gold_v)
    pred_v = normalize_vitals_for_compare(pred_v)

    for k in keys:
        if gold_v.get(k) != pred_v.get(k):
            return False
    return True


def f1_for_multilabel(gold_items, pred_items):
    gold_set = set(gold_items or [])
    pred_set = set(pred_items or [])

    tp = len(gold_set & pred_set)
    fp = len(pred_set - gold_set)
    fn = len(gold_set - pred_set)

    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
    return precision, recall, f1


def macro_metric_over_records(pairs, gold_getter, pred_getter):
    precisions = []
    recalls = []
    f1s = []

    for gold, pred in pairs:
        p, r, f1 = f1_for_multilabel(gold_getter(gold), pred_getter(pred))
        precisions.append(p)
        recalls.append(r)
        f1s.append(f1)

    n = len(pairs) or 1
    return sum(precisions) / n, sum(recalls) / n, sum(f1s) / n


def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    gold_files = {p.stem: p for p in GOLD_DIR.glob("ADI-*.json")}
    pred_files = {p.stem: p for p in PRED_DIR.glob("ADI-*.json")}

    common_ids = sorted(set(gold_files) & set(pred_files))
    gold_only = sorted(set(gold_files) - set(pred_files))
    pred_only = sorted(set(pred_files) - set(gold_files))

    pairs = []
    for rid in common_ids:
        gold = load_json(gold_files[rid])
        pred = load_json(pred_files[rid])
        pairs.append((gold, pred))

    n = len(pairs)

    reason_correct = 0
    follow_up_correct = 0
    vitals_correct = 0
    reason_errors = []
    vitals_errors = []

    for gold, pred in pairs:
        rid = safe_get(gold, "meta", "record_id", default="UNKNOWN")

        gold_reason = canonical_reason(safe_get(gold, "clinical", "reason_for_visit"))
        pred_reason = canonical_reason(safe_get(pred, "clinical", "reason_for_visit"))

        if gold_reason == pred_reason:
            reason_correct += 1
        else:
            reason_errors.append({
                "record_id": rid,
                "gold_reason_raw": safe_get(gold, "clinical", "reason_for_visit"),
                "pred_reason_raw": safe_get(pred, "clinical", "reason_for_visit"),
                "gold_reason_canonical": gold_reason,
                "pred_reason_canonical": pred_reason,
            })

        if follow_up_equal(
            safe_get(gold, "clinical", "follow_up"),
            safe_get(pred, "clinical", "follow_up"),
        ):
            follow_up_correct += 1

        gold_vitals = safe_get(gold, "clinical", "vitals", default={})
        pred_vitals = safe_get(pred, "clinical", "vitals", default={})

        if vitals_equal(gold_vitals, pred_vitals):
            vitals_correct += 1
        else:
            vitals_errors.append({
                "record_id": rid,
                "gold_vitals_normalized": normalize_vitals_for_compare(gold_vitals),
                "pred_vitals_normalized": normalize_vitals_for_compare(pred_vitals),
            })

    reason_acc = reason_correct / n if n else 0.0
    follow_up_acc = follow_up_correct / n if n else 0.0
    vitals_acc = vitals_correct / n if n else 0.0

    int_p, int_r, int_f1 = macro_metric_over_records(
        pairs,
        lambda g: safe_get(g, "clinical", "interventions", default=[]),
        lambda p: safe_get(p, "clinical", "interventions", default=[]),
    )

    prob_p, prob_r, prob_f1 = macro_metric_over_records(
        pairs,
        lambda g: canonicalize_problem_list(safe_get(g, "coding", "problems_normalized", default=[])),
        lambda p: canonicalize_problem_list(safe_get(p, "coding", "problems_normalized", default=[])),
    )

    metrics = {
        "records_evaluated": n,
        "reason_for_visit_accuracy": round(reason_acc, 4),
        "follow_up_accuracy": round(follow_up_acc, 4),
        "vitals_exact_match_rate": round(vitals_acc, 4),
        "interventions_macro_precision": round(int_p, 4),
        "interventions_macro_recall": round(int_r, 4),
        "interventions_macro_f1": round(int_f1, 4),
        "problems_macro_precision": round(prob_p, 4),
        "problems_macro_recall": round(prob_r, 4),
        "problems_macro_f1": round(prob_f1, 4),
        "gold_only_ids": gold_only,
        "pred_only_ids": pred_only,
        "reason_mismatches_sample": reason_errors[:15],
        "vitals_mismatches_sample": vitals_errors[:15],
    }

    metrics_path = REPORTS_DIR / "metrics.json"
    with metrics_path.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, ensure_ascii=False, indent=2)

    print(f"Wrote {metrics_path}")
    print("\nEvaluation summary")
    print(f"- records evaluated: {n}")
    print(f"- reason_for_visit accuracy: {reason_acc:.2f}")
    print(f"- follow_up accuracy: {follow_up_acc:.2f}")
    print(f"- vitals exact match rate: {vitals_acc:.2f}")
    print(f"- interventions macro F1: {int_f1:.4f} (P={int_p:.4f}, R={int_r:.4f})")
    print(f"- problems macro F1: {prob_f1:.4f} (P={prob_p:.4f}, R={prob_r:.4f})")

    if gold_only or pred_only:
        print("\nDataset alignment warnings")
        print(f"- gold only ids: {len(gold_only)}")
        print(f"- pred only ids: {len(pred_only)}")


if __name__ == "__main__":
    main()