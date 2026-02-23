# src/extract_rules.py
import re
from dateutil import parser

def extract_datetime(text: str):
    m = re.search(r"(\d{1,2}/\d{1,2}/\d{4}).*?(\d{1,2}:\d{2})", text)
    if not m:
        return None
    dt_str = f"{m.group(1)} {m.group(2)}"
    try:
        dt = parser.parse(dt_str, dayfirst=True)
        return dt.isoformat()
    except Exception:
        return None

def extract_bp(text: str):
    m = re.search(r"\bPA\s*(\d{2,3})/(\d{2,3})\b", text, flags=re.IGNORECASE)
    if not m:
        return (None, None)
    return (int(m.group(1)), int(m.group(2)))

def extract_hr(text: str):
    m = re.search(r"\bFC\s*(\d{2,3})\b", text, flags=re.IGNORECASE)
    return int(m.group(1)) if m else None

def extract_temp(text: str):
    m = re.search(r"\btemperatura\s*([0-9]{1,2}[.,][0-9])", text, flags=re.IGNORECASE)
    if not m:
        return None
    return float(m.group(1).replace(",", "."))

def extract_reason(text: str):
    m = re.search(r"Motivo della visita:\s*(.*?)(?:\.|Parametri:|$)", text, flags=re.IGNORECASE)
    return m.group(1).strip() if m else None

def extract_follow_up(text: str):
    m = re.search(r"(Programmato.*?)(?:\.|$)", text, flags=re.IGNORECASE)
    return m.group(1).strip() if m else None

def extract_interventions(text: str):
    t = text.lower()
    interventions = []
    if "medicazione" in t:
        interventions.append("medicazione")
    if "parametri" in t or "pa " in t.lower() or "fc " in t.lower():
        interventions.append("controllo_parametri_vitali")
    return interventions