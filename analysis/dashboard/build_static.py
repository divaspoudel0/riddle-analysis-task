"""Build the analysis report dashboard."""

from __future__ import annotations

import base64
import html
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from analysis.constants import FIGURES_DIR, REGION_ORDER
from analysis.corpus import load_corpus_metadata
from analysis.eval_analysis.data import coverage_report, load_human_evaluation
from analysis.tables.build import (
    corpus_coverage_display,
    model_performance_display,
)
from analysis.tables.build import (
    main as build_table_artifacts,
)

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
    figure_id: str | None = None


def figure(
    stem: str,
    title: str,
    caption: str,
    description: str,
    *,
    figure_id: str,
) -> FigureSpec:
    """Create a figure card specification."""
    return FigureSpec(stem, title, caption, description, figure_id=figure_id)


FIGURE_CATALOG: dict[str, tuple[FigureSpec, ...]] = {
    "Riddle analysis": (
        figure(
            "r_wildcard_theme_distribution",
            "Wildcard theme distribution",
            "Distribution of coded themes among Wild Card riddles.",
            "Shows which cultural and everyday themes make up the open-ended Wild Card category.",
            figure_id="R1",
        ),
        figure(
            "r_languages_by_country",
            "Corpus language coverage by country",
            "Distinct corpus languages represented in each country.",
            "Shows the geographic distribution of the benchmark’s language coverage; countries without a corpus language remain neutral gray.",
            figure_id="R2",
        ),
        figure(
            "r_answer_length_by_topic",
            "English answer length by topic",
            "Median and IQR of English riddle length by topic.",
            "Makes differences in typical length and spread visible across topics.",
            figure_id="R3",
        ),
        figure(
            "r_answer_length_by_region",
            "English answer length by region",
            "Median and IQR of English riddle length by region.",
            "Compares the amount of English context supplied by communities in different regions.",
            figure_id="R4",
        ),
    ),
    "Riddle writing": (
        figure(
            "w_topic_writing_difficulty",
            "Topic-writing difficulty",
            "Reported topic-writing difficulty by benchmark topic.",
            "Summarizes contributors’ self-reported difficulty when writing culturally specific riddles.",
            figure_id="W1",
        ),
        figure(
            "w_topic_difficulty_vs_model_accuracy",
            "Writing difficulty and model accuracy",
            "Topic difficulty compared with model accuracy; Wild Card is excluded.",
            "The correlation is descriptive: it compares the writing survey with model performance across eight fixed topics.",
            figure_id="W2",
        ),
        figure(
            "w_specificity_strategy",
            "Specificity strategy",
            "Contributors’ reported strategy for choosing answer specificity.",
            "Shows whether writers tend to choose a broad category, a specific entity, or another level of detail.",
            figure_id="W3",
        ),
        figure(
            "w_ai_use_functions",
            "Generative AI use",
            "Reported functions of generative AI during riddle writing.",
            "Counts the writing tasks for which contributors reported using generative AI.",
            figure_id="W4",
        ),
        figure(
            "w_confidence_distribution",
            "Confidence in community representation",
            "Self-reported confidence in community representation.",
            "Summarizes how confidently contributors felt they represented their community.",
            figure_id="W5",
        ),
        figure(
            "w_time_per_riddle",
            "Time per riddle",
            "Estimated time to write a complete riddle.",
            "Shows the reported effort required to produce one benchmark riddle.",
            figure_id="W6",
        ),
        figure(
            "w_resources_used",
            "Resources used while writing",
            "Resources selected while writing; selections are not mutually exclusive.",
            "Shows which references, tools, and personal knowledge contributors used during composition.",
            figure_id="W7",
        ),
    ),
    "Model results": (
        figure(
            "m_exact_match_accuracy_leaderboard",
            "Exact-match accuracy leaderboard",
            "Strict exact-match accuracy across model responses.",
            "Ranks models by the full-corpus exact-match rate.",
            figure_id="M1",
        ),
        figure(
            "m_exact_match_accuracy_by_topic",
            "Exact-match accuracy by topic",
            "Strict exact-match accuracy by benchmark topic.",
            "Highlights topic-level strengths and weaknesses behind the overall model ranking.",
            figure_id="M2",
        ),
        figure(
            "m_exact_match_accuracy_by_region",
            "Exact-match accuracy by region",
            "Strict exact-match accuracy by community region.",
            "Compares performance across the benchmark’s geographic groupings.",
            figure_id="M3",
        ),
        figure(
            "m_exact_match_accuracy_by_language_group",
            "Exact-match accuracy by language group",
            "Strict exact-match accuracy across multi-community language groups.",
            "Shows whether performance changes for language groups represented by several communities.",
            figure_id="M4",
        ),
        figure(
            "m_exact_match_accuracy_by_language",
            "Exact-match accuracy by language",
            "Strict exact-match accuracy by riddle language.",
            "Provides the most granular language-level view of model performance.",
            figure_id="M5",
        ),
        figure(
            "m_reasoning_accuracy_delta_by_topic",
            "Reasoning-mode accuracy delta",
            "Extended reasoning minus baseline accuracy, in percentage points, by topic.",
            "Measures how much the reasoning setting changes exact-match accuracy for the matched model snapshot.",
            figure_id="M6",
        ),
    ),
    "Evaluation": (
        figure(
            "e_accuracy_exact_match_vs_human_correct",
            "Exact match versus human correctness",
            "Exact-match accuracy compared with human-correct accuracy on complete communities.",
            "Separates strict automatic scoring from the human evaluation signal.",
            figure_id="E1",
        ),
        figure(
            "e_human_accuracy_distribution_by_community",
            "Human accuracy distribution",
            "Per-model human-correct accuracy across complete communities.",
            "Shows how consistently each model performs across communities.",
            figure_id="E2",
        ),
        figure(
            "e_human_accuracy_heatmap_by_community",
            "Human accuracy by community",
            "Human-correct accuracy for every model and complete community.",
            "Exposes community-specific strengths and failure patterns that averages hide.",
            figure_id="E3",
        ),
        figure(
            "e_human_correct_answers_missed_by_exact_match",
            "Human-correct answers missed by exact match",
            "Share of human-correct answers not captured by exact matching.",
            "Quantifies the answers that strict matching rejects even though a human marked them correct.",
            figure_id="E4",
        ),
        figure(
            "e_community_accuracy_exact_match_vs_human",
            "Community accuracy: exact match versus human",
            "Mean exact-match and human-correct accuracy by complete community.",
            "Compares the automatic floor and human-evaluation signal at the community level.",
            figure_id="E5",
        ),
        figure(
            "e_exact_match_agreement_by_community",
            "Exact-match agreement by community",
            "Cohen’s kappa between exact matching and human evaluation.",
            "Shows where strict matching agrees with human judgments and where it is less reliable.",
            figure_id="E6",
        ),
        figure(
            "e_outcome_failure_mode_composition",
            "Human-evaluation outcome composition",
            "Detailed outcome and failure-mode composition of human-scored responses.",
            "Breaks responses into exact, valid-but-different, partial, and incorrect outcomes.",
            figure_id="E7",
        ),
        FigureSpec(
            None,
            "LLM-as-a-judge tooling",
            "Optional semantic evaluation is available as a reproducible command-line analysis.",
            "Run `python -m analysis.eval_analysis.llm_judge_run` for a paid, provider-backed judge. Raw outputs remain private.",
            "../eval_analysis/llm_judge_run.py",
        ),
    ),
    "Progress Trackers": (
        figure(
            "r_human_validation_coverage",
            "Human validation coverage",
            "Availability of validation metadata by collection round.",
            "Shows how completely each collection round records validator names and answer scores.",
            figure_id="P1",
        ),
    ),
}

