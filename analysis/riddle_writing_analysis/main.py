"""Run the complete anonymized riddle-writing survey analysis."""

from analysis.riddle_writing_analysis import survey_audit
from analysis.riddle_writing_analysis.survey_analysis import (
    OUTPUT_DIR,
    load_survey,
    plot_ai_uses,
    plot_confidence_distribution,
    plot_resources_used,
    plot_specificity,
    plot_time_per_riddle,
    plot_topic_difficulty,
    summarize_scale_relationships,
)
from analysis.utils import write_csv


def main() -> None:
    """Regenerate every survey table and figure."""
    survey_audit.main()
    survey = load_survey()
    outputs = (
        (plot_topic_difficulty, "topic_difficulty.csv"),
        (plot_specificity, "specificity_strategy.csv"),
        (plot_ai_uses, "ai_use_functions.csv"),
        (plot_confidence_distribution, "confidence_distribution.csv"),
        (plot_time_per_riddle, "time_per_riddle.csv"),
        (plot_resources_used, "resources_used.csv"),
        (summarize_scale_relationships, "scale_spearman_correlations.csv"),
    )
    for transform, filename in outputs:
        write_csv(transform(survey), OUTPUT_DIR / filename)


if __name__ == "__main__":
    main()
