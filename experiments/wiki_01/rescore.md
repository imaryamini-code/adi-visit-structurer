# Re-score of experiments/wiki_01 with normalised follow-up

Follow-up is scored twice: as stored (scorer's own string parser) and after the phrase is parsed by the project's rules parser (same for every condition). Other metrics are unchanged.

## Scored against original

| condition | reason | follow-up as stored | follow-up normalised | vitals | int F1 | prob F1 |
|---|---|---|---|---|---|---|
| rules | 0.740 | 0.770 | 0.770 | 0.790 | 0.787 | 0.719 |
| adaptive+raw_mistral | 0.740 | 0.770 | 0.770 | 0.970 | 0.787 | 0.718 |
| adaptive+wiki_mistral | 0.740 | 0.780 | 0.780 | 0.970 | 0.787 | 0.722 |
| adaptive_mistral | 0.740 | 0.770 | 0.770 | 0.970 | 0.787 | 0.718 |
| hybrid+raw_mistral | 0.740 | 0.770 | 0.770 | 0.790 | 0.787 | 0.718 |
| hybrid+wiki_mistral | 0.740 | 0.770 | 0.770 | 0.790 | 0.787 | 0.718 |
| hybrid_mistral | 0.740 | 0.770 | 0.770 | 0.790 | 0.787 | 0.718 |

## Scored against reviewed_v1 (exploratory)

| condition | reason | follow-up as stored | follow-up normalised | vitals | int F1 | prob F1 |
|---|---|---|---|---|---|---|
| rules | 0.750 | 0.770 | 0.770 | 0.790 | 0.787 | 0.805 |
| adaptive+raw_mistral | 0.750 | 0.770 | 0.770 | 0.970 | 0.787 | 0.803 |
| adaptive+wiki_mistral | 0.750 | 0.780 | 0.780 | 0.970 | 0.787 | 0.808 |
| adaptive_mistral | 0.750 | 0.770 | 0.770 | 0.970 | 0.787 | 0.803 |
| hybrid+raw_mistral | 0.750 | 0.770 | 0.770 | 0.790 | 0.787 | 0.803 |
| hybrid+wiki_mistral | 0.750 | 0.770 | 0.770 | 0.790 | 0.787 | 0.803 |
| hybrid_mistral | 0.750 | 0.770 | 0.770 | 0.790 | 0.787 | 0.803 |

