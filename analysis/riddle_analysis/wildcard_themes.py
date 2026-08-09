"""Analyze and plot manually coded wildcard topic themes."""

from analysis.riddle_analysis.corpus_data import (
    load_corpus,
    plot_wildcard_themes,
)


def main() -> None:
    """Regenerate the wildcard-theme figure and supporting table."""
    plot_wildcard_themes(load_corpus())


if __name__ == "__main__":
    main()
