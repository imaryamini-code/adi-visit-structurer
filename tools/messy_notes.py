"""Make a 'messy' copy of the 100 synthetic notes to test how the pipeline copes with untidy writing.

    python3 -m tools.messy_notes            # writes data/synthetic/raw_messy/ and a manifest

Every clinical fact is kept (numbers, units and dates are never touched), so the original gold labels
still apply. What changes is the writing, in ways that real notes show:
  - typos in words of 5+ letters (swap two neighbouring letters, drop a letter, double a letter)
  - nurse shorthand (pressione arteriosa -> PA, frequenza cardiaca -> FC, paziente -> pz, ...)
  - lost accents and apostrophes, some lower-casing, double spaces, a missing full stop
A fixed seed makes it reproducible. This is a stress test on synthetic notes, not real clinical text.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from pathlib import Path

RAW = Path("data/synthetic/raw")
OUT = Path("data/synthetic/raw_messy")
SEED = 20261122
TYPO_RATE = 0.06

SHORTHAND = [
    (r"\bpressione arteriosa\b", "PA"), (r"\bfrequenza cardiaca\b", "FC"),
    (r"\btemperatura corporea\b", "TC"), (r"\bsaturazione\b", "sat."),
    (r"\bil paziente\b", "il pz"), (r"\bla paziente\b", "la pz"), (r"\bpaziente\b", "pz"),
    (r"\bdomiciliare\b", "dom."), (r"\bcontrollo\b", "ctrl"), (r"\bmedicazione\b", "medic."),
]
ACCENTS = str.maketrans("àèéìòù", "aeeiou")


def typo(word: str, rng: random.Random) -> str:
    i = rng.randrange(1, len(word) - 1)
    kind = rng.choice(["swap", "drop", "double"])
    if kind == "swap":
        return word[:i] + word[i + 1] + word[i] + word[i + 2:]
    if kind == "drop":
        return word[:i] + word[i + 1:]
    return word[:i] + word[i] + word[i:]


def messy(text: str, rng: random.Random) -> str:
    for pat, rep in SHORTHAND:
        if rng.random() < 0.7:
            text = re.sub(pat, rep, text, flags=re.I)

    def mutate(m: re.Match) -> str:
        w = m.group(0)
        return typo(w, rng) if len(w) >= 5 and rng.random() < TYPO_RATE else w
    # letters only: tokens with digits (values, units next to numbers, dates) are never touched
    text = re.sub(r"(?<![\w/,.])[A-Za-zÀ-ÿ]{5,}(?![\w/,.]*\d)", mutate, text)
    if rng.random() < 0.6:
        text = text.translate(ACCENTS).replace("'", " ")
    if rng.random() < 0.3:
        text = text.lower()
    if rng.random() < 0.5:
        text = re.sub(r"\. ", ".  ", text, count=rng.randint(1, 3))
    if rng.random() < 0.3:
        text = text.rstrip().rstrip(".")
    return text


def numbers(text: str):
    return re.findall(r"\d+(?:[.,]\d+)?", text)


def main() -> None:
    argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter).parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(SEED)
    changed = 0
    for p in sorted(RAW.glob("ADI-*.txt")):
        src = p.read_text(encoding="utf-8")
        out = messy(src, rng)
        assert numbers(src) == numbers(out), f"numbers changed in {p.name}"
        (OUT / p.name).write_text(out, encoding="utf-8")
        changed += out != src
    files = sorted(OUT.glob("ADI-*.txt"))
    digest = hashlib.sha256(b"".join(f.read_bytes() for f in files)).hexdigest()
    (OUT / "MANIFEST.json").write_text(json.dumps(
        {"seed": SEED, "typo_rate": TYPO_RATE, "notes": len(files), "notes_changed": changed,
         "sha256_of_all_notes": digest, "source": str(RAW)}, indent=2) + "\n", encoding="utf-8")
    print(f"{len(files)} notes written to {OUT}, {changed} differ from the originals, sha256 {digest[:12]}")


if __name__ == "__main__":
    main()
