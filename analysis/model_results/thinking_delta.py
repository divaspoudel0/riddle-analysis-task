"""Compare DeepSeek thinking and non-thinking performance by topic."""

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from analysis.constants import figure_stem
from analysis.model_results.model_data import canonical_topic, load_results
from analysis.style import PALETTE, acl_figure_size, apply_style, save_figure_pair

OUTPUT_DIR = Path(__file__).parent / "outputs"


def plot_thinking_delta(results: pd.DataFrame) -> None:
    """Write topic deltas for matched DeepSeek thinking/non-thinking runs."""
    models = ["deepseek-v4-pro", "deepseek-v4-pro-thinking"]
    paired = results[results.model_display.isin(models)].assign(
        topic=lambda frame: frame.riddle_id.map(canonical_topic)
    )
    means = (
        paired.groupby(["topic", "model_display"])["is_correct"]
        .mean()
        .unstack("model_display")
    )
    delta = means[models[1]] - means[models[0]]
    delta_pp = delta * 100
    apply_style()
    fig, ax = plt.subplots(figsize=acl_figure_size(1, 3.1))
    ax.barh(
        delta_pp.index,
        delta_pp,
        color=[
            PALETTE["bluish_green"] if value >= 0 else PALETTE["vermillion"]
            for value in delta_pp
        ],
    )
    ax.tick_params(axis="y", length=0)
    padding = max(abs(delta_pp).max() * 0.12, 0.5)
    ax.set_xlim(delta_pp.min() - padding, delta_pp.max() + padding)
    for position, value in enumerate(delta_pp):
        ax.text(
            value + (padding / 4 if value >= 0 else -padding / 4),
            position,
            f"{value:+.2f} pp",
            ha="left" if value >= 0 else "right",
            va="center",
            fontsize=7,
        )
    ax.set(
        xlabel="Thinking − non-thinking strict match rate (percentage points)",
        title="DeepSeek V4 Pro: effect of thinking mode",
    )
    fig.tight_layout()
    save_figure_pair(
        fig, figure_stem("model_results", "deepseek_thinking_delta_by_topic")
    )
    plt.close(fig)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(
        {"topic": delta.index, "thinking_minus_non_thinking_match_rate": delta.values}
    ).to_csv(OUTPUT_DIR / "deepseek_thinking_delta_by_topic.csv", index=False)


def main() -> None:
    """Regenerate the DeepSeek thinking-mode comparison."""
    plot_thinking_delta(load_results())


if __name__ == "__main__":
    main()