TAB_PREFIXES: dict[str, str] = {
    "Riddle analysis": "R",
    "Riddle writing": "W",
    "Model results": "M",
    "Evaluation": "E",
    "Progress Trackers": "P",
}

HIGHLIGHT_MODELS: tuple[str, ...] = (
    "gemini-3.1-pro-preview",
    "GPT5.5 [high]",
    "claude-opus-4-7 [thinking]",
    "deepseek-v4-pro",
    "Qwen/Qwen3.5-0.8B",
)

SOURCE_BY_STEM: dict[str, str] = {
    "r_wildcard_theme_distribution": "../riddle_analysis/corpus_data.py",
    "r_languages_by_country": "../riddle_analysis/coverage_map.py",
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
    card_id = (
        f' data-figure-id="{html.escape(spec.figure_id)}"' if spec.figure_id else ""
    )
    figure_label = (
        f'<span class="figure-id">{html.escape(spec.figure_id)}</span> '
        if spec.figure_id
        else ""
    )
    paper_action = ""
    if spec.stem and spec.figure_id:
        paper_action = f'<div class="figure-actions"><button type="button" class="paper-toggle" data-figure-id="{html.escape(spec.figure_id)}" aria-pressed="false">Add to Paper Figures</button></div>'
    return f'<article class="figure-card"{card_id}>{media}<h3>{figure_label}{title}</h3><p class="caption">{caption}</p><p class="description">{description}</p>{paper_action}{source_link}</article>'


def _overview_data() -> dict[str, object]:
    """Build JSON-safe data for the restored exploratory overview charts."""
    frame = load_human_evaluation()
    coverage = coverage_report(frame)
    complete = set(coverage.index[coverage["status"].eq("complete")])
    scored = frame[frame["community"].isin(complete) & ~frame["is_pending"]]
    accuracy = (
        scored.groupby(["model_display", "community"])["is_correct"]
        .mean()
        .mul(100)
        .unstack()
    )

    metadata = load_corpus_metadata().set_index("community")
    region_box: dict[str, dict[str, object]] = {}
    for region in REGION_ORDER:
        communities = [
            community
            for community in accuracy.columns
            if metadata["region"].get(community) == region
        ]
        if not communities:
            continue
        means = accuracy[communities].mean(axis=1)
        region_box[region] = {
            "all": [float(value) for value in means.dropna()],
            "highlights": {
                model: float(means[model])
                for model in HIGHLIGHT_MODELS
                if model in means.index and pd.notna(means[model])
            },
            "communities": len(communities),
        }

    human = frame[frame["is_human"] & frame["community"].isin(complete)].copy()
    human["is_hallucinated"] = (
        human["error_type_label"].fillna("").str.startswith("0.3")
    )
    bubble_frame = (
        human.groupby("model_display").agg(
            accuracy=("is_correct", "mean"),
            hallucination=("is_hallucinated", "mean"),
        )
        * 100
    )
    bubble = [
        {
            "model": model,
            "accuracy": float(row["accuracy"]),
            "hallucination": float(row["hallucination"]),
        }
        for model, row in bubble_frame.sort_values(
            "accuracy", ascending=False
        ).iterrows()
    ]

    ridge = {
        model: [float(value) for value in accuracy.loc[model].dropna()]
        for model in accuracy.mean(axis=1).sort_values().index
    }

    country_values: dict[str, list[float]] = {}
    for community in accuracy.columns:
        country = metadata.at[community, "country"]
        country_values.setdefault(country, []).extend(
            float(value) for value in accuracy[community].dropna()
        )
    choropleth = [
        {
            "country": country,
            "accuracy": round(sum(values) / len(values), 1),
            "n": len(values),
        }
        for country, values in sorted(country_values.items())
        if values
    ]

    coverage_records = json.loads(coverage.reset_index().to_json(orient="records"))
    return {
        "meta": {
            "complete": len(complete),
            "total": len(coverage),
            "models": len(accuracy.index),
        },
        "region_box": region_box,
        "region_order": [region for region in REGION_ORDER if region in region_box],
        "highlights": list(HIGHLIGHT_MODELS),
        "bubble": bubble,
        "ridge": ridge,
        "choropleth": choropleth,
        "coverage": coverage_records,
    }


def _overview_pane() -> str:
    """Render the first dashboard pane with its interactive chart containers."""
    return """<section id="tab-0" class="pane active overview-pane">
<div class="overview-intro"><h2>Overview</h2><div class="overview-stats"><span><strong id="overview-complete">—</strong> complete communities</span><span><strong id="overview-total">—</strong> communities in the coverage export</span><span><strong id="overview-models">—</strong> evaluated models</span></div></div>
<div class="overview-grid">
<article class="overview-panel overview-wide"><h3>Human accuracy by region</h3><div id="overview-region" class="overview-chart" role="img" aria-label="Box plot of human accuracy by region with representative model markers"></div><p class="overview-caption">Each box shows the spread of model means across complete communities in a region. Markers identify five representative model configurations. Regions without complete communities are omitted.</p></article>
<article class="overview-panel"><h3>Accuracy and hallucination</h3><div id="overview-bubble" class="overview-chart" role="img" aria-label="Scatter plot comparing model accuracy and hallucination rate"></div><p class="overview-caption">Each point is a model. Hallucination rate is the share of human-scored responses labeled with the 0.3 hallucination outcome.</p></article>
<article class="overview-panel"><h3>Human accuracy by country</h3><div id="overview-map" class="overview-chart" role="img" aria-label="Choropleth map of human accuracy by country"></div><p class="overview-caption">Country values average model accuracy across complete communities that map to that country. Unfilled countries have no complete community in this export.</p></article>
<article class="overview-panel overview-wide"><h3>Per-community accuracy distributions</h3><div id="overview-ridge" class="overview-chart" role="img" aria-label="Violin distributions of model accuracy across complete communities"></div><p class="overview-caption">Each distribution shows one model’s accuracy across complete communities. Models are ordered by their mean accuracy.</p></article>
</div></section>"""


def _progress_tracker_panel() -> str:
    """Render the human-evaluation progress tracker panel."""
    return """<article class="overview-panel overview-wide"><h2>Human-evaluation coverage</h2><p class="overview-caption">Coverage of human scoring across communities. Complete communities are used by the evaluation and model-result summaries.</p><div id="progress-coverage" class="overview-table"></div><p id="progress-coverage-note" class="overview-caption"></p></article>"""


def _overview_script(data: dict[str, object]) -> str:
    """Render the JavaScript that draws the interactive overview charts."""
    data_json = json.dumps(data, separators=(",", ":"))
    return f"""const OVERVIEW = {data_json};
const PLOT_LAYOUT = {{paper_bgcolor:'#fff',plot_bgcolor:'#fff',font:{{family:'-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif',size:12,color:'#17202a'}},margin:{{l:58,r:18,t:18,b:58}},xaxis:{{gridcolor:'#edf0f2',zeroline:false}},yaxis:{{gridcolor:'#edf0f2',zeroline:false}},hoverlabel:{{namelength:-1}}}};
const HIGHLIGHT_COLORS = ['#28658f','#c46b2b','#3b7d54','#7651a8','#8a5a44'];
const HIGHLIGHT_SYMBOLS = ['cross','diamond','triangle-up','triangle-down','star'];
function renderOverview() {{
  document.getElementById('overview-complete').textContent = OVERVIEW.meta.complete;
  document.getElementById('overview-total').textContent = OVERVIEW.meta.total;
  document.getElementById('overview-models').textContent = OVERVIEW.meta.models;
  const regions = OVERVIEW.region_order;
  const regionX = [], regionY = [];
  regions.forEach(function (region) {{ OVERVIEW.region_box[region].all.forEach(function (value) {{ regionX.push(region); regionY.push(value); }}); }});
  const regionTraces = [{{type:'box',x:regionX,y:regionY,name:'All models',boxpoints:false,fillcolor:'#e9f0f5',line:{{color:'#8ea4b5'}},showlegend:false,hovertemplate:'%{{x}}<br>%{{y:.1f}}%<extra></extra>'}}];
  OVERVIEW.highlights.forEach(function (model, index) {{
    const x = [], y = [];
    regions.forEach(function (region) {{ const value = OVERVIEW.region_box[region].highlights[model]; if (value != null) {{ x.push(region); y.push(value); }} }});
    regionTraces.push({{type:'scatter',mode:'markers',name:model,x:x,y:y,marker:{{symbol:HIGHLIGHT_SYMBOLS[index],color:HIGHLIGHT_COLORS[index],size:11,line:{{color:'#fff',width:1}}}},hovertemplate:model+'<br>%{{x}}: %{{y:.1f}}%<extra></extra>'}});
  }});
  Plotly.newPlot('overview-region',regionTraces,{{...PLOT_LAYOUT,height:500,margin:{{l:58,r:18,t:18,b:110}},yaxis:{{title:'Human accuracy (%)',range:[0,100],dtick:20,gridcolor:'#edf0f2',zeroline:false}},xaxis:{{type:'category',categoryorder:'array',categoryarray:regions,tickangle:-35,automargin:true}},legend:{{orientation:'h',y:1.15,font:{{size:10}}}}}},{{responsive:true,displaylogo:false}});

  const bubble = OVERVIEW.bubble;
  Plotly.newPlot('overview-bubble',[{{type:'scatter',mode:'markers+text',x:bubble.map(function (row) {{ return row.accuracy; }}),y:bubble.map(function (row) {{ return row.hallucination; }}),text:bubble.map(function (row) {{ return row.model; }}),textposition:'top center',textfont:{{size:8}},marker:{{size:12,color:bubble.map(function (row) {{ return row.accuracy; }}),colorscale:'Blues',cmin:0,cmax:100,line:{{color:'#52606d',width:.6}}}},hovertemplate:'%{{text}}<br>accuracy: %{{x:.1f}}%<br>hallucination: %{{y:.1f}}%<extra></extra>'}}],{{...PLOT_LAYOUT,height:500,xaxis:{{title:'Accuracy (%)',range:[0,100],gridcolor:'#edf0f2',zeroline:false}},yaxis:{{title:'Hallucination (%)',range:[0,100],gridcolor:'#edf0f2',zeroline:false}}}},{{responsive:true,displaylogo:false}});

  const countries = OVERVIEW.choropleth;
  Plotly.newPlot('overview-map',[{{type:'choropleth',locations:countries.map(function (row) {{ return row.country; }}),locationmode:'country names',z:countries.map(function (row) {{ return row.accuracy; }}),text:countries.map(function (row) {{ return row.country+': '+row.accuracy+'% ('+row.n+' model-community means)'; }}),hovertemplate:'%{{text}}<extra></extra>',colorscale:'Blues',zmin:0,zmax:100,marker:{{line:{{color:'#fff',width:.5}}}},colorbar:{{title:'Accuracy %',thickness:12,len:.7}}}}],{{height:500,margin:{{l:0,r:0,t:18,b:0}},geo:{{showframe:false,showcoastlines:false,landcolor:'#e7ebee',showcountries:true,countrycolor:'#fff',projection:{{type:'natural earth'}}}}}},{{responsive:true,displaylogo:false}});

  const models = Object.keys(OVERVIEW.ridge);
  const ridgeTraces = models.slice().reverse().map(function (model) {{ return {{type:'violin',x:OVERVIEW.ridge[model],y0:model,orientation:'h',side:'positive',width:2.5,points:false,bandwidth:6,spanmode:'hard',line:{{color:'#28658f',width:1}},fillcolor:'rgba(40,101,143,.28)',showlegend:false,hovertemplate:model+': %{{x:.1f}}%<extra></extra>'}}; }});
  Plotly.newPlot('overview-ridge',ridgeTraces,{{...PLOT_LAYOUT,height:Math.max(500,26*models.length),margin:{{l:185,r:20,t:18,b:48}},xaxis:{{title:'Accuracy (%)',range:[0,100],gridcolor:'#edf0f2',zeroline:false}},yaxis:{{automargin:true,type:'category'}}}},{{responsive:true,displaylogo:false}});

  const order = {{complete:0,partial:1,thin:2,not_started:3}};
  const coverage = OVERVIEW.coverage.slice().sort(function (a,b) {{ return order[a.status]-order[b.status] || b.pct_complete-a.pct_complete; }});
  document.getElementById('progress-coverage').innerHTML = '<table><thead><tr><th>Community</th><th>Status</th><th>Complete</th><th>Human</th><th>Pending</th><th>Eligible</th></tr></thead><tbody>'+coverage.map(function (row) {{ return '<tr><td>'+row.community+'</td><td><span class="status status-'+row.status+'">'+row.status.replace('_',' ')+'</span></td><td>'+((row.pct_complete == null) ? '—' : row.pct_complete+'%')+'</td><td>'+row.human_done+'</td><td>'+row.pending+'</td><td>'+row.human_eligible+'</td></tr>'; }}).join('')+'</tbody></table>';
  const unfinished = coverage.filter(function (row) {{ return row.status === 'not_started' || row.status === 'thin'; }}).map(function (row) {{ return row.community; }});
  document.getElementById('progress-coverage-note').textContent = unfinished.length ? 'Not started or thin coverage: '+unfinished.join(', ') : 'All communities have complete human-evaluation coverage.';
}}
renderOverview();
"""


def _paper_table_panel(
    title: str,
    caption: str,
    frame: pd.DataFrame,
    csv_href: str,
) -> str:
    """Render one publication table panel for the static dashboard."""
    table = frame.to_html(
        index=False,
        escape=True,
        classes="paper-table",
        border=0,
    )
    return f"""<article class="paper-table-panel"><h3>{html.escape(title)}</h3>
<p class="caption">{html.escape(caption)}</p><div class="paper-table-wrap">{table}</div>
<a class="source" href="{html.escape(csv_href)}">Download source CSV</a></article>"""


def _paper_tables_pane() -> str:
    """Render the paper tables using the shared table builders."""
    corpus = corpus_coverage_display()
    models = model_performance_display()
    return f"""<section id="tab-1" class="pane paper-tables-pane">
<div class="paper-table-grid">
{_paper_table_panel("Corpus coverage by region", "Counts of cultures, riddles, countries, and languages in the released corpus.", corpus, "../tables/outputs/table_01_corpus_coverage.csv")}
{_paper_table_panel("Model performance summary", "Exact-match and human-evaluation accuracy, with the highest- and lowest-performing communities.", models, "../tables/outputs/table_02_model_performance.csv")}
</div></section>"""


def _paper_figures_pane() -> str:
    """Render the paper-figure selection and ordering workspace."""
    return """<section id="tab-2" class="pane paper-figures-pane">
<div class="paper-figures-intro"><h2>Paper Figures</h2><p>Select figures from the analysis tabs to assemble a paper-ready figure sequence. Selected figures appear in the order you add them; use the controls on each preview to reorder them.</p><div class="paper-figure-summary"><span><strong id="paper-figure-count">0</strong> selected figures</span><button type="button" id="clear-paper-figures" class="paper-clear">Clear all</button></div></div>
<div id="paper-figure-empty" class="paper-figure-empty">No figures selected yet. Use “Add to Paper Figures” on any figure card.</div>
<div id="paper-figure-grid" class="paper-figure-grid" hidden></div>
</section>"""


def _paper_figures_script() -> str:
    """Render the client-side paper-figure selection and ordering behavior."""
    return """const paperFigureIds = [];
const sourceCards = new Map(Array.from(document.querySelectorAll('.figure-card[data-figure-id]')).map(function (card) { return [card.dataset.figureId, card]; }));
const paperFigureGrid = document.getElementById('paper-figure-grid');
const paperFigureEmpty = document.getElementById('paper-figure-empty');
const paperFigureCount = document.getElementById('paper-figure-count');
const clearPaperFigures = document.getElementById('clear-paper-figures');

function isPaperFigureSelected(figureId) {
  return paperFigureIds.indexOf(figureId) !== -1;
}

function updatePaperToggle(figureId) {
  const card = sourceCards.get(figureId);
  if (!card) return;
  const button = card.querySelector('.paper-toggle');
  const selected = isPaperFigureSelected(figureId);
  if (button) {
    button.textContent = selected ? 'Remove from Paper Figures' : 'Add to Paper Figures';
    button.setAttribute('aria-pressed', String(selected));
    button.classList.toggle('selected', selected);
  }
  card.classList.toggle('is-selected', selected);
}

function renderPaperFigures() {
  paperFigureGrid.replaceChildren();
  paperFigureIds.forEach(function (figureId, index) {
    const sourceCard = sourceCards.get(figureId);
    if (!sourceCard) return;
    const previewCard = sourceCard.cloneNode(true);
    previewCard.classList.add('paper-preview-card');
    const actions = previewCard.querySelector('.figure-actions');
    if (actions) {
      actions.innerHTML = '<span class="paper-order">Paper order ' + (index + 1) + ' of ' + paperFigureIds.length + '</span><div class="paper-order-controls"><button type="button" data-paper-move="-1" data-figure-id="' + figureId + '" aria-label="Move ' + figureId + ' up"' + (index === 0 ? ' disabled' : '') + '>Move up</button><button type="button" data-paper-move="1" data-figure-id="' + figureId + '" aria-label="Move ' + figureId + ' down"' + (index === paperFigureIds.length - 1 ? ' disabled' : '') + '>Move down</button></div>';
    }
    paperFigureGrid.appendChild(previewCard);
  });
  paperFigureGrid.hidden = paperFigureIds.length === 0;
  paperFigureEmpty.hidden = paperFigureIds.length !== 0;
  paperFigureCount.textContent = paperFigureIds.length;
  clearPaperFigures.disabled = paperFigureIds.length === 0;
  sourceCards.forEach(function (_card, figureId) { updatePaperToggle(figureId); });
}

function togglePaperFigure(figureId) {
  const index = paperFigureIds.indexOf(figureId);
  if (index === -1) paperFigureIds.push(figureId);
  else paperFigureIds.splice(index, 1);
  renderPaperFigures();
}

function movePaperFigure(figureId, direction) {
  const index = paperFigureIds.indexOf(figureId);
  const target = index + direction;
  if (index < 0 || target < 0 || target >= paperFigureIds.length) return;
  [paperFigureIds[index], paperFigureIds[target]] = [paperFigureIds[target], paperFigureIds[index]];
  renderPaperFigures();
}

document.querySelectorAll('.paper-toggle').forEach(function (button) {
  button.addEventListener('click', function () { togglePaperFigure(button.dataset.figureId); });
});
paperFigureGrid.addEventListener('click', function (event) {
  if (!(event.target instanceof Element)) return;
  const button = event.target.closest('button[data-paper-move]');
  if (button) movePaperFigure(button.dataset.figureId, Number(button.dataset.paperMove));
});
clearPaperFigures.addEventListener('click', function () { paperFigureIds.splice(0); renderPaperFigures(); });
renderPaperFigures();
"""


def build_html() -> str:
    """Render all dashboard tabs from the figure catalog."""
    generated = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    tabs: list[str] = [
        '<button class="tab active" data-target="tab-0">Overview</button>',
        '<button class="tab" data-target="tab-1">Tables</button>',
        '<button class="tab" data-target="tab-2">Paper Figures</button>',
    ]
    panes: list[str] = [_overview_pane(), _paper_tables_pane(), _paper_figures_pane()]
    for index, (name, specs) in enumerate(FIGURE_CATALOG.items(), start=3):
        tab_id = f"tab-{index}"
        active = ""
        tabs.append(
            f'<button class="tab{active}" data-target="{tab_id}">{html.escape(name)}</button>'
        )
        card_markup: list[str] = []
        for spec in specs:
            if spec.stem:
                prefix = TAB_PREFIXES[name]
                if not spec.figure_id or not spec.figure_id.startswith(prefix):
                    raise ValueError(
                        f"Figure {spec.stem!r} must have a {prefix}-prefixed ID"
                    )
            card_markup.append(_card(spec))
        cards = "\n".join(card_markup)
        progress_panel = (
            f'<div class="progress-grid">{_progress_tracker_panel()}</div>'
            if name == "Progress Trackers"
            else ""
        )
        panes.append(
            f'<section id="{tab_id}" class="pane{active}">{progress_panel}<div class="grid">{cards}</div></section>'
        )
    return HTML_TEMPLATE.format(
        generated=generated,
        tabs="\n".join(tabs),
        panes="\n".join(panes),
        overview_css=OVERVIEW_CSS,
        paper_figures_script=_paper_figures_script(),
        overview_script=_overview_script(_overview_data()),
    )


def main() -> None:
    """Write the self-contained dashboard HTML."""
    build_table_artifacts()
    OUTPUT.write_text(build_html(), encoding="utf-8")
    count = sum(
        spec.stem is not None for specs in FIGURE_CATALOG.values() for spec in specs
    )
    print(f"Wrote {OUTPUT} with {count} embedded figures")


HTML_TEMPLATE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Multicultural Riddles — Analysis report</title><link rel="icon" href="data:,">
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
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
.figure-card {{ background:var(--card); border:1px solid var(--line); border-radius:12px; overflow:hidden; box-shadow:0 2px 7px rgba(23,32,42,.04); }} .figure-card.is-selected {{ border-color:var(--blue); box-shadow:0 0 0 2px rgba(40,101,143,.14),0 2px 7px rgba(23,32,42,.04); }}
.figure-card img {{ display:block; width:100%; height:auto; background:#fff; border-bottom:1px solid var(--line); cursor:zoom-in; }} .figure-card h3,.figure-card p {{ margin-left:18px; margin-right:18px; }}
.figure-card h3 {{ font-size:17px; margin-top:16px; margin-bottom:4px; }} .figure-id {{ color:var(--blue); font-size:12px; letter-spacing:.04em; margin-right:5px; }} .caption {{ color:var(--ink); font-size:13px; font-style:italic; margin-top:0; margin-bottom:7px; }} .description {{ color:var(--muted); font-size:13px; margin-top:0; margin-bottom:18px; }}
.figure-actions {{ display:flex; align-items:center; justify-content:space-between; gap:12px; flex-wrap:wrap; margin:0 18px 14px; }} .paper-toggle,.paper-order-controls button,.paper-clear {{ border:1px solid #b9c8d3; border-radius:7px; background:#fff; color:var(--blue); cursor:pointer; font:inherit; font-size:12px; padding:6px 10px; }} .paper-toggle:hover,.paper-order-controls button:hover,.paper-clear:hover {{ background:#eef5fa; }} .paper-toggle.selected {{ background:#e8f2f8; border-color:var(--blue); font-weight:700; }} .paper-toggle:focus-visible,.paper-order-controls button:focus-visible,.paper-clear:focus-visible {{ outline:2px solid var(--blue); outline-offset:2px; }} .paper-toggle:disabled,.paper-order-controls button:disabled,.paper-clear:disabled {{ cursor:not-allowed; opacity:.5; }}
.source {{ display:block; color:var(--blue); font-size:12px; margin:0 18px 18px; text-decoration:none; }} .source:hover {{ text-decoration:underline; }}
.tool-card {{ display:flex; align-items:center; justify-content:center; min-height:180px; padding:24px; color:var(--blue); background:#eef5fa; border-bottom:1px solid var(--line); font-size:21px; font-weight:700; text-align:center; }} .tool-card span {{ display:block; color:var(--muted); font-size:13px; font-weight:400; margin-top:5px; }}
.paper-figures-intro {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:20px 22px; margin-bottom:22px; box-shadow:0 2px 7px rgba(23,32,42,.04); }} .paper-figures-intro h2 {{ margin:0 0 4px; font-size:21px; }} .paper-figures-intro p {{ color:var(--muted); font-size:14px; margin:0; max-width:880px; }} .paper-figure-summary {{ display:flex; align-items:center; justify-content:space-between; gap:12px; margin-top:16px; color:var(--muted); font-size:12px; }} .paper-figure-summary strong {{ color:var(--blue); font-size:20px; margin-right:4px; }} .paper-figure-empty {{ background:var(--card); border:1px dashed #b9c8d3; border-radius:12px; color:var(--muted); padding:32px 22px; text-align:center; }} .paper-figure-grid {{ display:grid; grid-template-columns:1fr; gap:22px; align-items:start; }} .paper-preview-card {{ width:100%; }} .paper-order {{ color:var(--muted); font-size:12px; font-weight:700; }} .paper-order-controls {{ display:flex; gap:6px; }}
{overview_css}
footer {{ color:var(--muted); font-size:12px; border-top:1px solid var(--line); margin-top:34px; padding-top:16px; }}
@media (max-width:600px) {{ .wrap {{ padding:24px 14px 44px; }} h1 {{ font-size:25px; }} .grid {{ grid-template-columns:1fr; }} .tab {{ padding-left:9px; padding-right:9px; }} }}
</style></head><body><main class="wrap">
<header><div class="eyebrow">Multicultural Riddles Benchmark</div><h1>Analysis report</h1><p class="intro">Corpus structure, riddle-writing process, model exact-match results, and evaluation evidence. Each card pairs a figure with its caption and a short reading guide. Generated {generated}.</p></header>
<nav class="tabs" aria-label="Analysis sections">{tabs}</nav>{panes}
<footer>Source figures live in <code>analysis/figures/</code>; publication tables are generated from <code>analysis/tables/</code>. Figure ownership and the reproducibility map are documented in <code>analysis/AGENTS.md</code>.</footer>
</main><script>
document.querySelectorAll('.tab').forEach(function (button) {{ button.addEventListener('click', function () {{ document.querySelectorAll('.tab,.pane').forEach(function (element) {{ element.classList.remove('active'); }}); button.classList.add('active'); document.getElementById(button.dataset.target).classList.add('active'); window.dispatchEvent(new Event('resize')); }}); }});
if (window.mediumZoom) {{ mediumZoom('.zoomable', {{ background: '#17202a' }}); }}
{paper_figures_script}
{overview_script}
</script></body></html>"""


OVERVIEW_CSS = """.overview-intro {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:20px 22px; margin-bottom:22px; box-shadow:0 2px 7px rgba(23,32,42,.04); }}
.overview-intro h2 {{ margin:0 0 4px; font-size:21px; }} .overview-intro p {{ color:var(--muted); font-size:14px; margin:0; max-width:880px; }}
.overview-stats {{ display:flex; flex-wrap:wrap; gap:8px 22px; margin-top:16px; color:var(--muted); font-size:12px; }} .overview-stats strong {{ color:var(--blue); font-size:20px; margin-right:4px; }}
.overview-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:22px; align-items:start; }} .overview-panel {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:18px 18px 14px; box-shadow:0 2px 7px rgba(23,32,42,.04); min-width:0; }} .overview-wide {{ grid-column:1 / -1; }}
.progress-grid {{ margin-bottom:22px; }} .progress-grid .overview-panel h2 {{ margin:0; font-size:21px; }}
.overview-panel h3 {{ margin:0; font-size:17px; }} .overview-chart {{ min-height:320px; width:100%; }} .overview-caption {{ color:var(--muted); font-size:12px; margin:0 2px 2px; }}
.overview-table {{ overflow-x:auto; margin-top:10px; }} .overview-table table {{ border-collapse:collapse; font-size:12px; min-width:720px; width:100%; }} .overview-table th,.overview-table td {{ border-bottom:1px solid var(--line); padding:7px 9px; text-align:left; white-space:nowrap; }} .overview-table th {{ color:var(--muted); font-weight:700; }} .status {{ border-radius:999px; display:inline-block; font-size:11px; padding:2px 7px; }} .status-complete {{ background:#e3f1e8; color:#27603a; }} .status-partial {{ background:#fff2d8; color:#7b5b18; }} .status-thin,.status-not_started {{ background:#f9e4e1; color:#8b3427; }}
.paper-table-grid {{ display:grid; gap:22px; }} .paper-table-panel {{ background:var(--card); border:1px solid var(--line); border-radius:12px; padding:18px 18px 14px; box-shadow:0 2px 7px rgba(23,32,42,.04); min-width:0; }} .paper-table-panel h3 {{ margin:0; font-size:17px; }} .paper-table-wrap {{ overflow-x:auto; margin-top:12px; }} .paper-table {{ border-collapse:collapse; font-size:12px; min-width:760px; width:100%; }} .paper-table th,.paper-table td {{ border-bottom:1px solid var(--line); padding:7px 9px; text-align:left; white-space:nowrap; }} .paper-table th {{ background:#f7f9fb; color:var(--muted); font-weight:700; }} .paper-table tbody tr:last-child {{ font-weight:700; background:#fbfcfd; }}
@media (max-width:800px) {{ .overview-grid {{ grid-template-columns:1fr; }} .overview-wide {{ grid-column:auto; }} }}"""


if __name__ == "__main__":
    main()
