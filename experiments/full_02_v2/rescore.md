# Re-score of experiments/full_02_v2 with normalised follow-up

Follow-up is scored twice: as stored (scorer's own string parser) and after the phrase is parsed by the project's rules parser (same for every condition). Other metrics are unchanged.

## Scored against original

| condition | reason | follow-up as stored | follow-up normalised | vitals | int F1 | prob F1 |
|---|---|---|---|---|---|---|
| rules | 0.870 | 0.930 | 0.930 | 0.790 | 0.797 | 0.851 |
| adaptive+raw_llama3.1_8b | 0.870 | 0.920 | 0.920 | 0.970 | 0.797 | 0.839 |
| adaptive+raw_mistral | 0.870 | 0.930 | 0.930 | 0.970 | 0.797 | 0.847 |
| adaptive+wiki_llama3.1_8b | 0.870 | 0.910 | 0.910 | 0.970 | 0.797 | 0.824 |
| adaptive+wiki_mistral | 0.870 | 0.930 | 0.930 | 0.970 | 0.797 | 0.853 |
| adaptive_llama3.1_8b | 0.870 | 0.910 | 0.910 | 0.970 | 0.797 | 0.867 |
| adaptive_mistral | 0.870 | 0.930 | 0.930 | 0.970 | 0.797 | 0.847 |
| hybrid+raw_llama3.1_8b | 0.870 | 0.930 | 0.930 | 0.790 | 0.797 | 0.789 |
| hybrid+raw_mistral | 0.870 | 0.930 | 0.930 | 0.790 | 0.797 | 0.792 |
| hybrid+wiki_llama3.1_8b | 0.870 | 0.930 | 0.930 | 0.790 | 0.797 | 0.777 |
| hybrid+wiki_mistral | 0.870 | 0.930 | 0.930 | 0.790 | 0.797 | 0.803 |
| hybrid_llama3.1_8b | 0.870 | 0.930 | 0.930 | 0.790 | 0.797 | 0.832 |
| hybrid_mistral | 0.870 | 0.930 | 0.930 | 0.790 | 0.797 | 0.808 |
| llm+raw_llama3.1_8b | 0.640 | 0.870 | 0.870 | 0.950 | 0.837 | 0.736 |
| llm+raw_mistral | 0.600 | 0.840 | 0.840 | 0.990 | 0.767 | 0.676 |
| llm+wiki_llama3.1_8b | 0.670 | 0.810 | 0.810 | 0.930 | 0.858 | 0.750 |
| llm+wiki_mistral | 0.650 | 0.910 | 0.910 | 0.960 | 0.786 | 0.750 |
| llm_llama3.1_8b | 0.590 | 0.850 | 0.850 | 1.000 | 0.817 | 0.822 |
| llm_mistral | 0.630 | 0.840 | 0.840 | 1.000 | 0.784 | 0.719 |

## Scored against reviewed_v1 (exploratory)

| condition | reason | follow-up as stored | follow-up normalised | vitals | int F1 | prob F1 |
|---|---|---|---|---|---|---|
| rules | 0.880 | 0.930 | 0.930 | 0.790 | 0.797 | 0.976 |
| adaptive+raw_llama3.1_8b | 0.880 | 0.920 | 0.920 | 0.970 | 0.797 | 0.960 |
| adaptive+raw_mistral | 0.880 | 0.930 | 0.930 | 0.970 | 0.797 | 0.968 |
| adaptive+wiki_llama3.1_8b | 0.880 | 0.910 | 0.910 | 0.970 | 0.797 | 0.938 |
| adaptive+wiki_mistral | 0.880 | 0.930 | 0.930 | 0.970 | 0.797 | 0.976 |
| adaptive_llama3.1_8b | 0.880 | 0.910 | 0.910 | 0.970 | 0.797 | 0.976 |
| adaptive_mistral | 0.880 | 0.930 | 0.930 | 0.970 | 0.797 | 0.968 |
| hybrid+raw_llama3.1_8b | 0.880 | 0.930 | 0.930 | 0.790 | 0.797 | 0.896 |
| hybrid+raw_mistral | 0.880 | 0.930 | 0.930 | 0.790 | 0.797 | 0.897 |
| hybrid+wiki_llama3.1_8b | 0.880 | 0.930 | 0.930 | 0.790 | 0.797 | 0.878 |
| hybrid+wiki_mistral | 0.880 | 0.930 | 0.930 | 0.790 | 0.797 | 0.910 |
| hybrid_llama3.1_8b | 0.880 | 0.930 | 0.930 | 0.790 | 0.797 | 0.931 |
| hybrid_mistral | 0.880 | 0.930 | 0.930 | 0.790 | 0.797 | 0.917 |
| llm+raw_llama3.1_8b | 0.670 | 0.870 | 0.870 | 0.950 | 0.837 | 0.841 |
| llm+raw_mistral | 0.620 | 0.840 | 0.840 | 0.990 | 0.767 | 0.777 |
| llm+wiki_llama3.1_8b | 0.670 | 0.810 | 0.810 | 0.930 | 0.858 | 0.851 |
| llm+wiki_mistral | 0.680 | 0.910 | 0.910 | 0.960 | 0.786 | 0.857 |
| llm_llama3.1_8b | 0.620 | 0.850 | 0.850 | 1.000 | 0.817 | 0.922 |
| llm_mistral | 0.650 | 0.840 | 0.840 | 1.000 | 0.784 | 0.826 |

