# Statistics for experiments/wiki_02_llm (gold: data/synthetic/gold)

Bootstrap: 5000 resamples of 100 notes, seed 20261116. 95% percentile intervals.

## Each condition (point estimate [95% CI])

| condition | reason | follow-up | vitals | interventions F1 | problems F1 |
|---|---|---|---|---|---|
| rules | 0.740 [0.65, 0.82] | 0.770 [0.68, 0.85] | 0.790 [0.71, 0.87] | 0.787 [0.75, 0.83] | 0.719 [0.65, 0.78] |
| llm+raw_mistral | 0.600 [0.50, 0.70] | 0.730 [0.64, 0.81] | 0.990 [0.97, 1.00] | 0.767 [0.71, 0.82] | 0.671 [0.57, 0.76] |
| llm+wiki_mistral | 0.650 [0.55, 0.74] | 0.860 [0.79, 0.92] | 0.960 [0.92, 0.99] | 0.786 [0.74, 0.83] | 0.745 [0.66, 0.82] |
| llm_mistral | 0.630 [0.53, 0.72] | 0.750 [0.66, 0.83] | 1.000 [1.00, 1.00] | 0.784 [0.74, 0.82] | 0.719 [0.62, 0.80] |

## Paired comparisons (B minus A)

Accuracy metrics: notes only A right / only B right and exact McNemar p. F1: difference and its paired 95% CI.
p-values are uncorrected for multiple comparisons: descriptive, not confirmatory.

| A | B | metric | A | B | difference | only A right / only B right | p (McNemar) or 95% CI of diff |
|---|---|---|---|---|---|---|---|
| rules | llm_mistral | reason | 0.740 | 0.630 | -0.110 | 16 / 5 | p = 0.0266 |
| rules | llm_mistral | follow_up | 0.770 | 0.750 | -0.020 | 8 / 6 | p = 0.7905 |
| rules | llm_mistral | vitals | 0.790 | 1.000 | +0.210 | 0 / 21 | p = 0.0000 |
| rules | llm_mistral | interventions F1 | 0.787 | 0.784 | -0.003 | - | [-0.062, +0.054] |
| rules | llm_mistral | problems F1 | 0.719 | 0.719 | +0.001 | - | [-0.076, +0.069] |
| llm_mistral | llm+raw_mistral | reason | 0.630 | 0.600 | -0.030 | 5 / 2 | p = 0.4531 |
| llm_mistral | llm+raw_mistral | follow_up | 0.750 | 0.730 | -0.020 | 3 / 1 | p = 0.6250 |
| llm_mistral | llm+raw_mistral | vitals | 1.000 | 0.990 | -0.010 | 1 / 0 | p = 1.0000 |
| llm_mistral | llm+raw_mistral | interventions F1 | 0.784 | 0.767 | -0.017 | - | [-0.061, +0.028] |
| llm_mistral | llm+raw_mistral | problems F1 | 0.719 | 0.671 | -0.048 | - | [-0.103, +0.000] |
| llm_mistral | llm+wiki_mistral | reason | 0.630 | 0.650 | +0.020 | 4 / 6 | p = 0.7539 |
| llm_mistral | llm+wiki_mistral | follow_up | 0.750 | 0.860 | +0.110 | 3 / 14 | p = 0.0127 |
| llm_mistral | llm+wiki_mistral | vitals | 1.000 | 0.960 | -0.040 | 4 / 0 | p = 0.1250 |
| llm_mistral | llm+wiki_mistral | interventions F1 | 0.784 | 0.786 | +0.002 | - | [-0.043, +0.049] |
| llm_mistral | llm+wiki_mistral | problems F1 | 0.719 | 0.745 | +0.025 | - | [-0.031, +0.085] |
