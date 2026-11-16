"""Knowledge layer for the LLM: retrieve guidance lines from a reviewed reference, leave-one-out.

kind="wiki": structured lines taken from the concept wiki  -> "frase" -> concept: value
kind="raw" : plain sentences of other notes (conventional retrieval, no structure)

The note being processed is always excluded (exclude_id), so a note can never see its own label.
Deterministic: same inputs give the same context string (needed for the LLM cache and manifest).
"""
from __future__ import annotations

import hashlib
import math
import re
from collections import Counter
from typing import Dict, List, Sequence, Tuple

from src.wiki import CONCEPTS, _sentences, facts_from_record

KINDS = ("wiki", "raw")
HEADER = ("ESEMPI da altre note gia' verificate. Usali solo per imparare formulazioni ed etichette; "
          "non copiare valori da qui: estrai SOLO dal TEXT qui sotto.")
_TOK = re.compile(r"[a-zàèéìòù0-9]{3,}")


def _tokens(s: str) -> List[str]:
    return _TOK.findall(s.lower())


class KnowledgeLayer:
    def __init__(self, reference: Sequence[Tuple[dict, str]], kind: str = "wiki",
                 k: int = 10, per_concept: int = 2, max_chars: int = 1800):
        if kind not in KINDS:
            raise ValueError(f"kind must be one of {KINDS}")
        self.kind, self.k, self.per_concept, self.max_chars = kind, k, per_concept, max_chars
        self.entries: List[Dict[str, str]] = []
        seen = set()
        for rec, text in reference:
            rid = rec["meta"]["record_id"]
            if kind == "wiki":
                for concept, value, ev in facts_from_record(rec, text):
                    if not ev:
                        continue
                    key = (concept, value, ev)
                    if key in seen:
                        continue
                    seen.add(key)
                    self.entries.append({"id": rid, "concept": concept, "value": value, "ev": ev})
            else:
                for s in _sentences(text):
                    if s in seen:
                        continue
                    seen.add(s)
                    self.entries.append({"id": rid, "concept": "", "value": "", "ev": s})
        df = Counter(t for e in self.entries for t in set(_tokens(e["ev"])))
        n = max(len(self.entries), 1)
        self.idf = {t: math.log(1 + n / c) for t, c in df.items()}

    def _score(self, q: Counter, ev: str) -> float:
        d = Counter(_tokens(ev))
        if not d:
            return 0.0
        num = sum(q[t] * d[t] * self.idf.get(t, 0.0) ** 2 for t in d if t in q)
        den = math.sqrt(sum((q[t] * self.idf.get(t, 0.0)) ** 2 for t in q)) * \
            math.sqrt(sum((d[t] * self.idf.get(t, 0.0)) ** 2 for t in d))
        return num / den if den else 0.0

    def context(self, text: str, exclude_id: str) -> str:
        q = Counter(_tokens(text))
        scored = sorted(((-self._score(q, e["ev"]), e["id"], e["concept"], e["value"], e["ev"])
                         for e in self.entries if e["id"] != exclude_id))
        scored = [s for s in scored if s[0] < 0]
        lines: List[str] = []
        if self.kind == "wiki":
            used: Counter = Counter()
            for _, _, concept, value, ev in scored:
                if used[concept] >= self.per_concept:
                    continue
                used[concept] += 1
                lines.append(f'- "{ev}" -> {CONCEPTS[concept]}: {value}')
        else:
            lines = [f'- "{ev}"' for _, _, _, _, ev in scored[: self.k]]
        if not lines:
            return ""
        kept, size = [], len(HEADER)
        for ln in lines:  # lines are ranked best-first; drop the tail so the prompt stays inside the model window
            if size + len(ln) + 1 > self.max_chars:
                break
            kept.append(ln)
            size += len(ln) + 1
        return "\n".join([HEADER, *kept]) if kept else ""

    def fingerprint(self) -> str:
        h = hashlib.sha256()
        for e in self.entries:
            h.update("\0".join([e["id"], e["concept"], e["value"], e["ev"]]).encode("utf-8") + b"\n")
        return h.hexdigest()
