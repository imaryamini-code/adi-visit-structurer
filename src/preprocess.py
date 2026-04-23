"""
src/preprocess.py
Text cleaning and normalization for ADI clinical notes.
"""
import re


_WRAPPER_PATTERNS = [
    r"^Ecco la nota clinica domiciliare ADI in italiano,\s*resa più naturale e professionale:\s*",
    r"^Ecco la nota clinica domiciliare ADI in italiano:\s*",
    r"^Ecco la nota clinica domiciliare in italiano:\s*",
    r"^Ecco la versione rivista della nota clinica in italiano:\s*",
    r"^Ecco la nota clinica domiciliare:\s*",
    r"^Nota clinica domiciliare ADI:\s*",
    r"^Nota clinica domiciliare:\s*",
]


def preprocess_text(text: str) -> str:
    """
    Strip LLM wrapper phrases and trailing notes from synthetic dictations,
    then normalize whitespace.
    """
    if not text:
        return ""

    t = text.strip()

    for pattern in _WRAPPER_PATTERNS:
        t = re.sub(pattern, "", t, flags=re.IGNORECASE)

    # Truncate at trailing "Nota:" sections added by the LLM
    t = re.split(r"\bNota:\b", t, flags=re.IGNORECASE)[0]

    t = re.sub(r"\s+", " ", t).strip()
    return t


# Aliases for compatibility with run_pipeline._pick_callable
preprocess = preprocess_text
clean_text = preprocess_text
clean = preprocess_text
normalize_text = preprocess_text
prepare_text = preprocess_text
