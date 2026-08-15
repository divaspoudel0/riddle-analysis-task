"""Build a self-contained static dashboard from Henry's flat file.

Self-contained: precomputes every metric from the flat file and bakes the
numbers into a single index.html with Plotly from CDN (free HuggingFace Static
Space — no server, no Streamlit).

This is the human-evaluation layer of the benchmark: the *ceiling* (what models
actually get right when a person judges) that complements the team's full-corpus
heuristic *floor*. Views: floor->ceiling leaderboard, community difficulty,
how-models-fail error types, judge-vs-human agreement, coverage.

Refresh: drop a newer data/model_riddle_results_flat.csv, rerun this script,
upload index.html to the Space. Metrics match the model_results_v0 pipeline.

    python build_static.py
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

DATA = Path(__file__).parent / "data"
FLAT = DATA / "model_riddle_results_flat.csv"
AUTO = DATA / "results_tidy.parquet"          # heuristic-judge output (static)
STATS = DATA / "human_eval_stats.xlsx"        # Henry's official completion stats
OUT = Path(__file__).parent / "index.html"    # repo root: HF Static Space entry

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


def load():
    """Read Henry's flat file + join the heuristic verdict. Single source of truth."""
    h = pd.read_csv(FLAT, low_memory=False)
    h = h[~h["riddle_id"].isin(EXCLUDED_RIDDLES)].copy()
    h["model_display"] = h["model_name"].map(MODEL_NAME_MAP)
    unmapped = sorted(h.loc[h["model_display"].isna(), "model_name"].dropna().unique())
    if unmapped:
        raise SystemExit(f"Unmapped model_name(s) {unmapped}; update MODEL_NAME_MAP.")
    auto = pd.read_parquet(AUTO)[["riddle_id", "model_display", "judge_verdict"]]
    h["is_human"] = h["scoring_method"].eq("human_eval")
    h["is_pending"] = h["scoring_method"].eq("pending_human_eval")
    h["is_correct"] = h["score"].eq(STRICT_SCORE)
    h["is_correct_lenient"] = h["score"].ge(LENIENT_SCORE)
    m = h.merge(auto, on=["riddle_id", "model_display"], how="left")
    mtime = datetime.fromtimestamp(FLAT.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
    return m, mtime


def henry_completion() -> pd.Series:
    """Official main-sheet completion % per community, from Henry's stats file.

    'main_pct_complete' = the community's main human evaluation, which excludes
    the separate 'extras' answer sheets (still ongoing). This is the number the
    analysis team sees; a community is complete at 100%.
    """
    hn = pd.read_excel(STATS, sheet_name="completion_by_community")
    hn = hn[~hn["community"].astype(str).str.contains("副本")]  # drop stray 'copy' row
    return hn.set_index("community")["main_pct_complete"]


def coverage(h: pd.DataFrame) -> pd.DataFrame:
    g = h.groupby("community")
    cov = pd.DataFrame({
        "human_done": g["is_human"].sum().astype(int),
        "pending": g["is_pending"].sum().astype(int),  # = un-validated extras
    })
    cov["human_eligible"] = cov["human_done"] + cov["pending"]
    # Authoritative completion = Henry's main-sheet %, not the flat-file ratio.
    cov["pct_complete"] = cov.index.map(henry_completion()).round(1)

    def status(pct):
        if pd.isna(pct) or pct == 0:
            return "not_started"
        if pct >= 99.5:
            return "complete"
        if pct < THIN_THRESHOLD * 100:
            return "thin"
        return "partial"

    cov["status"] = cov["pct_complete"].map(status)
    return cov.sort_values("pct_complete", ascending=False)


def leaderboard(m: pd.DataFrame, communities: set, strict: bool) -> pd.DataFrame:
    """Floor (heuristic) vs ceiling (human) on complete communities.

    Ceiling uses the flat-file score for every row, pending dropped (never
    filled). Floor is the heuristic judge on the very same rows.
    """
    col = "is_correct" if strict else "is_correct_lenient"
    sub = m[m["community"].isin(communities) & ~m["is_pending"]]
    ceil = sub.groupby("model_display")[col].mean().mul(100)
    floor = (sub.assign(auto=sub["judge_verdict"].eq("correct"))
             .groupby("model_display")["auto"].mean().mul(100))
    n = sub.groupby("model_display").size()
    human_share = sub.groupby("model_display")["is_human"].mean().mul(100)
    lb = pd.DataFrame({
        "Human (ceiling) %": ceil, "Heuristic (floor) %": floor,
        "n": n, "human-scored %": human_share.round(0),
    }).sort_values("Human (ceiling) %", ascending=False)
    lb.insert(0, "rank", range(1, len(lb) + 1))
    return lb.round(1)


def community_difficulty(m: pd.DataFrame, communities: set, strict: bool) -> pd.DataFrame:
    """Mean accuracy across all models per community (how hard each culture is)."""
    col = "is_correct" if strict else "is_correct_lenient"
    sub = m[m["community"].isin(communities) & ~m["is_pending"]]
    human = sub.groupby("community")[col].mean().mul(100)
    floor = (sub.assign(a=sub["judge_verdict"].eq("correct"))
             .groupby("community")["a"].mean().mul(100))
    return pd.DataFrame({"Human %": human, "Heuristic %": floor}).sort_values("Human %").round(1)


def community_kappa(m: pd.DataFrame, communities: set) -> tuple:
    """Cohen's kappa between heuristic judge and human, per community."""
    r = m[m["is_human"] & m["community"].isin(communities) & m["judge_verdict"].notna()].copy()
    r["h"] = r["score"].eq(STRICT_SCORE)
    r["j"] = r["judge_verdict"].eq("correct")

    def kappa(x):
        po = (x["h"] == x["j"]).mean()
        ph, pj = x["h"].mean(), x["j"].mean()
        pe = ph * pj + (1 - ph) * (1 - pj)
        return float("nan") if pe == 1 else (po - pe) / (1 - pe)

    per = r.groupby("community").apply(kappa).rename("kappa").sort_values()
    overall = kappa(r)
    misses = int((~r["j"] & r["h"]).sum())        # human-correct the judge missed
    overcredit = int((r["j"] & ~r["h"]).sum())     # judge-correct humans rejected
    return per.round(3), overall, misses, overcredit, len(r)

# ordered failure/outcome buckets + colours (how models fail, from human eval)
FAIL_ORDER = ["Correct", "Partially correct", "Explicit uncertainty",
              "Wrong entity", "Too broad", "Hallucinated", "Other incorrect"]
FAIL_COLORS = {
    "Correct": "#1a9e76", "Partially correct": "#8fcfb8",
    "Explicit uncertainty": "#4c9be8", "Wrong entity": "#e79a3c",
    "Too broad": "#efc84a", "Hallucinated": "#d1552f",
    "Other incorrect": "#a7adb5",
}


def records(df, index_name):
    df = df.reset_index().rename(columns={df.index.name or "index": index_name})
    return json.loads(df.to_json(orient="records"))


def fail_modes(m, communities: set):
    """Per-model outcome/error-type breakdown (%), human-scored rows only."""
    r = m[m["is_human"] & m["community"].isin(communities)].copy()

    def bucket(row):
        s, lab = row["score"], str(row.get("error_type_label") or "")
        if s == 3:
            return "Correct"
        if s == 2:
            return "Partially correct"
        if s == 1:
            return "Explicit uncertainty"
        if lab.startswith("0.3"):
            return "Hallucinated"
        if lab.startswith("0.1"):
            return "Too broad"
        if lab.startswith("0.2"):
            return "Wrong entity"
        return "Other incorrect"

    r["bucket"] = r.apply(bucket, axis=1)
    import pandas as pd
    piv = (pd.crosstab(r["model_display"], r["bucket"], normalize="index")
             .mul(100).round(1))
    for c in FAIL_ORDER:
        if c not in piv.columns:
            piv[c] = 0.0
    piv = piv[FAIL_ORDER].sort_values("Correct", ascending=False)
    return records(piv, "model")


TOKEN2COUNTRY = {
    "egypt": "Egypt", "morocco": "Morocco", "sudan": "Sudan", "syria": "Syria",
    "belarus": "Belarus", "bangladesh": "Bangladesh", "india": "India",
    "portuguese": "Brazil", "indonesia": "Indonesia", "bulgaria": "Bulgaria",
    "china": "China", "netherlands": "Netherlands", "canada": "Canada",
    "usa": "United States", "france": "France", "germany": "Germany",
    "hungary": "Hungary", "italy": "Italy", "uganda": "Uganda", "nepal": "Nepal",
    "iran": "Iran", "poland": "Poland", "portugal": "Portugal", "russia": "Russia",
    "serbia": "Serbia", "lanka": "Sri Lanka", "argentina": "Argentina",
    "cuba": "Cuba", "peru": "Peru", "kenya": "Kenya", "thailand": "Thailand",
    "pakistan": "Pakistan", "uzbekistan": "Uzbekistan", "nigeria": "Nigeria",
}
COUNTRY2REGION = {
    "United States": "North America", "Canada": "North America",
    "Argentina": "Latin America", "Cuba": "Latin America", "Peru": "Latin America",
    "Brazil": "Latin America",
    "Belarus": "Europe", "Bulgaria": "Europe", "Netherlands": "Europe",
    "France": "Europe", "Germany": "Europe", "Hungary": "Europe", "Italy": "Europe",
    "Poland": "Europe", "Portugal": "Europe", "Russia": "Europe", "Serbia": "Europe",
    "Egypt": "North Africa", "Morocco": "North Africa", "Sudan": "North Africa",
    "Uganda": "Sub-Saharan Africa", "Kenya": "Sub-Saharan Africa",
    "Nigeria": "Sub-Saharan Africa",
    "Syria": "West Asia", "Iran": "West Asia", "Uzbekistan": "Central Asia",
    "Bangladesh": "South Asia", "India": "South Asia", "Nepal": "South Asia",
    "Sri Lanka": "South Asia", "Pakistan": "South Asia",
    "China": "East Asia", "Indonesia": "Southeast Asia", "Thailand": "Southeast Asia",
}
HIGHLIGHT_MODELS = ["gemini-3.1-pro-preview", "GPT5.5 [high]",
                    "claude-opus-4-7 [thinking]", "deepseek-v4-pro", "Qwen/Qwen3.5-0.8B"]


def country_of(community):
    return TOKEN2COUNTRY.get(community.rsplit("_", 1)[-1])


def region_of(community):
    c = country_of(community)
    return COUNTRY2REGION.get(c) if c else None


def new_charts(m, complete):
    """Data for the exploratory chart set (region box, bubble, rank-flow, map, ridgeline)."""
    sub = m[m["community"].isin(complete) & ~m["is_pending"]]
    acc = sub.groupby(["model_display", "community"])["is_correct"].mean().mul(100).unstack()  # model x community

    fm = pd.DataFrame(fail_modes(m, complete)).set_index("model")
    bubble = [{"model": i, "accuracy": float(fm.loc[i, "Correct"]),
               "hallucination": float(fm.loc[i, "Hallucinated"])} for i in fm.index]

    lb = leaderboard(m, complete, True)  # sorted by ceiling desc
    floor_rank = {mdl: r + 1 for r, mdl in enumerate(lb.sort_values("Heuristic (floor) %", ascending=False).index)}
    rankflow = [{"model": mdl, "floor": float(lb.loc[mdl, "Heuristic (floor) %"]),
                 "ceiling": float(lb.loc[mdl, "Human (ceiling) %"]),
                 "floor_rank": floor_rank[mdl], "ceil_rank": r + 1}
                for r, mdl in enumerate(lb.index)]

    reg = {}
    for c in acc.columns:
        rg = region_of(c)
        if rg:
            reg.setdefault(rg, []).append(c)
    region_box = {}
    for rg, comms in reg.items():
        means = acc[comms].mean(axis=1)
        region_box[rg] = {
            "all": [round(float(v), 1) for v in means.dropna().values],
            "hi": {mdl: round(float(means[mdl]), 1) for mdl in HIGHLIGHT_MODELS
                   if mdl in means.index and pd.notna(means[mdl])},
            "n_cultures": len(comms)}

    ridge = {mdl: [round(float(v), 1) for v in acc.loc[mdl].dropna().values]
             for mdl in lb.index}

    chor = {}
    for c in acc.columns:
        co = country_of(c)
        if co:
            chor.setdefault(co, []).append(float(acc[c].mean()))
    choropleth = [{"country": co, "accuracy": round(sum(v) / len(v), 1), "n": len(v)}
                  for co, v in chor.items()]

    return {"bubble": bubble, "rankflow": rankflow, "region_box": region_box,
            "ridge": ridge, "choropleth": choropleth, "highlights": HIGHLIGHT_MODELS,
            "region_order": ["North America", "Latin America", "Europe", "North Africa",
                             "Sub-Saharan Africa", "West Asia", "Central Asia",
                             "South Asia", "East Asia", "Southeast Asia"]}


def main() -> None:
    m, mtime = load()
    cov = coverage(m.drop_duplicates(["community", "riddle_id", "model_display"]))
    complete = set(cov[cov.status == "complete"].index)

    data = {
        "meta": {
            "mtime": mtime, "complete": len(complete), "total": TOTAL_COMMUNITIES,
            "models": int(m["model_display"].nunique()),
            "human_rows": int(m["is_human"].sum()), "pending": int(m["is_pending"].sum()),
        },
        "leaderboard": {}, "difficulty": {},
        "fail_order": FAIL_ORDER, "fail_colors": FAIL_COLORS,
    }
    for tag, strict in [("strict", True), ("lenient", False)]:
        data["leaderboard"][tag] = records(leaderboard(m, complete, strict), "model")
        data["difficulty"][tag] = records(community_difficulty(m, complete, strict), "community")

    per, overall, misses, overcredit, n = community_kappa(m, complete)
    data["kappa"] = {"overall": round(overall, 3), "misses": misses,
                     "overcredit": overcredit, "n": n,
                     "per": records(per.to_frame("kappa"), "community")}
    data["failmodes"] = fail_modes(m, complete)
    data["charts"] = new_charts(m, complete)
    data["coverage"] = records(
        cov[["status", "pct_complete", "human_done", "pending", "human_eligible"]],
        "community")

    OUT.write_text(HTML.replace("__DATA__", json.dumps(data)), encoding="utf-8")
    print(f"Wrote {OUT}  (complete {len(complete)}/{TOTAL_COMMUNITIES}, "
          f"kappa {overall:.3f})")


HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Multicultural Riddles Benchmark</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
 :root{
   --ceil:#2f6f9f; --floor:#b8bfc7; --ink:#14181f; --mut:#5b6673; --line:#e7eaee;
   --bg:#fbfcfd; --card:#ffffff; --accent:#2f6f9f;
   --font:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
 }
 *{box-sizing:border-box}
 body{font-family:var(--font);color:var(--ink);background:var(--bg);margin:0;
   line-height:1.5;-webkit-font-smoothing:antialiased}
 .wrap{max-width:1080px;margin:0 auto;padding:32px 24px 56px}
 header{border-bottom:1px solid var(--line);padding-bottom:18px;margin-bottom:22px}
 h1{font-size:24px;font-weight:700;letter-spacing:-.01em;margin:0 0 6px}
 .sub{color:var(--mut);font-size:13.5px;max-width:760px}
 .pill{display:inline-block;background:#eaf2f8;color:#245b82;font-size:12px;
   font-weight:600;padding:3px 10px;border-radius:999px;margin-bottom:10px}
 .cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px;margin:20px 0}
 .card{background:var(--card);border:1px solid var(--line);border-radius:12px;
   padding:14px 16px;box-shadow:0 1px 2px rgba(20,24,31,.03)}
 .card .v{font-size:24px;font-weight:700;letter-spacing:-.02em}
 .card .l{color:var(--mut);font-size:12px;margin-top:2px}
 .tabs{display:flex;gap:4px;flex-wrap:wrap;border-bottom:1px solid var(--line);margin:8px 0 6px}
 .tab{padding:9px 14px;cursor:pointer;border:none;background:none;font-size:14px;
   font-weight:500;color:var(--mut);border-bottom:2px solid transparent;margin-bottom:-1px}
 .tab:hover{color:var(--ink)}
 .tab.on{color:var(--accent);border-bottom-color:var(--accent);font-weight:600}
 .toggle{display:flex;gap:6px;margin:16px 0 4px}
 .toggle button{border:1px solid var(--line);background:var(--card);color:var(--mut);
   font-size:13px;padding:6px 12px;border-radius:8px;cursor:pointer;font-family:var(--font)}
 .toggle button.on{background:var(--accent);border-color:var(--accent);color:#fff;font-weight:600}
 .pane{display:none;padding-top:10px} .pane.on{display:block}
 .h2{font-size:16px;font-weight:600;margin:6px 0 2px}
 .cap{color:var(--mut);font-size:12.5px;margin:8px 0 4px}
 .dl{display:inline-block;margin-top:10px;font-size:12.5px;color:var(--accent);
   border:1px solid var(--line);border-radius:8px;padding:5px 11px;text-decoration:none;cursor:pointer}
 table{border-collapse:collapse;width:100%;font-size:13px;margin-top:12px}
 th,td{border-bottom:1px solid var(--line);padding:7px 9px;text-align:left}
 th{color:var(--mut);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.03em}
 tr:hover td{background:#f7f9fb}
 .badge{padding:2px 9px;border-radius:999px;font-size:11.5px;font-weight:600}
 .complete{background:#e3f4e8;color:#1c7a3f}.partial{background:#fdf3e0;color:#9a6a12}
 .thin{background:#fdeaea;color:#b23}.not_started{background:#eef0f2;color:#697}
 .note{background:#f4f8fb;border:1px solid #dde8f1;border-radius:10px;padding:12px 14px;
   font-size:13px;color:#2c4a63;margin-top:12px}
 .foot{color:var(--mut);font-size:12px;margin-top:26px;padding-top:16px;
   border-top:1px solid var(--line);line-height:1.6}
</style></head><body><div class="wrap">
<header>
 <div class="pill">Human evaluation · provisional</div>
 <h1>🧩 Multicultural Riddles Benchmark</h1>
 <div class="sub" id="sub"></div>
</header>
<div class="cards" id="cards"></div>
<div class="tabs" id="tabs"></div>

<div id="lb" class="pane on">
 <div class="h2">Heuristic floor → human ceiling</div>
 <div class="toggle" id="toggle">
  <button data-sc="strict" class="on">Strict (correct = top score)</button>
  <button data-sc="lenient">Lenient (score ≥ 2)</button>
 </div>
 <div id="lbchart"></div>
 <div class="cap">Grey = automatic heuristic judge (lower bound). Blue = human judgement (upper bound). The gap is the lift from strict string-matching to human scoring.</div>
 <div id="lbtable"></div>
 <a class="dl" id="lbdl">Download leaderboard (CSV)</a>
</div>

<div id="fail" class="pane">
 <div class="h2">How models fail (human error types)</div>
 <div id="failchart"></div>
 <div class="cap" id="failcap"></div>
</div>

<div id="diff" class="pane">
 <div class="h2">How hard is each culture?</div>
 <div id="diffchart"></div>
 <div class="cap" id="diffcap"></div>
</div>

<div id="kappa" class="pane">
 <div class="h2">Does the auto-judge agree with humans?</div>
 <div class="cards" id="kcards"></div>
 <div id="kchart"></div>
 <div class="cap" id="kcap"></div>
</div>

<div id="cov" class="pane">
 <div class="h2">Human-eval coverage by community</div>
 <div id="covtable"></div>
 <div class="note" id="covnote"></div>
</div>

<div id="region" class="pane">
 <div class="h2">Model performance by region</div>
 <div id="regionchart"></div>
 <div class="cap" id="regioncap"></div>
</div>

<div id="calib" class="pane">
 <div class="h2">Calibration: accuracy vs hallucination</div>
 <div id="calibchart"></div>
 <div class="cap" id="calibcap"></div>
</div>

<div id="map" class="pane">
 <div class="h2">Human-eval accuracy by country</div>
 <div id="mapchart"></div>
 <div class="cap" id="mapcap"></div>
</div>

<div id="ridge" class="pane">
 <div class="h2">Distribution of per-culture accuracy (ridgeline)</div>
 <div id="ridgechart"></div>
 <div class="cap" id="ridgecap"></div>
</div>

<div id="insights" class="pane">
 <div class="h2">Key findings (provisional, 38/44 cultures)</div>
 <div class="note" style="line-height:1.75">
  <p style="margin:.2em 0"><b>1. Human-curated riddles remain hard for frontier models.</b> Under human evaluation the strongest model reaches only <b>80.1%</b> (Gemini 3.1 Pro), then GPT-5.5 (77.6%) and GPT-5.5 high (76.0%); the mean across all 24 models is 36.9%.</p>
  <p style="margin:.2em 0"><b>2. Exact-match scoring understates ability, most for the best models.</b> Human judging lifts every model above its heuristic score (Gemini 65.7% to 80.1%); overall the heuristic misses <b>50.2%</b> of the answers humans accept as correct.</p>
  <p style="margin:.2em 0"><b>3. When models fail, they fabricate rather than abstain.</b> Hallucination is the dominant error mode and grows as models weaken (from 5.4% for the strongest to 69.9% for the smallest); models almost never admit uncertainty (0.19% on average).</p>
  <p style="margin:.2em 0"><b>4. Difficulty varies enormously across cultures.</b> Mean accuracy ranges from 68.4% (English-US) to 5.2% (Mongondow, Indonesia); even top models collapse on the hardest cultures.</p>
  <p style="margin:.2em 0"><b>5. The auto-judge only moderately tracks humans.</b> Cohen's &kappa; = 0.56 overall, below 0.4 on non-Latin scripts (Cantonese, Serbian, Marathi, Telugu), so exact-match is a lower bound and human evaluation matters.</p>
  <p style="margin:.6em 0 0;color:var(--mut)"><b>Scope:</b> 24 models on v0; 38 of 44 communities with complete MAIN human evaluation. Provisional; every number validated against the official stats file.</p>
 </div>
</div>

<div class="foot" id="foot"></div>
</div>
<script>
const D=__DATA__;
const CEIL="#2f6f9f",FLOOR="#b8bfc7";
let SC="strict";

document.getElementById('sub').textContent=`Live from the human-eval flat file (updated ${D.meta.mtime}). Every score traces to the flat file — pending rows are dropped, never guessed. This is the human ceiling that complements the team's full-corpus heuristic floor. Provisional; numbers shift as coverage completes.`;
const cards=[['Communities complete',`${D.meta.complete} / ${D.meta.total}`],['Models',D.meta.models],['Human-scored rows',D.meta.human_rows.toLocaleString()],['Pending',D.meta.pending.toLocaleString()]];
document.getElementById('cards').innerHTML=cards.map(c=>`<div class="card"><div class="v">${c[1]}</div><div class="l">${c[0]}</div></div>`).join('');

const TABS=[['insights','📌 Key findings'],['lb','🏆 Leaderboard'],['fail','🔍 How models fail'],['region','🗺️ By region'],['calib','🎯 Calibration'],['map','🌐 Map'],['ridge','⛰️ Ridgeline'],['diff','🌍 Community difficulty'],['kappa','🤝 Judge vs human'],['cov','📊 Coverage']];
document.getElementById('tabs').innerHTML=TABS.map((t,i)=>`<button class="tab${i==0?' on':''}" data-p="${t[0]}">${t[1]}</button>`).join('');
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{
 document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));b.classList.add('on');
 document.querySelectorAll('.pane').forEach(p=>p.classList.remove('on'));
 document.getElementById(b.dataset.p).classList.add('on');window.dispatchEvent(new Event('resize'));});

const L={margin:{l:10,r:16,t:8,b:44},plot_bgcolor:'#fff',paper_bgcolor:'#fff',
 font:{family:'-apple-system,Segoe UI,Roboto,sans-serif',size:12,color:'#14181f'},
 xaxis:{gridcolor:'#eef0f2',zeroline:false},yaxis:{automargin:true}};

function dumbbell(el,rows,keyF,keyC,label,xlab){
 const y=rows.map(label);
 const segs=rows.map((r,i)=>({x:[r[keyF],r[keyC]],y:[y[i],y[i]],mode:'lines',line:{color:'#dfe3e8',width:3},showlegend:false,hoverinfo:'skip',type:'scatter'}));
 const f={x:rows.map(r=>r[keyF]),y,mode:'markers',type:'scatter',name:'Heuristic (floor)',marker:{color:FLOOR,size:10,line:{color:'#9aa0a6',width:1}}};
 const c={x:rows.map(r=>r[keyC]),y,mode:'markers',type:'scatter',name:'Human (ceiling)',marker:{color:CEIL,size:10}};
 Plotly.newPlot(el,[...segs,f,c],{...L,height:Math.max(400,27*rows.length),xaxis:{...L.xaxis,title:xlab,range:[0,100]},legend:{orientation:'h',y:1.07}},{displayModeBar:false,responsive:true});
}
function renderLB(){
 const lb=D.leaderboard[SC];
 dumbbell('lbchart',[...lb].sort((a,b)=>a['Human (ceiling) %']-b['Human (ceiling) %']),'Heuristic (floor) %','Human (ceiling) %',r=>r.model,`Accuracy (%), ${SC}`);
 document.getElementById('lbtable').innerHTML='<table><tr><th>#</th><th>Model</th><th>Human %</th><th>Heuristic %</th><th>human-judged %</th><th>n</th></tr>'+lb.map(r=>`<tr><td>${r.rank}</td><td>${r.model}</td><td><b>${r['Human (ceiling) %']}</b></td><td>${r['Heuristic (floor) %']}</td><td>${r['human-scored %']}</td><td>${r.n}</td></tr>`).join('')+'</table>';
 const d=D.difficulty[SC];
 dumbbell('diffchart',d,'Heuristic %','Human %',r=>r.community,`Mean accuracy across models (%), ${SC}`);
 document.getElementById('diffcap').textContent=`Mean accuracy across all ${D.meta.models} models per community. Hardest: ${d.slice(0,3).map(r=>r.community).join(', ')}. Easiest: ${d.slice(-3).map(r=>r.community).join(', ')}. Grey = heuristic floor, blue = human ceiling.`;
}
document.querySelectorAll('.toggle button').forEach(b=>b.onclick=()=>{
 document.querySelectorAll('.toggle button').forEach(x=>x.classList.remove('on'));b.classList.add('on');
 SC=b.dataset.sc;renderLB();});
renderLB();

// how models fail — stacked horizontal bars, models ordered by Correct desc
(function(){
 const rows=[...D.failmodes].reverse();  // plotly draws bottom-up
 const y=rows.map(r=>r.model);
 const traces=D.fail_order.map(cat=>({
   x:rows.map(r=>r[cat]||0),y,name:cat,type:'bar',orientation:'h',
   marker:{color:D.fail_colors[cat]},
   hovertemplate:'%{y}<br>'+cat+': %{x:.1f}%<extra></extra>'}));
 Plotly.newPlot('failchart',traces,{...L,barmode:'stack',height:Math.max(440,28*rows.length),
   xaxis:{...L.xaxis,title:'Share of human-scored responses (%)',range:[0,100]},
   legend:{orientation:'h',y:1.06,font:{size:11}}},{displayModeBar:false,responsive:true});
 const top=D.failmodes[0],bot=D.failmodes[D.failmodes.length-1];
 document.getElementById('failcap').innerHTML=`How each model's answers break down when a human judges them. <b>Hallucination (red) is the dominant failure mode and grows as capability drops</b> — from ${top.Hallucinated}% (${top.model}) to ${bot.Hallucinated}% (${bot.model}). Models almost never admit uncertainty (blue, ≤1%) — they produce a confident wrong answer instead. "Wrong entity" = right category, wrong specific answer; "too broad" = a more general answer.`;
})();

// kappa
const k=D.kappa;
document.getElementById('kcards').innerHTML=[["Overall Cohen's κ",k.overall],['Human-correct the judge missed',k.misses.toLocaleString()],['Judge over-credits',k.overcredit.toLocaleString()]].map(c=>`<div class="card"><div class="v">${c[1]}</div><div class="l">${c[0]}</div></div>`).join('');
const kp=[...k.per];
Plotly.newPlot('kchart',[{x:kp.map(r=>r.kappa),y:kp.map(r=>r.community),type:'bar',orientation:'h',marker:{color:kp.map(r=>r.kappa<0.4?'#d1552f':CEIL)},hovertemplate:'%{y}<br>κ %{x:.3f}<extra></extra>'}],{...L,height:Math.max(420,26*kp.length),xaxis:{...L.xaxis,title:"Cohen's κ (judge vs human)"},shapes:[{type:'line',x0:k.overall,x1:k.overall,y0:-0.5,y1:kp.length-0.5,line:{color:'#5b6673',dash:'dash',width:1.4}}]},{displayModeBar:false,responsive:true});
document.getElementById('kcap').innerHTML=`Two raters = the automatic judge and the human (not two humans — we have one annotator per riddle). On ${k.n.toLocaleString()} doubly-labelled rows. Red κ&lt;0.4 = string-matching unreliable (non-Latin scripts). Dashed line = overall κ ${k.overall}. The judge misses far more correct answers (${k.misses.toLocaleString()}) than it over-credits (${k.overcredit.toLocaleString()}).`;

// coverage
const ord={complete:0,partial:1,thin:2,not_started:3};
const cv=[...D.coverage].sort((a,b)=>ord[a.status]-ord[b.status]||b.pct_complete-a.pct_complete);
document.getElementById('covtable').innerHTML='<table><tr><th>Community</th><th>Status</th><th>% complete</th><th>human</th><th>pending</th><th>eligible</th></tr>'+cv.map(r=>`<tr><td>${r.community}</td><td><span class="badge ${r.status}">${r.status.replace('_',' ')}</span></td><td>${r.pct_complete??''}</td><td>${r.human_done}</td><td>${r.pending}</td><td>${r.human_eligible}</td></tr>`).join('')+'</table>';
const chase=cv.filter(r=>r.status=='not_started'||r.status=='thin').map(r=>r.community);
document.getElementById('covnote').textContent=chase.length?('Chase list (not started / thin): '+chase.join(', ')):'All started.';

// leaderboard CSV download
document.getElementById('lbdl').onclick=()=>{
 const lb=D.leaderboard[SC],cols=['rank','model','Human (ceiling) %','Heuristic (floor) %','human-scored %','n'];
 const csv=[cols.join(',')].concat(lb.map(r=>cols.map(c=>r[c]).join(','))).join('\n');
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));
 a.download='human_leaderboard_'+SC+'.csv';a.click();};

