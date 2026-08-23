"""Report each model's lowest exact-match-performing communities."""

from pathlib import Path

import pandas as pd

from analysis.model_results.model_data import load_results

OUTPUT_DIR = Path(__file__).parent / "outputs"
WORST_COMMUNITY_COUNT = 5


def worst_communities_by_model(
    results: pd.DataFrame, n: int = WORST_COMMUNITY_COUNT
) -> pd.DataFrame:
    """Return the ``n`` lowest exact-match communities for every model.

    Accuracy is calculated only over completed responses, consistent with the
    denominator policy used throughout the model-results analysis.
    """
    if n < 1:
        raise ValueError("n must be at least 1")

    completed = results.loc[results["is_completed"]]
    rates = (
        completed.groupby(["model_display", "instance_community"])["is_correct"]
        .agg(exact_match_accuracy="mean", n_completed="size")
        .reset_index()
        .sort_values(
            ["model_display", "exact_match_accuracy", "instance_community"],
            kind="stable",
        )
    )
    worst = rates.groupby("model_display", sort=False).head(n).copy()
    worst.insert(1, "rank", worst.groupby("model_display").cumcount() + 1)
    return worst.rename(columns={"instance_community": "community"}).reset_index(
        drop=True
    )


def write_worst_communities_by_model(results: pd.DataFrame) -> None:
    """Write the five lowest-accuracy communities for each evaluated model."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    worst_communities_by_model(results).to_csv(
        OUTPUT_DIR / "five_worst_communities_by_model.csv", index=False
    )


def main() -> None:
    """Regenerate the per-model lowest-performing-community table."""
    write_worst_communities_by_model(load_results())


if __name__ == "__main__":
    main()
