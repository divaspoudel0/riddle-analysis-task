"""Shared paths, taxonomies, and stable labels for analysis scripts."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_ROOT = Path(__file__).resolve().parent
CANONICAL_CORPUS_PATH = REPO_ROOT / "data_loading/pilot_dataset/pilot_dataset_v1.jsonl"
CORPUS_METADATA_PATH = ANALYSIS_ROOT / "corpus_metadata.csv"
FIGURES_DIR = ANALYSIS_ROOT / "figures"
MODEL_RESULTS_DATA_DIR = ANALYSIS_ROOT / "model_results" / "data"
MODEL_RESULTS_OUTPUT_DIR = ANALYSIS_ROOT / "model_results" / "outputs"
RIDDLE_ANALYSIS_OUTPUT_DIR = ANALYSIS_ROOT / "riddle_analysis" / "outputs"
RIDDLE_WRITING_OUTPUT_DIR = ANALYSIS_ROOT / "riddle_writing_analysis" / "outputs"
HUMAN_EVALUATION_FLAT_CSV = (
    ANALYSIS_ROOT / "eval_analysis" / "data" / "model_riddle_results_flat.csv"
)
MODEL_RESULTS_TIDY_CSV = (
    MODEL_RESULTS_DATA_DIR / "combined" / "processed" / "results_tidy.csv"
)
EXCLUDED_RIDDLE_IDS = frozenset({"spanish_cuba_history_016"})
ARTIFACT_PREFIXES: dict[str, str] = {
    "model_results": "m_",
    "riddle_analysis": "r_",
    "riddle_writing_analysis": "w_",
    "eval_analysis": "e_",
}

FIXED_TOPICS: tuple[str, ...] = (
    "Politics",
    "History",
    "Geography",
    "Arts",
    "Sports",
    "National Heritage",
    "Kid's World",
    "Everyday Life",
)
TOPICS: tuple[str, ...] = (*FIXED_TOPICS, "Wildcard")
SURVEY_TOPICS: tuple[str, ...] = (*FIXED_TOPICS, "Wild Card")
RUN_BATCH_ORDER: tuple[str, ...] = ("v0", "v1", "v2")
REGION_ORDER: tuple[str, ...] = (
    "North America",
    "Latin America",
    "Europe",
    "North Africa",
    "Sub-Saharan Africa",
    "West Asia",
    "Central Asia",
    "South Asia",
    "East Asia",
    "Southeast Asia",
    "Oceania & Pacific",
)
LANGUAGE_GROUP_ORDER: tuple[str, ...] = (
    "Arabic varieties",
    "Chinese varieties",
    "Spanish",
    "English",
    "French",
    "Portuguese",
    "Bengali",
)


def figure_stem(package: str, name: str) -> Path:
    """Return the approved central figure stem for one analysis package."""
    try:
        prefix = ARTIFACT_PREFIXES[package]
    except KeyError as error:
        raise ValueError(f"Unknown analysis package: {package}") from error
    return FIGURES_DIR / f"{prefix}{name}"
