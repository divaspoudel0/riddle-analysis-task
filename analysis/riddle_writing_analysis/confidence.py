"""Analyze contributors' confidence in community representation."""

from analysis.riddle_writing_analysis.survey_analysis import (
    OUTPUT_DIR,
    load_survey,
    plot_confidence_distribution,
)


def main() -> None:
    """Regenerate confidence figure and aggregate table."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plot_confidence_distribution(load_survey()).to_csv(
        OUTPUT_DIR / "confidence_distribution.csv", index=False
    )


if __name__ == "__main__":
    main()
