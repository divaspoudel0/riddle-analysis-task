"""Build the four-tab, self-contained analysis report dashboard."""

from __future__ import annotations

import base64
import html
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from analysis.constants import FIGURES_DIR

DASHBOARD_DIR = Path(__file__).parent
OUTPUT = DASHBOARD_DIR / "index.html"


@dataclass(frozen=True)
class FigureSpec:
    """Metadata for one figure card in the report dashboard."""

    stem: str | None
    title: str
    caption: str
    description: str
    source: str | None = None


def figure(stem: str, title: str, caption: str, description: str) -> FigureSpec:
    """Create a figure card specification."""
    return FigureSpec(stem, title, caption, description)


FIGURE_CATALOG: dict[str, tuple[FigureSpec, ...]] = {
    "Riddle analysis": (
        figure(
            "r_wildcard_theme_distribution",
            "Wildcard theme distribution",
            "Distribution of coded themes among Wild Card riddles.",
            "Shows which cultural and everyday themes make up the open-ended Wild Card category.",
        ),
        figure(
            "r_answer_length_by_topic",
            "English answer length by topic",
            "Median and IQR of English riddle length by topic.",
            "Makes differences in typical length and spread visible across topics.",
        ),
        figure(
            "r_answer_length_by_region",
            "English answer length by region",
            "Median and IQR of English riddle length by region.",
            "Compares the amount of English context supplied by communities in different regions.",
        ),
        figure(
            "r_human_validation_coverage",
            "Human validation coverage",
            "Availability of validation metadata by collection round.",
            "Shows how completely each collection round records validator names and answer scores.",
        ),
    ),
    "Riddle writing": (
        figure(
            "w_topic_writing_difficulty",
            "Topic-writing difficulty",
            "Reported topic-writing difficulty by benchmark topic.",
            "Summarizes contributors’ self-reported difficulty when writing culturally specific riddles.",
        ),
        figure(
            "w_topic_difficulty_vs_model_accuracy",
            "Writing difficulty and model accuracy",
            "Topic difficulty compared with model accuracy; Wild Card is excluded.",
            "The correlation is descriptive: it compares the writing survey with model performance across eight fixed topics.",
        ),
        figure(
            "w_specificity_strategy",
            "Specificity strategy",
            "Contributors’ reported strategy for choosing answer specificity.",
            "Shows whether writers tend to choose a broad category, a specific entity, or another level of detail.",
        ),
        figure(
            "w_ai_use_functions",
            "Generative AI use",
            "Reported functions of generative AI during riddle writing.",
            "Counts the writing tasks for which contributors reported using generative AI.",
        ),
        figure(
            "w_confidence_distribution",
            "Confidence in community representation",
            "Self-reported confidence in community representation.",
            "Summarizes how confidently contributors felt they represented their community.",
        ),
        figure(
            "w_time_per_riddle",
            "Time per riddle",
            "Estimated time to write a complete riddle.",
            "Shows the reported effort required to produce one benchmark riddle.",
        ),
        figure(
            "w_resources_used",
            "Resources used while writing",
            "Resources selected while writing; selections are not mutually exclusive.",
            "Shows which references, tools, and personal knowledge contributors used during composition.",
        ),
    ),
    "Model results": (
        figure(
            "m_exact_match_accuracy_leaderboard",
            "Exact-match accuracy leaderboard",
            "Strict exact-match accuracy across model responses.",
            "Ranks models by the full-corpus exact-match rate.",
        ),
        figure(
            "m_exact_match_accuracy_by_topic",
            "Exact-match accuracy by topic",
            "Strict exact-match accuracy by benchmark topic.",
            "Highlights topic-level strengths and weaknesses behind the overall model ranking.",
        ),
        figure(
            "m_exact_match_accuracy_by_region",
            "Exact-match accuracy by region",
            "Strict exact-match accuracy by community region.",
            "Compares performance across the benchmark’s geographic groupings.",
        ),
        figure(
            "m_exact_match_accuracy_by_language_group",
            "Exact-match accuracy by language group",
            "Strict exact-match accuracy across multi-community language groups.",
            "Shows whether performance changes for language groups represented by several communities.",
        ),
        figure(
            "m_exact_match_accuracy_by_language",
            "Exact-match accuracy by language",
            "Strict exact-match accuracy by riddle language.",
            "Provides the most granular language-level view of model performance.",
        ),
        figure(
            "m_reasoning_accuracy_delta_by_topic",
            "Reasoning-mode accuracy delta",
            "Extended reasoning minus baseline accuracy, in percentage points, by topic.",
            "Measures how much the reasoning setting changes exact-match accuracy for the matched model snapshot.",
        ),
    ),
    "Evaluation": (
        figure(
            "e_accuracy_exact_match_vs_human_correct",
            "Exact match versus human correctness",
            "Exact-match accuracy compared with human-correct accuracy on complete communities.",
            "Separates strict automatic scoring from the human evaluation signal.",
        ),
        figure(
            "e_human_accuracy_distribution_by_community",
            "Human accuracy distribution",
            "Per-model human-correct accuracy across complete communities.",
            "Shows how consistently each model performs across communities.",
        ),
        figure(
            "e_human_accuracy_heatmap_by_community",
            "Human accuracy by community",
            "Human-correct accuracy for every model and complete community.",
            "Exposes community-specific strengths and failure patterns that averages hide.",
        ),
        figure(
            "e_human_correct_answers_missed_by_exact_match",
            "Human-correct answers missed by exact match",
            "Share of human-correct answers not captured by exact matching.",
            "Quantifies the answers that strict matching rejects even though a human marked them correct.",
        ),
        figure(
            "e_community_accuracy_exact_match_vs_human",
            "Community accuracy: exact match versus human",
            "Mean exact-match and human-correct accuracy by complete community.",
            "Compares the automatic floor and human-evaluation signal at the community level.",
        ),
        figure(
            "e_exact_match_agreement_by_community",
            "Exact-match agreement by community",
            "Cohen’s kappa between exact matching and human evaluation.",
            "Shows where strict matching agrees with human judgments and where it is less reliable.",
        ),
        figure(
            "e_outcome_failure_mode_composition",
            "Human-evaluation outcome composition",
            "Detailed outcome and failure-mode composition of human-scored responses.",
            "Breaks responses into exact, valid-but-different, partial, and incorrect outcomes.",
        ),
        figure(
            "e_human_outcomes_and_culture_distribution",
            "Outcomes and community distribution",
            "Outcome composition paired with human-correct accuracy across communities.",
            "Connects each model’s response types with the spread of its performance across cultures.",
        ),
        FigureSpec(
            None,
            "LLM-as-a-judge tooling",
            "Optional semantic evaluation is available as a reproducible command-line analysis.",
            "Run `python -m analysis.eval_analysis.llm_judge_run` for a paid, provider-backed judge. Raw outputs remain private.",
            "../eval_analysis/llm_judge_run.py",
        ),
    ),
}

