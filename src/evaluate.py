"""
src/extract_rules.py
Rule-based extraction for ADI clinical notes.
Single source of truth — used by both app.py and run_pipeline.py.
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from src.italian_numbers import italian_word_to_number, extract_number_from_text


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clean(text: str) -> str:
    """Lowercase + collapse whitespace."""
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _normalize(text: str) -> str:
    """Full normalization: lowercase, accent strip, punctuation → space."""
    t = (text or "").lower()
    t = t.replace("é", "e").replace("è", "e").replace("à", "a").replace("ù", "u")
    t = re.sub(r"[^\w\s/%.'\-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _sentences(text: str) -> List[str]:
    text = (text or "").replace("\n", ". ")
    parts = re.split(r"[.;]\s+|\n+", text)
    return [_clean(p) for p in parts if _clean(p)]


def _match_any(text: str, keywords: List[str]) -> bool:
    t = _clean(text)
    return any(k in t for k in keywords)


def _match_all(text: str, keywords: List[str]) -> bool:
    t = _clean(text)
    return all(k in t for k in keywords)


# ---------------------------------------------------------------------------
# Date / time
# ---------------------------------------------------------------------------

def extract_datetime(text: str) -> Optional[str]:
    """Extract visit datetime from text like '15/02/2026 ore 10:30'."""
    patterns = [
        r"(\d{1,2}/\d{1,2}/\d{4})\s*(?:ore|alle)?\s*(\d{1,2}:\d{2})",
        r"(\d{1,2}-\d{1,2}-\d{4})\s*(?:ore|alle)?\s*(\d{1,2}:\d{2})",
    ]
    for pat in patterns:
        m = re.search(pat, text, flags=re.IGNORECASE)
        if not m:
            continue
        date_part = m.group(1).replace("-", "/")
        time_part = m.group(2)
        try:
            dt = datetime.strptime(f"{date_part} {time_part}", "%d/%m/%Y %H:%M")
            return dt.isoformat()
        except ValueError:
            continue
    return None


# ---------------------------------------------------------------------------
# Vital signs
# ---------------------------------------------------------------------------

def extract_bp(text: str) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract blood pressure as (systolic, diastolic) integers.
    Handles numeric (130/80) and spoken Italian (centotrenta su ottanta).
    Strips dates first to avoid false matches like 15/02.
    """
    t = _normalize(text)

    # Strip date patterns before looking for numeric BP
    t_no_dates = re.sub(r"\b\d{1,2}/\d{1,2}/\d{4}\b", "", t)
    t_no_dates = re.sub(r"\b\d{1,2}/\d{1,2}\b", "", t_no_dates)

    def valid(sys_v: int, dia_v: int) -> bool:
        return 70 <= sys_v <= 260 and 30 <= dia_v <= 150 and sys_v > dia_v

    def parse_num(raw: str, lo: int, hi: int) -> Optional[int]:
        raw = raw.strip()
        m = re.search(r"\b\d{2,3}\b", raw)
        if m:
            v = int(m.group(0))
            if lo <= v <= hi:
                return v
        v = italian_word_to_number(raw.replace(" ", ""))
        if v is None:
            v = extract_number_from_text(raw, lo, hi)
        return v if v is not None and lo <= v <= hi else None

    # 1) Explicit label patterns (most reliable)
    label_patterns = [
        (r"\bpressione(?:\s+arteriosa)?(?:\s+sistolica/diastolica)?\s*[:=]?\s*(\d{2,3})\s*/\s*(\d{2,3})\b", False),
        (r"\bpa\s*[:=]?\s*(\d{2,3})\s*/\s*(\d{2,3})\b", False),
        (r"\bpa\s*[:=]?\s*(\d{2,3})\s*-\s*(\d{2,3})\b", False),
        (r"\bmassima\s*[:=]?\s*([\w\s]+?)\s+(?:e\s+)?(?:la\s+)?minima\s*[:=]?\s*([\w\s]+?)(?:\s*\.|$)", False),
        (r"\bminima\s*[:=]?\s*([\w\s]+?)\s+(?:e\s+)?(?:la\s+)?massima\s*[:=]?\s*([\w\s]+?)(?:\s*\.|$)", True),
        (r"\bsistolica\s*[:=]?\s*(\d{2,3})\b.*\bdiastolica\s*[:=]?\s*(\d{2,3})\b", False),
    ]
    for pat, swap in label_patterns:
        m = re.search(pat, t_no_dates, flags=re.IGNORECASE)
        if not m:
            continue
        a = parse_num(m.group(1), 70, 260)
        b = parse_num(m.group(2), 30, 150)
        if a is None or b is None:
            continue
        sys_v, dia_v = (b, a) if swap else (a, b)
        if valid(sys_v, dia_v):
            return sys_v, dia_v

    # 2) Spoken "X su Y" — covers both numeric and words
    m = re.search(r"\b([\w]+(?:\s+[\w]+)?)\s+su\s+([\w]+(?:\s+[\w]+)?)\b", t_no_dates)
    if m:
        a = parse_num(m.group(1), 70, 260)
        b = parse_num(m.group(2), 30, 150)
        if a is not None and b is not None and valid(a, b):
            return a, b

    # 3) Bare NNN/NN — require 3-digit systolic to avoid date/time confusion
    m = re.search(r"\b(1[0-9]{2}|2[0-5][0-9])\s*/\s*(\d{2,3})\b", t_no_dates)
    if m:
        sys_v, dia_v = int(m.group(1)), int(m.group(2))
        if valid(sys_v, dia_v):
            return sys_v, dia_v

    # 4) Verbose: pressione arteriosa NNN mmHg (sistolica) e NN mmHg (diastolica)
    m = re.search(
        r"pressione arteriosa(?:\s+di)?\s*(\d{2,3})\s*mmhg\s*\(sistolica\)\s*e\s*(\d{2,3})\s*mmhg\s*\(diastolica\)",
        t_no_dates, flags=re.IGNORECASE,
    )
    if m:
        sys_v, dia_v = int(m.group(1)), int(m.group(2))
        if valid(sys_v, dia_v):
            return sys_v, dia_v

    return None, None


