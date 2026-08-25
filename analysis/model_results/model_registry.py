"""Write the data-derived model registry and paper selection audit."""

import pandas as pd

from analysis.constants import MODEL_RESULTS_OUTPUT_DIR
from analysis.model_results.model_data import load_scored_results
from analysis.model_results.model_selection import PAPER_MODEL_ORDER

OUTPUT_DIR = MODEL_RESULTS_OUTPUT_DIR


def write_model_registry(results: pd.DataFrame) -> None:
    """Write available models and the paper-selection decision table."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    registry = (
        results.groupby("model_display")
        .agg(
            model_id=("model_id", "first"),
            reasoning_mode=("reasoning_mode", "first"),
            evaluation_category=("eval_category", "first"),
            v0_rows=("run_batch", lambda values: int((values == "v0").sum())),
            v1_rows=("run_batch", lambda values: int((values == "v1").sum())),
            v2_rows=("run_batch", lambda values: int((values == "v2").sum())),
        )
        .reset_index()
    )
    registry["selected_for_paper"] = registry.model_display.isin(PAPER_MODEL_ORDER)
    registry.to_csv(OUTPUT_DIR / "models.csv", index=False)
    selection = pd.DataFrame({"model_display": PAPER_MODEL_ORDER})
    selection.insert(0, "paper_order", range(1, len(selection) + 1))
    selection["available_with_complete_v0_v2_coverage"] = selection.model_display.isin(
        registry.model_display
    )
    selection["figure_status"] = selection[
        "available_with_complete_v0_v2_coverage"
    ].map({True: "included", False: "awaiting complete results"})
    selection.to_csv(OUTPUT_DIR / "paper_model_selection.csv", index=False)


def main() -> None:
    """Regenerate model registry outputs."""
    write_model_registry(load_scored_results())


if __name__ == "__main__":
    main()
