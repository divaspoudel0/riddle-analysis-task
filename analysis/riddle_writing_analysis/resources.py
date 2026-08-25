"""Analyze resources contributors used while writing riddles."""

from analysis.constants import RIDDLE_WRITING_OUTPUT_DIR
from analysis.riddle_writing_analysis.survey_analysis import (
    load_survey,
    plot_resources_used,
)
from analysis.utils import write_csv


def main() -> None:
    """Regenerate resource-use figure and aggregate table."""
    write_csv(
        plot_resources_used(load_survey()),
        RIDDLE_WRITING_OUTPUT_DIR / "resources_used.csv",
    )


if __name__ == "__main__":
    main()
