const $ = (id) => document.getElementById(id);
const palette = {text:"#e8f1f7",muted:"#91a8b9",line:"#263f52",cyan:"#55d4df",blue:"#247fa0",orange:"#f5bb62"};
let records = [];
let metadata = {};
let meshData = null;
let assemblyRecords = [];
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
 setupNavigation();
 const reloadButton=$("reloadEvidence");
 if(reloadButton)reloadButton.addEventListener("click",async()=>{reloadButton.disabled=true;reloadButton.textContent="↻ Reloading…";meshData=null;await initMesh();reloadButton.disabled=false;reloadButton.textContent="↻ Reload spatial tally";});
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
  await initAssembly();
  await initMesh();
 }catch(error){
  showError("Could not load recorded evidence: "+error.message+". Start the local Python server from the repository root and check the source CSV path.");
  $("layoutView").innerHTML='<div class="loading">Evidence unavailable — no scientific values are fabricated.</div>';
  $("sourcePath").textContent="API unavailable";
  await initAssembly();
  await initMesh();
 }
}
document.addEventListener("DOMContentLoaded",init);
function setupNavigation(){
 const sidebar=document.querySelector(".sidebar");
 const toggle=$("navToggle");
 if(toggle&&sidebar)toggle.addEventListener("click",()=>{const open=sidebar.classList.toggle("nav-open");toggle.setAttribute("aria-expanded",String(open));});
 document.querySelectorAll(".nav-item[data-target]").forEach(link=>link.addEventListener("click",event=>{
  const target=$(link.dataset.target);if(!target)return;event.preventDefault();
  target.scrollIntoView({behavior:"smooth",block:"start"});history.replaceState(null,"","#"+link.dataset.target);
  document.querySelectorAll(".nav-item").forEach(item=>item.classList.toggle("active",item===link));
  if(sidebar&&window.matchMedia("(max-width: 680px)").matches){sidebar.classList.remove("nav-open");if(toggle)toggle.setAttribute("aria-expanded","false");}
 }));
 const sections=[...document.querySelectorAll(".section[id]")];
 if("IntersectionObserver" in window){const observer=new IntersectionObserver(entries=>{const visible=entries.filter(e=>e.isIntersecting).sort((a,b)=>b.intersectionRatio-a.intersectionRatio)[0];if(!visible)return;document.querySelectorAll(".nav-item").forEach(item=>item.classList.toggle("active",item.dataset.target===visible.target.id));},{rootMargin:"-15% 0px -65% 0px",threshold:[0,.2,.5]});sections.forEach(s=>observer.observe(s));}
}

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
 const paletteName=$("meshPalette").value;
 const z=f.values, raw=f.view==="relative_sd"?f.relative:f.mean;
 const xs=Array.from({length:f.item.dimensions[0]},(_,i)=>i),ys=Array.from({length:f.item.dimensions[1]},(_,i)=>i);
 const hover=(title)=>"x-bin %{x}<br>y-bin %{y}<br>"+title+" %{customdata:.6g}<extra></extra>";
 chart("meshHeatmap",[{type:"heatmap",x:xs,y:ys,z:z,customdata:raw,colorscale:f.view==="relative_sd"?"Magma":paletteName,colorbar:{title:{text:f.colorTitle,font:{size:10}}},hovertemplate:hover(f.colorTitle),connectgaps:false}],{margin:{l:50,r:25,t:10,b:45},xaxis:{...baseLayout.xaxis,title:"Mesh x-bin index"},yaxis:{...baseLayout.yaxis,title:"Mesh y-bin index",autorange:"reversed"},showlegend:false});
 chart("meshContour",[{type:"contour",x:xs,y:ys,z:z,customdata:raw,colorscale:f.view==="relative_sd"?"Magma":paletteName,contours:{coloring:"heatmap",showlines:true},colorbar:{title:{text:f.colorTitle,font:{size:10}}},hovertemplate:hover(f.colorTitle),connectgaps:false,ncontours:14}],{margin:{l:50,r:25,t:10,b:45},xaxis:{...baseLayout.xaxis,title:"Mesh x-bin index"},yaxis:{...baseLayout.yaxis,title:"Mesh y-bin index",autorange:"reversed"},showlegend:false});
 chart("meshSurface",[{type:"surface",x:xs,y:ys,z:z, surfacecolor:z,colorscale:f.view==="relative_sd"?"Magma":paletteName,colorbar:{title:{text:f.colorTitle,font:{size:10}}},hovertemplate:"x-bin %{x}<br>y-bin %{y}<br>Displayed value %{z:.6g}<extra></extra>",connectgaps:false,showscale:true}],{margin:{l:5,r:5,t:5,b:5},scene:{xaxis:{title:"X bin",gridcolor:palette.line,color:palette.muted},yaxis:{title:"Y bin",gridcolor:palette.line,color:palette.muted},zaxis:{title:f.colorTitle,gridcolor:palette.line,color:palette.muted},bgcolor:"rgba(0,0,0,0)",camera:{eye:{x:1.55,y:1.55,z:1.1}}}});
 const cy=Math.floor(f.mean.length/2), profileY=f.mean[cy]||[], profileSD=f.sd[cy]||[], profile=profileY.map((v,i)=>({x:i,y:f.view==="relative_sd"&&v>0?100*profileSD[i]/v:(f.view==="mean"&&scale==="log"&&v>0?Math.log10(v):v)}));
 chart("meshProfile",[{type:"scatter",mode:"lines+markers",name:f.colorTitle,x:profile.map(p=>p.x),y:profile.map(p=>p.y),line:{color:palette.cyan,width:2},marker:{size:4,color:palette.orange},connectgaps:false,hovertemplate:"x-bin %{x}<br>"+f.colorTitle+" %{y:.6g}<extra></extra>"}],{margin:{l:60,r:20,t:15,b:50},showlegend:false,xaxis:{...baseLayout.xaxis,title:"X mesh-bin index"},yaxis:{...baseLayout.yaxis,title:f.colorTitle}});
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