# Alias used in run_pipeline
extract_blood_pressure = extract_bp


def extract_hr(text: str) -> Optional[int]:
    """Extract heart rate in bpm. Handles digits and Italian words."""
    t = _normalize(text)

    numeric = [
        r"\bfc\s*[:=]?\s*(\d{2,3})\b",
        r"\bhr\s*[:=]?\s*(\d{2,3})\b",
        r"\bfrequenza\s+cardiaca(?:\s+di)?\s*(\d{2,3})\b",
        r"\b(\d{2,3})\s*bpm\b",
        r"\b(\d{2,3})\s*battiti(?:\s+al\s+minuto)?\b",
    ]
    for pat in numeric:
        m = re.search(pat, t, flags=re.IGNORECASE)
        if m:
            v = int(m.group(1))
            if 30 <= v <= 220:
                return v

    spoken = [
        r"\bfrequenza\s+cardiaca\s+([a-z]+(?:\s+[a-z]+)?)\b",
        r"\bfc\s+([a-z]+(?:\s+[a-z]+)?)\b",
        r"\b([a-z]+(?:\s+[a-z]+)?)\s+battiti(?:\s+al\s+minuto)?\b",
    ]
    for pat in spoken:
        m = re.search(pat, t, flags=re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            v = italian_word_to_number(raw.replace(" ", ""))
            if v is None:
                v = extract_number_from_text(raw, 30, 220)
            if v is not None and 30 <= v <= 220:
                return v

    return None


def extract_temp(text: str) -> Optional[float]:
    """Extract body temperature in Celsius. Handles both comma and dot decimals."""
    # Preserve decimal commas before normalization strips them
    t_raw = (text or "").lower().replace("é", "e").replace("è", "e")
    t_raw = re.sub(r"\s+", " ", t_raw).strip()

    patterns = [
        r"\btemperatura(?:\s+corporea)?\s*[:=]?\s*(\d{1,2}[.,]\d)\b",
        r"\btemp\s*[:=]?\s*(\d{1,2}[.,]\d)\b",
        r"\bt\s*[:=]?\s*(\d{1,2}[.,]\d)\b",
        r"\b(\d{1,2}[.,]\d)\s*°\s*c\b",
        r"\b(\d{1,2}[.,]\d)\s*gradi\b",
    ]
    for pat in patterns:
        m = re.search(pat, t_raw, flags=re.IGNORECASE)
        if m:
            val = float(m.group(1).replace(",", "."))
            if 33.0 <= val <= 42.5:
                return val

    return None


def extract_spo2(text: str) -> Optional[int]:
    """Extract oxygen saturation (SpO2) as integer percentage."""
    t = _normalize(text)

    numeric = [
        r"\bspo2\s*[:=]?\s*(\d{2,3})\s*%?\b",
        r"\bsato2\s*[:=]?\s*(\d{2,3})\s*%?\b",
        r"\bsaturazione(?:\s+di\s+ossigeno)?\s*[:=]?\s*(\d{2,3})\s*%?\b",
        r"\bsat\.?\s*[:=]?\s*(\d{2,3})\s*%?\b",
    ]
    for pat in numeric:
        m = re.search(pat, t, flags=re.IGNORECASE)
        if m:
            v = int(m.group(1))
            if 50 <= v <= 100:
                return v

    spoken = [
        r"\bspo2\s+([a-z]+(?:\s+[a-z]+)?)\b",
        r"\bsaturazione\s+([a-z]+(?:\s+[a-z]+)?)\b",
    ]
    for pat in spoken:
        m = re.search(pat, t, flags=re.IGNORECASE)
        if m:
            raw = m.group(1).strip()
            v = italian_word_to_number(raw.replace(" ", ""))
            if v is None:
                v = extract_number_from_text(raw, 50, 100)
            if v is not None and 50 <= v <= 100:
                return v

    return None


def extract_vitals(text: str) -> Dict[str, Any]:
    """Extract all vitals and return as a unified dict with numeric types."""
    sys_v, dia_v = extract_bp(text)
    hr = extract_hr(text)
    temp = extract_temp(text)
    spo2 = extract_spo2(text)
    return {
        "blood_pressure_systolic": sys_v,
        "blood_pressure_diastolic": dia_v,
        "heart_rate": hr,
        "temperature": temp,
        "spo2": spo2,
    }


# ---------------------------------------------------------------------------
# Reason for visit
# ---------------------------------------------------------------------------

def _reason_from_keywords(text: str) -> Optional[str]:
    t = _clean(text)

    # Specific conditions first (more precise → less precise)
    if _match_any(t, ["lesione da pressione", "piaga da decubito", "lesione da decubito", "decubito"]):
        return "medicazione e controllo lesione"
    if _match_any(t, ["dolore al ginocchio", "dolore ginocchio"]):
        return "rivalutazione dolore"
    if "dolore cronico" in t:
        return "rivalutazione dolore"
    if _match_any(t, ["stanchezza", "debolezza generale", "scarso appetito", "ridotto appetito", "inappetenza", "astenia", "capogiro", "nausea"]):
        return "valutazione sintomi generali"
    if _match_any(t, ["catetere vescicale", "catetere", "presidio urinario", "vescicale"]):
        return "controllo e gestione catetere"
    if _match_any(t, ["presidio stomale", "cute peristomale", "stomia", "colostomia", "ileostomia"]):
        return "controllo e gestione stomia"
    if _match_any(t, ["ossigenoterapia", "o2 terapia", "controllo respiratorio", "rivalutazione respiratoria", "dispnea", "affanno"]):
        return "controllo respiratorio e gestione ossigenoterapia"
    if _match_any(t, ["caduta recente", "post-caduta", "post caduta", "caduta", "scivolato", "trauma recente"]):
        return "rivalutazione caduta recente"
    if _match_any(t, ["cambio di medicazione", "cambio medicazione", "medicazione", "ferita", "ulcera", "piaga", "lesione"]):
        return "medicazione e controllo lesione"
    if _match_any(t, ["dolore", "algia", "sintomatologia algica", "nrs", "vas"]):
        if _match_any(t, ["parametri vitali", "pressione arteriosa", "frequenza cardiaca", "temperatura corporea"]):
            return "rivalutazione dolore"
        return "rivalutazione dolore"
    if _match_any(t, ["educazione del caregiver", "istruzione del caregiver", "supporto al caregiver", "caregiver", "familiare"]):
        return "educazione caregiver e controllo generale"
    if _match_any(t, [
        "monitoraggio dei parametri vitali", "monitoraggio dei parametri",
        "controllo dei parametri vitali", "controllo parametri vitali",
        "rilevazione dei parametri", "parametri vitali", "controllo parametri",
        "segni vitali", "monitoraggio segni vitali",
    ]):
        return "controllo parametri"
    if _match_any(t, ["verifica della terapia", "verifica terapia", "somministrazione", "farmaco", "terapia"]):
        return "controllo terapia e somministrazione farmaco"
    if _match_any(t, ["valutazione delle condizioni generali", "condizioni generali", "controllo generale", "valutazione generale", "rivalutazione clinica"]):
        return "controllo generale"

    return None


def extract_reason(text: str) -> Optional[str]:
    """
    Extract reason for visit.
    Tries explicit patterns first (Accesso domiciliare per...), then keyword rules.
    """
    sents = _sentences(text)
    lead_sentences = sents[:3]
    lead = " ".join(lead_sentences) if lead_sentences else text

    explicit_patterns = [
        r"\bAccesso domiciliare per\s+(.*?)(?:$|\.)",
        r"\bAccesso per\s+(.*?)(?:$|\.)",
        r"\bVisita ADI per\s+(.*?)(?:$|\.)",
        r"\bVisita per\s+(.*?)(?:$|\.)",
        r"\bVisita richiesta per\s+(.*?)(?:$|\.)",
        r"\bLa visita di oggi è stata(?:\s+occasionale)?\s+per\s+(.*?)(?:$|\.)",
        r"\bSottoposto a visita per\s+(.*?)(?:$|\.)",
        r"\bAccesso domiciliare di controllo generale per\s+(.*?)(?:$|\.)",
        r"\bAccesso domiciliare di\s+(.*?)(?:$|\.)",
        r"\bAccesso per rivalutazione\s+(.*?)(?:$|\.)",
        r"\bAccesso per monitoraggio\s+(.*?)(?:$|\.)",
    ]

    for pat in explicit_patterns:
        m = re.search(pat, lead, flags=re.IGNORECASE)
        if m:
            raw = _clean(m.group(1).strip(" .,:;"))
            result = _reason_from_keywords(raw)
            if result:
                return result

    for sent in lead_sentences:
        result = _reason_from_keywords(sent)
        if result:
            return result

    return _reason_from_keywords(text)


# Alias
extract_reason_for_visit = extract_reason


# ---------------------------------------------------------------------------
# Follow-up
# ---------------------------------------------------------------------------

def _timing_days(n: int, unit: str) -> Optional[int]:
    if "giorn" in unit:
        return n
    if "settiman" in unit:
        return n * 7
    if "mes" in unit:
        return n * 30
    return None


def _word_days(text: str) -> Optional[int]:
    word_map = {
        "due": 2, "tre": 3, "quattro": 4, "cinque": 5,
        "sei": 6, "sette": 7, "dieci": 10, "quattordici": 14,
    }
    for word, days in word_map.items():
        if re.search(rf"\b{word}\s+giorni\b", text):
            return days
        if re.search(rf"\b{word}\s+settimane\b", text):
            return days * 7
    return None


def extract_follow_up(text: str) -> Optional[Dict[str, Any]]:
    """
    Extract follow-up plan as a structured dict:
    {"type": str, "timing_days": int|None, "target": str|None}
    """
    t = _clean(text)

    def is_wound():
        return _match_any(t, ["ferita", "lesione", "ulcera", "piaga", "medicazione"])

    def is_caregiver():
        return _match_any(t, ["caregiver", "familiari", "familiare", "parenti"])

    # 1) Timed numeric patterns
    timed = [
        r"\btra\s+(\d+)\s+(giorni|settimane|mesi)\b",
        r"\bcontrollo\s+tra\s+(\d+)\s+(giorni|settimane|mesi)\b",
        r"\bricontrollo\s+tra\s+(\d+)\s+(giorni|settimane|mesi)\b",
        r"\brivalutazione\s+tra\s+(\d+)\s+(giorni|settimane|mesi)\b",
        r"\bfollow-?up\s+tra\s+(\d+)\s+(giorni|settimane|mesi)\b",
        r"\bentro\s+(\d+)\s+(giorni|settimane|mesi)\b",
        r"\bnei\s+prossimi\s+(\d+)\s+(giorni|settimane)\b",
        r"\bnelle\s+prossime\s+(\d+)\s+(settimane)\b",
        r"\bper\s+le\s+prossime\s+(\d+)\s+(giorni|settimane)\b",
        r"\bda\s+rivalutare\s+tra\s+(\d+)\s+(giorni|settimane|mesi)\b",
        r"\bin\s+(\d+)\s+(giorni|settimane|mesi)\b",
    ]
    for pat in timed:
        m = re.search(pat, t)
        if m:
            days = _timing_days(int(m.group(1)), m.group(2))
            ftype = "controllo_ferita" if is_wound() else "controllo"
            return {"type": ftype, "timing_days": days}

    # 2) Written-out numbers
    days = _word_days(t)
    if days is not None:
        ftype = "controllo_ferita" if is_wound() else "controllo"
        return {"type": ftype, "timing_days": days}

    # 3) "prossima settimana" = 7 days
    if "prossima settimana" in t or "settimana prossima" in t:
        ftype = "controllo_ferita" if is_wound() else "controllo"
        return {"type": ftype, "timing_days": 7}

    # 4) Phone contact
    if _match_any(t, ["ricontatto telefonico", "contatto telefonico", "telefon"]):
        target = "caregiver" if is_caregiver() else None
        return {"type": "ricontatto_telefonico", "timing_days": None, "target": target}

    # 5) Wound follow-up (no timing)
    if is_wound() and _match_any(t, ["controllo", "rivalutazione", "ricontrollo", "previsto", "programmato"]):
        return {"type": "controllo_ferita", "timing_days": None}

    # 6) Generic scheduled
    if _match_any(t, ["programmato", "previsto", "pianificato", "prossimo controllo",
                      "nuovo controllo", "secondo indicazioni", "al bisogno", "monitoraggio clinico"]):
        return {"type": "controllo", "timing_days": None}

    return None


# ---------------------------------------------------------------------------
# Interventions
# ---------------------------------------------------------------------------

_INTERVENTION_VOCAB = {
    "monitoraggio_parametri_vitali",
    "valutazione_generale",
    "medicazione",
    "somministrazione_farmaco",
    "monitoraggio_glicemia",
    "gestione_catetere",
    "gestione_stomia",
    "gestione_ossigenoterapia",
    "educazione_terapeutica",
}


def extract_interventions(
    text: str,
    vitals: Optional[Dict[str, Any]] = None,
    reason: Optional[str] = None,
) -> List[str]:
    """Extract interventions performed during the visit."""
    t = _clean(text)
    r = _clean(reason or "")
    found: List[str] = []

    # Vitals monitoring
    has_vitals = vitals and any(
        vitals.get(k) not in (None, "", [])
        for k in ("blood_pressure_systolic", "blood_pressure_diastolic",
                  "heart_rate", "temperature", "spo2",
                  "blood_pressure")
    )
    if has_vitals or _match_any(t, [
        "parametri rilevati", "rilevati parametri", "monitoraggio parametri",
        "controllo parametri", "parametri vitali", "segni vitali",
    ]):
        found.append("monitoraggio_parametri_vitali")

    # Wound care
    if _match_any(t, ["medicazione", "cambio medicazione", "lesione detersa", "ferita detersa", "lesione", "ferita", "ulcera", "piaga"]):
        found.append("medicazione")

    # Medication / therapy
    if _match_any(t, ["farmaco", "somministrato", "somministrazione", "terapia eseguita", "terapia praticata"]):
        found.append("somministrazione_farmaco")

    # Patient / caregiver education
    if _match_any(t, ["terapia", "aderenza terapeutica", "istruita", "educazione terapeutica",
                      "assunzione farmaci", "educato caregiver", "istruito caregiver",
                      "fornite indicazioni", "forniti consigli"]):
        found.append("educazione_terapeutica")

    # Catheter
    if _match_any(t, ["catetere", "vescicale", "sacca urine", "lavaggio catetere"]):
        found.append("gestione_catetere")

    # Stoma
    if _match_any(t, ["stomia", "presidio stomale", "sacca stomia", "placca stomia"]):
        found.append("gestione_stomia")

    # Oxygen therapy
    if _match_any(t, ["ossigenoterapia", "o2 terapia", "ossigeno terapia"]):
        found.append("gestione_ossigenoterapia")

    # Blood glucose
    if _match_any(t, ["glicemia", "glucosio capillare"]):
        found.append("monitoraggio_glicemia")

    # General assessment (or fallback)
    if _match_any(t, ["valutazione generale", "rivalutazione", "obiettività", "esame obiettivo", "controllo generale"]) or not found:
        found.append("valutazione_generale")

    # Reason-based additions
    reason_additions = {
        "lesione": "medicazione", "ferita": "medicazione",
        "catetere": "gestione_catetere", "stomia": "gestione_stomia",
        "terapia": "somministrazione_farmaco", "farmaco": "somministrazione_farmaco",
        "parametri": "monitoraggio_parametri_vitali", "segni vitali": "monitoraggio_parametri_vitali",
        "respiratorio": "gestione_ossigenoterapia", "ossigenoterapia": "gestione_ossigenoterapia",
    }
    for keyword, intervention in reason_additions.items():
        if keyword in r:
            found.append(intervention)

    # Deduplicate preserving order, filter to vocab
    seen = set()
    result = []
    for item in found:
        if item not in seen and item in _INTERVENTION_VOCAB:
            seen.add(item)
            result.append(item)
    return result


# ---------------------------------------------------------------------------
# Critical issues
# ---------------------------------------------------------------------------

def extract_critical_issues(
    text: str,
    spo2: Optional[int] = None,
) -> List[str]:
    """Detect potential clinical alerts from text + extracted SpO2."""
    t = _clean(text)
    issues: List[str] = []

    has_dyspnea = _match_any(t, ["dispnea", "affanno"])

    if spo2 is not None and spo2 < 92:
        issues.append("possibile instabilita respiratoria")

    tachy_pats = [
        r"\bfc\s*[:=]?\s*(1[1-9]\d|200)\b",
        r"\bfrequenza\s*cardiaca\s*[:=]?\s*(1[1-9]\d|200)\b",
        r"\b(1[1-9]\d|200)\s*bpm\b",
    ]
    has_tachy = any(re.search(p, t, flags=re.IGNORECASE) for p in tachy_pats)

    if has_dyspnea and spo2 is not None and spo2 < 94:
        issues.append("possibile instabilita clinica")
    elif has_dyspnea and has_tachy:
        issues.append("possibile instabilita clinica")

    if _match_any(t, ["caduta recente", "recente caduta", "post-caduta", "post caduta", "caduta domestica"]):
        issues.append("caduta_recente")

    return list(dict.fromkeys(issues))


# ---------------------------------------------------------------------------
# Anamnesis brief
# ---------------------------------------------------------------------------

def extract_anamnesis(text: str) -> Optional[str]:
    """
    Extract a brief anamnesis from the clinical note.
    Looks for patient background, medical history, and chronic conditions.
    """
    sents = _sentences(text)
    t = _clean(text)

    # Trigger keywords that signal anamnesis content
    anamnesis_triggers = [
        "paziente con", "paziente affetto", "paziente portatore",
        "anamnesi", "storia di", "storia clinica",
        "affetto da", "portatore di", "soffre di",
        "in terapia con", "in terapia domiciliare",
        "patologia nota", "diagnosi di", "follow up di",
        "ipertensione nota", "diabete noto", "bpco nota",
        "cardiopatia nota", "insufficienza renale",
        "pregressa", "pregresso",
    ]

    found_sentences = []
    for sent in sents:
        s = _clean(sent)
        if any(trigger in s for trigger in anamnesis_triggers):
            # Skip sentences that are mainly about vitals or interventions
            vital_words = ["pa ", "fc ", "spo2", "temperatura", "mmhg", "bpm"]
            if not any(v in s for v in vital_words):
                found_sentences.append(sent.strip())

    if not found_sentences:
        return None

    # Return first 2 relevant sentences joined, max 200 chars
    result = ". ".join(found_sentences[:2])
    if len(result) > 200:
        result = result[:200].rsplit(" ", 1)[0] + "..."
    return result.strip()

# ---------------------------------------------------------------------------
# Convenience: extract everything at once
# ---------------------------------------------------------------------------

def extract_all(text: str) -> Dict[str, Any]:
    """Run all extractors and return a unified dict."""
    vitals = extract_vitals(text)
    return {
        "visit_datetime": extract_datetime(text),
        "reason_for_visit": extract_reason(text),
        "anamnesis_brief": extract_anamnesis(text),
        "vitals": vitals,
        "interventions": extract_interventions(text, vitals=vitals),
        "follow_up": extract_follow_up(text),
        "critical_issues": extract_critical_issues(text, spo2=vitals.get("spo2")),
    }