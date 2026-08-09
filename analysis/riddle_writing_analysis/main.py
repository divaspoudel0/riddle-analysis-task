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


def main() -> None:
    """Regenerate every survey table and figure."""
    survey_audit.main()
    survey = load_survey()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plot_topic_difficulty(survey).to_csv(
        OUTPUT_DIR / "topic_difficulty.csv", index=False
    )
    plot_specificity(survey).to_csv(
        OUTPUT_DIR / "specificity_strategy.csv", index=False
    )
    plot_ai_uses(survey).to_csv(OUTPUT_DIR / "ai_use_functions.csv", index=False)
    plot_confidence_distribution(survey).to_csv(
        OUTPUT_DIR / "confidence_distribution.csv", index=False
    )
    plot_time_per_riddle(survey).to_csv(OUTPUT_DIR / "time_per_riddle.csv", index=False)
    plot_resources_used(survey).to_csv(OUTPUT_DIR / "resources_used.csv", index=False)
    summarize_scale_relationships(survey).to_csv(
        OUTPUT_DIR / "scale_spearman_correlations.csv", index=False
    )


if __name__ == "__main__":
    main()
