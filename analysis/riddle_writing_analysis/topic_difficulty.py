"""Analyze writing difficulty by benchmark topic."""

from analysis.riddle_writing_analysis.survey_analysis import (
    OUTPUT_DIR,
    load_survey,
    plot_topic_difficulty,
)


def main() -> None:
    """Regenerate topic-difficulty figure and aggregate table."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plot_topic_difficulty(load_survey()).to_csv(
        OUTPUT_DIR / "topic_difficulty.csv", index=False
    )


if __name__ == "__main__":
    main()
