# Routing replay of experiments/full_01

LLM answers come only from the run's saved cache; no model was called. Scores: reason / follow-up / vitals accuracy, micro-F1 interventions / problems.

## mistral, scored against original

| variant | reason | follow-up | vitals | int F1 | prob F1 | LLM-called notes | flagged notes |
|---|---|---|---|---|---|---|---|
| default (flag generic reason) | 0.740 | 0.770 | 0.970 | 0.787 | 0.718 | 60 | 11 |
| prefer_llm for generic reason | 0.740 | 0.770 | 0.970 | 0.787 | 0.718 | 60 | 11 |
| no escalation for empty problems | 0.740 | 0.770 | 0.970 | 0.787 | 0.719 | 57 | 11 |
| no grounding check | 0.740 | 0.770 | 0.970 | 0.787 | 0.718 | 60 | 11 |
| vitals only (all else rules) | 0.740 | 0.770 | 0.970 | 0.787 | 0.719 | 19 | 1 |

## mistral, scored against reviewed_v1 (exploratory)

| variant | reason | follow-up | vitals | int F1 | prob F1 | LLM-called notes | flagged notes |
|---|---|---|---|---|---|---|---|
| default (flag generic reason) | 0.750 | 0.770 | 0.970 | 0.787 | 0.803 | 60 | 11 |
| prefer_llm for generic reason | 0.750 | 0.770 | 0.970 | 0.787 | 0.803 | 60 | 11 |
| no escalation for empty problems | 0.750 | 0.770 | 0.970 | 0.787 | 0.805 | 57 | 11 |
| no grounding check | 0.750 | 0.770 | 0.970 | 0.787 | 0.803 | 60 | 11 |
| vitals only (all else rules) | 0.750 | 0.770 | 0.970 | 0.787 | 0.805 | 19 | 1 |

## llama3.1:8b, scored against original

| variant | reason | follow-up | vitals | int F1 | prob F1 | LLM-called notes | flagged notes |
|---|---|---|---|---|---|---|---|
| default (flag generic reason) | 0.740 | 0.760 | 0.970 | 0.787 | 0.734 | 60 | 8 |
| prefer_llm for generic reason | 0.740 | 0.760 | 0.970 | 0.787 | 0.734 | 60 | 8 |
| no escalation for empty problems | 0.740 | 0.760 | 0.970 | 0.787 | 0.719 | 57 | 8 |
| no grounding check | 0.740 | 0.760 | 0.970 | 0.787 | 0.734 | 60 | 8 |
| vitals only (all else rules) | 0.740 | 0.770 | 0.970 | 0.787 | 0.719 | 19 | 1 |

## llama3.1:8b, scored against reviewed_v1 (exploratory)

| variant | reason | follow-up | vitals | int F1 | prob F1 | LLM-called notes | flagged notes |
|---|---|---|---|---|---|---|---|
| default (flag generic reason) | 0.750 | 0.760 | 0.970 | 0.787 | 0.808 | 60 | 8 |
| prefer_llm for generic reason | 0.750 | 0.760 | 0.970 | 0.787 | 0.808 | 60 | 8 |
| no escalation for empty problems | 0.750 | 0.760 | 0.970 | 0.787 | 0.805 | 57 | 8 |
| no grounding check | 0.750 | 0.760 | 0.970 | 0.787 | 0.808 | 60 | 8 |
| vitals only (all else rules) | 0.750 | 0.770 | 0.970 | 0.787 | 0.805 | 19 | 1 |

