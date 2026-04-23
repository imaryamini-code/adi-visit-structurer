import json
import html
from pathlib import Path
from typing import Any

PRED_DIR = Path("data/synthetic/pred")
OUT_DIR = Path("reports/generated_visit_reports")
HTML_PATH = Path("reports/generated_visit_reports/index.html")


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def fmt_value(value: Any, fallback: str = "Non riportato") -> str:
    if value is None or value == "":
        return fallback
    if isinstance(value, list):
        if not value:
            return fallback
        return ", ".join(str(x) for x in value)
    return str(value)


def fmt_visit_datetime(dt: Any) -> str:
    if not dt:
        return "Non riportata"
    return str(dt).replace("T", " ")


def pretty_reason(reason: Any) -> str:
    mapping = {
        "controllo_parametri": "Controllo parametri vitali",
        "controllo parametri": "Controllo parametri vitali",
        "medicazione_lesione": "Medicazione e controllo lesione",
        "medicazione/controllo lesione": "Medicazione e controllo lesione",
        "medicazione e controllo lesione": "Medicazione e controllo lesione",
        "medicazione lesione da pressione": "Medicazione lesione da pressione",
        "medicazione piaga da decubito": "Medicazione piaga da decubito",
        "rivalutazione_dolore": "Rivalutazione dolore",
        "rivalutazione dolore": "Rivalutazione dolore",
        "valutazione dolore cronico": "Valutazione dolore cronico",
        "valutazione dolore e controllo parametri": "Valutazione dolore e controllo parametri",
        "controllo_terapia": "Controllo terapia",
        "controllo terapia e somministrazione farmaco": "Controllo terapia e somministrazione farmaco",
        "monitoraggio segni vitali e verifica terapia": "Monitoraggio segni vitali e verifica terapia",
        "controllo pressione e rivalutazione terapia": "Controllo pressione e rivalutazione terapia",
        "controllo_catetere": "Controllo e gestione catetere",
        "controllo e gestione catetere": "Controllo e gestione catetere",
        "controllo_stomia": "Controllo e gestione stomia",
        "controllo e gestione stomia": "Controllo e gestione stomia",
        "controllo_respiratorio": "Controllo respiratorio e gestione ossigenoterapia",
        "controllo respiratorio e gestione ossigenoterapia": "Controllo respiratorio e gestione ossigenoterapia",
        "sintomi_generali": "Valutazione sintomi generali",
        "riferiti sintomi generali": "Valutazione sintomi generali",
        "stanchezza e scarso appetito": "Stanchezza e scarso appetito",
        "caduta": "Rivalutazione post-caduta",
        "rivalutazione caduta recente": "Rivalutazione post-caduta",
        "controllo_generale": "Controllo generale",
        "controllo generale": "Controllo generale",
        "educazione caregiver e controllo generale": "Educazione caregiver e controllo generale",
    }
    if not reason:
        return "Non riportato"
    r = str(reason).strip()
    return mapping.get(r.lower(), r.replace("_", " ").capitalize())


def pretty_problem(problem: str) -> str:
    mapping = {
        "dolore_cronico": "Dolore cronico",
        "lesione_da_pressione": "Lesione da pressione",
        "caduta": "Caduta",
        "rischio_caduta": "Rischio di caduta",
        "ipertensione": "Ipertensione",
        "bpco": "BPCO / quadro respiratorio cronico",
        "scompenso_cardiaco": "Scompenso cardiaco",
        "diabete_tipo_2": "Diabete tipo 2",
        "malnutrizione": "Rischio nutrizionale / malnutrizione",
        "disidratazione": "Disidratazione",
        "astenia": "Astenia",
        "nausea": "Nausea",
        "capogiro": "Capogiro",
    }
    return mapping.get(problem, problem.replace("_", " ").capitalize())


def pretty_intervention(item: str) -> str:
    mapping = {
        "monitoraggio_parametri_vitali": "Monitoraggio parametri vitali",
        "valutazione_generale": "Valutazione generale",
        "consigli_alimentari": "Consigli alimentari",
        "educazione_alimentare": "Educazione alimentare",
        "medicazione": "Medicazione",
        "somministrazione_farmaco": "Somministrazione farmaco",
        "monitoraggio_glicemia": "Monitoraggio glicemia",
        "gestione_catetere": "Gestione catetere",
        "gestione_stomia": "Gestione stomia",
        "educazione_terapeutica": "Educazione terapeutica",
        "gestione_ossigenoterapia": "Gestione ossigenoterapia",
    }
    return mapping.get(item, item.replace("_", " ").capitalize())