SOURCE_BY_STEM: dict[str, str] = {
    "r_wildcard_theme_distribution": "../riddle_analysis/corpus_data.py",
    "r_answer_length_by_topic": "../riddle_analysis/corpus_data.py",
    "r_answer_length_by_region": "../riddle_analysis/corpus_data.py",
    "r_human_validation_coverage": "../riddle_analysis/corpus_audit.py",
    "w_topic_writing_difficulty": "../riddle_writing_analysis/survey_analysis.py",
    "w_topic_difficulty_vs_model_accuracy": "../riddle_writing_analysis/survey_analysis.py",
    "w_specificity_strategy": "../riddle_writing_analysis/survey_analysis.py",
    "w_ai_use_functions": "../riddle_writing_analysis/survey_analysis.py",
    "w_confidence_distribution": "../riddle_writing_analysis/survey_analysis.py",
    "w_time_per_riddle": "../riddle_writing_analysis/survey_analysis.py",
    "w_resources_used": "../riddle_writing_analysis/survey_analysis.py",
    "m_exact_match_accuracy_leaderboard": "../model_results/leaderboard.py",
    "m_exact_match_accuracy_by_topic": "../model_results/topic_performance.py",
    "m_exact_match_accuracy_by_region": "../model_results/group_performance.py",
    "m_exact_match_accuracy_by_language_group": "../model_results/group_performance.py",
    "m_exact_match_accuracy_by_language": "../model_results/group_performance.py",
    "m_reasoning_accuracy_delta_by_topic": "../model_results/thinking_delta.py",
    "e_accuracy_exact_match_vs_human_correct": "../eval_analysis/accuracy_comparison.py",
    "e_human_accuracy_distribution_by_community": "../eval_analysis/human_accuracy.py",
    "e_human_accuracy_heatmap_by_community": "../eval_analysis/human_accuracy.py",
    "e_human_correct_answers_missed_by_exact_match": "../eval_analysis/human_accuracy.py",
    "e_community_accuracy_exact_match_vs_human": "../eval_analysis/community_metrics.py",
    "e_exact_match_agreement_by_community": "../eval_analysis/community_metrics.py",
    "e_outcome_failure_mode_composition": "../eval_analysis/outcome_failure_modes.py",
    "e_human_outcomes_and_culture_distribution": "../eval_analysis/outcome_culture_composite.py",
}


