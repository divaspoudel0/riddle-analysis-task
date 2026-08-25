"""Analyze English riddle lengths by topic and region."""

from analysis.riddle_analysis.corpus_data import (
    load_corpus,
    plot_english_length_by_region,
    plot_english_length_by_topic,
)


def main() -> None:
    """Regenerate both English-length figures and their tables."""
    corpus = load_corpus()
    plot_english_length_by_topic(corpus)
    plot_english_length_by_region(corpus)


if __name__ == "__main__":
    main()
