"""Run the complete full-corpus model-results analysis suite."""

from analysis.constants import LANGUAGE_GROUP_ORDER, REGION_ORDER
from analysis.corpus import load_corpus_metadata
from analysis.model_results.community_performance import (
    write_worst_communities_by_model,
)
from analysis.model_results.data_audit import write_data_quality_report
from analysis.model_results.group_performance import plot_group_performance
from analysis.model_results.leaderboard import (
    load_human_eval_leaderboard,
    plot_leaderboard,
)
from analysis.model_results.model_data import load_scored_results
from analysis.model_results.model_registry import write_model_registry
from analysis.model_results.thinking_delta import plot_thinking_delta
from analysis.model_results.topic_performance import plot_topic_performance


def main() -> None:
    """Regenerate every model-result table and figure."""
    results = load_scored_results()
    write_data_quality_report(results)
    write_model_registry(results)
    plot_leaderboard(load_human_eval_leaderboard())
    plot_topic_performance(results)
    group_plots = [
        (
            "region",
            REGION_ORDER,
            "full_corpus_region_performance",
            "Strict match rate by region",
            "exact_match_accuracy_by_region",
            False,
        ),
        (
            "language_group",
            LANGUAGE_GROUP_ORDER,
            "full_corpus_language_group_performance",
            "Strict match rate across multi-community language groups",
            "exact_match_accuracy_by_language_group",
            False,
        ),
        (
            "language_code",
            tuple(sorted(load_corpus_metadata()["language_code"].unique())),
            "full_corpus_language_performance",
            "Strict match rate by language",
            "exact_match_accuracy_by_language",
            True,
        ),
    ]
    for column, order, name, title, figure_name, wide in group_plots:
        plot_group_performance(
            results, column, order, name, title, figure_name, wide=wide
        )
    plot_thinking_delta(results)
    write_worst_communities_by_model(results)


if __name__ == "__main__":
    main()
