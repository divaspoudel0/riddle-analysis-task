"""Analyze estimated time to write a riddle."""

from analysis.riddle_writing_analysis.survey_analysis import (
    OUTPUT_DIR,
    load_survey,
    plot_time_per_riddle,
)


def main() -> None:
    """Regenerate writing-time figure and aggregate table."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plot_time_per_riddle(load_survey()).to_csv(
        OUTPUT_DIR / "time_per_riddle.csv", index=False
    )


if __name__ == "__main__":
    main()
