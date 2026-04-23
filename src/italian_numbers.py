"""
src/italian_numbers.py
Convert Italian number words to integers.
Supports compound forms like centotrenta (130), settantadue (72).
"""
from __future__ import annotations

import re
from typing import Optional


UNITS = {
    "zero": 0, "uno": 1, "un": 1, "una": 1,
    "due": 2, "tre": 3, "quattro": 4, "cinque": 5,
    "sei": 6, "sette": 7, "otto": 8, "nove": 9,
}

TEENS = {
    "dieci": 10, "undici": 11, "dodici": 12, "tredici": 13,
    "quattordici": 14, "quindici": 15, "sedici": 16,
    "diciassette": 17, "diciotto": 18, "diciannove": 19,
}

TENS = {
    "venti": 20, "trenta": 30, "quaranta": 40, "cinquanta": 50,
    "sessanta": 60, "settanta": 70, "ottanta": 80, "novanta": 90,
}

HUNDREDS = {
    "cento": 100, "duecento": 200,
}


def _normalize(text: str) -> str:
    text = text.lower().strip()
    text = text.replace("é", "e").replace("è", "e")
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def italian_word_to_number(text: str) -> Optional[int]:
    """
    Convert an Italian number word (or compound) to an integer.

    Examples:
        settantadue  -> 72
        centotrenta  -> 130
        novantasette -> 97
    """
    t = _normalize(text).replace(" ", "")
    if not t:
        return None

    if t.isdigit():
        return int(t)

    for lookup in (UNITS, TEENS, TENS, HUNDREDS):
        if t in lookup:
            return lookup[t]

    # 21-99: e.g. settantadue
    for tens_word, tens_val in TENS.items():
        if t.startswith(tens_word):
            remainder = t[len(tens_word):]
            if not remainder:
                return tens_val
            if remainder in UNITS:
                return tens_val + UNITS[remainder]

    # 100-199: e.g. centotrenta
    if t.startswith("cento"):
        remainder = t[len("cento"):]
        if not remainder:
            return 100
        sub = italian_word_to_number(remainder)
        if sub is not None:
            return 100 + sub

    if t == "duecento":
        return 200

    return None


def extract_number_from_text(
    text: str,
    min_value: Optional[int] = None,
    max_value: Optional[int] = None,
) -> Optional[int]:
    """
    Find the first number in text — either as digits or Italian words.
    Optionally filter by range.
    """
    normalized = _normalize(text)

    # Try digits first
    m = re.search(r"\b\d{1,3}\b", normalized)
    if m:
        value = int(m.group(0))
        if (min_value is None or value >= min_value) and (max_value is None or value <= max_value):
            return value

    # Try single word tokens
    for word in normalized.split():
        value = italian_word_to_number(word)
        if value is not None:
            if (min_value is None or value >= min_value) and (max_value is None or value <= max_value):
                return value

    # Try joined pairs of tokens
    words = normalized.split()
    for i in range(len(words) - 1):
        joined = words[i] + words[i + 1]
        value = italian_word_to_number(joined)
        if value is not None:
            if (min_value is None or value >= min_value) and (max_value is None or value <= max_value):
                return value

    return None
