# Statistics for experiments/wiki_03_llama (gold: data/synthetic/gold)

Bootstrap: 5000 resamples of 100 notes, seed 20261116. 95% percentile intervals.

## Each condition (point estimate [95% CI])

| condition | reason | follow-up | vitals | interventions F1 | problems F1 |
|---|---|---|---|---|---|
| rules | 0.740 [0.65, 0.82] | 0.770 [0.68, 0.85] | 0.790 [0.71, 0.87] | 0.787 [0.75, 0.83] | 0.719 [0.65, 0.78] |
| adaptive+raw_llama3.1_8b | 0.740 [0.65, 0.82] | 0.770 [0.69, 0.85] | 0.970 [0.93, 1.00] | 0.787 [0.75, 0.83] | 0.710 [0.63, 0.77] |
| adaptive+wiki_llama3.1_8b | 0.740 [0.65, 0.82] | 0.750 [0.67, 0.83] | 0.970 [0.93, 1.00] | 0.787 [0.75, 0.83] | 0.701 [0.63, 0.77] |
| adaptive_llama3.1_8b | 0.740 [0.65, 0.82] | 0.760 [0.68, 0.84] | 0.970 [0.93, 1.00] | 0.787 [0.75, 0.83] | 0.734 [0.67, 0.80] |
| hybrid+raw_llama3.1_8b | 0.740 [0.65, 0.82] | 0.770 [0.68, 0.85] | 0.790 [0.71, 0.87] | 0.787 [0.75, 0.83] | 0.694 [0.62, 0.76] |
| hybrid+wiki_llama3.1_8b | 0.740 [0.65, 0.82] | 0.770 [0.68, 0.85] | 0.790 [0.71, 0.87] | 0.787 [0.75, 0.83] | 0.689 [0.62, 0.76] |
| hybrid_llama3.1_8b | 0.740 [0.65, 0.82] | 0.770 [0.68, 0.85] | 0.790 [0.71, 0.87] | 0.787 [0.75, 0.83] | 0.721 [0.65, 0.78] |
| llm+raw_llama3.1_8b | 0.640 [0.54, 0.73] | 0.790 [0.71, 0.87] | 0.950 [0.91, 0.99] | 0.837 [0.80, 0.87] | 0.702 [0.62, 0.78] |
| llm+wiki_llama3.1_8b | 0.670 [0.58, 0.76] | 0.710 [0.62, 0.80] | 0.930 [0.88, 0.98] | 0.858 [0.82, 0.89] | 0.726 [0.64, 0.80] |
| llm_llama3.1_8b | 0.590 [0.49, 0.68] | 0.720 [0.63, 0.80] | 1.000 [1.00, 1.00] | 0.817 [0.78, 0.85] | 0.727 [0.65, 0.80] |

## Paired comparisons (B minus A)

Accuracy metrics: notes only A right / only B right and exact McNemar p. F1: difference and its paired 95% CI.
p-values are uncorrected for multiple comparisons: descriptive, not confirmatory.

