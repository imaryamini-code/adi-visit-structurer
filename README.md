# ADI Visit Structurer

Structured extraction pipeline for Italian ADI (Assistenza Domiciliare Integrata) home-visit clinical notes.

## 🎯 Goal

Transform unstructured clinical dictations into structured JSON compliant with a predefined schema.

The system extracts:

- Visit metadata (datetime, operator)
- Reason for visit
- Vital signs (BP, HR, temperature, SpO2)
- Interventions
- Follow-up
- Normalized clinical problems
- Quality validation flags

---

## 🏗 Architecture

Pipeline flow:

raw text  
→ preprocessing  
→ rule-based extraction  
→ normalization (controlled vocabulary)  
→ quality validation  
→ JSON output  
→ evaluation metrics  

Core modules:

- `extract_rules.py` → structured extraction
- `normalize.py` → controlled vocabulary mapping
- `quality.py` → safety checks & warnings
- `run_pipeline.py` → main processing engine
- `evaluate.py` → metrics computation

---

## 🚀 How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt