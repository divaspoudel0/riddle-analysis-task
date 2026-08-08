"""Build a self-contained static dashboard from Henry's flat file.

Free HuggingFace Static Spaces cannot run Streamlit, so this precomputes every
metric (reusing app.py's exact functions) and bakes the numbers into a single
static/index.html with Plotly from CDN. Same five views as the Streamlit app.

Refresh: drop a newer data/model_riddle_results_flat.csv, rerun this script,
push static/index.html. Numbers are identical to human_eval.py / app.py.

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

import plotly.graph_objects as go  # noqa: E402

OUT = Path(__file__).parent / "index.html"  # repo root: HF Static Space entry

# community-name suffix token -> Plotly 'country names' label
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


def country_of(community: str):
    return TOKEN2COUNTRY.get(community.rsplit("_", 1)[-1])


def build_map(coverage_records: list) -> str:
    """Choropleth: number of cultures (communities) covered per country.

    Coverage map, concept by Pouya Sadeghi: colour a country by how many of the
    benchmark's cultures it contributes, binned 1 / 2 / 3 / 4 / 5-10.
    """
    agg: dict = {}
    for r in coverage_records:
        c = country_of(r["community"])
        if c:
            agg.setdefault(c, []).append(r["community"])
    countries, z, hover = [], [], []
    for c, comms in agg.items():
        n = len(comms)
        countries.append(c)
        z.append(min(n, 5))  # colour capped at the "5-10" bin
        plural = "culture" if n == 1 else "cultures"
        hover.append(f"<b>{c}</b><br>{n} {plural}<br>" + ", ".join(sorted(comms)))
    fig = go.Figure(go.Choropleth(
        locations=countries, locationmode="country names", z=z, text=hover,
        hovertemplate="%{text}<extra></extra>", colorscale="Blues",
        zmin=1, zmax=5, marker_line_color="white", marker_line_width=0.5,
        colorbar=dict(
            title=dict(text="Cultures covered per country", side="bottom"),
            orientation="h", y=-0.12, thickness=14, len=0.6,
            tickvals=[1, 2, 3, 4, 5], ticktext=["1", "2", "3", "4", "5–10"])))
    fig.update_geos(showcountries=True, countrycolor="#ffffff", showframe=True,
                    framecolor="#888", showcoastlines=False, landcolor="#e5e7eb",
                    projection_type="natural earth")
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), height=560,
                      paper_bgcolor="#fff")
    return fig.to_html(full_html=False, include_plotlyjs=False, div_id="mapdiv",
                       config={"displayModeBar": False, "responsive": True})


def records(df, index_name):
    df = df.reset_index().rename(columns={df.index.name or "index": index_name})
    return json.loads(df.to_json(orient="records"))


def main() -> None:
    m, mtime = app.load()
    cov = app.coverage(m.drop_duplicates(["community", "riddle_id", "model_display"]))
    complete = set(cov[cov.status == "complete"].index)

    data = {
        "meta": {
            "mtime": mtime,
            "complete": len(complete),
            "total": app.TOTAL_COMMUNITIES,
            "models": int(m["model_display"].nunique()),
            "human_rows": int(m["is_human"].sum()),
            "pending": int(m["is_pending"].sum()),
        },
        "leaderboard": {}, "difficulty": {},
    }
    for tag, strict in [("strict", True), ("lenient", False)]:
        lb = app.leaderboard(m, complete, strict)
        data["leaderboard"][tag] = records(lb, "model")
        d = app.community_difficulty(m, complete, strict)
        data["difficulty"][tag] = records(d, "community")

    per, overall, misses, overcredit, n = app.community_kappa(m, complete)
    data["kappa"] = {
        "overall": round(overall, 3), "misses": misses,
        "overcredit": overcredit, "n": n,
        "per": records(per.to_frame("kappa"), "community"),
    }
    data["coverage"] = records(
        cov[["status", "pct_complete", "human_done", "pending", "human_eligible"]],
        "community")

    map_html = build_map(data["coverage"])
    covered = sorted({country_of(r["community"]) for r in data["coverage"]
                      if country_of(r["community"])})

    OUT.parent.mkdir(parents=True, exist_ok=True)
    html = (HTML.replace("__DATA__", json.dumps(data))
                .replace("__MAP__", map_html)
                .replace("__NCOUNTRIES__", str(len(covered))))
    OUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUT}  (complete {len(complete)}/{app.TOTAL_COMMUNITIES}, "
          f"kappa {overall:.3f})")


HTML = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Multicultural Riddles — Human Evaluation</title>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
 :root{--floor:#9aa0a6;--ceil:#3b6fb6;--ink:#1c1e21;--mut:#6b7280;--line:#e5e7eb}
 *{box-sizing:border-box}
 body{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
   color:var(--ink);margin:0;padding:24px;max-width:1040px;margin:0 auto}
 h1{font-size:22px;margin:0 0 4px} .cap{color:var(--mut);font-size:13px;margin-bottom:16px}
 .cards{display:flex;gap:12px;flex-wrap:wrap;margin:12px 0 18px}
 .card{border:1px solid var(--line);border-radius:10px;padding:10px 14px;min-width:150px}
 .card .v{font-size:22px;font-weight:600} .card .l{color:var(--mut);font-size:12px}
 .tabs{display:flex;gap:6px;flex-wrap:wrap;border-bottom:1px solid var(--line);margin-bottom:14px}
 .tab{padding:8px 12px;cursor:pointer;border:none;background:none;font-size:14px;color:var(--mut)}
 .tab.on{color:var(--ceil);border-bottom:2px solid var(--ceil);font-weight:600}
 .pane{display:none} .pane.on{display:block}
 .toggle{margin:0 0 10px} .toggle label{margin-right:14px;font-size:14px;cursor:pointer}
 table{border-collapse:collapse;width:100%;font-size:13px;margin-top:12px}
 th,td{border-bottom:1px solid var(--line);padding:6px 8px;text-align:left}
 th{color:var(--mut);font-weight:600} .foot{color:var(--mut);font-size:12px;margin-top:18px;line-height:1.5}
 .info{background:#eef4fb;border:1px solid #cfe0f4;border-radius:8px;padding:12px;font-size:14px;color:#274b73}
 .badge{padding:2px 8px;border-radius:10px;font-size:12px}
 .complete{background:#e3f4e8;color:#1c7a3f}.partial{background:#fdf3e0;color:#9a6a12}
 .thin{background:#fdeaea;color:#b23}.not_started{background:#f1f1f3;color:#666}
</style></head><body>
<h1>🧩 Multicultural Riddles Benchmark — Human Evaluation</h1>
<div class="cap" id="cap"></div>
<div class="cards" id="cards"></div>
<div class="toggle" id="toggle">
 <label><input type="radio" name="sc" value="strict" checked> Strict (top score = 3)</label>
 <label><input type="radio" name="sc" value="lenient"> Lenient (score ≥ 2)</label>
</div>
<div class="tabs" id="tabs"></div>
<div id="lb" class="pane on"><div id="lbchart"></div><div class="cap" id="lbcap"></div><div id="lbtable"></div></div>
<div id="diff" class="pane"><div id="diffchart"></div><div class="cap" id="diffcap"></div></div>
<div id="kappa" class="pane"><div class="cards" id="kcards"></div><div id="kchart"></div><div class="cap" id="kcap"></div></div>
<div id="cov" class="pane"><div id="covtable"></div><div class="cap" id="covcap"></div></div>
<div id="map" class="pane"><p style="font-size:14px;margin:0 0 10px">Coverage map — concept by <b>Pouya Sadeghi</b> (Cohere Labs): cultures covered per country, across __NCOUNTRIES__ countries. Hover a country for its cultures.</p>__MAP__<div class="cap">Darker = more of the benchmark's cultures contributed by that country. Grey countries are not represented in the benchmark. Covers all 44 v0 cultures.</div></div>
<div class="foot" id="foot"></div>
<script>
const D=__DATA__;
const FLOOR="#9aa0a6",CEIL="#3b6fb6";
const cap=document.getElementById('cap');
cap.textContent=`Provisional leaderboard from Henry's flat file (updated ${D.meta.mtime}). Every score traces to the flat file; pending rows dropped, never guessed. Numbers shift as coverage completes.`;
const cards=[['Communities complete',`${D.meta.complete} / ${D.meta.total}`],['Models',D.meta.models],['Human-scored rows',D.meta.human_rows.toLocaleString()],['Pending',D.meta.pending.toLocaleString()]];
document.getElementById('cards').innerHTML=cards.map(c=>`<div class="card"><div class="v">${c[1]}</div><div class="l">${c[0]}</div></div>`).join('');
const TABS=[['lb','🏆 Leaderboard'],['diff','🌍 Community difficulty'],['kappa','🤝 Judge vs human'],['cov','📊 Coverage'],['map','🗺️ Coverage map']];
document.getElementById('tabs').innerHTML=TABS.map((t,i)=>`<button class="tab${i==0?' on':''}" data-p="${t[0]}">${t[1]}</button>`).join('');
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{
 document.querySelectorAll('.tab').forEach(x=>x.classList.remove('on'));b.classList.add('on');
 document.querySelectorAll('.pane').forEach(p=>p.classList.remove('on'));
 document.getElementById(b.dataset.p).classList.add('on');window.dispatchEvent(new Event('resize'));});
const L={margin:{l:10,r:16,t:10,b:44},plot_bgcolor:'#fff',paper_bgcolor:'#fff',font:{size:12},xaxis:{gridcolor:'#eef0f2',zeroline:false},yaxis:{automargin:true,ticklabelposition:'outside'}};
function dumbbell(el,rows,keyF,keyC,labels,xlab){
 const y=rows.map(labels),lo=rows.map(r=>r[keyF]),hi=rows.map(r=>r[keyC]);
 const segs=[];rows.forEach((r,i)=>segs.push({x:[r[keyF],r[keyC]],y:[y[i],y[i]],mode:'lines',line:{color:'#d0d3d8',width:3},showlegend:false,hoverinfo:'skip',type:'scatter'}));
 const f={x:lo,y,mode:'markers',type:'scatter',name:'Heuristic (floor)',marker:{color:FLOOR,size:10}};
 const c={x:hi,y,mode:'markers',type:'scatter',name:'Human (ceiling)',marker:{color:CEIL,size:10}};
 Plotly.newPlot(el,[...segs,f,c],{...L,height:Math.max(420,26*rows.length),xaxis:{...L.xaxis,title:xlab},legend:{orientation:'h',y:1.06}},{displayModeBar:false,responsive:true});
}
function render(sc){
 const lb=D.leaderboard[sc];
 dumbbell('lbchart',[...lb].sort((a,b)=>a['Human (ceiling) %']-b['Human (ceiling) %']),'Heuristic (floor) %','Human (ceiling) %',r=>r.model,`Accuracy (%), ${sc}`);
 document.getElementById('lbcap').textContent='Grey = heuristic auto-judge (lower bound). Blue = human judgement (upper bound).';
 document.getElementById('lbtable').innerHTML='<table><tr><th>#</th><th>Model</th><th>Human %</th><th>Heuristic %</th><th>human-scored %</th><th>n</th></tr>'+lb.map(r=>`<tr><td>${r.rank}</td><td>${r.model}</td><td>${r['Human (ceiling) %']}</td><td>${r['Heuristic (floor) %']}</td><td>${r['human-scored %']}</td><td>${r.n}</td></tr>`).join('')+'</table>';
 const d=D.difficulty[sc];
 dumbbell('diffchart',d,'Heuristic %','Human %',r=>r.community,`Mean accuracy across models (%), ${sc}`);
 document.getElementById('diffcap').textContent=`Hardest: ${d.slice(0,3).map(r=>r.community).join(', ')}. Easiest: ${d.slice(-3).map(r=>r.community).join(', ')}.`;
}
document.querySelectorAll('input[name=sc]').forEach(r=>r.onchange=e=>render(e.target.value));
render('strict');
// kappa
const k=D.kappa;
document.getElementById('kcards').innerHTML=[["Overall Cohen's κ",k.overall],['Human-correct the judge missed',k.misses.toLocaleString()],['Judge over-credits',k.overcredit.toLocaleString()]].map(c=>`<div class="card"><div class="v">${c[1]}</div><div class="l">${c[0]}</div></div>`).join('');
const kp=[...k.per];
Plotly.newPlot('kchart',[{x:kp.map(r=>r.kappa),y:kp.map(r=>r.community),type:'bar',orientation:'h',marker:{color:kp.map(r=>r.kappa<0.4?'#D55E00':CEIL)}}],{...L,height:Math.max(420,26*kp.length),xaxis:{...L.xaxis,title:"Cohen's κ (judge vs human)"},shapes:[{type:'line',x0:k.overall,x1:k.overall,y0:-0.5,y1:kp.length-0.5,line:{color:'#7F7F7F',dash:'dash',width:1.4}}]},{displayModeBar:false,responsive:true});
document.getElementById('kcap').textContent=`On ${k.n.toLocaleString()} human-scored rows. Red κ<0.4 = string-matching unreliable (non-Latin scripts). Dashed line = overall κ ${k.overall}. The judge misses far more correct answers (${k.misses.toLocaleString()}) than it over-credits (${k.overcredit.toLocaleString()}) — why the human ceiling sits above the heuristic floor.`;
// coverage
const ord={complete:0,partial:1,thin:2,not_started:3};
const cv=[...D.coverage].sort((a,b)=>ord[a.status]-ord[b.status]||b.pct_complete-a.pct_complete);
document.getElementById('covtable').innerHTML='<table><tr><th>Community</th><th>Status</th><th>% complete</th><th>human</th><th>pending</th><th>eligible</th></tr>'+cv.map(r=>`<tr><td>${r.community}</td><td><span class="badge ${r.status}">${r.status}</span></td><td>${r.pct_complete??''}</td><td>${r.human_done}</td><td>${r.pending}</td><td>${r.human_eligible}</td></tr>`).join('')+'</table>';
const chase=cv.filter(r=>r.status=='not_started'||r.status=='thin').map(r=>r.community);
document.getElementById('covcap').textContent=chase.length?('Chase list: '+chase.join(', ')):'';
document.getElementById('foot').innerHTML='Methodology: single human annotator per riddle (no inter-annotator agreement). Leaderboard restricted to communities with complete human coverage. Source of truth: model_riddle_results_flat.csv (Henry). Cuba riddle spanish_cuba_history_016 excluded (redone in v2). Provisional until coverage completes.';
</script></body></html>"""


if __name__ == "__main__":
    main()
