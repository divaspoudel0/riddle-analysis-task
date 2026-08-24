"""Analyze contributors' confidence in community representation."""

from analysis.constants import RIDDLE_WRITING_OUTPUT_DIR
from analysis.riddle_writing_analysis.survey_analysis import (
    load_survey,
    plot_confidence_distribution,
)
from analysis.utils import write_csv


def main() -> None:
    """Regenerate confidence figure and aggregate table."""
    write_csv(
        plot_confidence_distribution(load_survey()),
        RIDDLE_WRITING_OUTPUT_DIR / "confidence_distribution.csv",
    )


if __name__ == "__main__":
    main()
