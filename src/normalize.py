"""
src/normalize.py
Label normalization for reasons, interventions, and clinical problems.
All label mappings are aligned to the gold dataset vocabulary.
"""
from __future__ import annotations

from typing import Iterable, List, Optional


def _clean(text: str) -> str:
    return " ".join((text or "").strip().lower().split())


# ---------------------------------------------------------------------------
# Reason for visit
# ---------------------------------------------------------------------------

REASON_MAP = {
    # Symptoms
    "dolore toracico": "dolore toracico",
    "dolore lombare": "dolore lombare",
    "lombalgia": "dolore lombare",
    "dolore addominale": "dolore addominale",
    "dispnea": "dispnea",
    "affanno": "dispnea",
    "febbre": "febbre",
    "tosse febbre e lieve dispnea": "tosse, febbre e lieve dispnea",
    "tosse, febbre e lieve dispnea": "tosse, febbre e lieve dispnea",

    # Parameters
    "controllo parametri": "controllo parametri",
    "controllo parametri vitali": "controllo parametri",
    "monitoraggio parametri": "controllo parametri",
    "monitoraggio parametri vitali": "controllo parametri",
    "monitoraggio dei parametri vitali": "controllo parametri",

    # General
    "valutazione generale": "controllo generale",
    "controllo generale": "controllo generale",
    "valutazione clinica generale": "controllo generale",
    "rivalutazione clinica": "controllo generale",

    # Wound
    "medicazione": "medicazione e controllo lesione",
    "controllo lesione": "medicazione e controllo lesione",
    "medicazione lesione": "medicazione e controllo lesione",
    "medicazione e controllo lesione": "medicazione e controllo lesione",
    "medicazione/controllo lesione": "medicazione e controllo lesione",
    "medicazione lesione da pressione": "medicazione e controllo lesione",
    "medicazione piaga da decubito": "medicazione e controllo lesione",

    # Therapy
    "somministrazione terapia": "controllo terapia e somministrazione farmaco",
    "somministrazione farmaco": "controllo terapia e somministrazione farmaco",
    "controllo terapia": "controllo terapia e somministrazione farmaco",
    "controllo terapia e somministrazione farmaco": "controllo terapia e somministrazione farmaco",
    "controllo terapia/somministrazione farmaco": "controllo terapia e somministrazione farmaco",
    "monitoraggio segni vitali e verifica terapia": "controllo terapia e somministrazione farmaco",

    # Falls
    "recente caduta domestica": "rivalutazione caduta recente",
    "caduta recente": "rivalutazione caduta recente",
    "controllo post caduta": "rivalutazione caduta recente",
    "controllo post-caduta": "rivalutazione caduta recente",

    # Pain
    "rivalutazione dolore": "rivalutazione dolore",
    "valutazione dolore cronico": "rivalutazione dolore",
    "valutazione dolore e controllo parametri": "rivalutazione dolore",
    "dolore al ginocchio": "rivalutazione dolore",
    "dolore al ginocchio destro": "rivalutazione dolore",

    # Devices
    "controllo e gestione catetere": "controllo e gestione catetere",
    "controllo e gestione stomia": "controllo e gestione stomia",

    # Respiratory
    "controllo respiratorio e gestione ossigenoterapia": "controllo respiratorio e gestione ossigenoterapia",
    "controllo respiratorio": "controllo respiratorio e gestione ossigenoterapia",

    # Symptoms general
    "riferiti sintomi generali": "valutazione sintomi generali",
    "valutazione sintomi generali": "valutazione sintomi generali",
    "stanchezza e scarso appetito": "valutazione sintomi generali",

    # Caregiver
    "educazione caregiver e controllo generale": "educazione caregiver e controllo generale",
}


def normalize_reason(reason: Optional[str]) -> Optional[str]:
    if not reason:
        return None
    key = _clean(reason)
    if not key:
        return None
    if key in REASON_MAP:
        return REASON_MAP[key]

    # Heuristic fallbacks
    if any(x in key for x in ["lesione", "ferita", "ulcera", "piaga", "medicazione", "decubito"]):
        return "medicazione e controllo lesione"
    if any(x in key for x in ["dolore lombare", "lombalgia"]):
        return "dolore lombare"
    if "dolore toracico" in key:
        return "dolore toracico"
    if "dolore addominale" in key:
        return "dolore addominale"
    if "dolore" in key or "algia" in key:
        return "rivalutazione dolore"
    if "dispnea" in key or "affanno" in key or "respiratori" in key:
        return "controllo respiratorio e gestione ossigenoterapia"
    if "febbre" in key:
        return "febbre"
    if "caduta" in key:
        return "rivalutazione caduta recente"
    if any(x in key for x in ["parametri", "pressione", "frequenza cardiaca", "spo2", "saturazione"]):
        return "controllo parametri"
    if any(x in key for x in ["terapia", "farmaco", "somministrazione"]):
        return "controllo terapia e somministrazione farmaco"
    if "catetere" in key:
        return "controllo e gestione catetere"
    if "stomia" in key:
        return "controllo e gestione stomia"
    if any(x in key for x in ["caregiver", "familiare"]):
        return "educazione caregiver e controllo generale"
    if any(x in key for x in ["astenia", "stanchezza", "inappetenza", "nausea", "capogiro"]):
        return "valutazione sintomi generali"

    return key


