"""Analyze contributor-reported generative-AI uses."""

from analysis.riddle_writing_analysis.survey_analysis import (
    OUTPUT_DIR,
    load_survey,
    plot_ai_uses,
)


def main() -> None:
    """Regenerate AI-use figure and aggregate table."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    plot_ai_uses(load_survey()).to_csv(OUTPUT_DIR / "ai_use_functions.csv", index=False)


if __name__ == "__main__":
    main()
