# src/extract_rules.py
import re
from dateutil import parser


# ----------------------------
# DATETIME
# ----------------------------
def extract_datetime(text: str):
    """
    Extract datetime from patterns like:
      - 24/02/2026 09:10
      - 24/02/2026 ore 09:10
      - Visita ... del 24/02/2026 alle 10:00
    Returns ISO string if possible, else None.
    """
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
    Extract blood pressure safely (avoid matching dates like 24/02/2026).

    Handles:
      - PA 135/80
      - PA135/80
      - Pressione 135-80
      - 135/80 mmHg
      - Valori: 128/76
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    bp_patterns = [
        re.compile(r"\bPA\s*[:=]?\s*(\d{2,3})\s*/\s*(\d{2,3})\b", re.IGNORECASE),
        re.compile(r"\bPA\s*(\d{2,3})\s*/\s*(\d{2,3})\b", re.IGNORECASE),
        re.compile(r"\bpressione\s*(\d{2,3})\s*[-/]\s*(\d{2,3})\b", re.IGNORECASE),
        re.compile(r"\b(\d{2,3})\s*/\s*(\d{2,3})\s*(?:mmhg)?\b", re.IGNORECASE),
        re.compile(r"\b(\d{2,3})\s*-\s*(\d{2,3})\b", re.IGNORECASE),  # last resort
    ]

    allowed_cues = ("pa", "pressione", "parametri", "valori", "mmhg", "fc", "bpm", "temp", " t ")

    for line in lines:
        low = line.lower()

        # Only consider "clinical looking" lines
        if not any(cue in low for cue in allowed_cues):
            continue

        # If the line contains a date like 24/02/2026, ignore unless explicitly BP-cued
        if re.search(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", line):
            if "pa" not in low and "pressione" not in low:
                continue

        for pat in bp_patterns:
            m = pat.search(line)
            if m:
                sys = int(m.group(1))
                dia = int(m.group(2))

                # Sanity checks
                if 70 <= sys <= 250 and 40 <= dia <= 150:
                    return sys, dia

    return None, None


# ----------------------------
# HEART RATE
# ----------------------------
def extract_hr(text: str):
    """
    Handles:
      - FC 76
      - FC=74
      - frequenza 80 bpm
      - HR 80
    """
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
    """
    Handles:
      - temperatura 36.5
      - temp 36,6
      - T 36.4
    """
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
    """
    Handles:
      - SpO2 98
      - SatO2 97%
      - saturazione 96
    Returns integer or None.
    """
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
# REASON FOR VISIT (UPGRADED)
# ----------------------------
def extract_reason(text: str):
    """
    Primary:
      - Motivo della visita: ...
      - Motivo: ...

    Secondary:
      - Paziente riferisce ...
      - Riferisce ...
      - Riferito ...

    Fallback:
      - choose first meaningful sentence after datetime line containing key words.
    """
    # 1) Primary: Motivo
    m = re.search(r"\bMotivo(?: della visita)?\s*:\s*(.*?)(?:\.|\n|$)", text, flags=re.IGNORECASE)
    if m:
        reason = m.group(1).strip()
        return reason if reason else None

    # 2) Secondary: (Paziente )?riferisce ...
    m = re.search(r"\b(?:Paziente\s+)?Riferisce\s+(.*?)(?:\.|\n|$)", text, flags=re.IGNORECASE)
    if m:
        reason = m.group(1).strip()
        return reason if reason else None

    # 3) Secondary: Riferito ...
    m = re.search(r"\bRiferito\s+(.*?)(?:\.|\n|$)", text, flags=re.IGNORECASE)
    if m:
        reason = m.group(1).strip()
        return reason if reason else None

    # 4) Fallback: first "reason-like" line
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines:
        low = line.lower()

        # skip header/datetime lines
        if re.search(r"\b\d{1,2}/\d{1,2}/\d{4}\b", line) and re.search(r"\b\d{1,2}:\d{2}\b", line):
            continue
        if low.startswith(("visita",)):
            continue

        # reason keywords
        if any(k in low for k in [
            "controllo", "monitoraggio", "rivalutazione", "dolore", "caduta",
            "medicazione", "verifica", "stanchezza", "appetito"
        ]):
            return line.rstrip(".")
    return None


# ----------------------------
# FOLLOW UP
# ----------------------------
def extract_follow_up(text: str):
    """
    Handles:
      - Programmato nuovo controllo...
      - Follow up: ...
      - Follow-up: ...
      - controllo tra X giorni / prossima settimana
      - ricontatto telefonico ...
    """
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

        # If Follow up had a capturing group, return that group
        if m.lastindex and m.lastindex >= 1:
            val = m.group(1).strip()
            return val if val else None

        # Otherwise return entire matched phrase
        val = m.group(0).strip().rstrip(".")
        return val if val else None

    return None


# ----------------------------
# INTERVENTIONS (baseline)
# ----------------------------
def extract_interventions(text: str):
    """
    Minimal keyword-based interventions.
    """
    t = text.lower()
    interventions = []

    if "medicazione" in t:
        interventions.append("medicazione")

    # parameter/vitals check
    if (
        "parametri" in t
        or "pa" in t
        or "pressione" in t
        or "fc" in t
        or "bpm" in t
        or "temperatura" in t
        or "temp" in t
        or "spo2" in t
        or "saturazione" in t
        or "sato2" in t
    ):
        interventions.append("controllo_parametri_vitali")

    # remove duplicates but keep order
    seen = set()
    out = []
    for x in interventions:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out