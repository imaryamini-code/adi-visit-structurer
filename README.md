# ADI Assistant

> Transform clinical home-care notes into structured ADI reports in seconds.

ADI Assistant is a prototype system developed during an internship at **Cooperativa Servizi Sociali, Messina**, as part of a Bachelor's degree in Data Analysis at the University of Messina.

The project supports healthcare professionals by transforming **free-text or dictated ADI (Assistenza Domiciliare Integrata) home-care notes** into structured clinical report drafts aligned with real ADI workflows — reducing manual documentation effort while improving data consistency and usability.

---

## Key Features

- **Voice-to-text input** — clinical dictation transcribed via faster-whisper
- **Manual text input** — paste or type notes directly
- **Hybrid extraction pipeline** — rule-based NLP + optional local LLM (Mistral via Ollama)
- **Anamnesis extraction** — patient background and medical history detected automatically
- **Structured ADI-compatible output** — JSON with all clinical fields
- **Quality checks** — missing fields, inconsistent data, follow-up reminders
- **Interactive web dashboard** — review reports and raw JSON in one place
- **Clinical knowledge quiz** — 10-question ADI knowledge check
- **Attribute-Based Access Control (ABAC)** — role-based access enforcement at the backend
- **Role-specific dashboards** — clinical workspace, billing portal, and admin analytics
- **Audit log** — every access decision (permit and deny) logged for analysis

---

## What the System Extracts

From a single clinical note, the assistant generates:

| Field | Description |
|---|---|
| Reason for visit | Normalized clinical reason |
| Anamnesis brief | Patient background and medical history |
| Vital signs | Blood pressure, heart rate, temperature, SpO₂ |
| Interventions | Actions performed during the visit |
| Follow-up | Next steps, timing, and responsible party |
| Clinical problems | Normalized problem labels |
| Critical issues | Alerts for respiratory instability, falls, etc. |
| Quality warnings | Missing or inconsistent data flags |

---

## System Architecture

```
Voice / Text Input
        ↓
   Preprocessing          Strip LLM wrappers, normalize whitespace
        ↓
  Rule-based NLP          Extract vitals, reason, anamnesis, follow-up, interventions
        ↓
  LLM (optional)          Fill gaps rules couldn't cover (Mistral via Ollama)
        ↓
   Normalization           Align labels to ADI vocabulary
        ↓
  Quality checks           Detect missing fields and inconsistencies
        ↓
 Structured JSON output    ADI-compatible, web dashboard, batch reports
        ↓
   ABAC layer              Every request evaluated against role + resource + environment attributes
```

### Hybrid extraction

**Rules first** — deterministic and interpretable for structured data (vitals, dates, follow-up timing).  
**LLM as fallback** — handles variable clinical language when rules don't produce enough. Called only when needed via a smart gate (`_should_call_llm`), so the system runs without Ollama.

### Access control — ABAC vs RBAC

The system uses Attribute-Based Access Control rather than simple Role-Based Access Control. The key distinction: RBAC can say "doctors can read reports" but cannot say "doctors can only read their **own** reports." The ownership check (`subject.username == resource.owner`) requires comparing subject attributes against resource attributes at evaluation time — that is the defining capability of ABAC.

Every access decision is logged to `access_log.jsonl` and analysed by `access_log_analysis.py`.

---

## Roles and Access

| Role | Dashboard | Clinical reports | Payment records | Admin panel |
|---|---|---|---|---|
| `medico` | ✓ | own reports only | ✗ | ✗ |
| `infermiere` | ✓ | own reports only | ✗ | ✗ |
| `amministratore` | ✓ | all reports | read-only | ✓ |
| `finance` | ✗ | ✗ | ✓ | ✗ |

---

## Example Output

```json
{
  "clinical": {
    "reason_for_visit": "controllo parametri",
    "anamnesis_brief": "paziente con storia di ipertensione arteriosa nota, in terapia domiciliare",
    "vitals": {
      "blood_pressure": "130/80",
      "heart_rate": 72,
      "temperature": 36.7,
      "spo2": 97
    },
    "interventions": ["monitoraggio_parametri_vitali", "valutazione_generale"],
    "follow_up": "Nuovo controllo tra 7 giorni.",
    "critical_issues": []
  },
  "quality": {
    "missing_mandatory_fields": [],
    "warnings": []
  }
}
```