def _image_data(stem: str) -> str:
    """Return a PNG as a self-contained data URI."""
    path = FIGURES_DIR / f"{stem}.png"
    if not path.exists():
        raise FileNotFoundError(f"Dashboard figure is missing: {path}")
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def _card(spec: FigureSpec) -> str:
    """Render one figure or tooling card."""
    title = html.escape(spec.title)
    caption = html.escape(spec.caption)
    description = html.escape(spec.description)
    source = spec.source or (SOURCE_BY_STEM.get(spec.stem) if spec.stem else None)
    if source is None:
        raise ValueError(f"No source script configured for {spec.title!r}")
    source_label = html.escape(Path(source).name)
    source_link = f'<a class="source" href="{html.escape(source)}">Generated by <code>{source_label}</code></a>'
    if spec.stem:
        stem = html.escape(spec.stem)
        media = f'<img class="zoomable" data-stem="{stem}" src="{_image_data(spec.stem)}" alt="{title}">'
    else:
        media = '<div class="tool-card">LLM-as-a-judge<br><span>Optional, paid evaluation tooling</span></div>'
    return f'<article class="figure-card">{media}<h3>{title}</h3><p class="caption">{caption}</p><p class="description">{description}</p>{source_link}</article>'


def build_html() -> str:
    """Render all dashboard tabs from the figure catalog."""
    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    tabs: list[str] = []
    panes: list[str] = []
    for index, (name, specs) in enumerate(FIGURE_CATALOG.items()):
        tab_id = f"tab-{index}"
        active = " active" if index == 0 else ""
        tabs.append(
            f'<button class="tab{active}" data-target="{tab_id}">{html.escape(name)}</button>'
        )
        cards = "\n".join(_card(spec) for spec in specs)
        panes.append(
            f'<section id="{tab_id}" class="pane{active}"><div class="grid">{cards}</div></section>'
        )
    return HTML_TEMPLATE.format(
        generated=generated, tabs="\n".join(tabs), panes="\n".join(panes)
    )


def main() -> None:
    """Write the self-contained dashboard HTML."""
    OUTPUT.write_text(build_html(), encoding="utf-8")
    count = sum(
        spec.stem is not None for specs in FIGURE_CATALOG.values() for spec in specs
    )
    print(f"Wrote {OUTPUT} with {count} embedded figures")


