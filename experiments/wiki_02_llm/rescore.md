# Re-score of experiments/wiki_02_llm with normalised follow-up

Follow-up is scored twice: as stored (scorer's own string parser) and after the phrase is parsed by the project's rules parser (same for every condition). Other metrics are unchanged.

## Scored against original

| condition | reason | follow-up as stored | follow-up normalised | vitals | int F1 | prob F1 |
|---|---|---|---|---|---|---|
| rules | 0.740 | 0.770 | 0.770 | 0.790 | 0.787 | 0.719 |
| llm+raw_mistral | 0.600 | 0.730 | 0.730 | 0.990 | 0.767 | 0.671 |
| llm+wiki_mistral | 0.650 | 0.860 | 0.860 | 0.960 | 0.786 | 0.745 |
| llm_mistral | 0.630 | 0.750 | 0.750 | 1.000 | 0.784 | 0.719 |

## Scored against reviewed_v1 (exploratory)

| condition | reason | follow-up as stored | follow-up normalised | vitals | int F1 | prob F1 |
|---|---|---|---|---|---|---|
| rules | 0.750 | 0.770 | 0.770 | 0.790 | 0.787 | 0.805 |
| llm+raw_mistral | 0.620 | 0.730 | 0.730 | 0.990 | 0.767 | 0.770 |
| llm+wiki_mistral | 0.680 | 0.860 | 0.860 | 0.960 | 0.786 | 0.850 |
| llm_mistral | 0.650 | 0.750 | 0.750 | 1.000 | 0.784 | 0.826 |

