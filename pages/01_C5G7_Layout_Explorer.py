"""Custom CB-PFR workstation UI for the C5G7 layout smoke study."""
from pathlib import Path
import json
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="CB-PFR · Geometry Explorer", page_icon="⚛", layout="wide")
ROOT = Path(__file__).resolve().parents[1]
CSV = ROOT / "results" / "c5g7_layout_smoke_2026-10-10" / "candidate_summary.csv"
if not CSV.exists():
    st.error(f"Evidence CSV not found: {CSV}")
    st.stop()
df = pd.read_csv(CSV)
required = ["candidate_id","layout_signature","canonical_reference","seed","batches","inactive","particles_per_batch","keff_mean","keff_std_dev","aggregate_flux_score","aggregate_fission_score","mgxs_sha256_before_transport","mgxs_sha256_after_transport"]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error("Missing CSV columns: " + ", ".join(missing))
    st.stop()
data = []
for _, r in df.iterrows():
    sig = str(r["layout_signature"])
    if len(sig) != 4 or any(c not in "UM" for c in sig):
        continue
    data.append({
        "id":str(r["candidate_id"]), "sig":sig, "canonical":bool(r["canonical_reference"]),
        "seed":int(r["seed"]), "batches":int(r["batches"]), "inactive":int(r["inactive"]),
        "particles":int(r["particles_per_batch"]), "keff":float(r["keff_mean"]),
        "std":float(r["keff_std_dev"]), "flux":float(r["aggregate_flux_score"]),
        "fission":float(r["aggregate_fission_score"]),
        "hash0":str(r["mgxs_sha256_before_transport"]), "hash1":str(r["mgxs_sha256_after_transport"])
    })
if not data:
    st.error("No valid four-position layout records found.")
    st.stop()
payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
default_id = data[0]["id"]

