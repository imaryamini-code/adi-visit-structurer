# src/export_reports.py

from __future__ import annotations

import csv
import html
import json
from pathlib import Path
from typing import Any, Dict, List


PRED_DIR = Path("data/synthetic/pred")
REPORTS_DIR = Path("reports")
CSV_PATH = REPORTS_DIR / "summary_table.csv"
HTML_PATH = REPORTS_DIR / "dashboard.html"


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def format_vitals(vitals: Dict[str, Any]) -> str:
    if not vitals:
        return ""

    parts = []

    sys_bp = vitals.get("blood_pressure_systolic")
    dia_bp = vitals.get("blood_pressure_diastolic")
    if sys_bp is not None or dia_bp is not None:
        parts.append(f"BP: {sys_bp}/{dia_bp}")

    if vitals.get("heart_rate") is not None:
        parts.append(f"HR: {vitals.get('heart_rate')}")

    if vitals.get("temperature") is not None:
        parts.append(f"T: {vitals.get('temperature')}")

    if vitals.get("spo2") is not None:
        parts.append(f"SpO2: {vitals.get('spo2')}")

    return " | ".join(parts)


def safe_join(items: Any) -> str:
    if not items:
        return ""
    if isinstance(items, list):
        return ", ".join(str(x) for x in items)
    return str(items)


def follow_up_to_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        typ = value.get("type")
        days = value.get("timing_days")
        target = value.get("target")
        parts = [str(typ) if typ else None]
        if days is not None:
            parts.append(f"{days} giorni")
        if target:
            parts.append(str(target))
        return " | ".join(x for x in parts if x)
    return str(value)


def collect_rows() -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []

    for path in sorted(PRED_DIR.glob("ADI-*.json")):
        data = load_json(path)

        meta = data.get("meta", {}) or {}
        clinical = data.get("clinical", {}) or {}
        coding = data.get("coding", {}) or {}
        quality = data.get("quality", {}) or {}

        row = {
            "record_id": str(meta.get("record_id", path.stem)),
            "mode": str(meta.get("extraction_mode", "")),
            "reason_for_visit": str(clinical.get("reason_for_visit") or ""),
            "follow_up": follow_up_to_string(clinical.get("follow_up")),
            "interventions": safe_join(clinical.get("interventions")),
            "problems_normalized": safe_join(coding.get("problems_normalized")),
            "problems_suspects": safe_join(coding.get("problems_suspects")),
            "vitals": format_vitals(clinical.get("vitals", {}) or {}),
            "warnings": safe_join(quality.get("warnings")),
            "missing_fields": safe_join(quality.get("missing_mandatory_fields")),
        }
        rows.append(row)

    return rows


def export_csv(rows: List[Dict[str, str]]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "record_id",
        "mode",
        "reason_for_visit",
        "follow_up",
        "interventions",
        "problems_normalized",
        "problems_suspects",
        "vitals",
        "warnings",
        "missing_fields",
    ]

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def export_html(rows: List[Dict[str, str]]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    table_rows = []
    for r in rows:
        table_rows.append(
            "<tr>"
            f"<td>{html.escape(r['record_id'])}</td>"
            f"<td>{html.escape(r['mode'])}</td>"
            f"<td>{html.escape(r['reason_for_visit'])}</td>"
            f"<td>{html.escape(r['follow_up'])}</td>"
            f"<td>{html.escape(r['interventions'])}</td>"
            f"<td>{html.escape(r['problems_normalized'])}</td>"
            f"<td>{html.escape(r['problems_suspects'])}</td>"
            f"<td>{html.escape(r['vitals'])}</td>"
            f"<td>{html.escape(r['warnings'])}</td>"
            f"<td>{html.escape(r['missing_fields'])}</td>"
            "</tr>"
        )

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>ADI Visit Structurer Dashboard</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 24px;
      background: #f7f7f7;
      color: #222;
    }}
    h1 {{
      margin-bottom: 8px;
    }}
    p {{
      color: #555;
    }}
    .card {{
      background: white;
      padding: 16px;
      border-radius: 10px;
      box-shadow: 0 2px 8px rgba(0,0,0,0.08);
      margin-bottom: 20px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      background: white;
      border-radius: 10px;
      overflow: hidden;
    }}
    th, td {{
      border: 1px solid #ddd;
      padding: 10px;
      text-align: left;
      vertical-align: top;
      font-size: 14px;
    }}
    th {{
      background: #f0f0f0;
    }}
    tr:nth-child(even) {{
      background: #fafafa;
    }}
  </style>
</head>
<body>
  <div class="card">
    <h1>ADI Visit Structurer Dashboard</h1>
    <p>Total predicted records: {len(rows)}</p>
    <p>This dashboard summarizes structured outputs generated by the hybrid NLP pipeline.</p>
  </div>

  <table>
    <thead>
      <tr>
        <th>Record ID</th>
        <th>Mode</th>
        <th>Reason for Visit</th>
        <th>Follow Up</th>
        <th>Interventions</th>
        <th>Problems</th>
        <th>Suspects</th>
        <th>Vitals</th>
        <th>Warnings</th>
        <th>Missing Fields</th>
      </tr>
    </thead>
    <tbody>
      {''.join(table_rows)}
    </tbody>
  </table>
</body>
</html>
"""
    HTML_PATH.write_text(html_content, encoding="utf-8")


def main() -> None:
    rows = collect_rows()
    export_csv(rows)
    export_html(rows)
    print(f"Wrote {CSV_PATH}")
    print(f"Wrote {HTML_PATH}")


if __name__ == "__main__":
    main()