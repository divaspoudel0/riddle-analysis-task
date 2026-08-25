"""Analyze estimated time to write a riddle."""

from analysis.constants import RIDDLE_WRITING_OUTPUT_DIR
from analysis.riddle_writing_analysis.survey_analysis import (
    load_survey,
    plot_time_per_riddle,
)
from analysis.utils import write_csv


def main() -> None:
    """Regenerate writing-time figure and aggregate table."""
    write_csv(
        plot_time_per_riddle(load_survey()),
        RIDDLE_WRITING_OUTPUT_DIR / "time_per_riddle.csv",
    )


if __name__ == "__main__":
    main()
