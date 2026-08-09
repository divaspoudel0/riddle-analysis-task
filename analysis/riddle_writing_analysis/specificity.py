"""Analyze contributors' local-specificity strategies."""

from analysis.riddle_writing_analysis.survey_analysis import (
    OUTPUT_DIR,
    load_survey,
    plot_specificity,
)


def main() -> None:
    """Regenerate specificity figure and aggregate table."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plot_specificity(load_survey()).to_csv(
        OUTPUT_DIR / "specificity_strategy.csv", index=False
    )


if __name__ == "__main__":
    main()
