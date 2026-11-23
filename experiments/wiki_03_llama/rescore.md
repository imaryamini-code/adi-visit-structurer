# Re-score of experiments/wiki_03_llama with normalised follow-up

Follow-up is scored twice: as stored (scorer's own string parser) and after the phrase is parsed by the project's rules parser (same for every condition). Other metrics are unchanged.

## Scored against original

| condition | reason | follow-up as stored | follow-up normalised | vitals | int F1 | prob F1 |
|---|---|---|---|---|---|---|
| rules | 0.740 | 0.770 | 0.770 | 0.790 | 0.787 | 0.719 |
| adaptive+raw_llama3.1_8b | 0.740 | 0.770 | 0.770 | 0.970 | 0.787 | 0.710 |
| adaptive+wiki_llama3.1_8b | 0.740 | 0.750 | 0.750 | 0.970 | 0.787 | 0.701 |
| adaptive_llama3.1_8b | 0.740 | 0.760 | 0.760 | 0.970 | 0.787 | 0.734 |
| hybrid+raw_llama3.1_8b | 0.740 | 0.770 | 0.770 | 0.790 | 0.787 | 0.694 |
| hybrid+wiki_llama3.1_8b | 0.740 | 0.770 | 0.770 | 0.790 | 0.787 | 0.689 |
| hybrid_llama3.1_8b | 0.740 | 0.770 | 0.770 | 0.790 | 0.787 | 0.721 |
| llm+raw_llama3.1_8b | 0.640 | 0.790 | 0.790 | 0.950 | 0.837 | 0.702 |
| llm+wiki_llama3.1_8b | 0.670 | 0.710 | 0.710 | 0.930 | 0.858 | 0.726 |
| llm_llama3.1_8b | 0.590 | 0.720 | 0.720 | 1.000 | 0.817 | 0.727 |

## Scored against reviewed_v1 (exploratory)

| condition | reason | follow-up as stored | follow-up normalised | vitals | int F1 | prob F1 |
|---|---|---|---|---|---|---|
| rules | 0.750 | 0.770 | 0.770 | 0.790 | 0.787 | 0.805 |
| adaptive+raw_llama3.1_8b | 0.750 | 0.770 | 0.770 | 0.970 | 0.787 | 0.795 |
| adaptive+wiki_llama3.1_8b | 0.750 | 0.750 | 0.750 | 0.970 | 0.787 | 0.782 |
| adaptive_llama3.1_8b | 0.750 | 0.760 | 0.760 | 0.970 | 0.787 | 0.808 |
| hybrid+raw_llama3.1_8b | 0.750 | 0.770 | 0.770 | 0.790 | 0.787 | 0.774 |
| hybrid+wiki_llama3.1_8b | 0.750 | 0.770 | 0.770 | 0.790 | 0.787 | 0.767 |
| hybrid_llama3.1_8b | 0.750 | 0.770 | 0.770 | 0.790 | 0.787 | 0.792 |
| llm+raw_llama3.1_8b | 0.670 | 0.790 | 0.790 | 0.950 | 0.837 | 0.797 |
| llm+wiki_llama3.1_8b | 0.670 | 0.710 | 0.710 | 0.930 | 0.858 | 0.820 |
| llm_llama3.1_8b | 0.620 | 0.720 | 0.720 | 1.000 | 0.817 | 0.803 |

