# ADI Visit Structurer

Structured clinical data extraction from Italian ADI (Assistenza Domiciliare Integrata) home-visit notes using:

- Rule-based NLP
- Hybrid LLM + rules pipeline
- Local LLM via Ollama API
- Automated evaluation metrics

---

## 🎯 Project Goal

Transform unstructured Italian clinical visit notes into standardized structured JSON records containing:

- Reason for visit  
- Follow-up  
- Interventions  
- Vital signs  
- Normalized clinical problems  

The system supports both:

1. Rule-based extraction  
2. Hybrid extraction (LLM + rules)

---

## 🧠 Architecture

Raw Clinical Text  
↓  
Preprocessing  
↓  
Extraction Layer  
├── Rule-based extractors  
├── LLM extractor (Ollama API)  
↓  
Postprocessing & Normalization  
↓  
Quality Checks  
↓  
Structured JSON Output  
↓  
Evaluation Metrics  

---

## ⚙️ Modes

### 1️⃣ Rule-Based Mode

Uses regex and deterministic logic to extract:

- Blood pressure  
- Heart rate  
- Temperature  
- SpO₂  
- Interventions  
- Follow-up  

Run:

```bash
python -m src.run_pipeline
```

---

### 2️⃣ Hybrid Mode (Recommended)

Uses:

- LLM (Ollama) for free-text reasoning  
- Rules for vitals (more reliable)  
- Controlled vocabulary normalization  

Run:

```bash
python -m src.run_pipeline --hybrid
```

---

## 🤖 LLM Backend

This project uses **Ollama (local LLM API)**.

Model used:

```
llama3.1:8b
```

### Install Ollama

```bash
brew install ollama
ollama pull llama3.1:8b
```

Make sure Ollama is running:

```bash
ollama list
```

---

## 📊 Evaluation

After generating structured outputs:

```bash
python -m src.evaluate
```

Metrics reported:

- Text field accuracy  
- Vitals exact match rate  
- Macro F1 (interventions)  
- Macro F1 (normalized problems)  

Example results (Hybrid mode):

- Text field accuracy: 1.00  
- Vitals exact match: ~0.92–1.00  
- Interventions F1: 1.00  
- Problems F1: ~0.95  

---

## 🧪 Dataset

Synthetic dataset:

```
data/synthetic/raw/
data/synthetic/gold/
```

Total records: 13  

---

## 🧼 Postprocessing

Includes:

- Canonical follow-up normalization  
  (e.g., "3 giorni" → "programmato controllo tra 3 giorni")

- Intervention vocabulary mapping  
  (e.g., "rilevati parametri" → "controllo_parametri_vitali")

- Robust vital sign fallback regex  

---

## 🔐 Security

- `.env` is ignored  
- No secrets stored in repository  
- Ollama runs fully local  

---

## 📁 Project Structure

```
src/
├── preprocess.py
├── extract_rules.py
├── normalize.py
├── llm_extract.py
├── run_pipeline.py
└── evaluate.py

data/
reports/
```

---

## 👩‍💻 Author

Maryam Amini  
Data Analysis Student  
University of Messina  

---

## 📌 Summary

This project demonstrates:

- Hybrid NLP pipeline design  
- Structured information extraction  
- Local LLM integration via API  
- Evaluation-driven development  
- Clean software engineering practices