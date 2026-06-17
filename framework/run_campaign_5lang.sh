#!/usr/bin/env bash
#
# Run the 5-model campaign over pilot_dataset_5lang.jsonl
# (Hungarian, Tamil, Moroccan Arabic, Russian, Chinese).
#
# Models:
#   GPT-5.5 (high)            -> OPENAI_API_KEY
#   Claude Opus (thinking)    -> ANTHROPIC_API_KEY
#   Gemini Pro                -> GOOGLE_API_KEY
#   Tiny-Aya (Cohere API)     -> COHERE_API_KEY
#   Gemma 4 (OpenRouter)      -> OPENROUTER_API_KEY
#
# Usage:
#   ./run_campaign_5lang.sh                 # run every model whose API key is set
#   ./run_campaign_5lang.sh gpt55_high gemini_pro   # run only the named configs
#
# A model whose API key env var is unset is skipped with a warning, so a
# partial key set still produces a partial run.

set -euo pipefail

# Run from the framework directory so configs/ and ../data_loading resolve.
cd "$(dirname "$0")"

PYTHON_RUN="${PYTHON_RUN:-uv run python}"
OUTPUT_ROOT="${OUTPUT_ROOT:-runs}"
CONFIG_DIR="configs/campaign_5lang"

# config-stem -> required API key env var
declare -a CONFIGS=(
  "gpt55_high:OPENAI_API_KEY"
  "claude_opus_thinking:ANTHROPIC_API_KEY"
  "gemini_pro:GEMINI_API_KEY"
  "cohere_tiny_aya:COHERE_API_KEY"
  "gemma4_openrouter:OPENROUTER_API_KEY"
)

# Optional positional filter: only run the named config stems.
WANTED=("$@")
want() {
  [ ${#WANTED[@]} -eq 0 ] && return 0
  local c
  for c in "${WANTED[@]}"; do [ "$c" = "$1" ] && return 0; done
  return 1
}

ran=(); skipped=(); failed=()

for entry in "${CONFIGS[@]}"; do
  stem="${entry%%:*}"
  key_var="${entry##*:}"
  config="${CONFIG_DIR}/${stem}.yaml"

  want "$stem" || continue

  if [ ! -f "$config" ]; then
    echo "!! missing config: $config" >&2
    failed+=("$stem"); continue
  fi
  if [ -n "$key_var" ] && [ -z "${!key_var:-}" ]; then
    echo ">> SKIP $stem ($key_var not set)"
    skipped+=("$stem"); continue
  fi

  echo "== RUN  $stem  ($config)"
  if $PYTHON_RUN -m riddles_framework.cli --config "$config" --output-root "$OUTPUT_ROOT"; then
    ran+=("$stem")
  else
    echo "!! FAILED $stem" >&2
    failed+=("$stem")
  fi
done

echo
echo "Campaign summary:"
echo "  ran:     ${ran[*]:-(none)}"
echo "  skipped: ${skipped[*]:-(none)}"
echo "  failed:  ${failed[*]:-(none)}"

[ ${#failed[@]} -eq 0 ]