HTML_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Multicultural Riddles — Analysis report</title>
<script src="https://cdn.jsdelivr.net/npm/medium-zoom@1.1.0/dist/medium-zoom.min.js"></script>
<style>
:root {{ --ink:#17202a; --muted:#637080; --line:#dfe5ea; --blue:#28658f; --bg:#f7f9fb; --card:#fff; }}
* {{ box-sizing:border-box; }} body {{ margin:0; color:var(--ink); background:var(--bg); font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; line-height:1.5; }}
.wrap {{ max-width:1240px; margin:0 auto; padding:36px 24px 64px; }} header {{ max-width:840px; margin-bottom:28px; }}
.eyebrow {{ color:var(--blue); font-size:12px; font-weight:700; letter-spacing:.08em; text-transform:uppercase; }}
h1 {{ margin:5px 0 8px; font-size:30px; letter-spacing:-.025em; }} .intro {{ color:var(--muted); font-size:15px; margin:0; }}
.tabs {{ display:flex; gap:4px; flex-wrap:wrap; border-bottom:1px solid var(--line); margin-bottom:22px; }}
.tab {{ border:0; border-bottom:3px solid transparent; background:transparent; color:var(--muted); cursor:pointer; font:inherit; font-size:14px; padding:10px 15px; margin-bottom:-1px; }}
.tab:hover {{ color:var(--ink); }} .tab.active {{ color:var(--blue); border-bottom-color:var(--blue); font-weight:700; }}
.pane {{ display:none; }} .pane.active {{ display:block; }} .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(350px,1fr)); gap:22px; align-items:start; }}
.figure-card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; overflow:hidden; box-shadow:0 2px 7px rgba(23,32,42,.04); }}
.figure-card img {{ display:block; width:100%; height:auto; background:#fff; border-bottom:1px solid var(--line); cursor:zoom-in; }} .figure-card h3,.figure-card p {{ margin-left:18px; margin-right:18px; }}
.figure-card h3 {{ font-size:17px; margin-top:16px; margin-bottom:4px; }} .caption {{ color:var(--ink); font-size:13px; font-style:italic; margin-top:0; margin-bottom:7px; }} .description {{ color:var(--muted); font-size:13px; margin-top:0; margin-bottom:18px; }}
.source {{ display:block; color:var(--blue); font-size:12px; margin:0 18px 18px; text-decoration:none; }} .source:hover {{ text-decoration:underline; }}
.tool-card {{ display:flex; align-items:center; justify-content:center; min-height:180px; padding:24px; color:var(--blue); background:#eef5fa; border-bottom:1px solid var(--line); font-size:21px; font-weight:700; text-align:center; }} .tool-card span {{ display:block; color:var(--muted); font-size:13px; font-weight:400; margin-top:5px; }}
footer {{ color:var(--muted); font-size:12px; border-top:1px solid var(--line); margin-top:34px; padding-top:16px; }}
@media (max-width:600px) {{ .wrap {{ padding:24px 14px 44px; }} h1 {{ font-size:25px; }} .grid {{ grid-template-columns:1fr; }} .tab {{ padding-left:9px; padding-right:9px; }} }}
</style></head><body><main class="wrap">
<header><div class="eyebrow">Multicultural Riddles Benchmark</div><h1>Analysis report</h1><p class="intro">Corpus structure, riddle-writing process, model exact-match results, and evaluation evidence. Each card pairs a figure with its caption and a short reading guide. Generated {generated}.</p></header>
<nav class="tabs" aria-label="Analysis sections">{tabs}</nav>{panes}
<footer>Source figures live in <code>analysis/figures/</code>. Figure ownership and the reproducibility map are documented in <code>analysis/AGENTS.md</code>.</footer>
</main><script>
document.querySelectorAll('.tab').forEach(function (button) {{ button.addEventListener('click', function () {{ document.querySelectorAll('.tab,.pane').forEach(function (element) {{ element.classList.remove('active'); }}); button.classList.add('active'); document.getElementById(button.dataset.target).classList.add('active'); }}); }});
if (window.mediumZoom) {{ mediumZoom('.zoomable', {{ background: '#17202a' }}); }}
</script></body></html>"""


if __name__ == "__main__":
    main()
