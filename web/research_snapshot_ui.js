(function(){
  "use strict";
  const $ = selector => document.querySelector(selector);
  const $$ = selector => Array.from(document.querySelectorAll(selector));
  const COLORS = ["#56dbe4", "#78a9ff", "#f0bc67", "#75d6ad", "#bb9af7", "#ed8585", "#86b8c9"];
  let DATA = null;
  const number = (value, digits) => Number(value).toFixed(digits == null ? 3 : digits);
  const pp = value => (value > 0 ? "+" : "") + Number(value).toFixed(2) + " pp";
  const esc = value => String(value == null ? "" : value).replace(/[&<>"']/g, ch => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[ch]));
  const link = (url, label) => '<a href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">' + esc(label) + ' ↗</a>';
  const setText = (selector, value) => { const node=$(selector); if(node) node.textContent=value; };
  const layoutBase = {
    paper_bgcolor:"rgba(0,0,0,0)", plot_bgcolor:"rgba(0,0,0,0)",
    font:{family:"Manrope, sans-serif",color:"#b7c8d6",size:10},
    margin:{l:52,r:18,t:18,b:58},
    xaxis:{gridcolor:"#1b3445",linecolor:"#294455",zerolinecolor:"#294455",tickfont:{size:9}},
    yaxis:{gridcolor:"#1b3445",linecolor:"#294455",zerolinecolor:"#294455",tickfont:{size:9}},
    legend:{orientation:"h",y:-0.22,font:{size:9}}
  };
  const plotConfig={responsive:true,displaylogo:false,modeBarButtonsToRemove:["lasso2d","select2d"],toImageButtonOptions:{format:"png",scale:2}};
  function plot(id,traces,layout){
    const node=$("#"+id); if(!node)return;
    if(!window.Plotly){node.innerHTML='<div class="empty-state">Plotly.js did not load; the numeric tables below remain available.</div>';return;}
    try{Promise.resolve(window.Plotly.react(node,traces,Object.assign({},layoutBase,layout||{},{autosize:true}),plotConfig)).catch(error=>{node.innerHTML='<div class="empty-state">Chart render failed: '+esc(error.message||error)+'</div>';});}
    catch(error){node.innerHTML='<div class="empty-state">Chart render failed: '+esc(error.message||error)+'</div>';}
  }
  function tag(selector,text,kind){const node=$(selector);if(node){node.textContent=text;node.className="tag"+(kind?" "+kind:"");}}
  function renderCampaign() {
    const c=DATA.latestC5G7, v=c.v2a, p=c.policyReplay;
    const m=$$("#researchKpis .metric");
    if(m.length>=4) {
      m[0].innerHTML='<label>V2a low-budget records</label><strong>'+v.observedRuns.toLocaleString("en-US")+'</strong><small>200 common seed pools × 6 layouts</small>';
      m[1].innerHTML='<label>High-budget references</label><strong>'+c.highBudget.runs+'</strong><small>10 recorded runs / layout</small>';
      m[2].innerHTML='<label>Equal-budget decision blocks</label><strong>'+p.decisionBlocks+'</strong><small>18 evaluations per decision</small>';
      m[3].innerHTML='<label>Source convergence</label><strong>NOT CERTIFIED</strong><small>All low-budget rows require diagnostics review</small>';
    }
    tag("#researchSnapshotStatus","SNAPSHOT LOADED · 2026-10-16","success");
    setText("#researchSnapshotProvenance","Versioned data snapshot; V2a integrity checks passed and offline policy replay completed. Scientific convergence and official benchmark acceptance remain unestablished.");
    tag("#campaignStatusTag","INTEGRITY PASS · CONVERGENCE OPEN","warning");
    const integrity=$("#campaignIntegrity");
    if(integrity) integrity.innerHTML='<ul class="status-list">'+
      '<li><b>1,200 / 1,200</b> V2a observations inspected</li>'+
      '<li><b>200 complete pools</b>, six layouts per pool</li>'+
      '<li><b>200 distinct seed/pool IDs</b>; global statepoint hashes unique</li>'+
      '<li><b>One common MGXS hash</b>; seed-ledger audit PASS</li>'+
      '<li class="warning-item"><b>0 / 1,200</b> runs marked convergence-certified</li></ul>';
    const policy=$("#campaignPolicySummary");
    if(policy) policy.innerHTML='<ul class="status-list">'+
      '<li><b>Replay completed</b>; zero new OpenMC runs</li>'+
      '<li><b>60 calibration pools</b> + <b>140 held-out pools</b></li>'+
      '<li><b>28 decision blocks</b>, same 18-evaluation budget</li>'+
      '<li class="warning-item">Reference is an empirical high-budget model estimate, not exact physical truth</li></ul>';
    const source=$("#campaignSourceLinks");
    if(source) source.innerHTML=c.links.map(item=>link(item.url,item.label)).join("");
    plot("policyMatchChart",[{
      type:"bar",x:p.policies.map(x=>x.policy),y:p.policies.map(x=>x.matchRate*100),
      marker:{color:p.policies.map((x,i)=>i===0?COLORS[3]:(i===1?COLORS[0]:"#5b7890"))},
      text:p.policies.map(x=>(x.matchRate*100).toFixed(1)+"%"),textposition:"outside",cliponaxis:false,
      hovertemplate:"%{x}<br>Empirical-best match %{y:.1f}%<extra></extra>"
    }],{yaxis:{title:"Empirical-best match (%)",range:[0,62]},xaxis:{tickangle:-14,tickfont:{size:8}},showlegend:false,margin:{l:52,r:12,t:25,b:95}});
    plot("policyRegretChart",[{
      type:"bar",x:p.policies.map(x=>x.policy),y:p.policies.map(x=>x.meanRegret*1000),
      marker:{color:p.policies.map((x,i)=>i===0?COLORS[3]:(i===1?COLORS[0]:"#5b7890"))},
      text:p.policies.map(x=>(x.meanRegret*1000).toFixed(3)),textposition:"outside",cliponaxis:false,
      hovertemplate:"%{x}<br>Mean empirical regret ×10⁻³: %{y:.4f}<extra></extra>"
    }],{yaxis:{title:"Mean empirical regret (×10⁻³)",rangemode:"tozero"},xaxis:{tickangle:-14,tickfont:{size:8}},showlegend:false,margin:{l:64,r:12,t:22,b:95}});
    plot("v2aLayoutChart",[{
      type:"scatter",mode:"markers+lines",x:c.v2aLayoutSummary.map(x=>x.layout),y:c.v2aLayoutSummary.map(x=>x.meanF),
      error_y:{type:"data",array:c.v2aLayoutSummary.map(x=>x.sdF),visible:true,color:"#89a2b5",thickness:1.2,width:4},
      marker:{size:10,color:COLORS[0],line:{color:"#e5fbff",width:1}},line:{color:"#56dbe4",width:1.5},
      customdata:c.v2aLayoutSummary.map(x=>[x.n,x.meanK,x.sdK]),hovertemplate:"%{x}<br>Mean F_fission %{y:.6f}<br>Between-run SD ±%{error_y.array:.5f}<br>n=%{customdata[0]}<br>Mean k-effective %{customdata[1]:.6f}<extra></extra>"
    }],{yaxis:{title:"Mean F_fission proxy",range:[1.2,1.95]},xaxis:{title:"Layout"},showlegend:false});
    const tbl=$("#v2aLayoutTable");
    if(tbl) tbl.innerHTML='<table><thead><tr><th>Layout</th><th>n</th><th>Mean F ± SD</th><th>Mean k-effective</th><th>Status</th></tr></thead><tbody>'+
      c.v2aLayoutSummary.map(x=>'<tr><td><b>'+esc(x.layout)+'</b></td><td class="numeric">'+x.n+'</td><td class="numeric">'+number(x.meanF,6)+' ± '+number(x.sdF,5)+'</td><td class="numeric">'+number(x.meanK,6)+'</td><td class="warn">REVIEW REQUIRED</td></tr>').join("")+
      '</tbody></table><p class="caption">SD is across the 200 low-budget run-level observations; it is not the uncertainty of a converged physical truth.</p>';
  }
  function renderPaper() {
    const paper=DATA.paper, t=paper.t7;
    setText("#paperTitle",paper.title);
    const prov=$("#paperProvenance");
    if(prov) prov.innerHTML='<span class="provenance-chip">'+esc(paper.source_file)+'</span><span class="provenance-chip">6 pages</span><span class="provenance-chip">SHA-256 '+esc(paper.source_sha256.slice(0,16))+'…</span><span class="provenance-chip">Supplied PDF · 16 Oct 2026</span><a class="text-link" href="./RESEARCH_DATA_CROSSWALK_2026-10-16.md">Open data crosswalk ↗</a><a class="text-link" href="./research_snapshot.json" download>Download machine-readable snapshot ↗</a>';
    setText("#t7Design",t.regimes+" regimes · "+t.test_pools_per_regime.toLocaleString("en-US")+" test pools / regime");
    setText("#t7H1","NOT SUPPORTED · −3.8 / −1.8 pp");
    setText("#t7H2","PARTLY SUPPORTED · 88.0 → 97.3%");
    setText("#t7H3","SUPPORTED · 20,000 / 20,000");
    function drawT7Chart() {
      const metric=$("#t7MetricSelect")?$("#t7MetricSelect").value:"primary";
      const field=metric==="feasible"?"Feasible":"Primary";
      const series=[
        ["Point estimate","pointPrimary","pointFeasible",COLORS[1]],
        ["CB-PFR z=1","cbZ1Primary","cbZ1Feasible",COLORS[0]],
        ["CB-PFR tuned z*","cbZstarPrimary","cbZstarFeasible",COLORS[2]],
        ["Uniform margin tuned","uniformPrimary","uniformFeasible",COLORS[4]],
        ["Adaptive R&S + point","adaptivePointPrimary","adaptivePointFeasible",COLORS[3]],
        ["Adaptive R&S + CB-PFR","adaptiveCBPrimary","adaptiveCBFeasible",COLORS[5]]
      ];
      plot("t7PrimaryChart",series.map((s,i)=>({
        type:"bar",name:s[0],x:t.rows.map(r=>r.regime),y:t.rows.map(r=>r[metric==="feasible"?s[2]:s[1]]),
        marker:{color:s[3]},hovertemplate:"%{x}<br>"+s[0]+": %{y:.1f}%<extra></extra>"
      })),{barmode:"group",yaxis:{title:field+" selections (%)",range:[0,105]},xaxis:{tickangle:-18,tickfont:{size:8}},legend:{orientation:"h",y:-0.35,font:{size:8}},margin:{l:50,r:15,t:14,b:120}});
    }
    drawT7Chart();
    const chooser=$("#t7MetricSelect");
    if(chooser) chooser.addEventListener("change",drawT7Chart);
    const resultTable=$("#t7ResultsTable");
    if(resultTable) {
      const columns=[
        ["Point estimate","pointPrimary","pointFeasible"],
        ["CB-PFR z=1","cbZ1Primary","cbZ1Feasible"],
        ["CB-PFR tuned z*","cbZstarPrimary","cbZstarFeasible"],
        ["Uniform margin m*","uniformPrimary","uniformFeasible"],
        ["Replicate-SE z*","sampleSEPrimary","sampleSEFeasible"],
        ["Adaptive + point","adaptivePointPrimary","adaptivePointFeasible"],
        ["Adaptive + CB-PFR","adaptiveCBPrimary","adaptiveCBFeasible"]
      ];
      resultTable.innerHTML='<table><thead><tr><th>Regime</th>'+columns.map(c=>'<th>'+esc(c[0])+'<br>P / F (%)</th>').join("")+'</tr></thead><tbody>'+
        t.rows.map(r=>'<tr><td><b>'+esc(r.regime)+'</b></td>'+columns.map(c=>'<td class="numeric">'+number(r[c[1]],1)+' / '+number(r[c[2]],1)+'</td>').join("")+'</tr>').join("")+
        '</tbody></table><p class="caption">P = feasible and near-optimal primary endpoint; F = truly feasible selected-candidate rate. The small-pool row uses K=12; other regimes use K=40.</p>';
    }
    const matched=t.pairedMatched95;
    plot("t7MatchedChart",[{
      type:"bar",x:matched.map(r=>r.regime),y:matched.map(r=>r.delta),
      marker:{color:matched.map(r=>r.delta<0?COLORS[5]:(r.delta===0?"#688093":COLORS[3]))},
      error_y:{type:"data",array:matched.map(r=>r.high-r.delta),arrayminus:matched.map(r=>r.delta-r.low),visible:true,color:"#a8bdcc",thickness:1.2,width:4},
      text:matched.map(r=>pp(r.delta)),textposition:"outside",cliponaxis:false,
      hovertemplate:"%{x}<br>CB-PFR − uniform margin: %{y:+.1f} pp<extra></extra>"
    }],{yaxis:{title:"Difference in primary endpoint (pp)",zeroline:true,zerolinecolor:"#9aafbd"},xaxis:{tickangle:-18,tickfont:{size:8}},showlegend:false,margin:{l:62,r:12,t:18,b:90}});
    const matchedTable=$("#t7MatchedTable");
    if(matchedTable) matchedTable.innerHTML='<table><thead><tr><th>Regime</th><th>Δ vs uniform</th><th>Reported 95% interval</th></tr></thead><tbody>'+
      matched.map(r=>'<tr><td>'+esc(r.regime)+'</td><td class="numeric">'+pp(r.delta)+'</td><td class="numeric">['+number(r.low,1)+', '+number(r.high,1)+']</td></tr>').join("")+
      '</tbody></table><p class="caption">T7b is explicitly post hoc in the paper. Read as an operating-envelope exploration, not a prospectively confirmatory superiority test.</p>';
    const h=$("#t7TableNote");
    if(h) h.textContent=t.primary_endpoint+"; each cell in the table shows primary / truly feasible (%) per regime. Every row represents 20,000 synthetic test pools.";
    const sourceLinks=$("#campaignSourceLinks");
    const hypotheses=$("#t7HypothesisTable");
    if(hypotheses) hypotheses.innerHTML='<table><thead><tr><th>Hypothesis</th><th>Outcome</th><th>Verdict</th></tr></thead><tbody>'+t.hypotheses.map(hyp=>'<tr><td><b>'+esc(hyp.id)+'</b><br>'+esc(hyp.hypothesis)+'</td><td>'+esc(hyp.outcome)+'</td><td class="'+(hyp.verdict==="SUPPORTED"?"good":"warn")+'">'+esc(hyp.verdict)+'</td></tr>').join("")+'</tbody></table>';
  }
  function renderSynthetic() {
    const t2=DATA.syntheticBenchmarks.t2;
    const sum=$("#t2Summary");
    if(sum) sum.innerHTML='<div class="selected-candidate-metrics"><div class="selected-metric"><span>CB-PFR − point estimate</span><strong>'+pp(t2.vsPoint.deltaPp)+'</strong><small>Paired 95% CI ['+number(t2.vsPoint.ci[0],4)+', '+number(t2.vsPoint.ci[1],4)+'] pp</small></div><div class="selected-metric"><span>Required practical effect</span><strong>≥ '+t2.minEffectPp+' pp</strong><small>Prespecified rule was not met</small></div></div><p class="caption">The gain is statistically distinguishable from zero under this synthetic design but smaller than the prespecified practical-effect threshold; do not claim confirmatory superiority.</p>';
    const t2table=$("#t2ScenarioTable");
    if(t2table) t2table.innerHTML='<table><thead><tr><th>Scenario</th><th>Point (%)</th><th>CB-PFR (%)</th><th>Uniform (%)</th><th>CB − point</th></tr></thead><tbody>'+t2.scenarios.map(s=>'<tr><td>'+esc(s.name)+'</td><td class="numeric">'+number(s.point,2)+'</td><td class="numeric">'+number(s.cbpfr,2)+'</td><td class="numeric">'+number(s.uniform,2)+'</td><td class="numeric">'+pp(s.cbpfr-s.point)+'</td></tr>').join("")+'</tbody></table>';
    setText("#t2Source","Open T2 report ↗"); $("#t2Source").href=t2.sourceUrl;
    const t3=DATA.syntheticBenchmarks.t3;
    setText("#t3Summary",t3.decision);
    plot("t3DeltaChart",[
      {type:"bar",name:"CB-PFR − point",x:t3.regimes.map(r=>r.name),y:t3.regimes.map(r=>r.deltaPoint),marker:{color:COLORS[0]},hovertemplate:"%{x}<br>Δ versus point: %{y:+.1f} pp<extra></extra>"},
      {type:"bar",name:"CB-PFR − uniform margin",x:t3.regimes.map(r=>r.name),y:t3.regimes.map(r=>r.deltaUniform),marker:{color:COLORS[2]},hovertemplate:"%{x}<br>Δ versus uniform: %{y:+.1f} pp<extra></extra>"}
    ],{barmode:"group",yaxis:{title:"Feasible-selection difference (pp)",zeroline:true,zerolinecolor:"#8098a8"},xaxis:{tickangle:-18,tickfont:{size:8}},legend:{orientation:"h",y:-0.3,font:{size:8}},margin:{l:55,r:10,t:10,b:95}});
    const t3table=$("#t3RegimeTable");
    if(t3table) t3table.innerHTML='<table><thead><tr><th>Regime</th><th>Point (%)</th><th>CB-PFR (%)</th><th>Uniform (%)</th><th>Δ point</th><th>Δ uniform</th></tr></thead><tbody>'+t3.regimes.map(r=>'<tr><td>'+esc(r.name)+'</td><td class="numeric">'+number(r.point,1)+'</td><td class="numeric">'+number(r.cbpfr,1)+'</td><td class="numeric">'+number(r.uniform,1)+'</td><td class="numeric">'+pp(r.deltaPoint)+'</td><td class="numeric">'+pp(r.deltaUniform)+'</td></tr>').join("")+'</tbody></table>';
    $("#t3Source").href=t3.sourceUrl;
  }
  function renderClaimBoundary() {
    const a=$("#supportedClaims"), b=$("#unestablishedClaims");
    if(a) a.innerHTML=DATA.claimBoundary.supported.map(x=>'<li>'+esc(x)+'</li>').join("");
    if(b) b.innerHTML=DATA.claimBoundary.notEstablished.map(x=>'<li>'+esc(x)+'</li>').join("");
  }

  async function initResearchSnapshot(){
    try{
      const response=await fetch("/research_snapshot.json",{cache:"no-store",headers:{Accept:"application/json"}});
      if(!response.ok)throw new Error("HTTP "+response.status+" while reading research_snapshot.json");
      DATA=await response.json();
      renderCampaign(); renderPaper(); renderSynthetic(); renderClaimBoundary();
      const status=$("#researchSnapshotStatus");
      if(status){status.textContent="SNAPSHOT LOADED · "+(DATA.snapshot_date||"VERSIONED");status.classList.add("success");}
    }catch(error){
      tag("#researchSnapshotStatus","SNAPSHOT LOAD FAILED","warning");
      setText("#researchSnapshotProvenance","Could not load the research snapshot: "+error.message);
      ["policyMatchChart","policyRegretChart","v2aLayoutChart","t7PrimaryChart","t7MatchedChart","t3DeltaChart"].forEach(id=>{
        const node=$("#"+id);if(node)node.innerHTML='<div class="empty-state">Research snapshot unavailable: '+esc(error.message)+'</div>';
      });
    }
  }
  document.addEventListener("DOMContentLoaded",initResearchSnapshot);
})();