// ---------- exploratory charts ----------
const HICOL={'gemini-3.1-pro-preview':'#c0392b','GPT5.5 [high]':'#e69f00','claude-opus-4-7 [thinking]':'#2e8b57','deepseek-v4-pro':'#5b2c9f','Qwen/Qwen3.5-0.8B':'#8a5a44'};
const HIMK={'gemini-3.1-pro-preview':'cross','GPT5.5 [high]':'diamond','claude-opus-4-7 [thinking]':'triangle-up','deepseek-v4-pro':'triangle-down','Qwen/Qwen3.5-0.8B':'star'};
(function(){ // region box + markers
 const C=D.charts, regs=C.region_order.filter(r=>C.region_box[r]);
 const bx=[],by=[]; regs.forEach(r=>C.region_box[r].all.forEach(v=>{bx.push(r);by.push(v);}));
 const traces=[{type:'box',x:bx,y:by,name:'all models',boxpoints:false,marker:{color:'#aab4c0'},fillcolor:'#eef2f7',line:{color:'#aab4c0'},showlegend:false,hovertemplate:'%{x}<extra></extra>'}];
 C.highlights.forEach(mdl=>{const xs=[],ys=[];regs.forEach(r=>{const v=C.region_box[r].hi[mdl];if(v!=null){xs.push(r);ys.push(v);}});
   traces.push({type:'scatter',mode:'markers',name:mdl.replace(' [',' ').replace(']',''),x:xs,y:ys,marker:{symbol:HIMK[mdl]||'circle',color:HICOL[mdl]||'#333',size:12,line:{color:'white',width:1}},hovertemplate:'%{x}<br>'+mdl+': %{y:.1f}%<extra></extra>'});});
 Plotly.newPlot('regionchart',traces,{height:560,plot_bgcolor:'#fff',paper_bgcolor:'#fff',font:{family:'-apple-system,Segoe UI,Roboto,sans-serif',size:12,color:'#14181f'},margin:{l:58,r:16,t:8,b:120},yaxis:{type:'linear',title:'Human-eval accuracy (%)',range:[0,100],dtick:20,gridcolor:'#eef0f2',zeroline:false},xaxis:{type:'category',categoryorder:'array',categoryarray:regs,tickangle:-35,automargin:true},legend:{orientation:'h',y:1.13,font:{size:11}}},{responsive:true,displaylogo:false});
 document.getElementById('regioncap').textContent='Each box is the spread of all 24 models within a region (regions sorted easiest to hardest); coloured markers are five representative models. Drag to zoom, double-click to reset. Regions with no fully-evaluated cultures are omitted.';
})();
(function(){ // calibration bubble
 const b=D.charts.bubble;
 const tr={x:b.map(r=>r.accuracy),y:b.map(r=>r.hallucination),text:b.map(r=>r.model),mode:'markers+text',type:'scatter',textposition:'top center',textfont:{size:8},marker:{size:13,color:b.map(r=>r.accuracy),colorscale:'Blues',line:{color:'#5b6673',width:0.6}},hovertemplate:'%{text}<br>accuracy %{x:.1f}%<br>hallucination %{y:.1f}%<extra></extra>'};
 Plotly.newPlot('calibchart',[tr],{...L,height:520,xaxis:{...L.xaxis,title:'Accuracy (% correct, human eval)'},yaxis:{...L.yaxis,title:'Hallucination rate (%)'}},{displayModeBar:false,responsive:true});
 document.getElementById('calibcap').textContent='Each dot is a model. Strong inverse relationship: more accurate models hallucinate less. Because models rarely abstain, low accuracy shows up as more hallucination, not more admitted uncertainty.';
})();
(function(){ // map choropleth
 const c=D.charts.choropleth;
 const tr={type:'choropleth',locations:c.map(r=>r.country),locationmode:'country names',z:c.map(r=>r.accuracy),text:c.map(r=>r.country+': '+r.accuracy+'% ('+r.n+' culture(s))'),hovertemplate:'%{text}<extra></extra>',colorscale:'Blues',zmin:0,zmax:100,marker:{line:{color:'white',width:0.5}},colorbar:{title:'Accuracy %',thickness:12,len:0.7}};
 Plotly.newPlot('mapchart',[tr],{height:520,paper_bgcolor:'#fff',geo:{showframe:false,showcoastlines:false,landcolor:'#e5e7eb',showcountries:true,countrycolor:'white',projection:{type:'natural earth'}},margin:{l:0,r:0,t:0,b:0}},{displayModeBar:false,responsive:true});
 document.getElementById('mapcap').textContent='Mean human-eval accuracy per country over its fully-evaluated cultures. Grey countries are in the benchmark but not yet complete.';
})();
(function(){ // ridgeline
 const R=D.charts.ridge, models=Object.keys(R);
 const traces=models.slice().reverse().map(mdl=>({type:'violin',x:R[mdl],y0:mdl,orientation:'h',side:'positive',width:2.6,points:false,bandwidth:6,spanmode:'hard',line:{color:'#3b6fb6',width:1},fillcolor:'rgba(59,111,182,0.35)',showlegend:false,hovertemplate:mdl+': %{x:.0f}%<extra></extra>',meanline:{visible:false},box:{visible:false}}));
 Plotly.newPlot('ridgechart',traces,{height:Math.max(560,26*models.length),plot_bgcolor:'#fff',paper_bgcolor:'#fff',font:{size:11},margin:{l:175,r:20,t:8,b:44},xaxis:{title:'Per-culture accuracy (%)',range:[0,100],gridcolor:'#eef0f2',zeroline:false},yaxis:{automargin:true,type:'category'}},{responsive:true,displaylogo:false});
 document.getElementById('ridgecap').textContent="Each ridge is one model's distribution of accuracy across the "+D.meta.complete+" complete cultures (models ordered by mean). The bimodal shape - mass near 0 and near 100 - shows models tend to be near-perfect on well-represented cultures and near-zero on others.";
})();
document.getElementById('foot').innerHTML='Methodology: single human annotator per riddle (no inter-annotator agreement). Charts use the '+D.meta.complete+' of '+D.meta.total+' v0 communities whose MAIN human evaluation is complete (matching the official main_pct_complete from Henry); the separate \"extras\" answer sheets are still in progress. Scores are the human 0-3 rating where a person scored, else the automatic value; pending (extras) rows are dropped. Source of truth: model_riddle_results_flat.csv + human_eval_stats.xlsx (Henry Gagnier); per-model means match his stats exactly. Heuristic judge is reference-based string matching (no LLM). Cuba riddle spanish_cuba_history_016 excluded (redone in v2). Provisional until coverage completes.';
</script></body></html>"""


if __name__ == "__main__":
    main()
