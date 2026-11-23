# Saved experiment runs

Everything in the thesis tables can be reproduced from these folders without running a model.
All notes are synthetic. Temperature 0, one run per condition, Ollama 0.17.7.

| folder | what it is | thesis section |
|---|---|---|
| full_01 | rules, LLM only, hybrid, adaptive; Mistral and Llama 3.1 8B | 4.1 to 4.5, 4.8 |
| wiki_01, wiki_02_llm, wiki_03_llama | knowledge layer (none, wiki, raw retrieval) | 4.6 |
| full_02_v2 | improved rule extractors (v2), rebuilt from the saved answers (no model call) | 4.7 |
| merged/llm_cache | every saved LLM answer, keyed by sha256(prompt + model + note [+ context]) | replay and rebuilds |
| messy_01 | the untidy copy of the notes (data/synthetic/raw_messy) | 4.9 |

    python3 -m tools.rescore --run experiments/full_01        # scores with one follow-up parser
    python3 -m tools.stats --run experiments/full_01          # bootstrap intervals and McNemar
    python3 -m tools.replay_routing --run experiments/full_01 # routing variants from saved answers
    python3 -m tools.reason_flagging --run experiments/full_01 \
        --llm-runs experiments/wiki_02_llm:llm_mistral experiments/wiki_03_llama:llm_llama3.1_8b \
        --adaptive-runs adaptive_mistral adaptive_llama3.1_8b
