"""Analyze coverage of human-validation metadata."""

from analysis.riddle_analysis.corpus_audit import plot_validation_coverage
from analysis.riddle_analysis.corpus_data import load_corpus


def main() -> None:
    """Regenerate the human-validation coverage figure and table."""
    plot_validation_coverage(load_corpus())


if __name__ == "__main__":
    main()
