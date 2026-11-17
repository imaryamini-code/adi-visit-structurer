"""
src/routing.py
Adaptive field-level routing for the ADI pipeline.

Idea
----
The rule-based extractors run first (they are free and deterministic).
For each field we then decide, from evidence in the note itself, whether to

  * ACCEPT the rules result,
  * ESCALATE to the local LLM and verify its answer before using it, or
  * FLAG the field for human review when nothing can be verified.

The LLM is called at most ONCE per note, and only if at least one field needs it.
LLM answers are never trusted blindly:
  - numbers must appear in the note text (grounding) and be physiologically plausible
  - free-text answers are pushed back through the rule vocabularies
    (reason / follow-up / interventions / problems); if they cannot be mapped,
    the field is flagged instead of guessed.

Every decision is recorded in rec["routing"] so the behaviour can be audited and
evaluated (LLM call rate, flag rate, accuracy of each decision type).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import src.extract_rules as rules_mod
from src.normalize import normalize_problems

# Decision status values (kept as plain strings so they serialise to JSON as-is)
ACCEPTED = "accepted"                    # rules result kept, no LLM needed
NOT_MENTIONED = "not_mentioned"          # no evidence in the note -> null is legitimate
ESCALATED_ACCEPTED = "escalated_accepted"  # LLM answer verified and used
FLAGGED = "flagged"                      # needs human review

LLMFn = Callable[[str], Dict[str, Any]]  # text -> coerced {"clinical": {...}, "coding": {...}}


# ---------------------------------------------------------------------------
# Configuration (every threshold/policy is a knob so it can be ablated in experiments)
# ---------------------------------------------------------------------------

@dataclass
class RoutingConfig:
    escalate_missing_vitals: bool = True      # cue in text but rules found nothing
    escalate_implausible_vitals: bool = True  # rules value outside physiological range
    escalate_missing_reason: bool = True
    escalate_generic_reason: bool = True
    escalate_missing_follow_up: bool = True
    escalate_fallback_interventions: bool = True
    escalate_empty_problems: bool = True
    require_grounding: bool = True            # LLM numbers must appear in the note
    # What to do when rules gave only a generic reason and the LLM proposes something else:
    #   "flag"       -> keep the rules value, flag the field for human review
    #   "prefer_llm" -> use the LLM's (canonicalised) reason
    generic_reason_policy: str = "flag"
    generic_reasons: Tuple[str, ...] = ("controllo parametri", "controllo generale")


# ---------------------------------------------------------------------------
# Evidence cues: "does the note talk about this field at all?"
# ---------------------------------------------------------------------------

_CUES = {
    "blood_pressure": re.compile(r"\b(pressione|p\.a\.|pa|mmhg)\b|\bpa\s*[:=]?\s*\d"),
    "heart_rate": re.compile(r"\b(frequenza cardiaca|fc|battit\w*|bpm|polso)\b"),
    "temperature": re.compile(r"temperatura|°\s*c\b|\btc\b|\bgradi\b"),
    "spo2": re.compile(r"saturazione|spo2|sp02|\bsat\b|ossigenazione"),
    "follow_up": re.compile(
        r"controllo|ricontrollo|rivalutazione|prossim\w+|\btra\s+\w+\s+(giorni|settimane|mesi)|"
        r"\bentro\b|follow-?up|telefon\w*|programmat\w*|previst\w*|pianificat\w*"
    ),
}

_RANGES = {
    "blood_pressure_systolic": (60, 260),
    "blood_pressure_diastolic": (30, 150),
    "heart_rate": (30, 220),
    "temperature": (33.0, 42.0),
    "spo2": (50, 100),
}


def _norm_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower().replace(",", "."))


def _has_cue(name: str, text: str) -> bool:
    return bool(_CUES[name].search(_norm_text(text)))


_NUMBER_NEAR = re.compile(r"[^\d]{0,30}\d")


def _has_value_cue(name: str, text: str) -> bool:
    """
    A vital counts as 'mentioned with a value' only if the cue word is followed by a number
    within ~30 characters. This avoids escalating notes that say 'SpO2 non rilevata'.
    """
    t = _norm_text(text)
    return any(_NUMBER_NEAR.match(t, m.end()) for m in _CUES[name].finditer(t))


def _plausible(key: str, value: Any) -> bool:
    if not isinstance(value, (int, float)):
        return False
    lo, hi = _RANGES[key]
    return lo <= value <= hi


def _grounded(value: Any, text: str) -> bool:
    """True if the number appears as a standalone number in the note text."""
    if value is None:
        return False
    s = str(value)
    if isinstance(value, float) and value.is_integer():
        s = str(int(value))
    return bool(re.search(rf"(?<![\d.]){re.escape(s)}(?![\d])", _norm_text(text)))


# ---------------------------------------------------------------------------
# Decision log
# ---------------------------------------------------------------------------

@dataclass
class FieldDecision:
    status: str
    source: str            # "rules" | "llm" | "none"
    reason: str
    llm_suggestion: Any = None  # kept for audit when a field is flagged

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {"status": self.status, "source": self.source, "reason": self.reason}
        if self.llm_suggestion is not None:
            d["llm_suggestion"] = self.llm_suggestion
        return d


@dataclass
class RoutingResult:
    llm_called: bool = False
    llm_error: Optional[str] = None
    decisions: Dict[str, FieldDecision] = field(default_factory=dict)

    @property
    def needs_review(self) -> List[str]:
        return [k for k, d in self.decisions.items() if d.status == FLAGGED]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "llm_called": self.llm_called,
            "llm_error": self.llm_error,
            "needs_review": self.needs_review,
            "fields": {k: d.to_dict() for k, d in self.decisions.items()},
        }


# ---------------------------------------------------------------------------
# Step 1: which fields need the LLM?  (pure function of the note + rules output)
# ---------------------------------------------------------------------------

def plan_escalations(text: str, rec: Dict[str, Any], cfg: RoutingConfig) -> Dict[str, str]:
    """Return {field: reason} for every field that should be escalated to the LLM."""
    clin = rec["clinical"]
    vitals = clin.get("vitals") or {}
    plan: Dict[str, str] = {}

    # --- vitals ---------------------------------------------------------
    sys_v, dia_v = vitals.get("blood_pressure_systolic"), vitals.get("blood_pressure_diastolic")
    if sys_v is not None or dia_v is not None:
        ok = _plausible("blood_pressure_systolic", sys_v) and _plausible("blood_pressure_diastolic", dia_v)
        if ok and sys_v <= dia_v:
            ok = False
        if not ok and cfg.escalate_implausible_vitals:
            plan["blood_pressure"] = "rules value implausible"
    elif cfg.escalate_missing_vitals and _has_value_cue("blood_pressure", text):
        plan["blood_pressure"] = "note mentions blood pressure but rules found none"

    for key in ("heart_rate", "temperature", "spo2"):
        v = vitals.get(key)
        if v is not None:
            if not _plausible(key, v) and cfg.escalate_implausible_vitals:
                plan[key] = "rules value implausible"
        elif cfg.escalate_missing_vitals and _has_value_cue(key, text):
            plan[key] = f"note mentions {key} but rules found none"

    # --- reason ---------------------------------------------------------
    reason = clin.get("reason_for_visit")
    if not reason:
        if cfg.escalate_missing_reason:
            plan["reason_for_visit"] = "rules found no reason"
    elif cfg.escalate_generic_reason and reason in cfg.generic_reasons:
        plan["reason_for_visit"] = "rules returned only a generic reason"

    # --- follow-up ------------------------------------------------------
    if not clin.get("follow_up") and cfg.escalate_missing_follow_up and _has_cue("follow_up", text):
        plan["follow_up"] = "note mentions a follow-up but rules found none"

    # --- interventions --------------------------------------------------
    if cfg.escalate_fallback_interventions and (clin.get("interventions") or []) == ["valutazione_generale"]:
        plan["interventions"] = "rules produced only the generic fallback"

    # --- problems -------------------------------------------------------
    if cfg.escalate_empty_problems and not (rec["coding"].get("problems_normalized") or []):
        plan["problems"] = "rules found no problems"

    return plan


# ---------------------------------------------------------------------------
# Step 2: verify the LLM answer for each escalated field
# ---------------------------------------------------------------------------

def _resolve_vital(
    key: str, rec: Dict[str, Any], llm_vitals: Dict[str, Any], text: str,
    cfg: RoutingConfig, why: str,
) -> FieldDecision:
    cand = llm_vitals.get(key)
    if cand is not None and _plausible(key, cand) and (not cfg.require_grounding or _grounded(cand, text)):
        rec["clinical"]["vitals"][key] = cand
        return FieldDecision(ESCALATED_ACCEPTED, "llm", f"{why}; LLM value plausible and found in note")
    # Not verifiable. An implausible rules value is removed rather than kept.
    if rec["clinical"]["vitals"].get(key) is not None and "implausible" in why:
        rec["clinical"]["vitals"][key] = None
    return FieldDecision(FLAGGED, "none", f"{why}; LLM value missing, implausible or not in note",
                         llm_suggestion=cand)


def _resolve_blood_pressure(
    rec: Dict[str, Any], llm_vitals: Dict[str, Any], text: str, cfg: RoutingConfig, why: str,
) -> FieldDecision:
    s, d = llm_vitals.get("blood_pressure_systolic"), llm_vitals.get("blood_pressure_diastolic")
    good = (
        s is not None and d is not None
        and _plausible("blood_pressure_systolic", s) and _plausible("blood_pressure_diastolic", d)
        and s > d
        and (not cfg.require_grounding or (_grounded(s, text) and _grounded(d, text)))
    )
    v = rec["clinical"]["vitals"]
    if good:
        v["blood_pressure_systolic"], v["blood_pressure_diastolic"] = s, d
        return FieldDecision(ESCALATED_ACCEPTED, "llm", f"{why}; LLM pair plausible and found in note")
    if "implausible" in why:
        v["blood_pressure_systolic"] = v["blood_pressure_diastolic"] = None
    sugg = f"{s}/{d}" if (s is not None or d is not None) else None
    return FieldDecision(FLAGGED, "none", f"{why}; LLM pair missing, implausible or not in note",
                         llm_suggestion=sugg)


def _canonical_reason(llm_reason: Optional[str]) -> Optional[str]:
    """Push the LLM's free-text reason through the rule vocabulary."""
    if not llm_reason:
        return None
    fn = getattr(rules_mod, "_reason_from_keywords", None)
    return fn(llm_reason) if fn else None