def fmt_vitals(vitals: dict) -> list[str]:
    if not vitals:
        return ["Non riportati"]

    rows = []
    sys_bp = vitals.get("blood_pressure_systolic")
    dia_bp = vitals.get("blood_pressure_diastolic")
    hr = vitals.get("heart_rate")
    temp = vitals.get("temperature")
    spo2 = vitals.get("spo2")

    if sys_bp is not None and dia_bp is not None:
        rows.append(f"PA {sys_bp}/{dia_bp} mmHg")
    if hr is not None:
        rows.append(f"FC {hr} bpm")
    if temp is not None:
        rows.append(f"Temperatura {temp} °C")
    if spo2 is not None:
        rows.append(f"SpO2 {spo2}%")

    return rows or ["Non riportati"]


def fmt_follow_up(fu: Any) -> str:
    if not fu:
        return "Follow-up non riportato."

    if isinstance(fu, str):
        return fu

    if not isinstance(fu, dict):
        return "Follow-up non riportato."

    ftype = fu.get("type")
    days = fu.get("timing_days")
    target = fu.get("target")

    if ftype == "controllo_ferita":
        if days:
            return f"Controllo ferita programmato tra {days} giorni."
        return "Controllo ferita programmato."

    if ftype == "ricontatto_telefonico":
        if days and target:
            return f"Ricontatto telefonico con {target} previsto tra {days} giorni."
        if target:
            return f"Ricontatto telefonico con {target} previsto."
        return "Ricontatto telefonico previsto."

    if ftype == "controllo":
        if days:
            return f"Nuovo controllo programmato tra {days} giorni."
        return "Nuovo controllo programmato."

    if days:
        return f"{str(ftype).replace('_', ' ').capitalize()} tra {days} giorni."

    return str(ftype).replace("_", " ").capitalize() if ftype else "Follow-up non riportato."


def build_summary_sentence(rec: dict) -> str:
    clinical = rec.get("clinical", {})
    reason = pretty_reason(clinical.get("reason_for_visit"))
    interventions = clinical.get("interventions", [])
    problems = rec.get("coding", {}).get("problems_normalized", [])

    int_text = ", ".join(pretty_intervention(x) for x in interventions[:2]) if interventions else "valutazione clinica"
    prob_text = ", ".join(pretty_problem(x) for x in problems[:2]) if problems else "quadro clinico stabile"

    return (
        f"Accesso domiciliare eseguito per {reason.lower()}. "
        f"Durante la visita sono stati effettuati: {int_text.lower()}. "
        f"Principali elementi clinici rilevati: {prob_text.lower()}."
    )


