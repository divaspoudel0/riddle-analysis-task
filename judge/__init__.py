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
from judge.exact_match_judge import (
    extract_candidate_answer,
    judge_exact_match,
    judge_results,
    judge_row,
    normalize,
    reference_variants,
    summarize,
)

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
    # Deterministic exact-match judge
    "extract_candidate_answer",
    "judge_exact_match",
    "judge_results",
    "judge_row",
    "normalize",
    "reference_variants",
    "summarize",
]
