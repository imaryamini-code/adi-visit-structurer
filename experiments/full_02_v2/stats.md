# Statistics for experiments/full_02_v2 (gold: data/synthetic/gold)

Bootstrap: 5000 resamples of 100 notes, seed 20261116. 95% percentile intervals.

## Each condition (point estimate [95% CI])

| condition | reason | follow-up | vitals | interventions F1 | problems F1 |
|---|---|---|---|---|---|
| rules | 0.870 [0.80, 0.93] | 0.930 [0.88, 0.97] | 0.790 [0.71, 0.87] | 0.797 [0.76, 0.83] | 0.851 [0.78, 0.91] |
| adaptive+raw_llama3.1_8b | 0.870 [0.80, 0.93] | 0.920 [0.86, 0.97] | 0.970 [0.93, 1.00] | 0.797 [0.76, 0.83] | 0.839 [0.76, 0.90] |
| adaptive+raw_mistral | 0.870 [0.80, 0.93] | 0.930 [0.88, 0.97] | 0.970 [0.93, 1.00] | 0.797 [0.76, 0.83] | 0.847 [0.78, 0.91] |
| adaptive+wiki_llama3.1_8b | 0.870 [0.80, 0.93] | 0.910 [0.85, 0.96] | 0.970 [0.93, 1.00] | 0.797 [0.76, 0.83] | 0.824 [0.75, 0.89] |
| adaptive+wiki_mistral | 0.870 [0.80, 0.93] | 0.930 [0.88, 0.97] | 0.970 [0.93, 1.00] | 0.797 [0.76, 0.83] | 0.853 [0.78, 0.91] |
| adaptive_llama3.1_8b | 0.870 [0.80, 0.93] | 0.910 [0.85, 0.96] | 0.970 [0.93, 1.00] | 0.797 [0.76, 0.83] | 0.867 [0.80, 0.92] |
| adaptive_mistral | 0.870 [0.80, 0.93] | 0.930 [0.88, 0.97] | 0.970 [0.93, 1.00] | 0.797 [0.76, 0.83] | 0.847 [0.78, 0.91] |
| hybrid+raw_llama3.1_8b | 0.870 [0.80, 0.93] | 0.930 [0.88, 0.97] | 0.790 [0.71, 0.87] | 0.797 [0.76, 0.83] | 0.789 [0.71, 0.86] |
| hybrid+raw_mistral | 0.870 [0.80, 0.93] | 0.930 [0.88, 0.97] | 0.790 [0.71, 0.87] | 0.797 [0.76, 0.83] | 0.792 [0.71, 0.86] |
| hybrid+wiki_llama3.1_8b | 0.870 [0.80, 0.93] | 0.930 [0.88, 0.97] | 0.790 [0.71, 0.87] | 0.797 [0.76, 0.83] | 0.777 [0.70, 0.85] |
| hybrid+wiki_mistral | 0.870 [0.80, 0.93] | 0.930 [0.88, 0.97] | 0.790 [0.71, 0.87] | 0.797 [0.76, 0.83] | 0.803 [0.73, 0.87] |
| hybrid_llama3.1_8b | 0.870 [0.80, 0.93] | 0.930 [0.88, 0.97] | 0.790 [0.71, 0.87] | 0.797 [0.76, 0.83] | 0.832 [0.76, 0.90] |
| hybrid_mistral | 0.870 [0.80, 0.93] | 0.930 [0.88, 0.97] | 0.790 [0.71, 0.87] | 0.797 [0.76, 0.83] | 0.808 [0.73, 0.88] |
| llm+raw_llama3.1_8b | 0.640 [0.54, 0.73] | 0.870 [0.80, 0.93] | 0.950 [0.91, 0.99] | 0.837 [0.80, 0.87] | 0.736 [0.65, 0.82] |
| llm+raw_mistral | 0.600 [0.50, 0.70] | 0.840 [0.77, 0.91] | 0.990 [0.97, 1.00] | 0.767 [0.71, 0.82] | 0.676 [0.57, 0.76] |
| llm+wiki_llama3.1_8b | 0.670 [0.58, 0.76] | 0.810 [0.73, 0.88] | 0.930 [0.88, 0.98] | 0.858 [0.82, 0.89] | 0.750 [0.66, 0.83] |
| llm+wiki_mistral | 0.650 [0.55, 0.74] | 0.910 [0.85, 0.96] | 0.960 [0.92, 0.99] | 0.786 [0.74, 0.83] | 0.750 [0.66, 0.83] |
| llm_llama3.1_8b | 0.590 [0.49, 0.68] | 0.850 [0.78, 0.92] | 1.000 [1.00, 1.00] | 0.817 [0.78, 0.85] | 0.822 [0.74, 0.89] |
| llm_mistral | 0.630 [0.53, 0.72] | 0.840 [0.77, 0.91] | 1.000 [1.00, 1.00] | 0.784 [0.74, 0.82] | 0.719 [0.62, 0.80] |