def generate_text_report(rec: dict) -> str:
    meta = rec.get("meta", {})
    patient = rec.get("patient", {})
    clinical = rec.get("clinical", {})
    coding = rec.get("coding", {})
    quality = rec.get("quality", {})

    interventions = [pretty_intervention(x) for x in clinical.get("interventions", [])]
    problems = [pretty_problem(x) for x in coding.get("problems_normalized", [])]

    lines = []
    lines.append("REPORT VISITA ADI")
    lines.append("=" * 70)
    lines.append(f"Record ID: {fmt_value(meta.get('record_id'))}")
    lines.append(f"Data/Ora visita: {fmt_visit_datetime(meta.get('visit_datetime'))}")
    lines.append(f"Operatore: {fmt_value(meta.get('operator_role'))}")
    lines.append("")

    lines.append("DATI PAZIENTE")
    lines.append("-" * 70)
    lines.append(f"ID paziente: {fmt_value(patient.get('patient_id'))}")
    lines.append(f"Età: {fmt_value(patient.get('age'))}")
    lines.append(f"Sesso: {fmt_value(patient.get('sex'))}")
    lines.append("")

    lines.append("SINTESI CLINICA")
    lines.append("-" * 70)
    lines.append(build_summary_sentence(rec))
    lines.append("")

    lines.append("MOTIVO DELLA VISITA")
    lines.append("-" * 70)
    lines.append(pretty_reason(clinical.get("reason_for_visit")))
    lines.append("")

    lines.append("ANAMNESI / CONDIZIONI GENERALI")
    lines.append("-" * 70)
    lines.append(f"Anamnesi breve: {fmt_value(clinical.get('anamnesis_brief'))}")
    lines.append(f"Stato di coscienza: {fmt_value(clinical.get('consciousness'))}")
    lines.append(f"Mobilità: {fmt_value(clinical.get('mobility'))}")
    lines.append("")

    lines.append("PARAMETRI VITALI")
    lines.append("-" * 70)
    for item in fmt_vitals(clinical.get("vitals", {})):
        lines.append(f"- {item}")
    lines.append("")

    lines.append("INTERVENTI ESEGUITI")
    lines.append("-" * 70)
    if interventions:
        for item in interventions:
            lines.append(f"- {item}")
    else:
        lines.append("- Non riportati")
    lines.append("")

    lines.append("PROBLEMI CLINICI NORMALIZZATI")
    lines.append("-" * 70)
    if problems:
        for item in problems:
            lines.append(f"- {item}")
    else:
        lines.append("- Non riportati")
    lines.append("")

    lines.append("CRITICITÀ")
    lines.append("-" * 70)
    issues = clinical.get("critical_issues", [])
    if issues:
        for item in issues:
            lines.append(f"- {item}")
    else:
        lines.append("- Nessuna criticità segnalata")
    lines.append("")

    lines.append("FOLLOW-UP")
    lines.append("-" * 70)
    lines.append(fmt_follow_up(clinical.get("follow_up")))
    lines.append("")

    lines.append("CONTROLLO QUALITÀ")
    lines.append("-" * 70)
    warnings = quality.get("warnings", [])
    missing = quality.get("missing_mandatory_fields", [])

    if warnings:
        lines.append("Avvisi:")
        for w in warnings:
            lines.append(f"- {w}")
    else:
        lines.append("Avvisi: nessuno")

    if missing:
        lines.append("Campi mancanti:")
        for m in missing:
            lines.append(f"- {m}")
    else:
        lines.append("Campi mancanti: nessuno")

    lines.append("")
    lines.append("Report strutturato generato automaticamente dal sistema.")
    return "\n".join(lines)


def generate_html_card(rec: dict) -> str:
    meta = rec.get("meta", {})
    patient = rec.get("patient", {})
    clinical = rec.get("clinical", {})
    coding = rec.get("coding", {})
    quality = rec.get("quality", {})

    vitals_html = "".join(
        f"<li>{html.escape(v)}</li>" for v in fmt_vitals(clinical.get("vitals", {}))
    )

    interventions = [pretty_intervention(x) for x in (clinical.get("interventions", []) or [])] or ["Non riportati"]
    interventions_html = "".join(f"<li>{html.escape(str(v))}</li>" for v in interventions)

    problems = [pretty_problem(x) for x in (coding.get("problems_normalized", []) or [])] or ["Non riportati"]
    problems_html = "".join(f"<li>{html.escape(str(v))}</li>" for v in problems)

    issues = clinical.get("critical_issues", []) or ["Nessuna criticità segnalata"]
    issues_html = "".join(f"<li>{html.escape(str(v))}</li>" for v in issues)

    warnings = quality.get("warnings", []) or ["Nessuno"]
    warnings_html = "".join(f"<li>{html.escape(str(v))}</li>" for v in warnings)

    missing = quality.get("missing_mandatory_fields", []) or ["Nessuno"]
    missing_html = "".join(f"<li>{html.escape(str(v))}</li>" for v in missing)

    summary = build_summary_sentence(rec)

    return f"""
    <div class="card">
      <div class="header">
        <h2>{html.escape(fmt_value(meta.get("record_id")))}</h2>
        <div class="sub">{html.escape(fmt_visit_datetime(meta.get("visit_datetime")))}</div>
      </div>

      <div class="summary-box">
        {html.escape(summary)}
      </div>

      <div class="grid">
        <div class="section">
          <h3>Paziente</h3>
          <p><strong>ID:</strong> {html.escape(fmt_value(patient.get("patient_id")))}</p>
          <p><strong>Età:</strong> {html.escape(fmt_value(patient.get("age")))}</p>
          <p><strong>Sesso:</strong> {html.escape(fmt_value(patient.get("sex")))}</p>
          <p><strong>Operatore:</strong> {html.escape(fmt_value(meta.get("operator_role")))}</p>
        </div>

        <div class="section">
          <h3>Motivo visita</h3>
          <p>{html.escape(pretty_reason(clinical.get("reason_for_visit")))}</p>
          <p><strong>Anamnesi:</strong> {html.escape(fmt_value(clinical.get("anamnesis_brief")))}</p>
          <p><strong>Coscienza:</strong> {html.escape(fmt_value(clinical.get("consciousness")))}</p>
          <p><strong>Mobilità:</strong> {html.escape(fmt_value(clinical.get("mobility")))}</p>
        </div>

        <div class="section">
          <h3>Parametri vitali</h3>
          <ul>{vitals_html}</ul>
        </div>

        <div class="section">
          <h3>Interventi</h3>
          <ul>{interventions_html}</ul>
        </div>

        <div class="section">
          <h3>Problemi clinici</h3>
          <ul>{problems_html}</ul>
        </div>

        <div class="section">
          <h3>Criticità</h3>
          <ul>{issues_html}</ul>
        </div>

        <div class="section">
          <h3>Follow-up</h3>
          <p>{html.escape(fmt_follow_up(clinical.get("follow_up")))}</p>
        </div>

        <div class="section">
          <h3>Qualità del dato</h3>
          <p><strong>Avvisi</strong></p>
          <ul>{warnings_html}</ul>
          <p><strong>Campi mancanti</strong></p>
          <ul>{missing_html}</ul>
        </div>
      </div>
    </div>
    """


