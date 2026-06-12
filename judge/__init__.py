"""Judge package for riddles benchmarking."""

from judge.llm_as_a_judge import (
    JUDGE_OUTPUT_SCHEMA,
    JUDGE_SYSTEM_PROMPT,
    TARGET_MODELS,
    build_judge_messages,
    build_openrouter_payload,
    export_model_registry,
    models_by_alias,
    normalize_judge_instance,
    select_route,
)
from judge.exact_match_judge import candidate_answer, match

__all__ = [
    "JUDGE_OUTPUT_SCHEMA",
    "JUDGE_SYSTEM_PROMPT",
    "TARGET_MODELS",
    "build_judge_messages",
    "build_openrouter_payload",
    "export_model_registry",
    "models_by_alias",
    "normalize_judge_instance",
    "select_route",
    # Exact-match judge
    "candidate_answer",
    "match",
]
