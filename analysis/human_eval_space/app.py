"""Multicultural Riddles Benchmark — human evaluation Space.

Self-contained Streamlit app for the Cohere Labs lead team. Recomputes the
coverage tracker and the floor-vs-ceiling leaderboard directly from Henry's
flat file on every load, so dropping a newer
`data/model_riddle_results_flat.csv` (and pushing it to the Space) refreshes
every number and chart with no code change.

Single source of truth for scores = the flat file. Every non-pending row
carries a score (human 0-3, or auto: exact_match=3, empty/placeholder=0,
idk=1). The leaderboard is computed on COMPLETE communities only, using those
scores for every row, with pending rows DROPPED (never judge-filled) — so
every value traces to the flat file with zero assumptions. Provisional until
coverage completes; every view is labelled N/44.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA = Path(__file__).parent / "data"
FLAT = DATA / "model_riddle_results_flat.csv"
AUTO = DATA / "results_tidy.parquet"          # our heuristic-judge output (static)

TOTAL_COMMUNITIES = 44
EXPECTED_MODELS = 24
RIDDLES_PER_COMMUNITY = 100
THIN_THRESHOLD = 0.20
STRICT_SCORE = 3.0
LENIENT_SCORE = 2.0
EXCLUDED_RIDDLES = {"spanish_cuba_history_016"}  # Cuba: wrong v0 text, redone in v2

# Henry's model_name -> our display name (verified 24/24).
MODEL_NAME_MAP = {
    "Amazon-Nova-Lite": "Amazon Nova Lite v1",
    "Amazon-Nova-Micro": "Amazon Nova Micro v1",
    "Deepseek-v4-flash": "DeepSeek V4 Flash",
    "EuroLLM-Instruct": "EuroLLM-22B-Instruct-2512",
    "GPT5.5-high": "GPT5.5 [high]",
    "GPT5.5-none": "GPT5.5 [none]",
    "Gemini-2.5-Flash": "Gemini 2.5 Flash",
    "Gemini-2.5-Flash-Lite": "Gemini 2.5 Flash Lite",
    "Mistral-Large-3": "Mistral Large 3",
    "Olmo-3-32B-Think": "OLMo-3-32B-Think",
    "Qwen-3.5-0.8B": "Qwen/Qwen3.5-0.8B",
    "Qwen-SEA-LION-v4.5-27B-IT": "Qwen-SEA-LION-v4.5-27B-IT",
    "Qwen3.5-27B": "Qwen3.5 27B",
    "claude-opus-4-7": "claude-opus-4-7 [none]",
    "claude-opus-4-7-thinking": "claude-opus-4-7 [thinking]",
    "command-a-plus-05-2026": "Cohere Command A Plus",
    "deepseek-v4-pro": "deepseek-v4-pro",
    "deepseek-v4-pro-thinking": "deepseek-v4-pro-thinking",
    "gemini-3.1-pro-preview": "gemini-3.1-pro-preview",
    "gemma-4-31b": "Gemma 4 31B IT",
    "tiny-aya-earth": "Tiny-Aya earth",
    "tiny-aya-fire": "Tiny-Aya fire",
    "tiny-aya-global": "Tiny-Aya global",
    "tiny-aya-water": "Tiny-Aya water",
}

FLOOR_COLOR = "#9aa0a6"
CEIL_COLOR = "#3b6fb6"


@st.cache_data(show_spinner="Loading Henry's flat file…")
def load():
    """Read + join once per file version; cache keyed on file mtime."""
    h = pd.read_csv(FLAT, low_memory=False)
    h = h[~h["riddle_id"].isin(EXCLUDED_RIDDLES)].copy()
    h["model_display"] = h["model_name"].map(MODEL_NAME_MAP)
    unmapped = sorted(h.loc[h["model_display"].isna(), "model_name"].dropna().unique())
    if unmapped:
        st.error(f"Unmapped model_name(s) in flat file: {unmapped}. "
                 "Numbers withheld until the name map is updated.")
        st.stop()

    auto = pd.read_parquet(AUTO)[["riddle_id", "model_display", "judge_verdict"]]
    h["is_human"] = h["scoring_method"].eq("human_eval")
    h["is_pending"] = h["scoring_method"].eq("pending_human_eval")
    h["is_correct"] = h["score"].eq(STRICT_SCORE)
    h["is_correct_lenient"] = h["score"].ge(LENIENT_SCORE)
    m = h.merge(auto, on=["riddle_id", "model_display"], how="left")
    mtime = datetime.fromtimestamp(FLAT.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    return m, mtime


def coverage(h: pd.DataFrame) -> pd.DataFrame:
    g = h.groupby("community")
    cov = pd.DataFrame({
        "human_done": g["is_human"].sum().astype(int),
        "pending": g["is_pending"].sum().astype(int),
    })
    cov["human_eligible"] = cov["human_done"] + cov["pending"]
    cov["pct_complete"] = (
        cov["human_done"] / cov["human_eligible"].where(cov["human_eligible"] > 0) * 100
    ).round(1)

    def status(r):
        if r["human_done"] == 0:
            return "not_started"
        if r["human_eligible"] == 0 or r["pct_complete"] >= 99:
            return "complete"
        if r["pct_complete"] < THIN_THRESHOLD * 100:
            return "thin"
        return "partial"

    cov["status"] = cov.apply(status, axis=1)
    return cov.sort_values(["status", "pct_complete"])


def leaderboard(m: pd.DataFrame, communities: set, strict: bool) -> pd.DataFrame:
    """Floor (heuristic) vs ceiling (human/Henry) on complete communities.

    Ceiling uses Henry's score for every row, pending dropped (never filled).
    Floor is the heuristic judge on the very same rows.
    """
    col = "is_correct" if strict else "is_correct_lenient"
    sub = m[m["community"].isin(communities) & ~m["is_pending"]]
    ceil = sub.groupby("model_display")[col].mean().mul(100)
    floor = (
        sub.assign(auto=sub["judge_verdict"].eq("correct"))
        .groupby("model_display")["auto"].mean().mul(100)
    )
    n = sub.groupby("model_display").size()
    human_share = sub.groupby("model_display")["is_human"].mean().mul(100)
    lb = pd.DataFrame({
        "Human (ceiling) %": ceil, "Heuristic (floor) %": floor,
        "n": n, "human-scored %": human_share.round(0),
    }).sort_values("Human (ceiling) %", ascending=False)
    lb.insert(0, "rank", range(1, len(lb) + 1))
    return lb.round(1)


def dumbbell(lb: pd.DataFrame, strict: bool) -> go.Figure:
    d = lb.sort_values("Human (ceiling) %")
    fig = go.Figure()
    for i, (model, r) in enumerate(d.iterrows()):
        fig.add_trace(go.Scatter(
            x=[r["Heuristic (floor) %"], r["Human (ceiling) %"]], y=[model, model],
            mode="lines", line=dict(color="#d0d3d8", width=3),
            showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=d["Heuristic (floor) %"], y=d.index, mode="markers", name="Heuristic (floor)",
        marker=dict(color=FLOOR_COLOR, size=11),
        hovertemplate="%{y}<br>heuristic %{x:.1f}%<extra></extra>"))
    fig.add_trace(go.Scatter(
        x=d["Human (ceiling) %"], y=d.index, mode="markers", name="Human (ceiling)",
        marker=dict(color=CEIL_COLOR, size=11),
        hovertemplate="%{y}<br>human %{x:.1f}%<extra></extra>"))
    lab = "strict (top score)" if strict else "lenient (score ≥ 2)"
    fig.update_layout(
        height=max(420, 26 * len(d)), margin=dict(l=10, r=10, t=10, b=40),
        xaxis_title=f"Accuracy (%), {lab}", legend=dict(orientation="h", y=1.05),
        plot_bgcolor="white", font=dict(size=13))
    fig.update_xaxes(showgrid=True, gridcolor="#eef0f2", zeroline=False)
    return fig


# ------------------------------- UI -------------------------------
st.set_page_config(page_title="Multicultural Riddles — Human Eval",
                   page_icon="🧩", layout="wide")

if not FLAT.exists():
    st.error("data/model_riddle_results_flat.csv not found in the Space.")
    st.stop()

m, mtime = load()
cov = coverage(m.drop_duplicates(["community", "riddle_id", "model_display"]))
complete = set(cov[cov.status == "complete"].index)
counts = cov.status.value_counts().to_dict()

st.title("🧩 Multicultural Riddles Benchmark — Human Evaluation")
st.caption(
    f"Provisional leaderboard, live from Henry's flat file (updated {mtime}). "
    "Every score traces to the flat file; pending rows are dropped, never "
    "guessed. Numbers can still shift as human coverage completes.")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Communities complete", f"{len(complete)} / {TOTAL_COMMUNITIES}")
c2.metric("Models", m["model_display"].nunique())
c3.metric("Human-scored rows", f"{int(m['is_human'].sum()):,}")
c4.metric("Pending", f"{int(m['is_pending'].sum()):,}")

strict = st.radio("Scoring", ["Strict (top score = 3)", "Lenient (score ≥ 2)"],
                  horizontal=True) == "Strict (top score = 3)"

if not complete:
    st.warning("No community has complete human evaluation yet.")
    st.stop()

lb = leaderboard(m, complete, strict)

tab_lb, tab_cov = st.tabs(["🏆 Leaderboard", "📊 Coverage"])

with tab_lb:
    st.subheader(f"Floor → ceiling  (N={len(complete)}/{TOTAL_COMMUNITIES} "
                 "complete communities, provisional)")
    st.plotly_chart(dumbbell(lb, strict), use_container_width=True)
    st.caption("Grey = heuristic auto-judge (lower bound). Blue = human "
               "judgement (upper bound). The gap is the lift from strict "
               "string-matching to human scoring.")
    st.dataframe(
        lb[["rank", "Human (ceiling) %", "Heuristic (floor) %",
            "human-scored %", "n"]],
        use_container_width=True)
    st.download_button("Download leaderboard (CSV)",
                       lb.to_csv().encode(), "human_leaderboard.csv")

with tab_cov:
    st.subheader("Human-eval coverage by community")
    order = {"complete": 0, "partial": 1, "thin": 2, "not_started": 3}
    view = cov.reset_index().rename(columns={"index": "community"})
    view["_o"] = view["status"].map(order)
    view = view.sort_values(["_o", "pct_complete"], ascending=[True, False])
    st.dataframe(
        view[["community", "status", "pct_complete", "human_done",
              "pending", "human_eligible"]],
        use_container_width=True, hide_index=True)
    chase = view[view.status.isin(["not_started", "thin"])]["community"].tolist()
    if chase:
        st.info("Chase list (not started / thin): " + ", ".join(chase))

st.divider()
st.caption(
    "Methodology: single human annotator per riddle (no inter-annotator "
    "agreement). Leaderboard restricted to communities with complete human "
    "coverage; other communities excluded until done. Source of truth: "
    "model_riddle_results_flat.csv (Henry). Cuba riddle "
    "spanish_cuba_history_016 excluded (redone in v2).")
