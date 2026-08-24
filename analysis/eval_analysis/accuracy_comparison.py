"""Generate the exact-match versus human-correct accuracy figure."""

import matplotlib.pyplot as plt

from analysis.constants import figure_stem
from analysis.eval_analysis.plot_helpers import plot_accuracy_dumbbell
from analysis.model_results.leaderboard import load_human_eval_leaderboard
from analysis.style import save_figure_pair


def plot_exact_match_vs_human_correct():
    """Return the exact-match versus human-correct dumbbell chart."""
    results = load_human_eval_leaderboard().sort_values("human_accuracy")
    return plot_accuracy_dumbbell(
        results.set_index("model_display"),
        left_column="exact_match_accuracy",
        right_column="human_accuracy",
        left_label="Exact match",
        right_label="Human evaluation",
        x_label="Accuracy (%)",
        title=f"Exact-Match and Human-Evaluated Accuracy ({len(results)} Models)",
        figsize=(7.2, 8.0),
    )


def main() -> None:
    """Write the exact-match versus human-correct PNG/PDF pair."""
    fig = plot_exact_match_vs_human_correct()
    output = figure_stem("eval_analysis", "accuracy_exact_match_vs_human_correct")
    pdf_path, png_path = save_figure_pair(fig, output)
    plt.close(fig)
    print(f"Wrote {pdf_path} and {png_path}")


if __name__ == "__main__":
    main()