---

## Evaluation

The system includes a full evaluation module (`src/evaluate.py`) comparing structured predictions against a 100-record synthetic gold dataset.

**Results (rules-only baseline, 100 records):**

| Metric | Score |
|---|---|
| Reason for visit accuracy | 74% |
| Follow-up accuracy | 75% |
| Vitals exact match rate | 79% |
| Interventions macro F1 | 0.706 |
| Problems macro F1 | 0.448 |

To run evaluation:

```bash
python3 -m src.run_pipeline        # generate predictions
python3 -m src.evaluate            # compute metrics → reports/metrics.json
```

---

## Project Structure

```
adi-visit-structurer/
├── app.py                        # Flask web application
├── abac.py                       # ABAC policy engine + SQLite user store
├── access_log_analysis.py        # Access log analytics
├── requirements.txt
├── src/
│   ├── preprocess.py             # Text cleaning
│   ├── extract_rules.py          # Rule-based NLP (single source of truth)
│   ├── normalize.py              # Label normalization
│   ├── quality.py                # Quality checks
│   ├── llm_extract.py            # Local LLM via Ollama (Mistral)
│   ├── schema.py                 # LLM output coercion
│   ├── run_pipeline.py           # Batch pipeline
│   ├── evaluate.py               # Evaluation metrics
│   ├── voice_input.py            # Audio transcription (faster-whisper)
│   ├── italian_numbers.py        # Italian word-to-number parser
│   ├── generate_reports.py       # HTML/text report generation
│   ├── export_reports.py         # CSV/dashboard export
│   └── resources/
│       └── problem_lexicon.py
├── data/
│   └── synthetic/
│       ├── raw/                  # 100 synthetic dictations
│       ├── gold/                 # 100 gold-standard JSON records
│       └── pred/                 # Pipeline predictions
├── tools/
│   ├── generate_dataset.py       # Synthetic dataset generator
│   └── validate_dataset.py       # Dataset schema validator
├── templates/
│   ├── index.html                # Clinical workspace dashboard
│   ├── finance.html              # Billing portal (finance role)
│   ├── admin.html                # Access analytics (admin role)
│   ├── login.html                # Login page
│   ├── register.html             # Registration page
│   ├── quiz.html                 # Clinical knowledge quiz
│   └── access_denied.html        # ABAC denial page
├── static/
│   ├── style.css
│   └── app.js
├── reports/                      # Generated metrics and summaries
├── schemas/
│   └── visit_schema_v1.json
└── tests/
    ├── test_abac.py              # ABAC policy engine tests (20 tests)
    ├── test_pipeline_rules.py
    └── test_normalize.py
```

---

## How to Run

### 1. Create environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. (Optional) Start LLM for hybrid mode

```bash
ollama serve
ollama pull mistral
```

The system works without Ollama — it falls back to rule-only mode automatically.

### 4. Run batch pipeline

```bash
python3 -m src.run_pipeline           # rules only (fast)
python3 -m src.run_pipeline --hybrid  # rules + LLM
```

### 5. Run evaluation

```bash
python3 -m src.evaluate
# → reports/metrics.json
```

### 6. Start web app

```bash
python3 app.py
# → http://127.0.0.1:5002
```

### 7. Run tests

```bash
pytest tests/
```

### 8. Analyse access log

```bash
python3 access_log_analysis.py
# → reports/access_analysis.json
```

---

## Notes

- This is a **prototype** developed for research and demonstration purposes
- The dataset is **fully synthetic** — no real patient data is used
- The system is **not intended for clinical use**
- Passwords are salted and hashed with SHA-256 before storage
- The ABAC policy engine is a pure function with no side effects — fully unit-tested

---

## Future Improvements

- Integration with real (anonymized) clinical datasets
- Improved speech recognition for Italian clinical vocabulary
- Fine-tuned LLM prompting for higher extraction accuracy
- Structured extraction of Bartel Index scores and pain assessment fields aligned with DR.ADI.02 standards
- Deployment as a hosted web service with production-grade secret management

---

## Author

**Maryam Amini**  
Data Analysis Student — University of Messina  
Internship: Cooperativa Servizi Sociali, Messina

**Repository:** https://github.com/imaryamini-code/adi-visit-structurer