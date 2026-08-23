"""Run the complete human-evaluation analysis suite."""

from analysis.eval_analysis.accuracy_comparison import main as run_accuracy_comparison
from analysis.eval_analysis.community_metrics import main as run_community_metrics
from analysis.eval_analysis.human_accuracy import main as run_human_accuracy
from analysis.eval_analysis.model_summary import main as write_model_summary
from analysis.eval_analysis.outcome_failure_modes import (
    main as run_outcome_failure_modes,
)


def main() -> None:
    """Regenerate evaluation tables and evaluation figures."""
    write_model_summary()
    run_human_accuracy()
    run_accuracy_comparison()
    run_community_metrics()
    run_outcome_failure_modes()


if __name__ == "__main__":
    main()
