# src/extract_rules.py
import re
from dateutil import parser


# ----------------------------
# DATETIME
# ----------------------------
def extract_datetime(text: str):
    patterns = [
        r"(\d{1,2}/\d{1,2}/\d{4})\s*(?:ore|alle)?\s*(\d{1,2}:\d{2})",
    ]
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            dt_str = f"{m.group(1)} {m.group(2)}"
            try:
                dt = parser.parse(dt_str, dayfirst=True)
                return dt.isoformat()
            except Exception:
                return None
    return None


# ----------------------------
# BLOOD PRESSURE (SAFE)
# ----------------------------
def extract_bp(text: str):
    """
    Safe BP extraction that avoids matching dates like 24/02/2026.
    Handles PA 135/80, PA135/80, Pressione 135-80, 135/80 mmHg, Valori: 128/76
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    bp_patterns = [
        re.compile(r"\bPA\s*[:=]?\s*(\d{2,3})\s*/\s*(\d{2,3})\b", re.IGNORECASE),
        re.compile(r"\bPA\s*(\d{2,3})\s*/\s*(\d{2,3})\b", re.IGNORECASE),
        re.compile(r"\bpressione\s*(\d{2,3})\s*[-/]\s*(\d{2,3})\b", re.IGNORECASE),
        re.compile(r"\b(\d{2,3})\s*/\s*(\d{2,3})\s*(?:mmhg)?\b", re.IGNORECASE),
        re.compile(r"\b(\d{2,3})\s*-\s*(\d{2,3})\b", re.IGNORECASE),
    ]

    allowed_cues = ("pa", "pressione", "parametri", "valori", "mmhg", "fc", "bpm", "temp", " t ", "spo2", "saturazione", "sato2")

    for line in lines:
        low = line.lower()

        if not any(cue in low for cue in allowed_cues):
            continue

        # Avoid date lines unless explicitly BP-cued
        if re.search(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", line):
            if "pa" not in low and "pressione" not in low:
                continue

        for pat in bp_patterns:
            m = pat.search(line)
            if m:
                sys = int(m.group(1))
                dia = int(m.group(2))
                if 70 <= sys <= 250 and 40 <= dia <= 150:
                    return sys, dia

    return None, None


# ----------------------------
# HEART RATE
# ----------------------------
def extract_hr(text: str):
    patterns = [
        r"\bFC\s*[:=]?\s*(\d{2,3})\b",
        r"\bHR\s*[:=]?\s*(\d{2,3})\b",
        r"\bfrequenza\s*(\d{2,3})\s*(?:bpm)?\b",
        r"\b(\d{2,3})\s*bpm\b",
    ]
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            v = int(m.group(1))
            if 30 <= v <= 220:
                return v
    return None


# ----------------------------
# TEMPERATURE
# ----------------------------
def extract_temp(text: str):
    patterns = [
        r"\btemperatura\s*[:=]?\s*([0-9]{1,2}[.,][0-9])\b",
        r"\btemp\s*[:=]?\s*([0-9]{1,2}[.,][0-9])\b",
        r"\bT\s*[:=]?\s*([0-9]{1,2}[.,][0-9])\b",
    ]
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            val = float(m.group(1).replace(",", "."))
            if 30.0 <= val <= 43.0:
                return val
    return None


# ----------------------------
# SpO2
# ----------------------------
def extract_spo2(text: str):
    patterns = [
        r"\bSpO2\s*[:=]?\s*(\d{2,3})\s*%?\b",
        r"\bSatO2\s*[:=]?\s*(\d{2,3})\s*%?\b",
        r"\bsaturazione\s*[:=]?\s*(\d{2,3})\s*%?\b",
    ]
    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if m:
            v = int(m.group(1))
            if 50 <= v <= 100:
                return v
    return None


# ----------------------------
# REASON FOR VISIT (ROBUST)
# ----------------------------
def extract_reason(text: str):
    # Primary: Motivo
    m = re.search(r"\bMotivo(?: della visita)?\s*:\s*(.*?)(?:\.|\n|$)", text, flags=re.IGNORECASE)
    if m:
        reason = m.group(1).strip()
        return reason if reason else None

    # Secondary: (Paziente )?Riferisce ...
    m = re.search(r"\b(?:Paziente\s+)?Riferisce\s+(.*?)(?:\.|\n|$)", text, flags=re.IGNORECASE)
    if m:
        reason = m.group(1).strip()
        return reason if reason else None

    # Secondary: Riferito ...
    m = re.search(r"\bRiferito\s+(.*?)(?:\.|\n|$)", text, flags=re.IGNORECASE)
    if m:
        reason = m.group(1).strip()
        return reason if reason else None

    # Fallback: first reason-like line
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines:
        low = line.lower()

        # skip header/datetime
        if re.search(r"\b\d{1,2}/\d{1,2}/\d{4}\b", line) and re.search(r"\b\d{1,2}:\d{2}\b", line):
            continue
        if low.startswith("visita"):
            continue

        if any(k in low for k in [
            "controllo", "monitoraggio", "rivalutazione", "dolore", "caduta",
            "medicazione", "verifica", "stanchezza", "appetito"
        ]):
            return line.rstrip(".")
    return None


# ----------------------------
# FOLLOW UP (ROBUST)
# ----------------------------
def extract_follow_up(text: str):
    patterns = [
        r"\bProgrammato\b.*?(?:\.|\n|$)",
        r"\bFollow[-\s]?up\s*:\s*(.*?)(?:\.|\n|$)",
        r"\bcontrollo\b.*?\b(prossima settimana|tra\s+\d+\s+giorni)\b.*?(?:\.|\n|$)",
        r"\bricontatto\b.*?(?:\.|\n|$)",
    ]

    for p in patterns:
        m = re.search(p, text, flags=re.IGNORECASE)
        if not m:
            continue

        if m.lastindex and m.lastindex >= 1:
            val = m.group(1).strip()
            return val if val else None

        val = m.group(0).strip().rstrip(".")
        return val if val else None

    return None


# ----------------------------
# INTERVENTIONS (SAFE, NO HALLUCINATION)
# ----------------------------
def extract_interventions(text: str, vitals: dict | None = None):
    """
    Adds 'controllo_parametri_vitali' ONLY if:
      - at least one vital value exists, OR
      - the text explicitly states that vitals/parameters were measured.
    """
    t = text.lower()
    interventions = []

    if "medicazione" in t:
        interventions.append("medicazione")

    explicit_parametri = any(
        k in t for k in [
            "rilevati parametri", "rilevazione parametri", "controllo parametri",
            "monitoraggio segni vitali", "misurati parametri", "parametri rilevati"
        ]
    )

    any_vital_present = False
    if vitals:
        any_vital_present = any(
            vitals.get(k) is not None
            for k in ["blood_pressure_systolic", "blood_pressure_diastolic", "heart_rate", "temperature", "spo2"]
        )

    if explicit_parametri or any_vital_present:
        interventions.append("controllo_parametri_vitali")

    # remove duplicates but keep order
    seen = set()
    out = []
    for x in interventions:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out