## Paired comparisons (B minus A)

Accuracy metrics: notes only A right / only B right and exact McNemar p. F1: difference and its paired 95% CI.
p-values are uncorrected for multiple comparisons: descriptive, not confirmatory.

| A | B | metric | A | B | difference | only A right / only B right | p (McNemar) or 95% CI of diff |
|---|---|---|---|---|---|---|---|
| rules | adaptive_llama3.1_8b | reason | 0.870 | 0.870 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | adaptive_llama3.1_8b | follow_up | 0.930 | 0.910 | -0.020 | 3 / 1 | p = 0.6250 |
| rules | adaptive_llama3.1_8b | vitals | 0.790 | 0.970 | +0.180 | 0 / 18 | p = 0.0000 |
| rules | adaptive_llama3.1_8b | interventions F1 | 0.797 | 0.797 | +0.000 | - | [+0.000, +0.000] |
| rules | adaptive_llama3.1_8b | problems F1 | 0.851 | 0.867 | +0.016 | - | [+0.000, +0.043] |
| rules | adaptive_mistral | reason | 0.870 | 0.870 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | adaptive_mistral | follow_up | 0.930 | 0.930 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | adaptive_mistral | vitals | 0.790 | 0.970 | +0.180 | 0 / 18 | p = 0.0000 |
| rules | adaptive_mistral | interventions F1 | 0.797 | 0.797 | +0.000 | - | [+0.000, +0.000] |
| rules | adaptive_mistral | problems F1 | 0.851 | 0.847 | -0.004 | - | [-0.026, +0.020] |
| rules | hybrid_llama3.1_8b | reason | 0.870 | 0.870 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_llama3.1_8b | follow_up | 0.930 | 0.930 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_llama3.1_8b | vitals | 0.790 | 0.790 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_llama3.1_8b | interventions F1 | 0.797 | 0.797 | +0.000 | - | [+0.000, +0.000] |
| rules | hybrid_llama3.1_8b | problems F1 | 0.851 | 0.832 | -0.019 | - | [-0.054, +0.017] |
| rules | hybrid_mistral | reason | 0.870 | 0.870 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_mistral | follow_up | 0.930 | 0.930 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_mistral | vitals | 0.790 | 0.790 | +0.000 | 0 / 0 | p = 1.0000 |
| rules | hybrid_mistral | interventions F1 | 0.797 | 0.797 | +0.000 | - | [+0.000, +0.000] |
| rules | hybrid_mistral | problems F1 | 0.851 | 0.808 | -0.043 | - | [-0.082, -0.009] |
| rules | llm_llama3.1_8b | reason | 0.870 | 0.590 | -0.280 | 35 / 7 | p = 0.0000 |
| rules | llm_llama3.1_8b | follow_up | 0.930 | 0.850 | -0.080 | 9 / 1 | p = 0.0215 |
| rules | llm_llama3.1_8b | vitals | 0.790 | 1.000 | +0.210 | 0 / 21 | p = 0.0000 |
| rules | llm_llama3.1_8b | interventions F1 | 0.797 | 0.817 | +0.020 | - | [-0.027, +0.064] |
| rules | llm_llama3.1_8b | problems F1 | 0.851 | 0.822 | -0.029 | - | [-0.075, +0.014] |
| rules | llm_mistral | reason | 0.870 | 0.630 | -0.240 | 30 / 6 | p = 0.0001 |
| rules | llm_mistral | follow_up | 0.930 | 0.840 | -0.090 | 9 / 0 | p = 0.0039 |
| rules | llm_mistral | vitals | 0.790 | 1.000 | +0.210 | 0 / 21 | p = 0.0000 |
| rules | llm_mistral | interventions F1 | 0.797 | 0.784 | -0.013 | - | [-0.069, +0.041] |
| rules | llm_mistral | problems F1 | 0.851 | 0.719 | -0.132 | - | [-0.207, -0.068] |
| adaptive_llama3.1_8b | adaptive+raw_llama3.1_8b | reason | 0.870 | 0.870 | +0.000 | 0 / 0 | p = 1.0000 |
| adaptive_llama3.1_8b | adaptive+raw_llama3.1_8b | follow_up | 0.910 | 0.920 | +0.010 | 0 / 1 | p = 1.0000 |
| adaptive_llama3.1_8b | adaptive+raw_llama3.1_8b | vitals | 0.970 | 0.970 | +0.000 | 0 / 0 | p = 1.0000 |
| adaptive_llama3.1_8b | adaptive+raw_llama3.1_8b | interventions F1 | 0.797 | 0.797 | +0.000 | - | [+0.000, +0.000] |
| adaptive_llama3.1_8b | adaptive+raw_llama3.1_8b | problems F1 | 0.867 | 0.839 | -0.028 | - | [-0.073, +0.000] |
| adaptive_mistral | adaptive+raw_mistral | reason | 0.870 | 0.870 | +0.000 | 0 / 0 | p = 1.0000 |
| adaptive_mistral | adaptive+raw_mistral | follow_up | 0.930 | 0.930 | +0.000 | 0 / 0 | p = 1.0000 |
| adaptive_mistral | adaptive+raw_mistral | vitals | 0.970 | 0.970 | +0.000 | 0 / 0 | p = 1.0000 |
| adaptive_mistral | adaptive+raw_mistral | interventions F1 | 0.797 | 0.797 | +0.000 | - | [+0.000, +0.000] |
| adaptive_mistral | adaptive+raw_mistral | problems F1 | 0.847 | 0.847 | +0.000 | - | [+0.000, +0.000] |
| adaptive_llama3.1_8b | adaptive+wiki_llama3.1_8b | reason | 0.870 | 0.870 | +0.000 | 0 / 0 | p = 1.0000 |
| adaptive_llama3.1_8b | adaptive+wiki_llama3.1_8b | follow_up | 0.910 | 0.910 | +0.000 | 1 / 1 | p = 1.0000 |
| adaptive_llama3.1_8b | adaptive+wiki_llama3.1_8b | vitals | 0.970 | 0.970 | +0.000 | 0 / 0 | p = 1.0000 |
| adaptive_llama3.1_8b | adaptive+wiki_llama3.1_8b | interventions F1 | 0.797 | 0.797 | +0.000 | - | [+0.000, +0.000] |
| adaptive_llama3.1_8b | adaptive+wiki_llama3.1_8b | problems F1 | 0.867 | 0.824 | -0.043 | - | [-0.084, -0.012] |
| adaptive_mistral | adaptive+wiki_mistral | reason | 0.870 | 0.870 | +0.000 | 0 / 0 | p = 1.0000 |
| adaptive_mistral | adaptive+wiki_mistral | follow_up | 0.930 | 0.930 | +0.000 | 0 / 0 | p = 1.0000 |
| adaptive_mistral | adaptive+wiki_mistral | vitals | 0.970 | 0.970 | +0.000 | 0 / 0 | p = 1.0000 |
| adaptive_mistral | adaptive+wiki_mistral | interventions F1 | 0.797 | 0.797 | +0.000 | - | [+0.000, +0.000] |
| adaptive_mistral | adaptive+wiki_mistral | problems F1 | 0.847 | 0.853 | +0.006 | - | [+0.000, +0.020] |
| hybrid_llama3.1_8b | hybrid+raw_llama3.1_8b | reason | 0.870 | 0.870 | +0.000 | 0 / 0 | p = 1.0000 |
| hybrid_llama3.1_8b | hybrid+raw_llama3.1_8b | follow_up | 0.930 | 0.930 | +0.000 | 0 / 0 | p = 1.0000 |
| hybrid_llama3.1_8b | hybrid+raw_llama3.1_8b | vitals | 0.790 | 0.790 | +0.000 | 0 / 0 | p = 1.0000 |
| hybrid_llama3.1_8b | hybrid+raw_llama3.1_8b | interventions F1 | 0.797 | 0.797 | +0.000 | - | [+0.000, +0.000] |
| hybrid_llama3.1_8b | hybrid+raw_llama3.1_8b | problems F1 | 0.832 | 0.789 | -0.043 | - | [-0.092, +0.000] |
| hybrid_mistral | hybrid+raw_mistral | reason | 0.870 | 0.870 | +0.000 | 0 / 0 | p = 1.0000 |
| hybrid_mistral | hybrid+raw_mistral | follow_up | 0.930 | 0.930 | +0.000 | 0 / 0 | p = 1.0000 |
| hybrid_mistral | hybrid+raw_mistral | vitals | 0.790 | 0.790 | +0.000 | 0 / 0 | p = 1.0000 |
| hybrid_mistral | hybrid+raw_mistral | interventions F1 | 0.797 | 0.797 | +0.000 | - | [+0.000, +0.000] |
| hybrid_mistral | hybrid+raw_mistral | problems F1 | 0.808 | 0.792 | -0.016 | - | [-0.036, +0.000] |
| hybrid_llama3.1_8b | hybrid+wiki_llama3.1_8b | reason | 0.870 | 0.870 | +0.000 | 0 / 0 | p = 1.0000 |
| hybrid_llama3.1_8b | hybrid+wiki_llama3.1_8b | follow_up | 0.930 | 0.930 | +0.000 | 0 / 0 | p = 1.0000 |
| hybrid_llama3.1_8b | hybrid+wiki_llama3.1_8b | vitals | 0.790 | 0.790 | +0.000 | 0 / 0 | p = 1.0000 |
| hybrid_llama3.1_8b | hybrid+wiki_llama3.1_8b | interventions F1 | 0.797 | 0.797 | +0.000 | - | [+0.000, +0.000] |
| hybrid_llama3.1_8b | hybrid+wiki_llama3.1_8b | problems F1 | 0.832 | 0.777 | -0.055 | - | [-0.097, -0.022] |
| hybrid_mistral | hybrid+wiki_mistral | reason | 0.870 | 0.870 | +0.000 | 0 / 0 | p = 1.0000 |
| hybrid_mistral | hybrid+wiki_mistral | follow_up | 0.930 | 0.930 | +0.000 | 0 / 0 | p = 1.0000 |
| hybrid_mistral | hybrid+wiki_mistral | vitals | 0.790 | 0.790 | +0.000 | 0 / 0 | p = 1.0000 |
| hybrid_mistral | hybrid+wiki_mistral | interventions F1 | 0.797 | 0.797 | +0.000 | - | [+0.000, +0.000] |
| hybrid_mistral | hybrid+wiki_mistral | problems F1 | 0.808 | 0.803 | -0.005 | - | [-0.028, +0.018] |
| llm_llama3.1_8b | llm+raw_llama3.1_8b | reason | 0.590 | 0.640 | +0.050 | 3 / 8 | p = 0.2266 |
| llm_llama3.1_8b | llm+raw_llama3.1_8b | follow_up | 0.850 | 0.870 | +0.020 | 0 / 2 | p = 0.5000 |
| llm_llama3.1_8b | llm+raw_llama3.1_8b | vitals | 1.000 | 0.950 | -0.050 | 5 / 0 | p = 0.0625 |
| llm_llama3.1_8b | llm+raw_llama3.1_8b | interventions F1 | 0.817 | 0.837 | +0.020 | - | [-0.019, +0.058] |
| llm_llama3.1_8b | llm+raw_llama3.1_8b | problems F1 | 0.822 | 0.736 | -0.086 | - | [-0.153, -0.031] |
| llm_mistral | llm+raw_mistral | reason | 0.630 | 0.600 | -0.030 | 5 / 2 | p = 0.4531 |
| llm_mistral | llm+raw_mistral | follow_up | 0.840 | 0.840 | +0.000 | 3 / 3 | p = 1.0000 |
| llm_mistral | llm+raw_mistral | vitals | 1.000 | 0.990 | -0.010 | 1 / 0 | p = 1.0000 |
| llm_mistral | llm+raw_mistral | interventions F1 | 0.784 | 0.767 | -0.017 | - | [-0.061, +0.028] |
| llm_mistral | llm+raw_mistral | problems F1 | 0.719 | 0.676 | -0.043 | - | [-0.097, +0.005] |
| llm_llama3.1_8b | llm+wiki_llama3.1_8b | reason | 0.590 | 0.670 | +0.080 | 6 / 14 | p = 0.1153 |
| llm_llama3.1_8b | llm+wiki_llama3.1_8b | follow_up | 0.850 | 0.810 | -0.040 | 11 / 7 | p = 0.4807 |
| llm_llama3.1_8b | llm+wiki_llama3.1_8b | vitals | 1.000 | 0.930 | -0.070 | 7 / 0 | p = 0.0156 |
| llm_llama3.1_8b | llm+wiki_llama3.1_8b | interventions F1 | 0.817 | 0.858 | +0.041 | - | [+0.005, +0.077] |
| llm_llama3.1_8b | llm+wiki_llama3.1_8b | problems F1 | 0.822 | 0.750 | -0.072 | - | [-0.120, -0.033] |
| llm_mistral | llm+wiki_mistral | reason | 0.630 | 0.650 | +0.020 | 4 / 6 | p = 0.7539 |
| llm_mistral | llm+wiki_mistral | follow_up | 0.840 | 0.910 | +0.070 | 0 / 7 | p = 0.0156 |
| llm_mistral | llm+wiki_mistral | vitals | 1.000 | 0.960 | -0.040 | 4 / 0 | p = 0.1250 |
| llm_mistral | llm+wiki_mistral | interventions F1 | 0.784 | 0.786 | +0.002 | - | [-0.043, +0.049] |
| llm_mistral | llm+wiki_mistral | problems F1 | 0.719 | 0.750 | +0.031 | - | [-0.026, +0.089] |
