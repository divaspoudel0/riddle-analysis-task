"""Run all current analysis suites in their dependency order."""

from analysis.model_results.main import main as run_model_analysis
from analysis.riddle_analysis.main import main as run_riddle_analysis
from analysis.riddle_writing_analysis.main import main as run_writing_analysis


def main() -> None:
    """Regenerate corpus, model, then writing-analysis artifacts."""
    run_riddle_analysis()
    run_model_analysis()
    run_writing_analysis()


if __name__ == "__main__":
    main()
