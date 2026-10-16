(function(){
  "use strict";
  const $=id=>document.getElementById(id);
  const C={cyan:"#56dbe4",blue:"#78a9ff",amber:"#f0bc67",green:"#75d6ad",muted:"#91a8b9",grid:"#1b3445",text:"#dce7ef"};
  let DATA=null;
  const esc=v=>String(v==null?"":v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const pct=v=>Number(v)*100;
  const base={paper_bgcolor:"rgba(0,0,0,0)",plot_bgcolor:"rgba(0,0,0,0)",font:{family:"Manrope, sans-serif",color:C.muted,size:10},margin:{l:58,r:22,t:22,b:78},
    xaxis:{gridcolor:C.grid,linecolor:"#294455",zerolinecolor:"#294455",tickfont:{size:9},automargin:true},yaxis:{gridcolor:C.grid,linecolor:"#294455",zerolinecolor:"#294455",tickfont:{size:9},automargin:true},legend:{orientation:"h",y:-0.26,font:{size:9}},hoverlabel:{bgcolor:"#071622",bordercolor:"#426174",font:{color:C.text,size:10}}};
  const config={responsive:true,displaylogo:false,modeBarButtonsToRemove:["lasso2d","select2d"],toImageButtonOptions:{format:"png",scale:2}};
  function plot(id,traces,layout={}){
    const el=$(id);if(!el)return;
    if(!window.Plotly){el.innerHTML='<div class="empty-state"><b>Plotly unavailable</b><p>Numeric source data remain in the versioned snapshot.</p></div>';return;}
    Promise.resolve(window.Plotly.react(el,traces,Object.assign({},base,layout),config)).catch(err=>{el.innerHTML='<div class="empty-state"><b>Chart render failed</b><p>'+esc(err.message||err)+'</p></div>';});
  }
  function setStatus(text,warning=false){const el=$("uncertaintyLabStatus");if(el){el.textContent=text;el.className="tag"+(warning?" warning":" success");}}
  function renderOpenMC(){
    const camp=DATA.latestC5G7,v2a=camp.v2aLayoutSummary||[],high=camp.highBudget.layoutReference||[];
    if(!v2a.length){$("cmpV2aFChart").innerHTML='<div class="empty-state">V2a layout summary unavailable in the recorded snapshot.</div>';return;}
    const layouts=v2a.map(x=>x.layout),metric=$("cmpOpenMCMetric")?.value||"fission";
    if(metric==="fission"){
      const hi=Object.fromEntries(high.map(x=>[x.layout,x]));
      plot("cmpV2aFChart",[
        {type:"bar",name:"V2a low-budget · n=200/layout",x:layouts,y:v2a.map(x=>x.meanF),marker:{color:C.cyan},
          error_y:{type:"data",array:v2a.map(x=>x.sdF),visible:true,color:C.cyan,thickness:1.1,width:3},
          customdata:v2a.map(x=>[x.n,x.sdF,x.convergenceReviewRequired]),
          hovertemplate:"Layout %{x}<br>Mean F_fission %{y:.8f}<br>Between-run SD %{customdata[1]:.6g}<br>Runs %{customdata[0]}<br>Convergence review required: %{customdata[2]}<extra>V2a low-budget</extra>"},
        {type:"bar",name:"High-budget empirical reference · n=10/layout",x:layouts,y:layouts.map(l=>hi[l]?.meanF??null),marker:{color:C.amber},
          error_y:{type:"data",array:layouts.map(l=>hi[l]?.sdF??0),visible:true,color:C.amber,thickness:1.1,width:3},
          customdata:layouts.map(l=>[hi[l]?.n??null,hi[l]?.sdF??null]),
          hovertemplate:"Layout %{x}<br>Empirical reference mean F_fission %{y:.8f}<br>Between-run SD %{customdata[1]:.6g}<br>Replicates %{customdata[0]}<extra>High-budget reference</extra>"}
      ],{barmode:"group",margin:{l:68,r:20,t:20,b:58},xaxis:{...base.xaxis,title:"Fuel-loading layout"},yaxis:{...base.yaxis,title:"Dimensionless F_fission proxy"},legend:{orientation:"h",y:-0.24,font:{size:9}}});
      $("cmpV2aFTitle").textContent="F_fission by layout · mean ± between-run SD";
      $("cmpV2aFNote").textContent="Different compute budgets are separate traces. Error bars are between-run SD, not confidence intervals. High-budget means are empirical references, not exact physical truth; source convergence is not certified.";
    }else{
      plot("cmpV2aFChart",[{type:"bar",name:"V2a low-budget · n=200/layout",x:layouts,y:v2a.map(x=>x.meanK),marker:{color:C.blue},
        error_y:{type:"data",array:v2a.map(x=>x.sdK),visible:true,color:C.blue,thickness:1.1,width:3},
        customdata:v2a.map(x=>[x.n,x.sdK,x.convergenceReviewRequired]),
        hovertemplate:"Layout %{x}<br>Mean k-effective %{y:.8f}<br>Between-run SD %{customdata[1]:.6g}<br>Runs %{customdata[0]}<br>Convergence review required: %{customdata[2]}<extra>V2a low-budget</extra>"}],
      {margin:{l:68,r:20,t:20,b:58},xaxis:{...base.xaxis,title:"Fuel-loading layout"},yaxis:{...base.yaxis,title:"Mean k-effective"}});
      $("cmpV2aFTitle").textContent="k-effective by layout · mean ± between-run SD";
      $("cmpV2aFNote").textContent="Only V2a low-budget k-effective summaries are recorded in this snapshot. No high-budget k-effective uncertainty is synthesized. Source convergence is not certified.";
    }
    plot("cmpV2aKChart",[{type:"bar",name:"V2a low-budget mean k-effective",x:layouts,y:v2a.map(x=>x.meanK),marker:{color:C.blue},
      error_y:{type:"data",array:v2a.map(x=>x.sdK),visible:true,color:C.blue,thickness:1.1,width:3},
      customdata:v2a.map(x=>[x.n,x.sdK,x.convergenceReviewRequired]),
      hovertemplate:"Layout %{x}<br>Mean k-effective %{y:.8f}<br>Between-run SD %{customdata[1]:.6g}<br>n=%{customdata[0]}<br>Convergence review required: %{customdata[2]}<extra></extra>"}],
      {margin:{l:68,r:20,t:20,b:58},xaxis:{...base.xaxis,title:"Fuel-loading layout"},yaxis:{...base.yaxis,title:"Mean k-effective"}});
    $("cmpOpenMCDataNote").textContent="Snapshot "+DATA.snapshot_date+" · 1,200 low-budget V2a observations (200/layout), 60 high-budget reference runs (10/layout). Replay launched 0 new OpenMC runs. Data-integrity pass and physical convergence are separate statuses.";
  }
  function renderPolicy(){
    const items=DATA.latestC5G7.policyReplay.policies||[],names=items.map(x=>x.policy);
    plot("cmpPolicyMatchChart",[{type:"bar",name:"Empirical-best match",x:names,y:items.map(x=>pct(x.matchRate)),
      marker:{color:items.map(x=>x.policy.includes("Adaptive")?C.green:x.policy.includes("CB-PFR")?C.cyan:C.blue)},
      customdata:items.map(x=>[x.meanEvaluations,x.screenPassRate]),hovertemplate:"%{x}<br>Empirical-best match %{y:.2f}%<br>Mean evaluations %{customdata[0]}<br>Screen pass rate %{customdata[1]:.1%}<extra></extra>"}],
      {margin:{l:55,r:16,t:20,b:105},showlegend:false,xaxis:{...base.xaxis,tickangle:-18,title:"Policy"},yaxis:{...base.yaxis,title:"Empirical-best match rate (%)",rangemode:"tozero",range:[0,Math.max(60,...items.map(x=>pct(x.matchRate))+8)]},
       annotations:[{xref:"paper",yref:"paper",x:1,y:1.08,xanchor:"right",showarrow:false,text:"28 blocks · source snapshot has no match-rate CI",font:{size:9,color:C.muted}}]});
    const point=items.find(x=>/Point estimate/.test(x.policy));
    const rr=items.map(x=>{
      const ci=Array.isArray(x.ciRegretDifferenceVsPoint)?x.ciRegretDifferenceVsPoint:null;
      const delta=point?x.meanRegret-point.meanRegret:0,valid=ci&&ci.length===2&&ci.every(Number.isFinite);
      return {policy:x.policy,delta,ci:valid?ci:[delta,delta]};
    });
    plot("cmpPolicyRegretChart",[{type:"scatter",mode:"markers",name:"Mean regret difference vs point estimate",x:rr.map(x=>x.delta),y:rr.map(x=>x.policy),
      marker:{size:9,color:rr.map(x=>x.policy.includes("Adaptive")?C.green:x.policy.includes("CB-PFR")?C.cyan:C.blue)},
      error_x:{type:"data",symmetric:false,array:rr.map(x=>Math.max(0,x.ci[1]-x.delta)),arrayminus:rr.map(x=>Math.max(0,x.delta-x.ci[0])),visible:true,color:"#9bb0bf",thickness:1.3,width:4},
      customdata:rr.map(x=>x.ci),hovertemplate:"%{y}<br>Mean regret difference vs point %{x:.7g}<br>Reported bounds [%{customdata[0]:.7g}, %{customdata[1]:.7g}]<extra></extra>"}],
      {margin:{l:205,r:20,t:24,b:65},showlegend:false,xaxis:{...base.xaxis,title:"Difference in mean empirical regret vs point estimate · negative is lower",zeroline:true,zerolinecolor:C.amber,zerolinewidth:2},
       yaxis:{...base.yaxis,autorange:"reversed"},shapes:[{type:"line",xref:"x",x0:0,x1:0,yref:"paper",y0:0,y1:1,line:{color:C.amber,width:1.5,dash:"dot"}}]});
    $("cmpPolicyNote").textContent="Equal budget: 18 evaluations/decision block, 28 blocks (60 calibration + 140 held-out pools). Adaptive R&S matched the empirical reference in 50.0% of blocks; CB-PFR, point-estimate and uniform-margin each matched in 32.1%. Match-rate CIs are absent from the source snapshot. Regret intervals are the stored paired-bootstrap difference intervals; tied [0,0] bounds are shown as recorded.";
  }
  function renderSynthetic(){
    const rows=DATA.paper.t7.rows||[],endpoint=$("cmpT7Endpoint")?.value||"primary",field=endpoint==="feasible"?"Feasible":"Primary";
    const desc=endpoint==="feasible"?"Truly feasible selection (%)":"Feasible and near-optimal selection (%)";
    const series=[{key:"point"+field,label:"Point estimate",color:C.blue},{key:"cbZ1"+field,label:"CB-PFR z=1",color:C.amber},{key:"adaptiveCB"+field,label:"Adaptive R&S + CB-PFR z*",color:C.green}];
    plot("cmpT7Chart",series.map(s=>({type:"bar",name:s.label,x:rows.map(r=>r.regime),y:rows.map(r=>r[s.key]),marker:{color:s.color},hovertemplate:"Synthetic regime %{x}<br>"+s.label+": %{y:.1f}%<extra></extra>"})),
      {barmode:"group",margin:{l:62,r:18,t:20,b:84},xaxis:{...base.xaxis,title:"Author-generated synthetic regime",tickangle:-15},yaxis:{...base.yaxis,title:desc,range:[0,105]}});
    const matched=DATA.paper.t7.pairedMatched95||[];
    plot("cmpT7bChart",[{type:"scatter",mode:"markers",name:"CB-PFR − uniform margin at matched 95% feasibility",x:matched.map(r=>r.delta),y:matched.map(r=>r.regime),
      error_x:{type:"data",symmetric:false,array:matched.map(r=>r.high-r.delta),arrayminus:matched.map(r=>r.delta-r.low),visible:true,color:C.cyan,thickness:1.5,width:4},
      marker:{size:8,color:matched.map(r=>r.delta<0?C.amber:C.cyan)},customdata:matched.map(r=>[r.low,r.high]),
      hovertemplate:"%{y}<br>Difference %{x:+.1f} pp<br>Reported 95% interval [%{customdata[0]:+.1f}, %{customdata[1]:+.1f}] pp<extra></extra>"}],
      {margin:{l:130,r:25,t:24,b:58},showlegend:false,xaxis:{...base.xaxis,title:"CB-PFR − uniform margin (percentage points)",zeroline:true},
       yaxis:{...base.yaxis,autorange:"reversed"},shapes:[{type:"line",xref:"x",x0:0,x1:0,yref:"paper",y0:0,y1:1,line:{color:C.amber,width:1.5,dash:"dot"}}]});
    $("cmpT7Note").textContent="T7: 20,000 synthetic test pools/regime after 5,000 development/tuning pools. Primary endpoint = feasible and within 0.10 of best feasible energy. Author-generated synthetic method evidence only—not OpenMC physical results. T7b is post hoc.";
  }
  document.addEventListener("DOMContentLoaded",async()=>{
    $("cmpOpenMCMetric")?.addEventListener("change",renderOpenMC);
    $("cmpT7Endpoint")?.addEventListener("change",renderSynthetic);
    try{
      const response=await fetch("/research_snapshot.json",{cache:"no-store",headers:{Accept:"application/json"}});
      if(!response.ok)throw new Error("HTTP "+response.status);
      DATA=await response.json();
      if(!DATA.latestC5G7||!DATA.syntheticBenchmarks||!DATA.paper?.t7)throw new Error("The recorded snapshot is missing expected comparison groups.");
      renderOpenMC();renderPolicy();renderSynthetic();setStatus("SNAPSHOT "+DATA.snapshot_date+" · ANALYSIS READY");
    }catch(error){
      setStatus("COMPARISON DATA UNAVAILABLE",true);
      ["cmpV2aFChart","cmpV2aKChart","cmpPolicyMatchChart","cmpPolicyRegretChart","cmpT7Chart","cmpT7bChart"].forEach(id=>{const el=$(id);if(el)el.innerHTML='<div class="empty-state"><b>Source data unavailable</b><p>'+esc(error.message||error)+'</p></div>';});
    }
  });
})();