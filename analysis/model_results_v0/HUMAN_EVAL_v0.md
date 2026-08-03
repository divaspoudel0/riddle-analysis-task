# Human evaluation report: v0

Generated 2026-08-03 by human_eval.py from `model_riddle_results_flat.csv`. Rerun as coverage grows; do not edit by hand.

Scores are hybrid: human where a human scored the answer, filled with the heuristic judge score elsewhere (Henry's cap policy). Accuracy is the strict top-score rate; human_graded is the mean human score / 3.

## Coverage

complete: 16, partial: 21, thin: 2, not started: 5 (of 44 communities). Full per-community table in `data/processed/human_eval_coverage.csv`.

Not started (chase these): arabic_egypt, arabic_morocco, arabic_sudan, luganda_uganda, lumasaba_uganda.

## Hybrid leaderboard

| model | accuracy (%) | human graded (%) | human share (%) |
|---|---|---|---|
| gemini-3.1-pro-preview | 75.8 | 74.2 | 40.9 |
| GPT5.5 [none] | 72.9 | 71.3 | 45.8 |
| GPT5.5 [high] | 71.4 | 79.4 | 41.5 |
| claude-opus-4-7 [thinking] | 62.2 | 60.9 | 51.0 |
| deepseek-v4-pro-thinking | 60.5 | 53.6 | 51.6 |
| claude-opus-4-7 [none] | 56.1 | 50.3 | 55.9 |
| deepseek-v4-pro | 55.0 | 47.7 | 56.1 |
| Gemini 2.5 Flash | 45.0 | 44.2 | 50.7 |
| Gemma 4 31B IT | 36.6 | 30.5 | 67.2 |
| Mistral Large 3 | 35.9 | 31.0 | 59.8 |
| DeepSeek V4 Flash | 35.4 | 34.2 | 50.1 |
| Cohere Command A Plus | 31.8 | 38.6 | 44.6 |
| Qwen-SEA-LION-v4.5-27B-IT | 31.6 | 30.8 | 55.5 |
| Gemini 2.5 Flash Lite | 30.7 | 29.7 | 57.0 |
| Qwen3.5 27B | 25.7 | 24.4 | 63.9 |
| EuroLLM-22B-Instruct-2512 | 13.8 | 13.0 | 73.6 |
| Amazon Nova Lite v1 | 13.0 | 15.1 | 60.0 |
| OLMo-3-32B-Think | 11.3 | 13.8 | 49.1 |
| Amazon Nova Micro v1 | 7.3 | 10.8 | 54.0 |
| Tiny-Aya earth | 6.2 | 8.0 | 81.9 |
| Tiny-Aya fire | 6.1 | 7.9 | 81.9 |
| Tiny-Aya global | 6.0 | 7.5 | 79.7 |
| Tiny-Aya water | 6.0 | 7.7 | 81.4 |
| Qwen/Qwen3.5-0.8B | 0.5 | 1.4 | 55.4 |

> human share = fraction of a model's rows that carry a real human score; the rest are judge-filled. These numbers move as coverage grows, so rerun after each refresh.
