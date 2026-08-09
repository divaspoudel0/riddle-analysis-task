"""Build a self-contained static dashboard from Henry's flat file.

Free HuggingFace Static Spaces cannot run Streamlit, so this precomputes every
metric (reusing app.py's exact functions) and bakes the numbers into a single
self-contained index.html with Plotly from CDN.

This is the human-evaluation layer of the benchmark: the *ceiling* (what models
actually get right when a person judges) that complements the team's full-corpus
heuristic *floor*. Views: floor->ceiling leaderboard, community difficulty,
how-models-fail error types, judge-vs-human agreement, coverage.

Refresh: drop a newer data/model_riddle_results_flat.csv, rerun this script,
push index.html. Numbers are identical to human_eval.py / app.py.

    python build_static.py
"""

from __future__ import annotations

import json
import sys
import types
from pathlib import Path

# stub streamlit and exec only app.py's compute half (before the UI marker),
# so we reuse the exact functions without running the Streamlit UI.
_st = types.ModuleType("streamlit")
_st.cache_data = lambda *a, **k: (lambda f: f)
sys.modules["streamlit"] = _st

_APP = Path(__file__).parent / "app.py"
_src = _APP.read_text().split("# ------------------------------- UI")[0]
app = types.ModuleType("app")
app.__file__ = str(_APP)
exec(compile(_src, str(_APP), "exec"), app.__dict__)

OUT = Path(__file__).parent / "index.html"  # repo root: HF Static Space entry

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


def main() -> None:
    m, mtime = app.load()
    cov = app.coverage(m.drop_duplicates(["community", "riddle_id", "model_display"]))
    complete = set(cov[cov.status == "complete"].index)

    data = {
        "meta": {
            "mtime": mtime, "complete": len(complete), "total": app.TOTAL_COMMUNITIES,
            "models": int(m["model_display"].nunique()),
            "human_rows": int(m["is_human"].sum()), "pending": int(m["is_pending"].sum()),
        },
        "leaderboard": {}, "difficulty": {},
        "fail_order": FAIL_ORDER, "fail_colors": FAIL_COLORS,
    }
    for tag, strict in [("strict", True), ("lenient", False)]:
        data["leaderboard"][tag] = records(app.leaderboard(m, complete, strict), "model")
        data["difficulty"][tag] = records(app.community_difficulty(m, complete, strict), "community")

    per, overall, misses, overcredit, n = app.community_kappa(m, complete)
    data["kappa"] = {"overall": round(overall, 3), "misses": misses,
                     "overcredit": overcredit, "n": n,
                     "per": records(per.to_frame("kappa"), "community")}
    data["failmodes"] = fail_modes(m, complete)
    data["coverage"] = records(
        cov[["status", "pct_complete", "human_done", "pending", "human_eligible"]],
        "community")

    OUT.write_text(HTML.replace("__DATA__", json.dumps(data)), encoding="utf-8")
    print(f"Wrote {OUT}  (complete {len(complete)}/{app.TOTAL_COMMUNITIES}, "
          f"kappa {overall:.3f})")


HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Multicultural Riddles — Human Evaluation</title>
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
 <h1>🧩 Multicultural Riddles Benchmark — Human Evaluation</h1>
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

<div class="foot" id="foot"></div>
</div>
<script>
const D=__DATA__;
const CEIL="#2f6f9f",FLOOR="#b8bfc7";
let SC="strict";

document.getElementById('sub').textContent=`Live from the human-eval flat file (updated ${D.meta.mtime}). Every score traces to the flat file — pending rows are dropped, never guessed. This is the human ceiling that complements the team's full-corpus heuristic floor. Provisional; numbers shift as coverage completes.`;
const cards=[['Communities complete',`${D.meta.complete} / ${D.meta.total}`],['Models',D.meta.models],['Human-scored rows',D.meta.human_rows.toLocaleString()],['Pending',D.meta.pending.toLocaleString()]];
document.getElementById('cards').innerHTML=cards.map(c=>`<div class="card"><div class="v">${c[1]}</div><div class="l">${c[0]}</div></div>`).join('');

const TABS=[['lb','🏆 Leaderboard'],['fail','🔍 How models fail'],['diff','🌍 Community difficulty'],['kappa','🤝 Judge vs human'],['cov','📊 Coverage']];
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

document.getElementById('foot').innerHTML='Methodology: single human annotator per riddle (no inter-annotator agreement). Leaderboard and error types restricted to communities with complete human coverage. Source of truth: model_riddle_results_flat.csv (Henry Gagnier). Heuristic judge is reference-based string matching (no LLM). Cuba riddle spanish_cuba_history_016 excluded (redone in v2). Provisional until coverage completes.';
</script></body></html>"""


if __name__ == "__main__":
    main()