html = r"""
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{color-scheme:dark;--bg:#07111b;--panel:#0c1b29;--line:#263f52;--text:#e8f1f7;--muted:#9aafbf;--cyan:#55d4df;--orange:#f5bb62;--purple:#f5bb62;--green:#4bd5a5}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--text);font-family:Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;font-size:12px}body{overflow-x:hidden}
.app{background:radial-gradient(ellipse at 55% 32%,#102536 0,#07111b 60%);min-height:1060px}
.top{height:58px;display:flex;align-items:center;gap:18px;padding:0 16px;background:#0a1925;border-bottom:1px solid #263f52}
.brand{min-width:260px;display:flex;align-items:center;gap:9px}.atom{width:34px;color:var(--cyan)}.brand b{font-size:19px;letter-spacing:.04em}.brand small{display:block;font-size:9px;color:var(--muted)}
.nav{display:flex;align-self:stretch;flex:1;overflow:hidden}.nav button{border:0;border-bottom:2px solid transparent;background:none;color:var(--muted);padding:0 12px;white-space:nowrap;cursor:pointer}.nav button.active{color:white;background:#123242;border-color:var(--cyan)}
.online{color:var(--muted);white-space:nowrap;font-size:10px}.dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--green);margin-right:6px}
.grid{display:grid;grid-template-columns:205px minmax(350px,1fr) 220px;gap:9px;padding:10px}
.sidebar,.right,.panel,.mini{background:rgba(5,24,43,.94);border:1px solid var(--line);border-radius:5px;min-width:0;overflow:hidden}
.sidebar{padding:10px}.sec{font-size:11px;font-weight:700;letter-spacing:.04em;padding:3px 0 9px;border-bottom:1px solid var(--line);margin-bottom:7px}.menu button{display:block;width:100%;text-align:left;border:0;background:transparent;color:var(--muted);padding:9px 7px;cursor:pointer}.menu button.active{background:#123242;color:#eaf7ff;border-left:2px solid var(--cyan)}
.tree{font-size:10px;line-height:2;color:#a9c4e1;margin:8px 0}.tree .muted{padding-left:12px;color:var(--muted)}.state{display:flex;justify-content:space-between;margin:9px 0;color:#a8c3de;font-size:10px}.ok{color:var(--green)}.warn{color:#ffd07b}
.main{display:flex;flex-direction:column;gap:9px;min-width:0}.head{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:10px 12px;border-bottom:1px solid var(--line);background:linear-gradient(90deg,#102536,#0c1b29)}.head h2{font-size:13px;margin:3px 0 0}.eyebrow{font-size:9px;letter-spacing:.14em;color:var(--cyan);text-transform:uppercase}.tools{display:flex;gap:6px;align-items:center}.badge{border:1px solid #76532f;color:var(--orange);border-radius:12px;padding:4px 7px;font-size:9px;white-space:nowrap}
select{max-width:100%;background:var(--panel);color:var(--text);border:1px solid var(--line);border-radius:4px;padding:7px;font-size:10px}
.tabs{display:flex;padding:0 10px;background:#0a1925;border-bottom:1px solid var(--line)}.tabs button{background:none;border:0;border-bottom:2px solid transparent;color:#9aafbf;padding:9px 13px;cursor:pointer}.tabs button.active{color:var(--cyan);border-color:var(--cyan)}
.viewport{position:relative;display:grid;grid-template-columns:minmax(0,1fr) 145px;min-height:360px;background:radial-gradient(ellipse at 48% 48%,#102536 0,var(--bg) 70%)}svg.geometry{width:100%;height:100%;min-height:360px;display:block}.legend{align-self:start;margin:10px 8px 10px 0;border:1px solid var(--line);background:#0a1925;padding:10px;border-radius:4px}.legend-title{font-size:11px;margin-bottom:8px}.leg{display:flex;align-items:center;gap:7px;margin:10px 0;color:#c4d9ef;font-size:10px}.swatch{width:10px;height:10px;border-radius:2px;display:inline-block;flex-shrink:0}.footnote{position:absolute;left:11px;bottom:9px;color:#9aafbf;font-size:9px}
.lower{display:grid;grid-template-columns:1.1fr 1fr;gap:9px}.mini .body{padding:11px}.metrics{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:7px}.metric{padding:9px;background:#102536;border:1px solid var(--line);border-radius:4px;min-width:0}.label{font-size:9px;color:#9aafbf;margin-bottom:7px}.value{font-size:18px;font-weight:700;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.caption{font-size:9px;color:var(--muted);margin-top:4px}
.composition{display:flex;align-items:center;gap:12px}.donut{width:110px;height:110px;flex-shrink:0}.comp-list{display:grid;gap:11px;flex:1}.comp-row{display:grid;grid-template-columns:10px 1fr auto;gap:6px;align-items:center;color:#c0d0dc;font-size:10px}.comp-row strong{color:#e8f1f7}
.info{padding:11px;border-bottom:1px solid var(--line)}.info-title{font-weight:700;font-size:11px;margin-bottom:10px}.row{display:grid;grid-template-columns:1fr auto;gap:7px;margin:9px 0;font-size:10px}.row span:first-child{color:#9aafbf}.row span:last-child{text-align:right;color:#d5e7fa;overflow-wrap:anywhere}.layers{display:grid;gap:12px;color:var(--muted);font-size:10px}.layers input{accent-color:var(--cyan)}
table{width:100%;border-collapse:collapse;font-size:10px}th,td{text-align:left;padding:8px;border-bottom:1px solid var(--line);white-space:nowrap}th{color:var(--muted);background:#102536}td{color:var(--text)}tr.selected td{background:#123242;color:var(--text)}.tablewrap{padding:10px;overflow:auto}
.bottom{margin:0 10px 10px;border:1px solid var(--line);background:#06192c;border-radius:5px;padding:10px 12px;display:flex;gap:12px;flex-wrap:wrap;color:#9aafbf;font-size:9px}
button:focus-visible,select:focus-visible,input:focus-visible{outline:2px solid var(--cyan);outline-offset:2px}
@media(max-width:1150px){.grid{grid-template-columns:175px minmax(0,1fr)}.right{grid-column:1/-1;display:grid;grid-template-columns:repeat(4,minmax(0,1fr))}.info{border-right:1px solid #143b5e}.brand{min-width:200px}.nav button{padding:0 7px}.online{display:none}}
@media(max-width:760px){.top{height:auto;flex-wrap:wrap;padding:9px}.brand{min-width:0}.nav{order:3;flex-basis:100%;height:34px;overflow:auto}.grid{grid-template-columns:1fr}.sidebar{display:none}.right{grid-column:auto;display:block}.viewport{grid-template-columns:1fr}.legend{display:none}.lower{grid-template-columns:1fr}.metrics{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style></head><body><div class="app">
<header class="top"><div class="brand"><svg class="atom" viewBox="0 0 48 48" fill="none" stroke="currentColor" stroke-width="1.7"><ellipse cx="24" cy="24" rx="21" ry="8" transform="rotate(55 24 24)"/><ellipse cx="24" cy="24" rx="21" ry="8" transform="rotate(-55 24 24)"/><ellipse cx="24" cy="24" rx="21" ry="8"/><circle cx="24" cy="24" r="3" fill="currentColor"/></svg><div><b>CB-PFR</b><small>CONFIDENCE-BOUNDED PHYSICAL FEASIBILITY RANKING</small></div></div><nav class="nav"><button class="active">Geometry</button><button data-jump="results">Recorded Metrics</button><button data-jump="qubo">QUBO Constraint</button><button data-jump="prov">Provenance</button></nav><div class="online"><i class="dot"></i>Evidence loaded</div></header>
<div class="grid">
<aside class="sidebar"><div class="sec">VISUALIZATION WORKSPACE</div><div class="menu"><button class="active">▦ &nbsp; Geometry Explorer</button><button data-jump="results">⌁ &nbsp; Recorded Metrics</button><button data-jump="qubo">◇ &nbsp; QUBO Constraint</button><button data-jump="prov">♧ &nbsp; Provenance &amp; Validation</button></div><div style="height:18px"></div><div class="sec">SIMULATION DATA</div><div class="tree"><b>C5G7 layout study</b><div class="muted">Assembly placements</div><div class="muted">Candidate summary CSV</div><div class="muted">MGXS identity hashes</div><b>Recorded results</b><div class="muted">k-effective summary</div><div class="muted">Aggregate flux scores</div><div class="muted">Aggregate fission scores</div><b>Candidate layouts</b><div id="treeCandidates"></div></div><div style="height:12px"></div><div class="sec">SYSTEM STATUS</div><div class="state"><span>Evidence CSV</span><span class="ok">● Loaded</span></div><div class="state"><span>Layout parser</span><span class="ok">● Ready</span></div><div class="state"><span>Full-core geometry</span><span class="warn">○ Not supplied</span></div></aside>
<main class="main">
<section class="panel"><div class="head"><div><div class="eyebrow">Geometry workspace</div><h2>Reactor Layout Explorer</h2></div><div class="tools"><span class="badge">2×2 DESIGN STUDY</span><select id="pick" aria-label="Select candidate"></select></div></div><div class="tabs"><button class="active" data-tab="layout">Placement</button><button data-tab="materials">Material key</button><button data-tab="3d">3D viewport</button><button data-tab="comparison">Comparison</button></div><div class="viewport"><div id="threeViewport" style="display:none;position:relative;min-height:360px;width:100%;grid-column:1/-1;background:radial-gradient(ellipse at 50% 45%,#102536 0,#07111b 75%);"><div id="threeStatus" style="position:absolute;left:12px;top:10px;z-index:2;color:#9aafbf;font-size:10px">3D SCHEMATIC · ROTATE / ZOOM · NOT TO SCALE</div><div id="threeCanvas" style="width:100%;height:400px"></div></div><svg id="geometry" class="geometry" viewBox="0 0 600 400" role="img" aria-label="Four-position material placement schematic"></svg><div class="legend"><div class="legend-title">Material legend</div><div class="leg"><i class="swatch" style="background:#55d4df"></i>UO₂ assembly</div><div class="leg"><i class="swatch" style="background:#f5bb62"></i>MOX assembly</div><div class="leg"><i class="swatch" style="background:#247fa0"></i>Reference outline</div><div class="caption" style="line-height:1.5;margin-top:12px">Grid is a visual aid only; cell-level physics geometry is not supplied.</div></div><div class="footnote">SCHEMATIC · FOUR ASSEMBLY POSITIONS · NOT A FULL-CORE MESH</div></div></section>
<div class="lower"><section class="mini" id="results"><div class="head"><h2>Simulation results</h2><span class="badge">RECORDED CSV</span></div><div class="body"><div class="metrics"><div class="metric"><div class="label">k-effective · mean</div><div class="value" id="keff">—</div><div class="caption" id="std">reported std. dev.</div></div><div class="metric"><div class="label">Aggregate flux score</div><div class="value" id="flux">—</div><div class="caption">repository score</div></div><div class="metric"><div class="label">Aggregate fission score</div><div class="value" id="fission">—</div><div class="caption">repository score</div></div></div><div style="margin-top:12px" class="label">RUN CONFIGURATION</div><div class="row"><span>Seed</span><span id="seed">—</span></div><div class="row"><span>Batches / inactive</span><span id="batches">—</span></div><div class="row"><span>Particles / batch</span><span id="particles">—</span></div></div></section>
<section class="mini" id="prov"><div class="head"><h2>Material composition</h2><span class="badge">LAYOUT-BASED</span></div><div class="body"><div class="composition"><svg id="donut" class="donut" viewBox="0 0 120 120"></svg><div class="comp-list"><div class="comp-row"><i class="swatch" style="background:#55d4df"></i><span>UO₂ positions</span><strong id="uCount">—</strong></div><div class="comp-row"><i class="swatch" style="background:#f5bb62"></i><span>MOX positions</span><strong id="mCount">—</strong></div><div class="comp-row"><i class="swatch" style="background:#247fa0"></i><span>Canonical reference</span><strong id="canonical">—</strong></div></div></div><div class="caption" style="line-height:1.5;margin-top:12px">Composition describes the four-position design vector, not material volume fractions.</div></div></section></div>
<section class="mini" id="qubo"><div class="head"><h2>Candidate comparison</h2><span class="badge">DESCRIPTIVE · NOT A WINNER RANKING</span></div><div id="plotlyChart" style="height:300px;padding:8px 10px" aria-label="Plotly chart of recorded candidate k-effective results"><div style="padding:20px;color:#9aafbf;font-size:11px">Loading interactive comparison chart…</div></div><div class="tablewrap"><table><thead><tr><th>Candidate</th><th>Layout</th><th>k-effective mean</th><th>Reported std. dev.</th><th>Flux score</th><th>Fission score</th></tr></thead><tbody id="rows"></tbody></table></div></section>
</main>
<aside class="right"><div class="info"><div class="info-title">GEOMETRY INFORMATION</div><div class="row"><span>Model</span><span>C5G7 layout study</span></div><div class="row"><span>Representation</span><span>2×2 positions</span></div><div class="row"><span>Material types</span><span>2</span></div><div class="row"><span>Layout records</span><span id="nLayouts">—</span></div></div><div class="info"><div class="info-title">SELECTED CANDIDATE</div><div class="row"><span>Candidate ID</span><span id="candidateId">—</span></div><div class="row"><span>Signature</span><span id="signature">—</span></div><div class="row"><span>Seed</span><span id="seed2">—</span></div><div class="row"><span>Canonical</span><span id="canonical2">—</span></div></div><div class="info"><div class="info-title">LAYERS</div><div class="layers"><label><input type="checkbox" data-layer="labels" checked> Position labels</label><label><input type="checkbox" data-layer="outline" checked> Outer outline</label></div><div class="caption" style="line-height:1.5;margin-top:10px">These controls affect the schematic only.</div></div><div class="info"><div class="info-title">MGXS PROVENANCE</div><div class="row"><span>Hash before</span><span id="hash0">—</span></div><div class="row"><span>Hash after</span><span id="hash1">—</span></div><div class="caption" style="line-height:1.5">Hash equality is an integrity check, not physical validation.</div></div></aside>
</div><div class="bottom"><span><i class="dot"></i> Evidence CSV loaded</span><span>CB-PFR</span><span id="footCandidate">Candidate: —</span><span id="footKeff">k-effective: —</span><span style="margin-left:auto">Research prototype · not benchmark-grade</span></div></div>
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<script>
const DATA=__DATA__, NS="http://www.w3.org/2000/svg", byId=id=>document.getElementById(id);
const layers={labels:true,outline:true};
function el(tag,attrs,text){const n=document.createElementNS(NS,tag);Object.entries(attrs||{}).forEach(([k,v])=>n.setAttribute(k,v));if(text!==undefined)n.textContent=text;return n;}
function pts(cx,cy,r){return Array.from({length:6},(_,i)=>{const a=(-30+i*60)*Math.PI/180;return (cx+r*Math.cos(a)).toFixed(1)+","+(cy+r*Math.sin(a)).toFixed(1)}).join(" ");}
function draw(d){const svg=byId("geometry");svg.replaceChildren();
const addText=(x,y,text,size=10,fill="#9bb9d7",anchor="start",weight=400)=>svg.append(el("text",{x,y,fill,"font-size":size,"font-family":"ui-monospace,SFMono-Regular,Menlo,monospace","text-anchor":anchor,"font-weight":weight},text));
const addLine=(x1,y1,x2,y2,stroke="#244d70",width=1,dash="")=>svg.append(el("line",{x1,y1,x2,y2,stroke,"stroke-width":width,...(dash?{"stroke-dasharray":dash}:{})}));
/* Coordinate frame: the repository supplies four categorical assembly positions, not pin-resolved geometry. */
addText(24,24,"XY PLACEMENT MAP",10,"#42caff","start",700);addText(576,24,"SCHEMATIC / NOT TO SCALE",9,"#7999b8","end",500);
const x0=156,y0=72,cell=144;
if(layers.outline){svg.append(el("rect",{x:x0-2,y:y0-2,width:cell*2+4,height:cell*2+4,fill:"#061426",stroke:"#4b91c5","stroke-width":1.5}));}
addLine(x0,y0+cell,x0+cell*2,y0+cell,"#386180",1,"4 4");addLine(x0+cell,y0,x0+cell,y0+cell*2,"#386180",1,"4 4");
const pos=[[0,0],[1,0],[0,1],[1,1]];
pos.forEach(([cx,cy],i)=>{const x=x0+cx*cell,y=y0+cy*cell,u=d.sig[i]==="U",color=u?"#2da8f4":"#e4a04b",label=u?"UO₂":"MOX";
svg.append(el("rect",{x:x+3,y:y+3,width:cell-6,height:cell-6,fill:u?"#0b3150":"#3a291c",stroke:color,"stroke-width":1.8}));

if(layers.labels){addText(x+12,y+20,["P00","P10","P01","P11"][i],9,"#c5d9ec","start",600);addText(x+cell/2,y+cell/2+5,label,22,"#f1f7ff","middle",700);addText(x+cell/2,y+cell-12,u?"URANIUM OXIDE":"MIXED OXIDE",8,color,"middle",600);}
});
/* Coordinate axes and ticks are orientation aids, not physical dimensions. */
addLine(x0,y0+cell*2+20,x0+cell*2,y0+cell*2+20,"#7ea3c3",1);addLine(x0,y0+cell*2+15,x0,y0+cell*2+25,"#7ea3c3",1);addLine(x0+cell,y0+cell*2+15,x0+cell,y0+cell*2+25,"#7ea3c3",1);addLine(x0+cell*2,y0+cell*2+15,x0+cell*2,y0+cell*2+25,"#7ea3c3",1);
addText(x0+cell/2,y0+cell*2+36,"COLUMN 0",8,"#7999b8","middle");addText(x0+cell+cell/2,y0+cell*2+36,"COLUMN 1",8,"#7999b8","middle");
addText(124,y0+cell/2,"ROW 0",8,"#7999b8","end");addText(124,y0+cell+cell/2,"ROW 1",8,"#7999b8","end");
addText(24,374,"4 CATEGORICAL POSITIONS · NO PIN-RESOLVED MODEL PROVIDED",8,"#7999b8","start",500);
}
function donut(d){const svg=byId("donut");svg.replaceChildren();const m=d.sig.split("").filter(c=>c==="M").length,u=4-m,c=2*Math.PI*42;
svg.append(el("circle",{cx:60,cy:60,r:42,fill:"none",stroke:"#55d4df","stroke-width":13}));
svg.append(el("circle",{cx:60,cy:60,r:42,fill:"none",stroke:"#f5bb62","stroke-width":13,"stroke-dasharray":(c*m/4)+" "+(c*(1-m/4)),"stroke-dashoffset":c*.25,transform:"rotate(-90 60 60)"}));
svg.append(el("text",{x:60,y:57,"text-anchor":"middle",fill:"#f0f7ff","font-size":17,"font-weight":700},u+" / "+m));
svg.append(el("text",{x:60,y:71,"text-anchor":"middle",fill:"#9aafbf","font-size":9},"UO₂ / MOX"));}
function render(){const d=DATA.find(x=>x.id===byId("pick").value)||DATA[0];draw(d);donut(d);
byId("keff").textContent=d.keff.toFixed(6);byId("std").textContent="± "+d.std.toFixed(6)+" reported std. dev.";byId("flux").textContent=d.flux.toFixed(3);byId("fission").textContent=d.fission.toFixed(5);
byId("seed").textContent=d.seed;byId("batches").textContent=d.batches+" / "+d.inactive;byId("particles").textContent=d.particles.toLocaleString();
byId("uCount").textContent=d.sig.split("").filter(c=>c==="U").length+" / 4";byId("mCount").textContent=d.sig.split("").filter(c=>c==="M").length+" / 4";byId("canonical").textContent=d.canonical?"Yes":"No";
byId("candidateId").textContent=d.id;byId("signature").textContent=d.sig;byId("seed2").textContent=d.seed;byId("canonical2").textContent=d.canonical?"Yes":"No";
byId("hash0").textContent=d.hash0.slice(0,12)+"…";byId("hash1").textContent=d.hash1.slice(0,12)+"…";byId("footCandidate").textContent="Candidate: "+d.id;byId("footKeff").textContent="k-effective: "+d.keff.toFixed(6);
document.querySelectorAll("#rows tr").forEach(tr=>tr.classList.toggle("selected",tr.dataset.id===d.id));}
DATA.forEach(d=>{const o=document.createElement("option");o.value=d.id;o.textContent=d.id+" · "+d.sig;byId("pick").append(o);});
byId("pick").value=__DEFAULT__;
byId("treeCandidates").innerHTML=DATA.map(d=>'<div class="muted" data-pick="'+d.id+'" style="cursor:pointer">● '+d.sig+' · '+d.id.replace("c5g7-2x2-","")+'</div>').join("");
byId("rows").innerHTML=DATA.map(d=>'<tr data-id="'+d.id+'" style="cursor:pointer"><td>'+d.id+'</td><td>'+d.sig+'</td><td>'+d.keff.toFixed(6)+'</td><td>'+d.std.toFixed(6)+'</td><td>'+d.flux.toFixed(3)+'</td><td>'+d.fission.toFixed(5)+'</td></tr>').join("");
byId("pick").addEventListener("change",render);
document.querySelectorAll("[data-pick]").forEach(n=>n.addEventListener("click",()=>{byId("pick").value=n.dataset.pick;render();}));
document.querySelectorAll("#rows tr").forEach(n=>n.addEventListener("click",()=>{byId("pick").value=n.dataset.id;render();}));
document.querySelectorAll("[data-layer]").forEach(n=>n.addEventListener("change",()=>{layers[n.dataset.layer]=n.checked;render();}));
document.querySelectorAll("[data-jump]").forEach(n=>n.addEventListener("click",()=>byId(n.dataset.jump).scrollIntoView({behavior:"smooth",block:"nearest"})));
document.querySelectorAll("[data-tab]").forEach(n=>n.addEventListener("click",()=>{document.querySelectorAll("[data-tab]").forEach(b=>b.classList.toggle("active",b===n));const is3d=n.dataset.tab==="3d";byId("threeViewport").style.display=is3d?"block":"none";byId("geometry").style.display=is3d?"none":"block";if(is3d){initThree();byId("threeViewport").scrollIntoView({behavior:"smooth",block:"nearest"});}else if(n.dataset.tab==="comparison")byId("qubo").scrollIntoView({behavior:"smooth",block:"nearest"});else if(n.dataset.tab==="materials")byId("prov").scrollIntoView({behavior:"smooth",block:"nearest"});else window.scrollTo({top:0,behavior:"smooth"});}));
byId("nLayouts").textContent=DATA.length;render();renderPlotly();
</script>
<script>
function renderPlotly(){
 const host=byId("plotlyChart");
 if(!window.Plotly){host.innerHTML='<div style="padding:20px;color:#ffd07b;font-size:11px">Plotly CDN tidak dapat dimuat. Grafik interaktif memerlukan koneksi internet.</div>';return;}
 const sorted=[...DATA].sort((a,b)=>a.id.localeCompare(b.id));
 const names=sorted.map(d=>d.id.replace("c5g7-2x2-",""));
 const trace={type:"bar",x:names,y:sorted.map(d=>d.keff),error_y:{type:"data",array:sorted.map(d=>d.std),visible:true,color:"#c0d0dc",thickness:1.2,width:3},marker:{color:sorted.map(d=>d.canonical?"#42caff":"#e4a04b")},customdata:sorted.map(d=>[d.sig,d.flux,d.fission]),hovertemplate:"Candidate %{x}<br>Layout %{customdata[0]}<br>k-effective %{y:.6f}<br>Reported std. dev. shown as error bar<br>Flux score %{customdata[1]:.3f}<br>Fission score %{customdata[2]:.5f}<extra></extra>"};
 Plotly.newPlot(host,[trace],{paper_bgcolor:"rgba(0,0,0,0)",plot_bgcolor:"rgba(0,0,0,0)",font:{color:"#c0d0dc",family:"Inter, sans-serif",size:10},margin:{l:65,r:20,t:18,b:55},xaxis:{title:"Candidate",gridcolor:"#263f52",linecolor:"#3b586b"},yaxis:{title:"Recorded k-effective mean",gridcolor:"#263f52",linecolor:"#3b586b",zerolinecolor:"#3b586b"},showlegend:false,hoverlabel:{bgcolor:"#0c1b29",bordercolor:"#55d4df",font:{color:"#e8f1f7"}}},{responsive:true,displaylogo:false});
}
</script>
<script type="module">
let threeStarted=false;
window.initThree=async function(){
 if(threeStarted)return;threeStarted=true;
 const host=document.getElementById("threeCanvas"),status=document.getElementById("threeStatus");
 try{
  const THREE=await import("https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js");
  const {OrbitControls}=await import("https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/controls/OrbitControls.js");
  const scene=new THREE.Scene();scene.background=new THREE.Color("#07111b");
  const camera=new THREE.PerspectiveCamera(42,host.clientWidth/400,0.1,1000);camera.position.set(5.8,6.5,8.2);
  const renderer=new THREE.WebGLRenderer({antialias:true,alpha:false});renderer.setPixelRatio(Math.min(window.devicePixelRatio||1,2));renderer.setSize(host.clientWidth,400);renderer.outputColorSpace=THREE.SRGBColorSpace;host.replaceChildren(renderer.domElement);
  const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.target.set(0,0.2,0);
  scene.add(new THREE.AmbientLight(0xc5ddff,2.1));const key=new THREE.DirectionalLight(0xffffff,2.6);key.position.set(4,8,5);scene.add(key);
  const grid=new THREE.GridHelper(7,14,0x28618a,0x163653);grid.position.y=-0.03;scene.add(grid);
  const axes=new THREE.AxesHelper(2.2);axes.position.set(-3.25,0,-3.25);scene.add(axes);
  const group=new THREE.Group();scene.add(group);
  function rebuild(){
   while(group.children.length){const obj=group.children.pop();obj.geometry?.dispose();if(obj.material){if(Array.isArray(obj.material))obj.material.forEach(m=>m.dispose());else obj.material.dispose();}}
   const d=DATA.find(x=>x.id===byId("pick").value)||DATA[0];
   const positions=[[-1,0.6,-1],[1,0.6,-1],[-1,0.6,1],[1,0.6,1]];
   positions.forEach(([x,y,z],i)=>{
    const u=d.sig[i]==="U",color=u?0x238fd0:0xd58a3c;
    const geo=new THREE.BoxGeometry(1.72,1.1,1.72);
    const mat=new THREE.MeshStandardMaterial({color,metalness:0.18,roughness:0.48,transparent:true,opacity:0.92});
    const mesh=new THREE.Mesh(geo,mat);mesh.position.set(x,y,z);mesh.userData={label:["P00","P10","P01","P11"][i],material:u?"UO₂":"MOX"};group.add(mesh);
    const edges=new THREE.LineSegments(new THREE.EdgesGeometry(geo),new THREE.LineBasicMaterial({color:0xb8d9f5,transparent:true,opacity:0.7}));edges.position.copy(mesh.position);group.add(edges);
   });
   status.textContent="3D CATEGORICAL SCHEMATIC · "+d.id+" · "+d.sig+" · NOT A PIN-RESOLVED MODEL";
  }
  const raycaster=new THREE.Raycaster(),pointer=new THREE.Vector2();
  renderer.domElement.addEventListener("pointerdown",event=>{
   const rect=renderer.domElement.getBoundingClientRect();pointer.x=((event.clientX-rect.left)/rect.width)*2-1;pointer.y=-((event.clientY-rect.top)/rect.height)*2+1;raycaster.setFromCamera(pointer,camera);
   const hits=raycaster.intersectObjects(group.children.filter(o=>o.isMesh),false);
   if(hits.length){const m=hits[0].object;status.textContent=m.userData.label+" · "+m.userData.material+" · "+(DATA.find(x=>x.id===byId("pick").value)||DATA[0]).id;}
  });
  function resize(){const w=host.clientWidth||600;camera.aspect=w/400;camera.updateProjectionMatrix();renderer.setSize(w,400);}
  window.addEventListener("resize",resize);byId("pick").addEventListener("change",rebuild);
  const animate=()=>{requestAnimationFrame(animate);controls.update();renderer.render(scene,camera);};rebuild();animate();
 }catch(err){status.textContent="3D viewport unavailable: WebGL/CDN load failed. 2D schematic remains available.";console.error(err);}
}
</script>
</body></html>
"""
html = html.replace("__DATA__", payload).replace("__DEFAULT__", json.dumps(default_id))
components.html(html, height=1120, scrolling=True)