/* Assembly-level fission proxy: use the repository's explicit four-position records. */
async function initAssembly(){
 try{
  const response=await fetch("/api/assembly",{headers:{Accept:"application/json"}});
  if(!response.ok)throw new Error("HTTP "+response.status);
  const payload=await response.json();assemblyRecords=payload.records||[];
  if(!assemblyRecords.length)throw new Error("No assembly fission proxy records found.");
  const select=$("assemblyCandidate");
  select.innerHTML=assemblyRecords.map((r,i)=>'<option value="'+i+'">'+r.candidate_id+' · '+r.layout_signature+'</option>').join("");
  select.addEventListener("change",drawAssembly);
  drawAssembly();
 }catch(error){
  $("assemblyMap").innerHTML='<div class="loading">Assembly map unavailable: '+error.message+'</div>';
  $("assemblyBar").innerHTML='<div class="loading">No recorded assembly values displayed.</div>';
  $("assemblyCaption").textContent="Source: results/c5g7_assembly_fission_proxy_smoke_2026-10-11.csv";
 }
}
function drawAssembly(){
 const i=Number($("assemblyCandidate").value),r=assemblyRecords[i];if(!r)return;
 const positions=["p00","p01","p10","p11"],vals=positions.map(p=>Number(r[p+"_fission_rate"]));
 const materials=String(r.layout_signature).split("").map(c=>c==="M"?"MOX":"UO₂");
 const grid=[[vals[0],vals[1]],[vals[2],vals[3]]];
 const materialGrid=[[materials[0],materials[1]],[materials[2],materials[3]]];
 chart("assemblyMap",[{type:"heatmap",x:["Left","Right"],y:["Top","Bottom"],z:grid,customdata:materialGrid,colorscale:"Viridis",showscale:true,colorbar:{title:{text:"Fission-rate proxy",font:{size:10}}},text:grid.map((row,y)=>row.map((v,x)=>materialGrid[y][x]+"<br>"+positions[y*2+x]+"<br>"+v.toExponential(3))),texttemplate:"%{customdata}<br>%{z:.3g}",textfont:{color:"#ffffff",size:13},hovertemplate:"Position %{x}, %{y}<br>Material %{customdata}<br>Fission-rate proxy %{z:.6g}<extra></extra>"}],{margin:{l:55,r:25,t:12,b:45},xaxis:{...baseLayout.xaxis,title:"Assembly column"},yaxis:{...baseLayout.yaxis,title:"Assembly row",autorange:"reversed"},showlegend:false});
 chart("assemblyBar",[{type:"bar",x:positions,y:vals,marker:{color:materials.map(m=>m==="MOX"?palette.orange:palette.cyan),line:{color:"#e8f1f7",width:1}},customdata:materials,hovertemplate:"%{x} · %{customdata}<br>Proxy %{y:.7g}<extra></extra>",text:vals.map(v=>v.toExponential(2)),textposition:"outside"}],{margin:{l:55,r:20,t:25,b:45},xaxis:{...baseLayout.xaxis,title:"Assembly position"},yaxis:{...baseLayout.yaxis,title:"Integrated fission-rate proxy"},showlegend:false});
 $("assemblyCaption").textContent=r.candidate_id+" · layout "+r.layout_signature+" · seed "+r.seed+" · keff "+Number(r.keff_mean).toFixed(6)+" ± "+Number(r.keff_std_dev).toExponential(2)+" · status: "+r.status;
}
