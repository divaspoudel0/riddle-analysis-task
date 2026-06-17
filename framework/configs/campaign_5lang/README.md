# Campaign — 5 models × 5-language pilot dataset

Runs five models over
[`pilot_dataset_5lang.jsonl`](../../../data_loading/pilot_dataset/pilot_dataset_5lang.jsonl)
(Hungarian, Tamil, Moroccan Arabic, Russian, Chinese — 500 riddles).

| Config | Model | Provider / access | API key |
| --- | --- | --- | --- |
| `gpt55_high.yaml` | GPT-5.5 (reasoning high) | openai / direct_api | `OPENAI_API_KEY` |
| `claude_opus_thinking.yaml` | Claude Opus (extended thinking) | anthropic / direct_api | `ANTHROPIC_API_KEY` |
| `gemini_pro.yaml` | Gemini Pro | google / direct_api | `GOOGLE_API_KEY` |
| `cohere_tiny_aya.yaml` | Cohere Tiny-Aya (`tiny-aya-global`) | cohere / direct_api | `COHERE_API_KEY` |
| `gemma4_openrouter.yaml` | Gemma 4 (open weights) | openrouter / openrouter | `OPENROUTER_API_KEY` |

All five share the same run condition for comparability: prompt
`riddle_master` v1, English prompt, source-language riddle, no hint,
`max_output_tokens: 4096`. Reasoning is enabled (`reasoning_mode: high`) only
for GPT-5.5 and Claude Opus, which support it.

**JSON output is prompt-driven.** The `riddle_master` prompt instructs the model
to return only a JSON object (`{"riddle_answer": ..., "reasoning": ...}`), so all
models — including Tiny-Aya — emit JSON without relying on a provider-specific
JSON API mode. There is no `response_format` knob: the run config no longer
carries it (the loader defaults to `free_form`).

Tiny-Aya runs via the **Cohere API** (`provider: cohere`, model
`tiny-aya-global`) using the existing Cohere adapter and `COHERE_API_KEY`.

## Run

```bash
cd framework

# every model whose API key is set (others are skipped with a warning)
./run_campaign_5lang.sh

# only specific models
./run_campaign_5lang.sh gpt55_high gemini_pro

# or a single model directly
uv run python -m riddles_framework.cli \
  --config configs/campaign_5lang/gpt55_high.yaml
```

Outputs land in `framework/runs/<run_id>/` (`results.jsonl`, run config,
metadata, manifest). Score them with the evaluators in
[`../../../evals`](../../../evals/README.md).

## ⚠️ Placeholders to confirm before a real run

The hosted `provider_model_name` strings are scaffold placeholders (consistent
with the other configs in `configs/`). Replace each with the exact provider
model slug your team has API access to before billing a real run — in
particular `google/gemma-4-31b-it` (OpenRouter). The GPT-5.5, Claude Opus, and
Gemini Pro slugs are also placeholders.

`cohere_tiny_aya.yaml` uses the model slug `tiny-aya-global` on the Cohere API,
so it has no placeholder slug — just confirm `COHERE_API_KEY` is set.