def resolve_escalations(
    text: str, rec: Dict[str, Any], plan: Dict[str, str], llm_out: Dict[str, Any], cfg: RoutingConfig,
    follow_up_parser: Optional[Callable[[str], Any]] = None,
) -> Dict[str, FieldDecision]:
    out: Dict[str, FieldDecision] = {}
    clin_llm = (llm_out or {}).get("clinical", {}) or {}
    cod_llm = (llm_out or {}).get("coding", {}) or {}
    llm_vitals = clin_llm.get("vitals", {}) or {}

    for fld, why in plan.items():
        if fld == "blood_pressure":
            out[fld] = _resolve_blood_pressure(rec, llm_vitals, text, cfg, why)

        elif fld in ("heart_rate", "temperature", "spo2"):
            out[fld] = _resolve_vital(fld, rec, llm_vitals, text, cfg, why)

        elif fld == "reason_for_visit":
            raw = clin_llm.get("reason_for_visit")
            canon = _canonical_reason(raw)
            current = rec["clinical"].get("reason_for_visit")
            if not current:
                if canon:
                    rec["clinical"]["reason_for_visit"] = canon
                    out[fld] = FieldDecision(ESCALATED_ACCEPTED, "llm", f"{why}; LLM reason mapped to vocabulary")
                else:
                    out[fld] = FieldDecision(FLAGGED, "none", f"{why}; LLM reason missing or not mappable",
                                             llm_suggestion=raw)
            else:  # generic reason from rules
                if not canon or canon == current:
                    out[fld] = FieldDecision(ACCEPTED, "rules", f"{why}; LLM agrees or adds nothing usable")
                elif cfg.generic_reason_policy == "prefer_llm" and canon not in cfg.generic_reasons:
                    rec["clinical"]["reason_for_visit"] = canon
                    out[fld] = FieldDecision(ESCALATED_ACCEPTED, "llm", f"{why}; LLM gave a more specific reason")
                else:
                    out[fld] = FieldDecision(FLAGGED, "rules", f"{why}; LLM disagrees ({canon!r})",
                                             llm_suggestion=canon)

        elif fld == "follow_up":
            raw = clin_llm.get("follow_up")
            parse = follow_up_parser or rules_mod.extract_follow_up
            parsed = parse(raw) if raw else None  # LLM reads, rules canonicalise
            if parsed:
                rec["clinical"]["follow_up"] = parsed
                out[fld] = FieldDecision(ESCALATED_ACCEPTED, "llm", f"{why}; LLM phrase parsed by rules")
            else:
                out[fld] = FieldDecision(FLAGGED, "none", f"{why}; LLM follow-up missing or not parseable",
                                         llm_suggestion=raw)

        elif fld == "interventions":
            vocab = getattr(rules_mod, "_INTERVENTION_VOCAB", set())
            extra = [i for i in (clin_llm.get("interventions") or []) if i in vocab and i != "valutazione_generale"]
            if extra:
                rec["clinical"]["interventions"] = list(dict.fromkeys(extra))
                out[fld] = FieldDecision(ESCALATED_ACCEPTED, "llm", f"{why}; LLM interventions in vocabulary")
            else:
                out[fld] = FieldDecision(ACCEPTED, "rules", f"{why}; LLM found nothing more specific")

        elif fld == "problems":
            llm_probs = normalize_problems(cod_llm.get("problems_normalized") or []) or []
            if llm_probs:
                rec["coding"]["problems_normalized"] = list(dict.fromkeys(llm_probs))
                out[fld] = FieldDecision(ESCALATED_ACCEPTED, "llm", f"{why}; LLM problems in vocabulary")
            else:
                out[fld] = FieldDecision(NOT_MENTIONED, "none", f"{why}; LLM also found none")
    return out


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def route_record(
    text: str,
    rec: Dict[str, Any],
    llm_fn: Optional[LLMFn],
    cfg: Optional[RoutingConfig] = None,
    follow_up_parser: Optional[Callable[[str], Any]] = None,
) -> RoutingResult:
    """
    Apply adaptive routing to a record that already contains the rules output.
    Mutates rec in place and returns the decision log (also stored in rec["routing"]).
    """
    cfg = cfg or RoutingConfig()
    result = RoutingResult()
    plan = plan_escalations(text, rec, cfg)

    # Fields not escalated: record why they were accepted.
    for key in ("blood_pressure", "heart_rate", "temperature", "spo2"):
        if key not in plan:
            present = (
                rec["clinical"]["vitals"].get("blood_pressure_systolic") is not None
                if key == "blood_pressure" else rec["clinical"]["vitals"].get(key) is not None
            )
            result.decisions[key] = (
                FieldDecision(ACCEPTED, "rules", "plausible value found by rules")
                if present else FieldDecision(NOT_MENTIONED, "none", "no mention in note")
            )
    for key, val in (
        ("reason_for_visit", rec["clinical"].get("reason_for_visit")),
        ("follow_up", rec["clinical"].get("follow_up")),
        ("interventions", rec["clinical"].get("interventions")),
        ("problems", rec["coding"].get("problems_normalized")),
    ):
        if key not in plan:
            result.decisions[key] = (
                FieldDecision(ACCEPTED, "rules", "specific value found by rules")
                if val else FieldDecision(NOT_MENTIONED, "none", "no evidence in note")
            )

    if plan:
        llm_out: Dict[str, Any] = {}
        if llm_fn is None:
            result.llm_error = "no LLM available"
        else:
            try:
                llm_out = llm_fn(text)
                result.llm_called = True
            except RuntimeError as e:  # Ollama down / invalid JSON after retries
                result.llm_error = str(e).splitlines()[0]
        if result.llm_error:
            for fld, why in plan.items():
                result.decisions[fld] = FieldDecision(FLAGGED, "none", f"{why}; LLM unavailable")
        else:
            result.decisions.update(resolve_escalations(text, rec, plan, llm_out, cfg, follow_up_parser))

    rec["routing"] = result.to_dict()
    return result
