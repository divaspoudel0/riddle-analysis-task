"""Run the complete current-corpus analysis suite."""

from analysis.riddle_analysis.corpus_audit import (
    plot_validation_coverage,
    write_quality_report,
)
from analysis.riddle_analysis.corpus_data import (
    load_corpus,
    plot_english_length_by_region,
    plot_english_length_by_topic,
    plot_wildcard_themes,
    save_tables,
)
from analysis.riddle_analysis.coverage_map import plot_languages_by_country


def main() -> None:
    """Regenerate all riddle-corpus tables and figures."""
    corpus = load_corpus()
    save_tables(corpus)
    write_quality_report(corpus)
    plot_languages_by_country()
    plot_wildcard_themes(corpus)
    plot_english_length_by_topic(corpus)
    plot_validation_coverage(corpus)
    plot_english_length_by_region(corpus)


if __name__ == "__main__":
    main()