| A | B | metric | A | B | difference | only A right / only B right | p (McNemar) or 95% CI of diff |
|---|---|---|---|---|---|---|---|
| rules | adaptive_llama3.1_8b | reason | 0.740 | 0.740 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | adaptive_llama3.1_8b | follow_up | 0.770 | 0.760 | -0.010 | 2 / 1 | p = 1.0000 |
| rules | adaptive_llama3.1_8b | vitals | 0.790 | 0.970 | +0.180 | 0 / 18 | p = 0.0000 |
| rules | adaptive_llama3.1_8b | interventions F1 | 0.787 | 0.787 | +0.000 | - | [+0.000, +0.000] |
| rules | adaptive_llama3.1_8b | problems F1 | 0.719 | 0.734 | +0.015 | - | [+0.000, +0.040] |
| rules | hybrid_llama3.1_8b | reason | 0.740 | 0.740 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_llama3.1_8b | follow_up | 0.770 | 0.770 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_llama3.1_8b | vitals | 0.790 | 0.790 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_llama3.1_8b | interventions F1 | 0.787 | 0.787 | +0.000 | - | [+0.000, +0.000] |
| rules | hybrid_llama3.1_8b | problems F1 | 0.719 | 0.721 | +0.002 | - | [-0.021, +0.031] |
| rules | llm_llama3.1_8b | reason | 0.740 | 0.590 | -0.150 | 20 / 5 | p = 0.0041 |
| rules | llm_llama3.1_8b | follow_up | 0.770 | 0.720 | -0.050 | 13 / 8 | p = 0.3833 |
| rules | llm_llama3.1_8b | vitals | 0.790 | 1.000 | +0.210 | 0 / 21 | p = 0.0000 |
| rules | llm_llama3.1_8b | interventions F1 | 0.787 | 0.817 | +0.030 | - | [-0.020, +0.078] |
| rules | llm_llama3.1_8b | problems F1 | 0.719 | 0.727 | +0.009 | - | [-0.030, +0.049] |
| adaptive_llama3.1_8b | adaptive+raw_llama3.1_8b | reason | 0.740 | 0.740 | +0.000 | 0 / 0 | p = 1.0000 |
| adaptive_llama3.1_8b | adaptive+raw_llama3.1_8b | follow_up | 0.760 | 0.770 | +0.010 | 0 / 1 | p = 1.0000 |
| adaptive_llama3.1_8b | adaptive+raw_llama3.1_8b | vitals | 0.970 | 0.970 | +0.000 | 0 / 0 | p = 1.0000 |
| adaptive_llama3.1_8b | adaptive+raw_llama3.1_8b | interventions F1 | 0.787 | 0.787 | +0.000 | - | [+0.000, +0.000] |
| adaptive_llama3.1_8b | adaptive+raw_llama3.1_8b | problems F1 | 0.734 | 0.710 | -0.024 | - | [-0.062, +0.000] |
| adaptive_llama3.1_8b | adaptive+wiki_llama3.1_8b | reason | 0.740 | 0.740 | +0.000 | 0 / 0 | p = 1.0000 |
| adaptive_llama3.1_8b | adaptive+wiki_llama3.1_8b | follow_up | 0.760 | 0.750 | -0.010 | 1 / 0 | p = 1.0000 |
| adaptive_llama3.1_8b | adaptive+wiki_llama3.1_8b | vitals | 0.970 | 0.970 | +0.000 | 0 / 0 | p = 1.0000 |
| adaptive_llama3.1_8b | adaptive+wiki_llama3.1_8b | interventions F1 | 0.787 | 0.787 | +0.000 | - | [+0.000, +0.000] |
| adaptive_llama3.1_8b | adaptive+wiki_llama3.1_8b | problems F1 | 0.734 | 0.701 | -0.033 | - | [-0.066, -0.008] |
| hybrid_llama3.1_8b | hybrid+raw_llama3.1_8b | reason | 0.740 | 0.740 | +0.000 | 0 / 0 | p = 1.0000 |
| hybrid_llama3.1_8b | hybrid+raw_llama3.1_8b | follow_up | 0.770 | 0.770 | +0.000 | 0 / 0 | p = 1.0000 |
| hybrid_llama3.1_8b | hybrid+raw_llama3.1_8b | vitals | 0.790 | 0.790 | +0.000 | 0 / 0 | p = 1.0000 |
| hybrid_llama3.1_8b | hybrid+raw_llama3.1_8b | interventions F1 | 0.787 | 0.787 | +0.000 | - | [+0.000, +0.000] |
| hybrid_llama3.1_8b | hybrid+raw_llama3.1_8b | problems F1 | 0.721 | 0.694 | -0.027 | - | [-0.068, +0.001] |
| hybrid_llama3.1_8b | hybrid+wiki_llama3.1_8b | reason | 0.740 | 0.740 | +0.000 | 0 / 0 | p = 1.0000 |
| hybrid_llama3.1_8b | hybrid+wiki_llama3.1_8b | follow_up | 0.770 | 0.770 | +0.000 | 0 / 0 | p = 1.0000 |
| hybrid_llama3.1_8b | hybrid+wiki_llama3.1_8b | vitals | 0.790 | 0.790 | +0.000 | 0 / 0 | p = 1.0000 |
| hybrid_llama3.1_8b | hybrid+wiki_llama3.1_8b | interventions F1 | 0.787 | 0.787 | +0.000 | - | [+0.000, +0.000] |
| hybrid_llama3.1_8b | hybrid+wiki_llama3.1_8b | problems F1 | 0.721 | 0.689 | -0.032 | - | [-0.065, -0.004] |
| llm_llama3.1_8b | llm+raw_llama3.1_8b | reason | 0.590 | 0.640 | +0.050 | 3 / 8 | p = 0.2266 |
| llm_llama3.1_8b | llm+raw_llama3.1_8b | follow_up | 0.720 | 0.790 | +0.070 | 0 / 7 | p = 0.0156 |
| llm_llama3.1_8b | llm+raw_llama3.1_8b | vitals | 1.000 | 0.950 | -0.050 | 5 / 0 | p = 0.0625 |
| llm_llama3.1_8b | llm+raw_llama3.1_8b | interventions F1 | 0.817 | 0.837 | +0.020 | - | [-0.019, +0.058] |
| llm_llama3.1_8b | llm+raw_llama3.1_8b | problems F1 | 0.727 | 0.702 | -0.025 | - | [-0.089, +0.031] |
| llm_llama3.1_8b | llm+wiki_llama3.1_8b | reason | 0.590 | 0.670 | +0.080 | 6 / 14 | p = 0.1153 |
| llm_llama3.1_8b | llm+wiki_llama3.1_8b | follow_up | 0.720 | 0.710 | -0.010 | 13 / 12 | p = 1.0000 |
| llm_llama3.1_8b | llm+wiki_llama3.1_8b | vitals | 1.000 | 0.930 | -0.070 | 7 / 0 | p = 0.0156 |
| llm_llama3.1_8b | llm+wiki_llama3.1_8b | interventions F1 | 0.817 | 0.858 | +0.041 | - | [+0.005, +0.077] |
| llm_llama3.1_8b | llm+wiki_llama3.1_8b | problems F1 | 0.727 | 0.726 | -0.001 | - | [-0.055, +0.044] |
