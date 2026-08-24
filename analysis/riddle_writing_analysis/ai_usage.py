"""Analyze contributor-reported generative-AI uses."""

from analysis.constants import RIDDLE_WRITING_OUTPUT_DIR
from analysis.riddle_writing_analysis.survey_analysis import (
    load_survey,
    plot_ai_uses,
)
from analysis.utils import write_csv


def main() -> None:
    """Regenerate AI-use figure and aggregate table."""
    write_csv(
        plot_ai_uses(load_survey()),
        RIDDLE_WRITING_OUTPUT_DIR / "ai_use_functions.csv",
    )


if __name__ == "__main__":
    main()
