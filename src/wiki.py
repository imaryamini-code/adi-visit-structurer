"""WikiLLM-style Markdown knowledge layer (prototype).

Builds a persistent Markdown wiki from structured ADI records, in one of three
organisations, always keeping provenance: every fact line ends with
``[source: ADI-xxxx]`` and (when found) a short evidence quote from the original note.

Layouts
  document : one .md per source note (A)
  concept  : one .md per clinical concept, aggregating across notes (B)
  patient  : one .md per patient, concept sub-sections per visit (C)

Only deterministic code here (no LLM), so a wiki can be rebuilt byte-for-byte.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

LAYOUTS = ("document", "concept", "patient")

# concept key -> title (order = order of sections)
CONCEPTS: Dict[str, str] = {
    "reason": "Motivo della visita",
    "vitals": "Misurazioni e parametri vitali",
    "interventions": "Trattamenti e interventi",
    "follow_up": "Follow-up",
    "problems": "Problemi clinici (codificati)",
    "critical": "Criticità",
}

Fact = Tuple[str, str, Optional[str]]  # (concept, text, evidence)


def _sentences(text: str) -> List[str]:
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


def _evidence(text: str, needles: Iterable[str]) -> Optional[str]:
    """First sentence of the raw note containing any needle (numbers / cues)."""
    sents = _sentences(text)
    for n in needles:
        if not n:
            continue
        for s in sents:
            if n.lower() in s.lower():
                return s[:240]
    return None


_STOP = {"generale", "generali", "della", "delle", "dello", "degli", "visita", "controllo"}


def _stems(label: str) -> List[str]:
    """Word stems (first 5 letters) of a label, ignoring very generic words."""
    words = re.findall(r"[a-zàèéìòù]{5,}", label.lower().replace("_", " "))
    return [w[:5] for w in words if w not in _STOP]


def _evidence_by_stems(text: str, label: str) -> Optional[str]:
    """Sentence with the most label stems; needs >=1 hit. Best-effort, can return None."""
    stems = _stems(label)
    best, best_n = None, 0
    for s in _sentences(text):
        low = s.lower()
        n = sum(1 for st in set(stems) if st in low)
        if n > best_n:
            best, best_n = s, n
    return best[:240] if best else None


def _num(v) -> List[str]:
    if v is None:
        return []
    s = str(v)
    return [s, s.replace(".", ",")] if "." in s else [s]


def facts_from_record(rec: dict, text: str = "") -> List[Fact]:
    c = rec.get("clinical", {})
    out: List[Fact] = []

    if c.get("reason_for_visit"):
        out.append(("reason", c["reason_for_visit"],
                    _evidence_by_stems(text, c["reason_for_visit"]) or _evidence(text, ["visita", "motivo"])))

    v = c.get("vitals") or {}
    parts, needles = [], []
    sys_, dia = v.get("blood_pressure_systolic"), v.get("blood_pressure_diastolic")
    if sys_ is not None and dia is not None:
        parts.append(f"PA {sys_}/{dia} mmHg")
        needles += [f"{sys_}/{dia}"]
    for key, label, unit in (("heart_rate", "FC", "bpm"), ("temperature", "T", "°C"), ("spo2", "SpO2", "%")):
        if v.get(key) is not None:
            parts.append(f"{label} {v[key]} {unit}")
            needles += _num(v[key])
    if parts:
        out.append(("vitals", ", ".join(parts), _evidence(text, needles)))

    for iv in c.get("interventions") or []:
        out.append(("interventions", iv.replace("_", " "), _evidence_by_stems(text, iv)))

    fu = c.get("follow_up") or {}
    if fu.get("type") or fu.get("timing_days") is not None:
        t = fu.get("type") or "controllo"
        d = fu.get("timing_days")
        out.append(("follow_up", f"{t}" + (f" entro {d} giorni" if d is not None else ""),
                    _evidence(text, ["controllo", "prossima", "settiman", "giorni"])))

    for p in (rec.get("coding") or {}).get("problems_normalized") or []:
        label = p if isinstance(p, str) else (p.get("label") or p.get("code") or json.dumps(p, ensure_ascii=False))
        out.append(("problems", str(label), _evidence_by_stems(text, str(label))))

    for ci in c.get("critical_issues") or []:
        out.append(("critical", str(ci), _evidence_by_stems(text, str(ci))))
    return out


def _line(fact: Fact, rid: str, *, with_id: bool = False, date: str = "") -> str:
    concept, txt, ev = fact
    head = f"- {rid} · {date} · " if with_id else "- "
    tail = f" [source: {rid}]"
    if ev:
        tail += f' — evidenza: "{ev}"'
    return head + txt + tail


def _date(rec: dict) -> str:
    return (rec.get("meta", {}).get("visit_datetime") or "")[:10]


def load_records(pred_dir: Path, raw_dir: Path) -> List[Tuple[dict, str]]:
    out = []
    for f in sorted(Path(pred_dir).glob("ADI-*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        rawf = Path(raw_dir) / f"{f.stem}.txt"
        text = rawf.read_text(encoding="utf-8") if rawf.exists() else ""
        out.append((rec, text))
    return out


def build_wiki(records: List[Tuple[dict, str]], layout: str, out_dir: Path,
               patients: Optional[Dict[str, str]] = None) -> List[Path]:
    """Write the wiki; return the list of files written. `patients` maps record_id -> patient_id."""
    if layout not in LAYOUTS:
        raise ValueError(f"layout must be one of {LAYOUTS}")
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    written: List[Path] = []

    def w(name: str, body: str) -> None:
        p = out_dir / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
        written.append(p)

    idx = [f"# Wiki ADI — organizzazione: {layout}", ""]

    if layout == "document":
        for rec, text in records:
            rid = rec["meta"]["record_id"]
            lines = [f"# {rid}", f"Data visita: {_date(rec)}", ""]
            by: Dict[str, List[str]] = {}
            for f in facts_from_record(rec, text):
                by.setdefault(f[0], []).append(_line(f, rid))
            for k, title in CONCEPTS.items():
                if k in by:
                    lines += [f"## {title}", *by[k], ""]
            w(f"documents/{rid}.md", "\n".join(lines))
            idx.append(f"- [{rid}](documents/{rid}.md)")

    elif layout == "concept":
        buckets: Dict[str, List[str]] = {k: [] for k in CONCEPTS}
        for rec, text in records:
            rid = rec["meta"]["record_id"]
            for f in facts_from_record(rec, text):
                buckets[f[0]].append(_line(f, rid, with_id=True, date=_date(rec)))
        for k, title in CONCEPTS.items():
            w(f"concepts/{k}.md", "\n".join([f"# {title}", "", *buckets[k], ""]))
            idx.append(f"- [{title}](concepts/{k}.md) — {len(buckets[k])} voci")

    else:  # patient
        patients = patients or {}
        groups: Dict[str, List[Tuple[dict, str]]] = {}
        for rec, text in records:
            rid = rec["meta"]["record_id"]
            groups.setdefault(patients.get(rid, rid), []).append((rec, text))
        for pid in sorted(groups):
            lines = [f"# Paziente {pid}", ""]
            for rec, text in sorted(groups[pid], key=lambda x: _date(x[0])):
                rid = rec["meta"]["record_id"]
                lines += [f"## Visita {_date(rec)} ({rid})"]
                by: Dict[str, List[str]] = {}
                for f in facts_from_record(rec, text):
                    by.setdefault(f[0], []).append(_line(f, rid))
                for k, title in CONCEPTS.items():
                    if k in by:
                        lines += [f"### {title}", *by[k]]
                lines.append("")
            w(f"patients/{pid}.md", "\n".join(lines))
            idx.append(f"- [{pid}](patients/{pid}.md) — {len(groups[pid])} visite")

    w("index.md", "\n".join(idx) + "\n")
    return written


_SRC_RE = re.compile(r"\[source: (ADI-\d+)\]")


def check_provenance(wiki_dir: Path, known_ids: Iterable[str]) -> Dict[str, int]:
    """Every fact line (starts with '- ' and is not an index link) must cite a known source."""
    known = set(known_ids)
    facts = untagged = unknown = 0
    for p in Path(wiki_dir).rglob("*.md"):
        if p.name == "index.md":
            continue
        for ln in p.read_text(encoding="utf-8").splitlines():
            if not ln.startswith("- "):
                continue
            facts += 1
            m = _SRC_RE.findall(ln)
            if not m:
                untagged += 1
            elif any(i not in known for i in m):
                unknown += 1
    return {"fact_lines": facts, "untagged": untagged, "unknown_source": unknown}
