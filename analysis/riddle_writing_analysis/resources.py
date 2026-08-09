"""Analyze resources contributors used while writing riddles."""

from analysis.riddle_writing_analysis.survey_analysis import (
    OUTPUT_DIR,
    load_survey,
    plot_resources_used,
)


def main() -> None:
    """Regenerate resource-use figure and aggregate table."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plot_resources_used(load_survey()).to_csv(
        OUTPUT_DIR / "resources_used.csv", index=False
    )


if __name__ == "__main__":
    main()
