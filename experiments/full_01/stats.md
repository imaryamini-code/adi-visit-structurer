# Statistics for experiments/full_01 (gold: data/synthetic/gold)

Bootstrap: 5000 resamples of 100 notes, seed 20261116. 95% percentile intervals.

## Each condition (point estimate [95% CI])

| condition | reason | follow-up | vitals | interventions F1 | problems F1 |
|---|---|---|---|---|---|
| rules | 0.740 [0.65, 0.82] | 0.770 [0.68, 0.85] | 0.790 [0.71, 0.87] | 0.787 [0.75, 0.83] | 0.719 [0.65, 0.78] |
| adaptive_llama3.1_8b | 0.740 [0.65, 0.82] | 0.760 [0.68, 0.84] | 0.970 [0.93, 1.00] | 0.787 [0.75, 0.83] | 0.734 [0.67, 0.80] |
| adaptive_mistral | 0.740 [0.65, 0.82] | 0.770 [0.68, 0.85] | 0.970 [0.93, 1.00] | 0.787 [0.75, 0.83] | 0.718 [0.65, 0.78] |
| hybrid_llama3.1_8b | 0.740 [0.65, 0.82] | 0.770 [0.68, 0.85] | 0.790 [0.71, 0.87] | 0.787 [0.75, 0.83] | 0.721 [0.65, 0.78] |
| hybrid_mistral | 0.740 [0.65, 0.82] | 0.770 [0.68, 0.85] | 0.790 [0.71, 0.87] | 0.787 [0.75, 0.83] | 0.718 [0.65, 0.78] |
| llm_llama3.1_8b | 0.590 [0.49, 0.68] | 0.720 [0.63, 0.80] | 1.000 [1.00, 1.00] | 0.817 [0.78, 0.85] | 0.727 [0.65, 0.80] |
| llm_mistral | 0.630 [0.53, 0.72] | 0.750 [0.66, 0.83] | 1.000 [1.00, 1.00] | 0.784 [0.74, 0.82] | 0.719 [0.62, 0.80] |

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
| rules | adaptive_mistral | reason | 0.740 | 0.740 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | adaptive_mistral | follow_up | 0.770 | 0.770 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | adaptive_mistral | vitals | 0.790 | 0.970 | +0.180 | 0 / 18 | p = 0.0000 |
| rules | adaptive_mistral | interventions F1 | 0.787 | 0.787 | +0.000 | - | [+0.000, +0.000] |
| rules | adaptive_mistral | problems F1 | 0.719 | 0.718 | -0.001 | - | [-0.019, +0.020] |
| rules | hybrid_llama3.1_8b | reason | 0.740 | 0.740 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_llama3.1_8b | follow_up | 0.770 | 0.770 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_llama3.1_8b | vitals | 0.790 | 0.790 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_llama3.1_8b | interventions F1 | 0.787 | 0.787 | +0.000 | - | [+0.000, +0.000] |
| rules | hybrid_llama3.1_8b | problems F1 | 0.719 | 0.721 | +0.002 | - | [-0.021, +0.031] |
| rules | hybrid_mistral | reason | 0.740 | 0.740 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_mistral | follow_up | 0.770 | 0.770 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_mistral | vitals | 0.790 | 0.790 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_mistral | interventions F1 | 0.787 | 0.787 | +0.000 | - | [+0.000, +0.000] |
| rules | hybrid_mistral | problems F1 | 0.719 | 0.718 | -0.001 | - | [-0.019, +0.020] |
| rules | llm_llama3.1_8b | reason | 0.740 | 0.590 | -0.150 | 20 / 5 | p = 0.0041 |
| rules | llm_llama3.1_8b | follow_up | 0.770 | 0.720 | -0.050 | 13 / 8 | p = 0.3833 |
| rules | llm_llama3.1_8b | vitals | 0.790 | 1.000 | +0.210 | 0 / 21 | p = 0.0000 |
| rules | llm_llama3.1_8b | interventions F1 | 0.787 | 0.817 | +0.030 | - | [-0.020, +0.078] |
| rules | llm_llama3.1_8b | problems F1 | 0.719 | 0.727 | +0.009 | - | [-0.030, +0.049] |
| rules | llm_mistral | reason | 0.740 | 0.630 | -0.110 | 16 / 5 | p = 0.0266 |
| rules | llm_mistral | follow_up | 0.770 | 0.750 | -0.020 | 8 / 6 | p = 0.7905 |
| rules | llm_mistral | vitals | 0.790 | 1.000 | +0.210 | 0 / 21 | p = 0.0000 |
| rules | llm_mistral | interventions F1 | 0.787 | 0.784 | -0.003 | - | [-0.062, +0.054] |
| rules | llm_mistral | problems F1 | 0.719 | 0.719 | +0.001 | - | [-0.076, +0.069] |
