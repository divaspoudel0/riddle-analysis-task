"""Compare the topic-level effect of extended reasoning across model families.

The full-corpus table has a matched DeepSeek pair, but the human-evaluation
snapshot additionally contains matched GPT-5.5 and Claude Opus 4.7 variants.
This figure uses that common snapshot so each family is compared under the
same strict (score == 3) human-evaluation criterion.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm

from analysis.constants import TOPICS, figure_stem
from analysis.eval_analysis.data import FLAT_CSV as HUMAN_EVAL_PATH
from analysis.eval_analysis.data import MODEL_NAME_MAP
from analysis.eval_analysis.model_summary import complete_communities
from analysis.model_results.load_results import EXCLUDED_RIDDLES
from analysis.model_results.model_data import canonical_topic
from analysis.style import PALETTE, acl_figure_size, apply_style, save_figure_pair

OUTPUT_DIR = Path(__file__).parent / "outputs"

# ``baseline`` is the no/standard-reasoning run and ``reasoning`` is the
# matched extended-reasoning run. Keep these explicit rather than inferring
# modes from display strings: they are a substantive experimental choice.
MODEL_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("DeepSeek V4 Pro", "deepseek-v4-pro", "deepseek-v4-pro-thinking"),
    ("GPT-5.5", "GPT5.5 [none]", "GPT5.5 [high]"),
    (
        "Claude Opus 4.7",
        "claude-opus-4-7 [none]",
        "claude-opus-4-7 [thinking]",
    ),
)


def thinking_mode_deltas(flat_csv: Path = HUMAN_EVAL_PATH) -> pd.DataFrame:
    """Return strict human-evaluated accuracy deltas by topic and model pair.

    Only completed communities are included, matching the inclusion rule used
    for ``e_human_eval_model_summary.csv``. Values are percentage points.
    """
    frame = pd.read_csv(flat_csv, low_memory=False)
    frame = frame[~frame["riddle_id"].isin(EXCLUDED_RIDDLES)].copy()
    frame["model_display"] = frame["model_name"].map(MODEL_NAME_MAP)
    frame["topic"] = frame["riddle_id"].map(canonical_topic)

    complete = complete_communities(frame)
    scored = frame[
        frame["community"].isin(complete)
        & ~frame["scoring_method"].eq("pending_human_eval")
    ].copy()
    scored["is_strictly_correct"] = scored["score"].eq(3.0)

    records: list[dict[str, str | float | int]] = []
    for label, baseline, reasoning in MODEL_PAIRS:
        paired = scored[scored["model_display"].isin((baseline, reasoning))]
        missing = {baseline, reasoning} - set(paired["model_display"])
        if missing:
            raise ValueError(
                f"Missing matched human-evaluation runs: {sorted(missing)}"
            )
        counts = paired.groupby("model_display").size()
        rates = (
            paired.groupby(["topic", "model_display"])["is_strictly_correct"]
            .mean()
            .unstack("model_display")
            .reindex(index=TOPICS, columns=(baseline, reasoning))
        )
        if rates.isna().any().any():
            raise ValueError(f"Incomplete topic coverage for {label}.")
        for topic, row in rates.iterrows():
            records.append(
                {
                    "topic": topic,
                    "model_family": label,
                    "baseline_model": baseline,
                    "reasoning_model": reasoning,
                    "baseline_n": int(counts[baseline]),
                    "reasoning_n": int(counts[reasoning]),
                    "reasoning_minus_baseline_pp": (row[reasoning] - row[baseline])
                    * 100,
                }
            )
    return pd.DataFrame.from_records(records)


def plot_thinking_delta(_results: pd.DataFrame | None = None) -> None:
    """Write the three-family reasoning-mode comparison figure and data table.

    ``_results`` is retained for compatibility with the model-results driver;
    the figure deliberately draws from the broader human-evaluation snapshot.
    """
    deltas = thinking_mode_deltas()
    apply_style()
    fig, ax = plt.subplots(figsize=acl_figure_size(1, 4.0), layout="constrained")
    model_order = [pair[0] for pair in MODEL_PAIRS]
    table = deltas.pivot(
        index="topic",
        columns="model_family",
        values="reasoning_minus_baseline_pp",
    ).reindex(index=TOPICS, columns=model_order)
    color_limit = abs(table.to_numpy()).max()
    norm = TwoSlopeNorm(vmin=-color_limit, vcenter=0, vmax=color_limit)
    cmap = LinearSegmentedColormap.from_list(
        "reasoning_delta",
        (PALETTE["vermillion"], PALETTE["light_grey"], PALETTE["bluish_green"]),
    )
    image = ax.imshow(table, cmap=cmap, norm=norm, aspect="auto")
    ax.set_xticks(range(len(model_order)), ["DeepSeek", "GPT-5.5", "Claude"])
    ax.set_yticks(range(len(TOPICS)), TOPICS)
    ax.tick_params(axis="both", length=0)
    ax.grid(False)
    ax.set_ylabel("Riddle topic")
    ax.set_title("Human Evaluated Accuracy")
    for row, topic in enumerate(TOPICS):
        for column, model in enumerate(model_order):
            value = table.loc[topic, model]
            ax.text(
                column,
                row,
                f"{value:+.1f}",
                ha="center",
                va="center",
                fontsize=8,
                color=PALETTE["black"],
            )
    colorbar = fig.colorbar(image, ax=ax, pad=0.02, shrink=0.82)
    colorbar.set_label("Extended reasoning − baseline (pp)")
    save_figure_pair(
        fig, figure_stem("model_results", "reasoning_accuracy_delta_by_topic")
    )
    plt.close(fig)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    deltas.to_csv(OUTPUT_DIR / "reasoning_mode_delta_by_topic.csv", index=False)


def main() -> None:
    """Regenerate the human-evaluated reasoning-mode comparison."""
    plot_thinking_delta()


if __name__ == "__main__":
    main()
