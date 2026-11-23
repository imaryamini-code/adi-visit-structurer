# Re-score of experiments/messy_01 with normalised follow-up

Follow-up is scored twice: as stored (scorer's own string parser) and after the phrase is parsed by the project's rules parser (same for every condition). Other metrics are unchanged.

## Scored against original

| condition | reason | follow-up as stored | follow-up normalised | vitals | int F1 | prob F1 |
|---|---|---|---|---|---|---|
| rules | 0.740 | 0.730 | 0.730 | 0.600 | 0.793 | 0.675 |
| adaptive_llama3.1_8b | 0.740 | 0.760 | 0.760 | 0.960 | 0.793 | 0.695 |
| adaptive_mistral | 0.740 | 0.740 | 0.740 | 0.960 | 0.793 | 0.683 |
| hybrid_llama3.1_8b | 0.740 | 0.730 | 0.730 | 0.600 | 0.793 | 0.698 |
| hybrid_mistral | 0.740 | 0.730 | 0.730 | 0.600 | 0.793 | 0.714 |
| llm_llama3.1_8b | 0.600 | 0.730 | 0.730 | 1.000 | 0.837 | 0.691 |
| llm_mistral | 0.620 | 0.720 | 0.720 | 0.990 | 0.773 | 0.718 |

## Scored against reviewed_v1 (exploratory)

| condition | reason | follow-up as stored | follow-up normalised | vitals | int F1 | prob F1 |
|---|---|---|---|---|---|---|
| rules | 0.730 | 0.730 | 0.730 | 0.600 | 0.793 | 0.761 |
| adaptive_llama3.1_8b | 0.730 | 0.760 | 0.760 | 0.960 | 0.793 | 0.767 |
| adaptive_mistral | 0.730 | 0.740 | 0.740 | 0.960 | 0.793 | 0.767 |
| hybrid_llama3.1_8b | 0.730 | 0.730 | 0.730 | 0.600 | 0.793 | 0.766 |
| hybrid_mistral | 0.730 | 0.730 | 0.730 | 0.600 | 0.793 | 0.800 |
| llm_llama3.1_8b | 0.600 | 0.730 | 0.730 | 1.000 | 0.837 | 0.762 |
| llm_mistral | 0.630 | 0.720 | 0.720 | 0.990 | 0.773 | 0.823 |

