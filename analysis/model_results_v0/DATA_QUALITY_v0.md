# Data quality report: v0 model runs

Generated 2026-07-19 by data_quality_report.py. Do not edit by hand; rerun the script.

Rows: 105600, models: 24, communities: 44, conditions: 1

## Per-model response health

unparsed = response present but no answer extractable (mostly reasoning that never reaches the JSON answer). truncated = unparsed with >= 4000 output tokens, i.e. the model hit the shared token budget before answering.

| model | rows | empty | unparsed | truncated | judge correct | judge unknown |
|---|---|---|---|---|---|---|
| Amazon Nova Lite v1 | 4400 | 0 | 1 | 0 | 450 | 24 |
| Amazon Nova Micro v1 | 4400 | 0 | 14 | 0 | 279 | 71 |
| Cohere Command A Plus | 4400 | 0 | 1136 | 1122 | 1089 | 127 |
| DeepSeek V4 Flash | 4400 | 0 | 3 | 0 | 1306 | 5 |
| EuroLLM-22B-Instruct-2512 | 4400 | 0 | 19 | 10 | 531 | 1 |
| GPT5.5 [high] | 4400 | 527 | 0 | 0 | 2542 | 0 |
| GPT5.5 [none] | 4400 | 130 | 0 | 0 | 2581 | 1 |
| Gemini 2.5 Flash | 4400 | 0 | 2 | 0 | 1638 | 18 |
| Gemini 2.5 Flash Lite | 4400 | 0 | 4 | 2 | 1129 | 3 |
| Gemma 4 31B IT | 4400 | 0 | 1 | 0 | 1275 | 19 |
| Mistral Large 3 | 4400 | 0 | 0 | 0 | 1308 | 0 |
| OLMo-3-32B-Think | 4400 | 0 | 407 | 393 | 407 | 102 |
| Qwen-SEA-LION-v4.5-27B-IT | 4400 | 45 | 447 | 445 | 1100 | 17 |
| Qwen/Qwen3.5-0.8B | 4400 | 0 | 8 | 0 | 14 | 6 |
| Qwen3.5 27B | 4400 | 0 | 1 | 1 | 892 | 34 |
| Tiny-Aya earth | 4400 | 0 | 17 | 12 | 209 | 0 |
| Tiny-Aya fire | 4400 | 0 | 20 | 19 | 207 | 1 |
| Tiny-Aya global | 4400 | 0 | 6 | 6 | 226 | 0 |
| Tiny-Aya water | 4400 | 0 | 18 | 18 | 204 | 0 |
| claude-opus-4-7 [none] | 4400 | 83 | 0 | 0 | 2006 | 13 |
| claude-opus-4-7 [thinking] | 4400 | 94 | 0 | 0 | 2211 | 148 |
| deepseek-v4-pro | 4400 | 1 | 3 | 3 | 1981 | 60 |
| deepseek-v4-pro-thinking | 4400 | 69 | 4 | 2 | 2169 | 30 |
| gemini-3.1-pro-preview | 4400 | 0 | 90 | 90 | 2783 | 76 |

## Notable findings

Threshold: models with more than 5% of rows empty or unparsed.

- Cohere Command A Plus: 25.8% of rows have no extractable answer (1122 of 1136 unparsed rows hit the token budget).
- GPT5.5 [high]: 12.0% of rows have no extractable answer (0 of 0 unparsed rows hit the token budget).
- OLMo-3-32B-Think: 9.2% of rows have no extractable answer (393 of 407 unparsed rows hit the token budget).
- Qwen-SEA-LION-v4.5-27B-IT: 11.2% of rows have no extractable answer (445 of 447 unparsed rows hit the token budget).

## Version notes (hand-maintained context, append per version)

- v0: Command A+ July 13 rerun fixed earlier empty responses (404s) but 1,122 of its 1,136 unparsed rows hit the 4,096 token budget mid-reasoning; kept as-is for v0, scored as format failures, flagged to leads 15 Jul 2026.
- v0: Amazon Nova Micro emits pseudo-JSON with single-quoted values; handled in load_results.extract_answer.
- v0: Qwen-SEA-LION and OLMo-3-32B-Think spill reasoning and truncate before answering on a subset of rows; treated as genuine no-answers.
- v0: judge abstention detection (NO_ANSWER_PHRASES_RAW) covers ~6 of 30+ benchmark languages; honest-uncertainty rates are lower bounds. Raised with Abdellah 19 Jul 2026; rerun scoring once the phrase list is extended.
