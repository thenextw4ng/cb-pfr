const $ = (id) => document.getElementById(id);
const palette = {text:"#e8f1f7",muted:"#91a8b9",line:"#263f52",cyan:"#55d4df",blue:"#247fa0",orange:"#f5bb62"};
let records = [];
let metadata = {};
const number = (x, digits=5) => Number.isFinite(Number(x)) ? Number(x).toFixed(digits) : "—";
const has = (row,key) => row[key] !== null && row[key] !== undefined && row[key] !== "" && Number.isFinite(Number(row[key]));
function label(row){return String(row.candidate_id ?? "Candidate") + " · " + String(row.layout_signature ?? "layout");}
function layoutCells(signature){
  const chars=String(signature??"").toUpperCase().replace(/[^UM]/g,"");
  const cells=(chars.length>=4?chars.slice(0,4):"UMUM").split("");
  return '<div class="assembly-grid">'+cells.map((c,i)=>'<div class="assembly '+(c==="M"?"mox-cell":"")+'">'+(c==="M"?"MOX":"UO₂")+'<small>POSITION '+(i+1)+'</small></div>').join("")+'</div>';
}
const baseLayout={paper_bgcolor:"rgba(0,0,0,0)",plot_bgcolor:"rgba(0,0,0,0)",font:{family:"Manrope, sans-serif",color:palette.muted,size:10},margin:{l:55,r:18,t:15,b:65},xaxis:{gridcolor:"#1e3545",linecolor:palette.line,tickangle:-28},yaxis:{gridcolor:"#1e3545",linecolor:palette.line,zerolinecolor:palette.line},hoverlabel:{bgcolor:"#102536",bordercolor:palette.line,font:{color:palette.text}}};
const config={displaylogo:false,responsive:true,modeBarButtonsToRemove:["lasso2d","select2d"]};
function chart(id,traces,layout={}){if(window.Plotly)Plotly.react($(id),traces,{...baseLayout,...layout},config);else $(id).innerHTML='<div class="loading">Plotly.js failed to load. Check your internet connection.</div>';}
function showCandidate(){
 const id=$("candidateSelect").value,row=records.find(r=>String(r.candidate_id)===id);if(!row)return;
 $("layoutView").innerHTML=layoutCells(row.layout_signature);
 $("layoutCaption").textContent=label(row)+" · seed "+(row.seed??"not recorded");
 drawCandidateChart();
}
function drawCandidateChart(){
 const key=$("metricSelect").value;
 const valid=records.filter(r=>has(r,key)).sort((a,b)=>Number(a[key])-Number(b[key]));
 const selected=$("candidateSelect").value;
 if(!valid.length){$("candidateChart").innerHTML='<div class="loading">No recorded values for this metric.</div>';return;}
 const error=key==="keff_mean"?"keff_std_dev":null;
 chart("candidateChart",[{type:"bar",x:valid.map(label),y:valid.map(r=>Number(r[key])),marker:{color:valid.map(r=>String(r.candidate_id)===selected?palette.cyan:"#31536a")},error_y:error?{type:"data",array:valid.map(r=>has(r,error)?Number(r[error]):0),visible:true,color:palette.muted,thickness:1.2,width:3}:undefined,customdata:valid.map(r=>[r.candidate_id,r.layout_signature,r.seed]),hovertemplate:"Candidate %{customdata[0]}<br>Layout %{customdata[1]}<br>Seed %{customdata[2]}<br>Value %{y:.7g}<extra></extra>"}],{yaxis:{...baseLayout.yaxis,title:key==="keff_mean"?"Reported k-effective mean":"Repository score (units not specified)"},xaxis:{...baseLayout.xaxis,title:"Candidate / layout"}});
}
function drawOtherCharts(){
 const vals=records.filter(r=>has(r,"keff_mean"));
 chart("distributionChart",[{type:"histogram",x:vals.map(r=>Number(r.keff_mean)),nbinsx:Math.min(18,Math.max(5,Math.ceil(Math.sqrt(vals.length)))),marker:{color:palette.blue,line:{color:palette.cyan,width:1}},hovertemplate:"k-effective %{x:.6f}<br>Records %{y}<extra></extra>"}],{bargap:.12,xaxis:{...baseLayout.xaxis,title:"Reported k-effective mean"},yaxis:{...baseLayout.yaxis,title:"Record count"}});
 const flux=records.filter(r=>has(r,"aggregate_flux_score")),fis=records.filter(r=>has(r,"aggregate_fission_score"));
 const traces=[];
 if(flux.length)traces.push({type:"bar",name:"Aggregate flux",x:flux.map(r=>String(r.candidate_id)),y:flux.map(r=>Number(r.aggregate_flux_score)),marker:{color:palette.cyan},hovertemplate:"Candidate %{x}<br>Flux score %{y:.5g}<extra></extra>"});
 if(fis.length)traces.push({type:"bar",name:"Aggregate fission",x:fis.map(r=>String(r.candidate_id)),y:fis.map(r=>Number(r.aggregate_fission_score)),marker:{color:palette.orange},hovertemplate:"Candidate %{x}<br>Fission score %{y:.5g}<extra></extra>"});
 if(!traces.length){$("aggregateChart").innerHTML='<div class="loading">No aggregate scores are present in the source dataset.</div>';return;}
 chart("aggregateChart",traces,{barmode:"group",legend:{orientation:"h",y:1.12,x:0},xaxis:{...baseLayout.xaxis,title:"Candidate ID"},yaxis:{...baseLayout.yaxis,title:"Repository score (units unspecified)"}});
}
function showError(message){const el=$("apiError");el.hidden=false;el.textContent=message;}
async function init(){
 try{
  const response=await fetch("/api/candidates",{headers:{Accept:"application/json"}});
  if(!response.ok)throw new Error("API returned HTTP "+response.status);
  const payload=await response.json();records=payload.records||[];metadata=payload.metadata||{};
  if(!records.length)throw new Error("The API returned no candidate records.");
  $("sourcePath").textContent=metadata.source||"Source path not provided by API";
  const layouts=new Set(records.map(r=>r.layout_signature).filter(Boolean));
  const seeds=new Set(records.map(r=>String(r.seed)).filter(s=>s!=="undefined"&&s!=="null"));
  const ks=records.filter(r=>has(r,"keff_mean")).map(r=>Number(r.keff_mean));
  const metrics=[["Candidate records",records.length.toLocaleString(),"Rows in current candidate summary"],["Unique layouts",layouts.size.toLocaleString(),"Distinct recorded signatures"],["k-effective span",ks.length?number(Math.min(...ks),5)+" – "+number(Math.max(...ks),5):"—","Reported mean values"],["Recorded seeds",seeds.size.toLocaleString(),"Distinct seed values"]];
  $("metrics").innerHTML=metrics.map(m=>'<article class="metric"><label>'+m[0]+'</label><strong>'+m[1]+'</strong><small>'+m[2]+'</small></article>').join("");
  $("candidateSelect").innerHTML=records.map(r=>'<option value="'+String(r.candidate_id).replaceAll('"',"&quot;")+'">'+label(r)+'</option>').join("");
  $("candidateSelect").addEventListener("change",showCandidate);$("metricSelect").addEventListener("change",drawCandidateChart);
  showCandidate();drawOtherCharts();
 }catch(error){
  showError("Could not load recorded evidence: "+error.message+". Start the local Python server from the repository root and check the source CSV path.");
  $("layoutView").innerHTML='<div class="loading">Evidence unavailable — no scientific values are fabricated.</div>';
  $("sourcePath").textContent="API unavailable";
 }
}
document.addEventListener("DOMContentLoaded",init);