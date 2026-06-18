# `riddles_framework.batch` — getting results faster and cheaper

Get a run's results **much faster (and cheaper)** than the serial runner: fill
its CacheSaver cache concurrently or via offline Batch APIs, then run the normal
CLI for instant cache hits. Two backends, one shared cache layer:

- **threadpool** — N concurrent real-time calls for OpenAI-compatible providers
  (Cohere, OpenRouter, Together).
- **batch** — provider Batch APIs (OpenAI / Anthropic / Gemini): offline,
  cheaper, high throughput.

Both write entries CacheSaver reads back verbatim, so afterwards:

```bash
uv run python -m riddles_framework.cli --config <same config>   # 100% cache hits
```

## Why not just thread the runner?

CacheSaver's `SyncWrapper` runs an asyncio pipeline (per-key locks, an online
batcher) via `asyncio.run` per call — it's serial and **not thread-safe**. So we
read/write the underlying `diskcache` directly (`cache_compat.py`), reproducing
CacheSaver's exact key and entry format. Verified against real runs: the
reconstructed key matches, and a live CacheSaver client reads our entries as
hits.

## Usage

```bash
# OpenAI-compatible -> concurrent real-time
python -m riddles_framework.batch.fill --config configs/campaign_5lang/cohere_tiny_aya.yaml --workers 12

# OpenAI / Anthropic / Gemini -> Batch API (auto-selected)
python -m riddles_framework.batch.fill --config configs/campaign_5lang/gpt55_high.yaml --backend batch

# see misses without making any calls
python -m riddles_framework.batch.fill --config <cfg> --dry-run
```

Only cache **misses** are fetched. Changing the prompt/model/params changes the
key, so a different config legitimately re-fills.

## Provider cache formats (validated)

| Provider | Cache key | Cache entry |
| --- | --- | --- |
| OpenAI / Cohere / OpenRouter / Together | default hash | `openai…ChatCompletion` |
| Anthropic | default hash | `anthropic…Message` |
| Gemini | custom hash (≡ default when no `config`) | `google…GenerateContentResponse` |

## Test status

- `cache_compat`, `threadpool`, `fill` — unit-tested; cache round-trip and
  hit-detection verified against real run caches.
- `openai_batch`, `anthropic_batch`, `gemini_batch` — **validated live**
  end-to-end on a small slice (submit → poll → download → write-back → verified
  cache hits): OpenAI `gpt-5.5` 10/10, Anthropic `claude-haiku-4-5` 5/5, Gemini
  `gemini-3.1-pro-preview` 5/5.
- `gemini_batch` was validated against **google-genai 2.8.0**; that SDK's batch
  surface changes between versions, so re-check `batches.create` /
  `dest.inlined_responses` if you upgrade.
