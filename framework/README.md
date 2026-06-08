# Benchmark Framework (T2.2.1)

Base benchmarking framework for the Multicultural Riddles project.

## Layout

```
framework/
├── pyproject.toml
├── README.md
├── CONTRIBUTING.md
├── configs/                              # example run configs (YAML)
├── tests/                                # pytest suite
└── src/
    └── riddles_framework/                # the installed package
        ├── constants.py
        ├── exceptions.py
        ├── schemas.py
        ├── utils.py
        ├── community_display.py              # community key → display name mapping
        ├── dataset_loader.py
        ├── prompts.py
        ├── prompt_templates/                 # instruction templates (YAML)
        │   ├── riddle_basic_v1.yaml
        │   ├── riddle_basic_v2.yaml
        │   ├── riddle_with_uncertainty_v1.yaml
        │   └── riddle_with_cultural_context_v1.yaml
        ├── writers.py
        ├── registry.py
        ├── factory.py
        ├── cache_clients.py
        ├── runner.py
        ├── yaml_config.py
        ├── model_specs.py
        ├── cli.py
        └── models/                           # provider adapters
            ├── base.py                       # Model ABC every adapter implements
            ├── dummy.py                      # reference adapter, used for smoke tests
            ├── openai_adapter.py
            ├── anthropic_adapter.py
            ├── gemini_adapter.py
            ├── openrouter_adapter.py
            └── transformers_local_adapter.py
```

## What this framework does

- loads the pilot dataset JSONL
- builds prompts for benchmark conditions
- runs models through a stable model interface
- supports multiple providers and access patterns
- optionally uses CacheSaver for caching and reproducibility
- writes standardized run artifacts for downstream evaluation

## What it does not do

- build the dataset (that's the data-loading package)
- define automatic scoring (T2.3)
- perform human evaluation

## Input

```
data_loading/pilot_dataset/pilot_dataset_v1.jsonl
```

## Output

```
runs/<run_id>/
  run_config.json
  run_metadata.json
  results.jsonl
  manifest.json
```

This is the contract for the analysis team.

## Benchmark conditions

Supported: `source_no_hint`, `source_with_hint`, `english_no_hint`.

Not supported in v1: `english_with_hint`. The runner fails fast before touching the filesystem if this is configured.

## Design choices (per project lead feedback)

These are non-obvious and worth knowing before changing anything:

**Temperature is `Optional[float]` and defaults to `None`.** Many reasoning models (OpenAI o-series, Anthropic thinking, DeepSeek R1) can fall into degenerate loops at low temperature. We let the model's default apply unless temperature is explicitly set in the YAML. Setting `temperature: null` or omitting it altogether is the recommended path for reasoning runs.

**Arbitrary provider parameters via `model_params:`.** Rather than adding a new `RunConfig` field every time someone wants `top_p` or `frequency_penalty`, the YAML config takes a `model_params:` dict that flows verbatim into the provider's request, merged LAST so it overrides anything the adapter set automatically. Use it for top_p, frequency_penalty, presence_penalty, top_k, etc.

**Default response format is JSON.** Per project guidance, structured output is the default. Set `response_format: free_form` in YAML if you need free text.

**Prompt templates live as YAML files, selectable by `(template_id, template_version)`.** See `src/riddles_framework/prompt_templates/`. To add a new template, drop in a new YAML file with `template_id`, `template_version`, and `instruction_text`. No code change required. Optional `recommended_response_format` is informational; the actual format used is whatever `RunConfig.response_format` says.

## Install

API-only (no torch). Works for OpenAI, Anthropic, Gemini, and OpenRouter (which uses the OpenAI SDK under the hood):

```bash
uv sync
```

With local inference (also installs torch + transformers; needed for the local Hugging Face adapter):

```bash
uv sync --extra local
```

## Run

Smoke test with the dummy model:

```bash
uv run python -m riddles_framework.cli --config configs/dummy.yaml
```

Real provider:

```bash
export OPENAI_API_KEY=...
uv run python -m riddles_framework.cli --config configs/openai_gpt55_high.yaml
```

## Tests

```bash
uv run pytest
```

## Known v1 limitations

- **Refusal tagging is heuristic, conservative, and English-only.** Tags clear policy refusals (e.g. "I can't help with that") but does NOT tag honest uncertainty (e.g. "I cannot determine") as a refusal — that's a signal the benchmark wants to measure, not suppress. Source-language refusals will not be tagged. Downstream T2.3 / human eval may refine this.
- **`model_specs.py` and the configs' `provider_model_name` fields are scaffolds.** Placeholder strings (`gpt-5.5-high`, `claude-opus-4.7`, etc.) must be replaced with real provider strings your team has access to before any production run.
- **Resume mode is not implemented.** If a run crashes mid-way, the entire run must be re-executed. Cache (when enabled) will short-circuit already-seen prompts, but `results.jsonl` itself starts fresh per run.
- **Provider SDK surfaces evolve.** Some adapter-level knobs (reasoning effort, web search toggles, Gemini call surface) are best-effort and may need adjustment by whoever owns that provider.

## Adding a new model

Don't touch the runner. See `CONTRIBUTING.md`.
