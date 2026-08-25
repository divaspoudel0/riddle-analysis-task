"""Run all current analysis suites, including country coverage, in order."""

from analysis.dashboard.build_static import main as build_dashboard
from analysis.eval_analysis.main import main as run_eval_analysis
from analysis.model_results.main import main as run_model_analysis
from analysis.riddle_analysis.main import main as run_riddle_analysis
from analysis.riddle_writing_analysis.main import main as run_writing_analysis


def main() -> None:
    """Regenerate corpus figures, including the country coverage map."""
    run_riddle_analysis()
    run_eval_analysis()
    run_model_analysis()
    run_writing_analysis()
    build_dashboard()


if __name__ == "__main__":
    main()
