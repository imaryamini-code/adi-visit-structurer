"""
access_log_analysis.py

Analyses access_log.jsonl produced by abac.py.
This is your data analysis contribution to the security project.

Run:   python3 access_log_analysis.py
Output: reports/access_analysis.json  +  printed summary

Can also be imported and called from a Flask route for live stats.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

LOG_FILE   = Path("access_log.jsonl")
REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)


def load_log() -> List[Dict[str, Any]]:
    if not LOG_FILE.exists():
        return []
    entries = []
    for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return entries


def analyze(entries: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Run full analysis. Pass entries directly (for live dashboard use)
    or leave None to load from disk.
    """
    if entries is None:
        entries = load_log()
    if not entries:
        return {"error": "No log entries found", "total_events": 0}

    total   = len(entries)
    denied  = [e for e in entries if not e["permitted"]]
    permitted = [e for e in entries if e["permitted"]]

    # 1. Denial rate by role
    role_totals  = Counter(e["subject_role"] for e in entries)
    role_denials = Counter(e["subject_role"] for e in denied)
    denial_rate_by_role = {
        role: {
            "total_requests": role_totals[role],
            "denied": role_denials.get(role, 0),
            "denial_rate_pct": round(role_denials.get(role, 0) / role_totals[role] * 100, 1),
        }
        for role in role_totals
    }

    # 2. Hourly pattern
    hour_counts: Dict[int, Dict[str, int]] = defaultdict(lambda: {"total": 0, "denied": 0})
    for e in entries:
        try:
            h = datetime.fromisoformat(e["timestamp"]).hour
            hour_counts[h]["total"] += 1
            if not e["permitted"]:
                hour_counts[h]["denied"] += 1
        except Exception:
            continue
    hourly_pattern = {f"{h:02d}:00": hour_counts[h] for h in sorted(hour_counts)}

    # 3. Off-hours clinical access (anomaly detection)
    off_hours = [
        e for e in entries
        if e["subject_role"] in ("infermiere", "medico")
        and _is_off_hours(e.get("timestamp", ""))
    ]

    # 4. High-risk resources — accessed by 2+ distinct roles
    resource_roles: Dict[str, set] = defaultdict(set)
    for e in entries:
        resource_roles[e["resource_type"]].add(e["subject_role"])
    high_risk = {rt: sorted(roles) for rt, roles in resource_roles.items() if len(roles) >= 2}

    # 5. Ownership violations — "not the owner" in denial reason
    ownership_violations = [e for e in denied if "not the owner" in e.get("reason", "").lower()]

    # 6. Top denial reasons
    top_denials = Counter(e["reason"] for e in denied).most_common(5)

    # 7. Endpoint activity
    endpoint_counts = Counter(
        f"{e.get('method','?')} {e.get('endpoint','?')}" for e in entries
    ).most_common(10)

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "total_events": total,
        "total_permitted": len(permitted),
        "total_denied": len(denied),
        "overall_denial_rate_pct": round(len(denied) / total * 100, 1) if total else 0,
        "denial_rate_by_role": denial_rate_by_role,
        "hourly_pattern": hourly_pattern,
        "off_hours_clinical_events": len(off_hours),
        "off_hours_details": off_hours[:10],
        "high_risk_resources": high_risk,
        "ownership_violations_count": len(ownership_violations),
        "ownership_violations_sample": ownership_violations[:5],
        "top_denial_reasons": [{"reason": r, "count": c} for r, c in top_denials],
        "endpoint_activity": dict(endpoint_counts),
        "recent_events": list(reversed(entries[-30:])),
    }


def _is_off_hours(ts: str) -> bool:
    try:
        h = datetime.fromisoformat(ts).hour
        return h < 8 or h >= 20
    except Exception:
        return False


def print_summary(s: Dict[str, Any]) -> None:
    print("\n=== ADI Assistant — Access Log Analysis ===\n")
    print(f"  Total events : {s['total_events']}")
    print(f"  Permitted    : {s['total_permitted']}")
    print(f"  Denied       : {s['total_denied']}  ({s['overall_denial_rate_pct']}%)\n")

    print("Denial rate by role:")
    for role, stats in s["denial_rate_by_role"].items():
        bar = "█" * int(stats["denial_rate_pct"] / 5)
        print(f"  {role:20s}  {stats['denied']:3d}/{stats['total_requests']:3d}  "
              f"{stats['denial_rate_pct']:5.1f}%  {bar}")

    print(f"\nOff-hours clinical access: {s['off_hours_clinical_events']} events")
    if s["off_hours_clinical_events"] > 0:
        print("  → These are anomalies. Review who accessed what outside shift hours.")

    if s["high_risk_resources"]:
        print("\nHigh-risk resources (multiple roles accessing):")
        for rt, roles in s["high_risk_resources"].items():
            print(f"  {rt:30s}  roles: {', '.join(roles)}")

    print(f"\nOwnership violations: {s['ownership_violations_count']}")
    for v in s["ownership_violations_sample"][:3]:
        print(f"  {v['subject_username']} tried to read report owned by {v['resource_owner']}")

    print("\nTop denial reasons:")
    for item in s["top_denial_reasons"]:
        print(f"  {item['count']:3d}x  {item['reason'][:90]}")

    print(f"\nFull report → {REPORT_DIR / 'access_analysis.json'}\n")


if __name__ == "__main__":
    entries = load_log()
    summary = analyze(entries)
    out = REPORT_DIR / "access_analysis.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print_summary(summary)