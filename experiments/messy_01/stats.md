# Statistics for experiments/messy_01 (gold: data/synthetic/gold)

Bootstrap: 5000 resamples of 100 notes, seed 20261116. 95% percentile intervals.

## Each condition (point estimate [95% CI])

| condition | reason | follow-up | vitals | interventions F1 | problems F1 |
|---|---|---|---|---|---|
| rules | 0.740 [0.65, 0.82] | 0.730 [0.64, 0.82] | 0.600 [0.50, 0.69] | 0.793 [0.75, 0.83] | 0.675 [0.59, 0.75] |
| adaptive_llama3.1_8b | 0.740 [0.65, 0.82] | 0.760 [0.67, 0.84] | 0.960 [0.92, 0.99] | 0.793 [0.75, 0.83] | 0.695 [0.61, 0.77] |
| adaptive_mistral | 0.740 [0.65, 0.82] | 0.740 [0.65, 0.82] | 0.960 [0.92, 0.99] | 0.793 [0.75, 0.83] | 0.683 [0.60, 0.76] |
| hybrid_llama3.1_8b | 0.740 [0.65, 0.82] | 0.730 [0.64, 0.82] | 0.600 [0.50, 0.69] | 0.793 [0.75, 0.83] | 0.698 [0.62, 0.76] |
| hybrid_mistral | 0.740 [0.65, 0.82] | 0.730 [0.64, 0.82] | 0.600 [0.50, 0.69] | 0.793 [0.75, 0.83] | 0.714 [0.64, 0.78] |
| llm_llama3.1_8b | 0.600 [0.50, 0.69] | 0.730 [0.64, 0.82] | 1.000 [1.00, 1.00] | 0.837 [0.80, 0.87] | 0.691 [0.61, 0.76] |
| llm_mistral | 0.620 [0.52, 0.71] | 0.720 [0.63, 0.81] | 0.990 [0.97, 1.00] | 0.773 [0.73, 0.82] | 0.718 [0.62, 0.80] |

## Paired comparisons (B minus A)

Accuracy metrics: notes only A right / only B right and exact McNemar p. F1: difference and its paired 95% CI.
p-values are uncorrected for multiple comparisons: descriptive, not confirmatory.

| A | B | metric | A | B | difference | only A right / only B right | p (McNemar) or 95% CI of diff |
|---|---|---|---|---|---|---|---|
| rules | adaptive_llama3.1_8b | reason | 0.740 | 0.740 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | adaptive_llama3.1_8b | follow_up | 0.730 | 0.760 | +0.030 | 0 / 3 | p = 0.2500 |
| rules | adaptive_llama3.1_8b | vitals | 0.600 | 0.960 | +0.360 | 0 / 36 | p = 0.0000 |
| rules | adaptive_llama3.1_8b | interventions F1 | 0.793 | 0.793 | +0.000 | - | [+0.000, +0.000] |
| rules | adaptive_llama3.1_8b | problems F1 | 0.675 | 0.695 | +0.020 | - | [-0.004, +0.053] |
| rules | adaptive_mistral | reason | 0.740 | 0.740 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | adaptive_mistral | follow_up | 0.730 | 0.740 | +0.010 | 0 / 1 | p = 1.0000 |
| rules | adaptive_mistral | vitals | 0.600 | 0.960 | +0.360 | 0 / 36 | p = 0.0000 |
| rules | adaptive_mistral | interventions F1 | 0.793 | 0.793 | +0.000 | - | [+0.000, +0.000] |
| rules | adaptive_mistral | problems F1 | 0.675 | 0.683 | +0.008 | - | [-0.014, +0.037] |
| rules | hybrid_llama3.1_8b | reason | 0.740 | 0.740 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_llama3.1_8b | follow_up | 0.730 | 0.730 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_llama3.1_8b | vitals | 0.600 | 0.600 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_llama3.1_8b | interventions F1 | 0.793 | 0.793 | +0.000 | - | [+0.000, +0.000] |
| rules | hybrid_llama3.1_8b | problems F1 | 0.675 | 0.698 | +0.023 | - | [-0.018, +0.069] |
| rules | hybrid_mistral | reason | 0.740 | 0.740 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_mistral | follow_up | 0.730 | 0.730 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_mistral | vitals | 0.600 | 0.600 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_mistral | interventions F1 | 0.793 | 0.793 | +0.000 | - | [+0.000, +0.000] |
| rules | hybrid_mistral | problems F1 | 0.675 | 0.714 | +0.039 | - | [+0.003, +0.082] |
| rules | llm_llama3.1_8b | reason | 0.740 | 0.600 | -0.140 | 21 / 7 | p = 0.0125 |
| rules | llm_llama3.1_8b | follow_up | 0.730 | 0.730 | +0.000 | 11 / 11 | p = 1.0000 |
| rules | llm_llama3.1_8b | vitals | 0.600 | 1.000 | +0.400 | 0 / 40 | p = 0.0000 |
| rules | llm_llama3.1_8b | interventions F1 | 0.793 | 0.837 | +0.045 | - | [+0.002, +0.087] |
| rules | llm_llama3.1_8b | problems F1 | 0.675 | 0.691 | +0.016 | - | [-0.037, +0.071] |
| rules | llm_mistral | reason | 0.740 | 0.620 | -0.120 | 20 / 8 | p = 0.0357 |
| rules | llm_mistral | follow_up | 0.730 | 0.720 | -0.010 | 8 / 7 | p = 1.0000 |
| rules | llm_mistral | vitals | 0.600 | 0.990 | +0.390 | 0 / 39 | p = 0.0000 |
| rules | llm_mistral | interventions F1 | 0.793 | 0.773 | -0.020 | - | [-0.072, +0.032] |
| rules | llm_mistral | problems F1 | 0.675 | 0.718 | +0.043 | - | [-0.040, +0.125] |
