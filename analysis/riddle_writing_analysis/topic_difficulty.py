"""Analyze writing difficulty by benchmark topic."""

from analysis.constants import RIDDLE_WRITING_OUTPUT_DIR
from analysis.riddle_writing_analysis.survey_analysis import (
    load_survey,
    plot_topic_difficulty,
)
from analysis.utils import write_csv


def main() -> None:
    """Regenerate topic-difficulty figure and aggregate table."""
    write_csv(
        plot_topic_difficulty(load_survey()),
        RIDDLE_WRITING_OUTPUT_DIR / "topic_difficulty.csv",
    )


if __name__ == "__main__":
    main()