# ---------------------------------------------------------------------------
# Interventions
# ---------------------------------------------------------------------------

INTERVENTION_MAP = {
    # Vitals
    "monitoraggio parametri": "monitoraggio_parametri_vitali",
    "monitoraggio parametri vitali": "monitoraggio_parametri_vitali",
    "monitoraggio dei parametri vitali": "monitoraggio_parametri_vitali",
    "controllo parametri": "monitoraggio_parametri_vitali",
    "controllo parametri vitali": "monitoraggio_parametri_vitali",
    "rilevati parametri": "monitoraggio_parametri_vitali",
    "monitoraggio_parametri_vitali": "monitoraggio_parametri_vitali",

    # General
    "valutazione generale": "valutazione_generale",
    "valutazione clinica": "valutazione_generale",
    "valutazione clinica generale": "valutazione_generale",
    "controllo generale": "valutazione_generale",
    "valutazione_generale": "valutazione_generale",

    # Meds
    "somministrazione terapia": "somministrazione_farmaco",
    "somministrazione farmaco": "somministrazione_farmaco",
    "somministrata terapia": "somministrazione_farmaco",
    "terapia": "somministrazione_farmaco",
    "controllo terapia": "somministrazione_farmaco",
    "somministrazione_farmaco": "somministrazione_farmaco",

    # Wound
    "medicazione": "medicazione",
    "medicazione lesione": "medicazione",
    "controllo lesione": "medicazione",

    # Education
    "educazione caregiver": "educazione_terapeutica",
    "educazione sanitaria": "educazione_terapeutica",
    "educazione terapeutica": "educazione_terapeutica",
    "educazione_terapeutica": "educazione_terapeutica",

    # Devices
    "gestione catetere": "gestione_catetere",
    "gestione_catetere": "gestione_catetere",
    "gestione stomia": "gestione_stomia",
    "gestione_stomia": "gestione_stomia",
    "gestione ossigenoterapia": "gestione_ossigenoterapia",
    "gestione_ossigenoterapia": "gestione_ossigenoterapia",

    # Glucose
    "monitoraggio glicemia": "monitoraggio_glicemia",
    "monitoraggio_glicemia": "monitoraggio_glicemia",
}


def normalize_interventions(interventions: Optional[Iterable[str]]) -> List[str]:
    if not interventions:
        return []

    normalized: List[str] = []
    for item in interventions:
        key = _clean(str(item))
        if not key:
            continue
        mapped = INTERVENTION_MAP.get(key)
        if mapped is None:
            # Heuristic fallback
            if any(x in key for x in ["parametri", "pressione", "frequenza cardiaca", "spo2", "saturazione", "temperatura"]):
                mapped = "monitoraggio_parametri_vitali"
            elif any(x in key for x in ["medicazione", "ferita", "lesione", "ulcera", "piaga"]):
                mapped = "medicazione"
            elif any(x in key for x in ["somministrazione", "farmaco"]):
                mapped = "somministrazione_farmaco"
            elif any(x in key for x in ["caregiver", "educazione"]):
                mapped = "educazione_terapeutica"
            elif any(x in key for x in ["catetere"]):
                mapped = "gestione_catetere"
            elif any(x in key for x in ["stomia"]):
                mapped = "gestione_stomia"
            elif any(x in key for x in ["ossigenoterapia"]):
                mapped = "gestione_ossigenoterapia"
            elif any(x in key for x in ["glicemia"]):
                mapped = "monitoraggio_glicemia"
            elif any(x in key for x in ["valutazione", "controllo generale"]):
                mapped = "valutazione_generale"
            else:
                mapped = key
        normalized.append(mapped)

    return _unique_keep_order(normalized)


# ---------------------------------------------------------------------------
# Clinical problems
# ---------------------------------------------------------------------------

