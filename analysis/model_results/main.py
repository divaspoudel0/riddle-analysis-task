"""Run the complete full-corpus model-results analysis suite."""

from analysis.constants import LANGUAGE_GROUP_ORDER, REGION_ORDER
from analysis.model_results.group_performance import plot_group_performance
from analysis.model_results.data_audit import write_data_quality_report
from analysis.model_results.leaderboard import plot_leaderboard
from analysis.model_results.model_data import load_results
from analysis.model_results.model_registry import write_model_registry
from analysis.model_results.outcome_distribution import plot_outcomes
from analysis.model_results.thinking_delta import plot_thinking_delta
from analysis.model_results.topic_performance import plot_topic_performance


def main() -> None:
    """Regenerate every model-result table and figure."""
    results = load_results()
    write_data_quality_report(results)
    write_model_registry(results)
    plot_leaderboard(results)
    plot_topic_performance(results)
    plot_outcomes(results)
    plot_group_performance(
        results,
        "region",
        REGION_ORDER,
        "full_corpus_region_performance",
        "Strict match rate by region",
    )
    plot_group_performance(
        results,
        "language_group",
        LANGUAGE_GROUP_ORDER,
        "full_corpus_language_group_performance",
        "Strict match rate across multi-community language groups",
    )
    plot_thinking_delta(results)


if __name__ == "__main__":
    main()
