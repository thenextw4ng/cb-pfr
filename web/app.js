(function () {
  "use strict";
  const $ = (selector, root) => (root || document).querySelector(selector);
  const $$ = (selector, root) => Array.from((root || document).querySelectorAll(selector));
  const COLORS = ["#56dbe4", "#78a9ff", "#f0bc67", "#75d6ad", "#bb9af7", "#ed8585", "#86b8c9"];
  let DATA = null;
  const number = (value, digits) => Number(value).toFixed(digits == null ? 3 : digits);
  const percent = value => (Number(value) * 100).toFixed(1) + "%";
  const pp = value => (value > 0 ? "+" : "") + Number(value).toFixed(2) + " pp";
  const esc = value => String(value == null ? "" : value).replace(/[&<>"']/g, ch => ({ "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;" }[ch]));
  const link = (url, label) => '<a href="' + esc(url) + '" target="_blank" rel="noopener noreferrer">' + esc(label) + ' ↗</a>';
  const setText = (selector, value) => { const node=$(selector); if(node) node.textContent=value; };
  const plotConfig = {responsive:true, displaylogo:false, modeBarButtonsToRemove:["lasso2d","select2d"], toImageButtonOptions:{format:"png",scale:2}};
  const layoutBase = {
    paper_bgcolor:"rgba(0,0,0,0)", plot_bgcolor:"rgba(0,0,0,0)", font:{family:"Manrope, sans-serif",color:"#b7c8d6",size:10},
    margin:{l:52,r:18,t:18,b:58}, xaxis:{gridcolor:"#1b3445",linecolor:"#294455",zerolinecolor:"#294455",tickfont:{size:9}},
    yaxis:{gridcolor:"#1b3445",linecolor:"#294455",zerolinecolor:"#294455",tickfont:{size:9}}, legend:{orientation:"h",y:-0.22,font:{size:9}}
  };
  function plot(id, traces, layout) {
    const node=$("#"+id);
    if(!node) return;
    if(!window.Plotly) {
      node.innerHTML='<div class="empty-state">Interactive charts need the Plotly library connection. The table values remain available below.</div>';
      return;
    }
    window.Plotly.react(node, traces, Object.assign({}, layoutBase, layout || {}, {autosize:true}), plotConfig);
  }
  function plotUnavailable(id, message) {
    const node=$("#"+id);
    if(node) node.innerHTML='<div class="empty-state">'+esc(message)+'</div>';
  }
  function tag(selector, text, kind) {
    const node=$(selector);
    if(node) { node.textContent=text; node.className="tag"+(kind ? " "+kind : ""); }
  }
  function makeCell(material, pos, label) {
    const klass=material==="M" ? "mox" : "uo2";
    const name=material==="M" ? "MOX" : "UO₂";
    return '<div class="assembly-cell '+klass+'"><small>'+esc(pos)+'</small><b>'+esc(material)+'</b><small>'+name+'</small>'+(label?'<span class="caption">'+esc(label)+'</span>':"")+'</div>';
  }
  function selectedLayout() {
    const chooser=$("#candidateSelect");
    return DATA.latestC5G7.v2aLayoutSummary.find(row=>row.layout===(chooser?chooser.value:"MMUU")) || DATA.latestC5G7.v2aLayoutSummary[0];
  }
  function renderCandidate() {
    if(!DATA) return;
    const layout=selectedLayout();
    const sig=layout.layout;
    setText("#selectedCandidateId","c5g7-2x2-"+sig);
    setText("#selectedCandidateMetaLine","V2a · n = "+layout.n+" · low-budget run-level aggregate");
    const signature=$("#selectedCandidateSignature");
    if(signature) signature.innerHTML=sig.split("").map((ch,i)=>makeCell(ch,"P"+(i+1),"")).join("");
    const grid=$("#layoutView");
    if(grid) grid.innerHTML='<div class="layout-grid">'+sig.split("").map((ch,i)=>makeCell(ch,"Position "+(i+1),"")).join("")+'</div>';
    setText("#layoutCaption","Signature "+sig+" · two MOX + two UO₂. The display order is a label order, not a claim about measured pin-wise geometry.");
    const metrics=$("#selectedCandidateMetrics");
    if(metrics) metrics.innerHTML=
      '<div class="selected-metric"><span>Mean F_fission proxy</span><strong>'+number(layout.meanF,6)+'</strong><small>Between-run SD '+number(layout.sdF,5)+' · n=200</small></div>'+
      '<div class="selected-metric"><span>Mean k-effective</span><strong>'+number(layout.meanK,6)+'</strong><small>Between-run SD '+number(layout.sdK,5)+'</small></div>';
    tag("#selectedRecordTag","DIAGNOSTIC REVIEW REQUIRED","warning");
    const runInfo=$("#selectedCandidateRunInfo");
    if(runInfo) runInfo.innerHTML='<span class="mini-chip">800 batches</span><span class="mini-chip">500 inactive</span><span class="mini-chip">2,000 particles/batch</span><span class="mini-chip">1 thread</span>';
    const checks=$("#selectedCandidateChecks");
    if(checks) checks.innerHTML='<span class="mini-chip">Data integrity: PASS</span><span class="mini-chip">Convergence: NOT CERTIFIED</span><span class="mini-chip">Safety acceptance: NOT CLAIMED</span>';
    const metricSelect=$("#metricSelect");
    const metric=metricSelect?metricSelect.value:"meanF";
    const rows=DATA.latestC5G7.v2aLayoutSummary;
    const values=rows.map(r=>metric==="meanK"?r.meanK:r.meanF);
    const errors=rows.map(r=>metric==="meanK"?r.sdK:r.sdF);
    plot("candidateChart",[{
      type:"scatter",mode:"markers+lines",x:rows.map(r=>r.layout),y:values,
      error_y:{type:"data",array:errors,visible:true,color:"#718fa5",thickness:1.1,width:5},
      marker:{size:10,color:COLORS[0],line:{color:"#d7f8ff",width:1}},line:{color:COLORS[0],width:1.5},
      customdata:rows.map(r=>[r.n,r.convergenceReviewRequired]),hovertemplate:"Layout %{x}<br>Mean: %{y:.6f}<br>Between-run SD: %{error_y.array:.5f}<br>n=%{customdata[0]}<extra></extra>"
    }],{yaxis:{title:metric==="meanK"?"Mean k-effective":"Mean F_fission proxy",gridcolor:"#1b3445"},xaxis:{title:"Fuel-layout signature"},showlegend:false});
  }
  function renderLegacyCharts() {
    const rows=DATA.latestC5G7.v2aLayoutSummary;
    plot("distributionChart",[{
      type:"scatter",mode:"markers",x:rows.map(r=>r.layout),y:rows.map(r=>r.meanK),
      error_y:{type:"data",array:rows.map(r=>r.sdK),visible:true,color:"#829bad"},
      marker:{size:10,color:COLORS[1],line:{width:1,color:"#e1eeff"}},
      customdata:rows.map(r=>r.n),hovertemplate:"%{x}<br>Mean k-effective %{y:.6f}<br>Between-run SD ±%{error_y.array:.5f}<br>n=%{customdata}<extra></extra>"
    }],{xaxis:{title:"Layout"},yaxis:{title:"Mean k-effective"},showlegend:false});
    plot("aggregateChart",[{
      type:"bar",x:rows.map(r=>r.layout),y:rows.map(r=>r.meanF),
      error_y:{type:"data",array:rows.map(r=>r.sdF),visible:true,color:"#9bb1c1"},
      marker:{color:COLORS[0]},hovertemplate:"%{x}<br>Mean F_fission %{y:.6f}<br>Between-run SD ±%{error_y.array:.5f}<extra></extra>"
    }],{xaxis:{title:"Layout"},yaxis:{title:"F_fission proxy"},showlegend:false});
  }
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
  function renderAssemblyAndGeometry() {
    tag("#assemblyFieldStatus","RUN-LEVEL F PROXY","success");
    setText("#assemblyFieldProvenance","V2a has 200 observations per layout, but the browser snapshot stores derived F_fission and k-effective summaries rather than four independent assembly tallies per selected run.");
    const map=$("#assemblyMap");
    if(map) map.innerHTML='<div class="empty-state"><b>No fabricated spatial field.</b><br>The 2 × 2 position-level fission-tally vector is not included in this snapshot. Use the linked archived run artifacts to inspect raw per-run data before creating a position heatmap.</div>';
    tag("#geometryStatus","GEOMETRY SOURCE NOT LOADED","warning");
    setText("#geometryProvenance","This static HTML bundle does not contain geometry.xml or native OpenMC plot outputs. The layout schematic in Candidate Observatory is a material-label view, not a pin-resolved reconstruction.");
    const prev=$("#geometryPreview");
    if(prev) prev.innerHTML='<div class="empty-state"><b>Geometry not bundled in this web snapshot.</b><br>Use the repository model/evidence archives; no pin or geometry field is synthesized here.</div>';
    setText("#geometryCaption","Model viewer requires a committed geometry.xml / native plot artifact.");
    const list=$("#geometryArtifactList");
    if(list) list.innerHTML='<div class="artifact-list-row">'+link("https://github.com/thenextw4ng/cb-pfr/tree/research/cbpfr-four-gate-closeout-2026-10-12/evidence/openmc_local_baseline_2026-10-11","Canonical local OpenMC evidence")+'</div><div class="artifact-list-row">'+link("https://github.com/thenextw4ng/cb-pfr/actions/runs/38853860378","Latest C5G7 campaign artifacts")+'</div>';
    tag("#meshStatus","STATEPOINT TALLY NOT EXPORTED","warning");
    setText("#meshProvenance","The browser snapshot does not bundle the raw 51 × 51 statepoint array. No contour, profile, heatmap, or 3D surface is drawn from layout-level aggregates.");
    ["#meshHeatmap","#meshContour","#meshProfile","#meshSurface"].forEach(sel=>plotUnavailable(sel,"True per-bin statepoint data + uncertainty is not bundled in this snapshot. No spatial field is inferred."));
    const kpis=$("#fieldKpis");
    if(kpis) kpis.innerHTML='<article class="metric"><label>Mesh dimensions</label><strong>Not loaded</strong><small>Requires statepoint export</small></article><article class="metric"><label>Finite bins</label><strong>—</strong><small>Not inferred</small></article><article class="metric"><label>Positive mean bins</label><strong>—</strong><small>Not inferred</small></article><article class="metric"><label>Maximum mean</label><strong>—</strong><small>Not inferred</small></article>';
    const controls=$$(".field-controls select");
    controls.forEach(el=>el.disabled=true);
    const reloadMesh=$("#reloadEvidence");
    if(reloadMesh) reloadMesh.addEventListener("click",()=>setText("#meshSummaryNote","No statepoint export is attached to this static snapshot. Reloading cannot manufacture missing per-bin data."));
    const reloadGeo=$("#reloadGeometry");
    if(reloadGeo) reloadGeo.addEventListener("click",()=>setText("#geometryCaption","The geometry source is not bundled in this snapshot; see the linked repository evidence archive."));
    const area=$("#assemblyBar");
    const rows=DATA.latestC5G7.v2aLayoutSummary;
    plot("assemblyBar",[{
      type:"bar",x:rows.map(r=>r.layout),y:rows.map(r=>r.meanF),
      error_y:{type:"data",array:rows.map(r=>r.sdF),visible:true,color:"#879eb2"},
      marker:{color:COLORS[0]},hovertemplate:"%{x}<br>Mean F_fission %{y:.6f}<extra></extra>"
    }],{xaxis:{title:"Layout"},yaxis:{title:"Mean F_fission proxy"},showlegend:false});
  }
  function initNavigation() {
    const sidebar=$(".sidebar"), toggle=$("#navToggle");
    if(toggle&&sidebar) toggle.addEventListener("click",()=>{const open=sidebar.classList.toggle("nav-open");toggle.setAttribute("aria-expanded",open?"true":"false");});
    $$(".nav-item[data-target]").forEach(item=>item.addEventListener("click",()=>{
      $$(".nav-item").forEach(n=>n.classList.remove("active"));item.classList.add("active");
      if(sidebar) sidebar.classList.remove("nav-open");
      if(toggle) toggle.setAttribute("aria-expanded","false");
    }));
    if("IntersectionObserver" in window){
      const observer=new IntersectionObserver(entries=>{
        entries.filter(e=>e.isIntersecting).forEach(e=>{
          const id=e.target.id;
          $$(".nav-item").forEach(n=>n.classList.toggle("active",n.getAttribute("data-target")===id));
        });
      },{rootMargin:"-14% 0px -72% 0px",threshold:0});
      $$(".main > section[id],.main[id]").forEach(sec=>observer.observe(sec));
    }
  }
  function renderIntegrity() {
    setText("#sourcePath","web/research_snapshot.json · snapshot 2026-10-16 · "+DATA.latestC5G7.workflowUrl);
    const rows=$$("#integrity .integrity-row");
    if(rows[0]){
      const h=rows[0].querySelector("b");if(h)h.textContent="Versioned research snapshot loaded";
      const p=rows[0].querySelector("p");if(p)p.textContent="web/research_snapshot.json · T7 paper values + latest C5G7 campaign replay summary";
      const mark=rows[0].querySelector(".check");if(mark)mark.textContent="✓";
    }
    setText("#meshSummaryNote","Spatial tally arrays are intentionally not approximated from F_fission or k-effective aggregates.");
  }
  function bindControls() {
    const cs=$("#candidateSelect");
    if(cs) {
      cs.innerHTML=DATA.latestC5G7.v2aLayoutSummary.map(r=>'<option value="'+esc(r.layout)+'">'+esc(r.layout)+'</option>').join("");
      cs.value="MMUU";cs.addEventListener("change",renderCandidate);
    }
    const ms=$("#metricSelect");
    if(ms) {
      ms.innerHTML='<option value="meanF">F_fission proxy mean</option><option value="meanK">k-effective mean</option>';
      ms.value="meanF";ms.addEventListener("change",renderCandidate);
    }
  }
  async function init() {
    initNavigation();
    try {
      const response=await fetch("./research_snapshot.json",{cache:"no-store"});
      if(!response.ok) throw new Error("HTTP "+response.status+" while loading research_snapshot.json");
      DATA=await response.json();
      bindControls();
      renderCandidate();
      renderLegacyCharts();
      renderCampaign();
      renderPaper();
      renderSynthetic();
      renderClaimBoundary();
      renderAssemblyAndGeometry();
      renderIntegrity();
    } catch(err) {
      tag("#researchSnapshotStatus","SNAPSHOT LOAD FAILED","danger");
      const note=$("#researchSnapshotProvenance");
      if(note) note.textContent="Could not load research_snapshot.json: "+err.message+". Serve the web directory over HTTP rather than opening index.html directly.";
      const errBox=$("#apiError");
      if(errBox){errBox.hidden=false;errBox.textContent="Data loading error: "+err.message;}
      ["candidateChart","distributionChart","aggregateChart","policyMatchChart","policyRegretChart","v2aLayoutChart","t7PrimaryChart"].forEach(id=>plotUnavailable(id,"Research snapshot unavailable."));
    }
  }
  document.addEventListener("DOMContentLoaded",init);
  window.addEventListener("resize",()=>{if(window.Plotly)$$(".chart,.field-chart").forEach(node=>{try{window.Plotly.Plots.resize(node);}catch(_){}});});
})();