# Labels aligned to gold dataset vocabulary and problem_lexicon.py
PROBLEM_MAP = {
    # Pain
    "dolore": "dolore",
    "dolore cronico": "dolore",
    "dolore_cronico": "dolore",
    "dolore generico": "dolore",
    "dolore_generico": "dolore",
    "dolore toracico": "dolore",
    "dolore lombare": "dolore",
    "lombalgia": "dolore",
    "dolore addominale": "dolore",
    "dolore al ginocchio": "dolore",

    # Wounds — gold uses "lesione_da_pressione"
    "ferita": "lesione_da_pressione",
    "lesione": "lesione_da_pressione",
    "lesione cutanea": "lesione_da_pressione",
    "lesione_cutanea": "lesione_da_pressione",
    "lesione da pressione": "lesione_da_pressione",
    "lesione_da_pressione": "lesione_da_pressione",
    "lesione da decubito": "lesione_da_pressione",
    "piaga da decubito": "lesione_da_pressione",
    "ulcera": "lesione_da_pressione",
    "piaga": "lesione_da_pressione",
    "decubito": "lesione_da_pressione",

    # Falls — gold uses "caduta" not "caduta_recente"
    "caduta": "caduta",
    "caduta recente": "caduta",
    "caduta_recente": "caduta",
    "caduta domestica": "caduta",
    "rischio caduta": "rischio_caduta",
    "rischio_caduta": "rischio_caduta",

    # Cardiac
    "ipertensione": "ipertensione",
    "ipertensione arteriosa": "ipertensione",
    "pressione alta": "ipertensione",
    "scompenso cardiaco": "scompenso_cardiaco",
    "scompenso_cardiaco": "scompenso_cardiaco",
    "insufficienza cardiaca": "scompenso_cardiaco",

    # Respiratory
    "dispnea": "dispnea",
    "affanno": "dispnea",
    "bpco": "bpco",
    "bronchite cronica": "bpco",

    # Metabolic
    "diabete": "diabete_tipo_2",
    "diabete tipo 2": "diabete_tipo_2",
    "diabete_tipo_2": "diabete_tipo_2",
    "diabete mellito tipo 2": "diabete_tipo_2",

    # Symptoms
    "febbre": "febbre",
    "astenia": "astenia",
    "stanchezza": "astenia",
    "debolezza": "astenia",
    "nausea": "nausea",
    "capogiro": "capogiro",
    "vertigini": "capogiro",
    "insonnia": "insonnia",

    # Nutrition / hydration
    "inappetenza": "inappetenza",
    "scarso appetito": "inappetenza",
    "ridotto appetito": "inappetenza",
    "malnutrizione": "malnutrizione",
    "disidratazione": "disidratazione",
    "poca idratazione": "disidratazione",
}


def normalize_problems(text_or_items) -> List[str]:
    """
    Normalize clinical problems.

    Accepts either:
    - a free-text string (keyword scan)
    - a list of raw problem labels
    """
    if text_or_items is None:
        return []

    found: List[str] = []

    if isinstance(text_or_items, str):
        t = _clean(text_or_items)
        for raw, mapped in PROBLEM_MAP.items():
            if raw in t:
                found.append(mapped)
        return _unique_keep_order(found)

    for item in text_or_items:
        key = _clean(str(item))
        if not key:
            continue
        mapped = PROBLEM_MAP.get(key)
        if mapped is None:
            # Heuristic fallback
            if "dolore" in key or "algia" in key:
                mapped = "dolore"
            elif any(x in key for x in ["lesione", "ferita", "ulcera", "decubito", "piaga"]):
                mapped = "lesione_da_pressione"
            elif "caduta" in key:
                mapped = "caduta"
            elif "ipertension" in key or "pressione alta" in key:
                mapped = "ipertensione"
            elif "dispnea" in key or "affanno" in key:
                mapped = "dispnea"
            elif "bpco" in key:
                mapped = "bpco"
            elif "scompenso" in key:
                mapped = "scompenso_cardiaco"
            elif "diabete" in key or "glicemia" in key:
                mapped = "diabete_tipo_2"
            elif "astenia" in key or "stanchezza" in key or "debolezza" in key:
                mapped = "astenia"
            elif "nausea" in key:
                mapped = "nausea"
            elif "capogiro" in key or "vertigine" in key:
                mapped = "capogiro"
            elif "inappetenza" in key or "appetito" in key:
                mapped = "inappetenza"
            elif "malnutrizione" in key:
                mapped = "malnutrizione"
            elif "disidrat" in key:
                mapped = "disidratazione"
            elif "insonnia" in key:
                mapped = "insonnia"
            elif "febbre" in key:
                mapped = "febbre"
            else:
                mapped = key
        found.append(mapped)

    return _unique_keep_order(found)


# ---------------------------------------------------------------------------
# Internal utility
# ---------------------------------------------------------------------------

def _unique_keep_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for item in items:
        key = _clean(item)
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item)
    return out
