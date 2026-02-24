# src/extract_rules.py
import re
from typing import Optional, Tuple, List


def _norm_space(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    # remove trailing punctuation
    s = re.sub(r"[ \t]*[.]+$", "", s)
    return s


def extract_datetime(text: str) -> Optional[str]:
    # Common formats: 24/02/2026 15:30, 24-02-2026, 24/02/26, 15:30
    m = re.search(
        r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})(?:\s+(\d{1,2}:\d{2}))?\b", text
    )
    if m:
        date = m.group(1)
        time = m.group(2)
        return f"{date} {time}" if time else date

    m = re.search(r"\b(\d{1,2}:\d{2})\b", text)
    if m:
        return m.group(1)

    return None


def extract_bp(text: str) -> Tuple[Optional[int], Optional[int]]:
    # Matches: "PA 150/95", "Pressione 120/80", "BP: 120/80"
    m = re.search(
        r"\b(?:pa|p\.a\.|pressione|bp)\b[^\d]{0,10}(\d{2,3})\s*/\s*(\d{2,3})\b",
        text,
        flags=re.IGNORECASE,
    )
    if not m:
        # fallback: bare 120/80
        m = re.search(r"\b(\d{2,3})\s*/\s*(\d{2,3})\b", text)
        if not m:
            return None, None

    return int(m.group(1)), int(m.group(2))


def extract_hr(text: str) -> Optional[int]:
    # Matches: "FC 88", "HR 88", "bpm 88"
    m = re.search(
        r"\b(?:fc|f\.c\.|hr|bpm|frequenza\s*cardiaca)\b[^\d]{0,10}(\d{2,3})\b",
        text,
        flags=re.IGNORECASE,
    )
    if not m:
        return None
    val = int(m.group(1))
    if val < 20 or val > 250:
        return None
    return val


def extract_temp(text: str) -> Optional[float]:
    # Matches: "temperatura 36,8", "Temp 37", "T 36.7"
    m = re.search(
        r"\b(?:t|temp|temperatura)\b[^\d]{0,10}(\d{2}(?:[.,]\d)?)\b",
        text,
        flags=re.IGNORECASE,
    )
    if not m:
        return None
    s = m.group(1).replace(",", ".")
    try:
        val = float(s)
    except ValueError:
        return None
    if val < 30 or val > 45:
        return None
    return val


def extract_spo2(text: str) -> Optional[int]:
    # Normalize unicode subscripts (SpO₂, O₂) -> SpO2, O2
    t = text.replace("₂", "2").replace("O₂", "O2").replace("o₂", "o2")

    patterns = [
        r"""\b(spo2|sao2|sato2|o2\s*sat|sat(?:urazione)?\s*(?:o2)?)\b[^\d]{0,10}([0-9]{2,3})\s*%?""",
        r"""\b(sat)\b[^\d]{0,10}([0-9]{2,3})\s*%?""",
    ]

    for pat in patterns:
        m = re.search(pat, t, flags=re.IGNORECASE)
        if m:
            val = int(m.group(2))
            if 50 <= val <= 100:
                return val
    return None


def extract_reason(text: str) -> Optional[str]:
    """
    Expected gold looks like short phrases, e.g.
      "controllo generale"
      "controllo pressione e rivalutazione terapia"
    Raw notes often have:
      "Motivo della visita: ...."
    """
    # Match "Motivo della visita: <...>."
    m = re.search(
        r"\bmotivo\s+della\s+visita\s*:\s*(.+?)(?:\.\s|\n|$)",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        return _norm_space(m.group(1)).lower()

    # Fallback: "Motivo: ..."
    m = re.search(
        r"\bmotivo\s*:\s*(.+?)(?:\.\s|\n|$)",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        return _norm_space(m.group(1)).lower()

    return None


def extract_follow_up(text: str) -> Optional[str]:
    """
    Gold examples:
      "programmato controllo tra 7 giorni"
      "programmato controllo tra 3 giorni"
      "programmato nuovo controllo"
    We extract only the 'Programmato ...' clause.
    """
    # Match "Programmato ...." up to period/newline/end
    m = re.search(
        r"\bprogrammato\b\s*(.+?)(?:\.\s|\n|$)",
        text,
        flags=re.IGNORECASE,
    )
    if m:
        out = "programmato " + _norm_space(m.group(1))
        return out.lower()

    return None


def extract_interventions(text: str) -> List[str]:
    """
    Must match gold labels exactly.
    Gold uses:
      - "medicazione"
      - "controllo_parametri_vitali"
    """
    t = text.lower()
    out: List[str] = []

    # medicazione / dressing / wound care
    if "medicazione" in t or "bendaggio" in t:
        out.append("medicazione")

    # vitals check / parameters
    if "parametri" in t or "pa " in t or "fc " in t or "temperatura" in t:
        out.append("controllo_parametri_vitali")

    # Deduplicate while preserving order
    seen = set()
    deduped = []
    for x in out:
        if x not in seen:
            seen.add(x)
            deduped.append(x)
    return deduped