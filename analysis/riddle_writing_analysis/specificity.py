"""Analyze contributors' local-specificity strategies."""

from analysis.constants import RIDDLE_WRITING_OUTPUT_DIR
from analysis.riddle_writing_analysis.survey_analysis import (
    load_survey,
    plot_specificity,
)
from analysis.utils import write_csv


def main() -> None:
    """Regenerate specificity figure and aggregate table."""
    write_csv(
        plot_specificity(load_survey()),
        RIDDLE_WRITING_OUTPUT_DIR / "specificity_strategy.csv",
    )


if __name__ == "__main__":
    main()
