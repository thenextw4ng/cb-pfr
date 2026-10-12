const $ = (id) => document.getElementById(id);
const palette = {text:"#e8f1f7",muted:"#91a8b9",line:"#263f52",cyan:"#55d4df",blue:"#247fa0",orange:"#f5bb62"};
let records = [];
let metadata = {};
let meshData = null;
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
  await initMesh();
 }catch(error){
  showError("Could not load recorded evidence: "+error.message+". Start the local Python server from the repository root and check the source CSV path.");
  $("layoutView").innerHTML='<div class="loading">Evidence unavailable — no scientific values are fabricated.</div>';
  $("sourcePath").textContent="API unavailable";
 }
}
document.addEventListener("DOMContentLoaded",init);

/* Spatial visualization is loaded from the archived OpenMC HDF5 statepoint via the local Python API. */
const fieldPalette = {Viridis:"Viridis",Cividis:"Cividis",Plasma:"Plasma",Magma:"Magma",Turbo:"Turbo"};
function fieldStats(values){
 const finite=values.flat().filter(v=>Number.isFinite(v));
 const positive=finite.filter(v=>v>0);
 return {finite:finite.length,positive:positive.length,min:finite.length?Math.min(...finite):null,max:finite.length?Math.max(...finite):null,mean:finite.length?finite.reduce((a,b)=>a+b,0)/finite.length:null};
}
function currentField(){
 if(!meshData)return null;
 const score=$("meshScore").value, view=$("meshView").value, scale=$("meshScale").value;
 const item=meshData.mesh_tallies[0], record=item.scores[score];
 if(!record)return null;
 const mean=record.mean, sd=record.std_dev;
 const relative=mean.map((row,y)=>row.map((v,x)=>Number.isFinite(v)&&v>0&&Number.isFinite(sd[y][x])&&sd[y][x]>=0?100*sd[y][x]/v:null));
 let values=(view==="relative_sd"?relative:mean).map(row=>row.map(v=>v===null?null:Number(v)));
 let colorTitle=view==="relative_sd"?"Relative Monte Carlo SD (%)":"Tally mean";
 if(view==="mean"&&scale==="log"){
  values=values.map(row=>row.map(v=>v!==null&&v>0?Math.log10(v):null));
  colorTitle="log₁₀(tally mean)";
 } else if(view==="mean") colorTitle="Tally mean";
 return {item,score,view,mean,sd,relative,values,colorTitle,stats:fieldStats(mean)};
}
function drawMesh(){
 if(!meshData)return;
 const f=currentField();
 if(!f){$("meshStatus").textContent="SCORE UNAVAILABLE";return;}
 const palette=$("meshPalette").value;
 const z=f.values, raw=f.view==="relative_sd"?f.relative:f.mean;
 const xs=Array.from({length:f.item.dimensions[0]},(_,i)=>i),ys=Array.from({length:f.item.dimensions[1]},(_,i)=>i);
 const hover=(title)=>"x-bin %{x}<br>y-bin %{y}<br>"+title+" %{customdata:.6g}<extra></extra>";
 chart("meshHeatmap",[{type:"heatmap",x:xs,y:ys,z:z,customdata:raw,colorscale:f.view==="relative_sd"?"Magma":palette,colorbar:{title:{text:f.colorTitle,font:{size:10}}},hovertemplate:hover(f.colorTitle),connectgaps:false}],{margin:{l:50,r:25,t:10,b:45},xaxis:{...baseLayout.xaxis,title:"Mesh x-bin index"},yaxis:{...baseLayout.yaxis,title:"Mesh y-bin index",autorange:"reversed"},showlegend:false});
 chart("meshContour",[{type:"contour",x:xs,y:ys,z:z,customdata:raw,colorscale:f.view==="relative_sd"?"Magma":palette,contours:{coloring:"heatmap",showlines:true},colorbar:{title:{text:f.colorTitle,font:{size:10}}},hovertemplate:hover(f.colorTitle),connectgaps:false,ncontours:14}],{margin:{l:50,r:25,t:10,b:45},xaxis:{...baseLayout.xaxis,title:"Mesh x-bin index"},yaxis:{...baseLayout.yaxis,title:"Mesh y-bin index",autorange:"reversed"},showlegend:false});
 chart("meshSurface",[{type:"surface",x:xs,y:ys,z:z, surfacecolor:z,colorscale:f.view==="relative_sd"?"Magma":palette,colorbar:{title:{text:f.colorTitle,font:{size:10}}},hovertemplate:"x-bin %{x}<br>y-bin %{y}<br>Displayed value %{z:.6g}<extra></extra>",connectgaps:false,showscale:true}],{margin:{l:5,r:5,t:5,b:5},scene:{xaxis:{title:"X bin",gridcolor:palette.line,color:palette.muted},yaxis:{title:"Y bin",gridcolor:palette.line,color:palette.muted},zaxis:{title:f.colorTitle,gridcolor:palette.line,color:palette.muted},bgcolor:"rgba(0,0,0,0)",camera:{eye:{x:1.55,y:1.55,z:1.1}}}});
 const st=f.stats;
 $("fieldKpis").innerHTML=[["Mesh dimensions",f.item.dimensions[0]+" × "+f.item.dimensions[1],"Archived tally bins"],["Finite bins",st.finite.toLocaleString(),"Finite recorded means"],["Positive bins",st.positive.toLocaleString(),"Positive mean tally values"],["Max tally mean",st.max===null?"—":st.max.toExponential(4),"Recorded "+f.score+" mean"]].map(m=>'<article class="metric"><label>'+m[0]+'</label><strong>'+m[1]+'</strong><small>'+m[2]+'</small></article>').join("");
}
async function initMesh(){
 try{
  const response=await fetch("/api/mesh",{headers:{Accept:"application/json"}});
  if(!response.ok){let detail="HTTP "+response.status;try{detail=(await response.json()).error||detail}catch(_){}throw new Error(detail)}
  meshData=await response.json();
  if(!meshData.mesh_tallies||!meshData.mesh_tallies.length)throw new Error("No compatible 2D mesh tally in the archived statepoint.");
  const item=meshData.mesh_tallies[0];
  $("meshStatus").textContent=meshData.provenance.hash_matches===true?"SHA-256 VERIFIED":meshData.provenance.hash_matches===false?"HASH MISMATCH":"HASH NOT CHECKED";
  $("meshStatus").classList.toggle("warning",meshData.provenance.hash_matches===false);
  $("meshProvenance").textContent=meshData.provenance.source+" · "+item.dimensions.join(" × ")+" bins · tally "+item.tally_name+" · SHA-256 "+meshData.provenance.sha256+". "+(meshData.provenance.hash_matches===true?"Archive member hash matches the committed baseline.":meshData.provenance.hash_matches===false?"WARNING: archive hash differs from the recorded baseline; verify provenance before scientific comparison.":"Baseline hash was unavailable; provenance has not been hash-verified.")+" Mesh indices are not mapped to physical assembly coordinates.";
  const scoreSelect=$("meshScore");scoreSelect.innerHTML=Object.keys(item.scores).map(k=>'<option value="'+k+'">'+k+'</option>').join("");
  ["meshScore","meshView","meshScale","meshPalette"].forEach(id=>$(id).addEventListener("change",drawMesh));
  drawMesh();
 }catch(error){
  $("meshStatus").textContent="SPATIAL DATA UNAVAILABLE";
  $("meshStatus").classList.add("warning");
  $("meshProvenance").textContent="The archived spatial tally could not be loaded: "+error.message;
  ["meshHeatmap","meshContour","meshSurface"].forEach(id=>$(id).innerHTML='<div class="loading">No spatial values displayed. No scientific data have been fabricated.</div>');
 }
}