def generate_index_html(cards: list[str]) -> str:
    return f"""<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="utf-8" />
  <title>ADI Generated Visit Reports</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      margin: 24px;
      background: #f7f7f9;
      color: #222;
    }}
    h1 {{
      margin-bottom: 8px;
    }}
    .intro {{
      margin-bottom: 24px;
      color: #555;
    }}
    .card {{
      background: white;
      border-radius: 14px;
      padding: 20px;
      margin-bottom: 20px;
      box-shadow: 0 2px 10px rgba(0,0,0,0.08);
    }}
    .header {{
      border-bottom: 1px solid #eee;
      margin-bottom: 16px;
      padding-bottom: 8px;
    }}
    .header h2 {{
      margin: 0;
    }}
    .sub {{
      color: #666;
      margin-top: 4px;
    }}
    .summary-box {{
      background: #eef4ff;
      border-left: 4px solid #4c7bd9;
      padding: 12px 14px;
      border-radius: 8px;
      margin-bottom: 16px;
      line-height: 1.5;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      gap: 16px;
    }}
    .section {{
      background: #fafafa;
      border-radius: 10px;
      padding: 14px;
    }}
    .section h3 {{
      margin-top: 0;
      margin-bottom: 10px;
      font-size: 16px;
    }}
    ul {{
      margin: 0;
      padding-left: 18px;
    }}
    p {{
      margin: 6px 0;
    }}
  </style>
</head>
<body>
  <h1>Report Visite ADI Generati Automaticamente</h1>
  <div class="intro">
    Output strutturati generati automaticamente a partire dai JSON clinici estratti dal sistema.
  </div>
  {''.join(cards)}
</body>
</html>
"""


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pred_files = sorted(PRED_DIR.glob("ADI-*.json"))
    if not pred_files:
        print(f"No prediction files found in {PRED_DIR}")
        return

    cards = []

    for path in pred_files:
        rec = load_json(path)
        record_id = rec.get("meta", {}).get("record_id", path.stem)

        text_report = generate_text_report(rec)
        out_txt = OUT_DIR / f"{record_id}.txt"
        out_txt.write_text(text_report, encoding="utf-8")

        cards.append(generate_html_card(rec))

    html_content = generate_index_html(cards)
    HTML_PATH.write_text(html_content, encoding="utf-8")

    print(f"Generated {len(pred_files)} text reports in: {OUT_DIR}")
    print(f"Generated HTML report index: {HTML_PATH}")


if __name__ == "__main__":
    main()