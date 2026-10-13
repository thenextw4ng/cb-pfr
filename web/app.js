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
  const raw=String(signature??"").trim().toUpperCase();
  if(!/^[UM]{4}$/.test(raw)){
    return '<div class="empty-state"><b>Placement unavailable</b><p>The selected candidate does not contain a validated four-position U/M signature. No default arrangement is substituted.</p></div>';
  }
  const cells=raw.split("");
  const positions=["p00","p01","p10","p11"];
  return '<div class="assembly-grid">'+cells.map((c,i)=>'<div class="assembly '+(c==="M"?"mox-cell":"")+'">'+(c==="M"?"MOX":"UO₂")+'<small>'+positions[i]+' · '+(i+1)+'</small></div>').join("")+'</div>';
}
const baseLayout={paper_bgcolor:"rgba(0,0,0,0)",plot_bgcolor:"rgba(0,0,0,0)",font:{family:"Manrope, sans-serif",color:palette.muted,size:10},margin:{l:55,r:18,t:15,b:65},xaxis:{gridcolor:"#1e3545",linecolor:palette.line,tickangle:-28},yaxis:{gridcolor:"#1e3545",linecolor:palette.line,zerolinecolor:palette.line},hoverlabel:{bgcolor:"#102536",bordercolor:palette.line,font:{color:palette.text}}};
const config={displaylogo:false,responsive:true,modeBarButtonsToRemove:["lasso2d","select2d"]};
function chart(id,traces,layout={}){
 const el=$(id);if(!el)return;
 if(!window.Plotly){el.innerHTML='<div class="empty-state"><b>Plotting engine unavailable</b><p>Plotly.js could not be loaded. Check network access to the chart CDN, then reload the page.</p></div>';return;}
 try{
  Promise.resolve(Plotly.react(el,traces,{...baseLayout,...layout},config)).catch(error=>{
   const msg=String(error?.message||error).replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
   el.innerHTML='<div class="empty-state"><b>Chart render failed</b><p>'+msg+'</p></div>';
  });
 }catch(error){el.innerHTML='<div class="empty-state"><b>Chart render failed</b><p>'+String(error.message||error)+'</p></div>';}
}
function showCandidate(){
 const id=$("candidateSelect").value,row=records.find(r=>String(r.candidate_id)===id);if(!row)return;
 $("layoutView").innerHTML=layoutCells(row.layout_signature);
 $("layoutCaption").textContent=label(row)+" · seed "+(row.seed??"not recorded")+" · signature "+(row.layout_signature??"not recorded");
 drawCandidateChart();
 drawAssemblyField();
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
  await initGeometry();
  await initMesh();
 }catch(error){
  showError("Could not load recorded evidence: "+error.message+". Start the local Python server from the repository root and check the source CSV path.");
  $("layoutView").innerHTML='<div class="loading">Evidence unavailable — no scientific values are fabricated.</div>';
  $("sourcePath").textContent="API unavailable";
  await initGeometry();
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
 const scale=$("meshScale").value;
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
  ["meshHeatmap","meshContour","meshProfile","meshSurface"].forEach(id=>$(id).innerHTML='<div class="empty-state"><b>Spatial data unavailable</b><p>'+String(error.message||error)+'</p><p>No scientific values have been fabricated.</p></div>');
 }
}

/* Displays existing external geometry artifacts only; never synthesizes a reactor layout. */
async function initGeometry(){
 const refresh=$("reloadGeometry");
 if(refresh)refresh.addEventListener("click",async()=>{refresh.disabled=true;refresh.textContent="↻ Scanning…";await loadGeometryArtifacts();refresh.disabled=false;refresh.textContent="↻ Refresh artifacts";});
 await loadGeometryArtifacts();
}
async function loadGeometryArtifacts(){
 try{
  const response=await fetch("/api/geometry-artifacts",{headers:{Accept:"application/json"}});
  if(!response.ok)throw new Error("HTTP "+response.status);
  const payload=await response.json(),items=payload.artifacts||[];
  $("geometryStatus").textContent=items.length?items.length+" ARTIFACT(S) FOUND":"NO GEOMETRY ARTIFACTS";
  $("geometryStatus").classList.toggle("warning",!items.length);
  $("geometryProvenance").textContent=items.length?"Found "+items.length+" existing file(s) in repository output folders. Preview uses original files; no geometry is inferred.":"No supported geometry visualization files were found in approved output folders. Generate them from the actual OpenMC model inputs, then refresh.";
  const list=$("geometryArtifactList");
  if(!items.length){
   list.innerHTML='<div class="empty-state"><b>No external geometry output found</b><p>Expected OpenMC-generated PNG slice/raytrace plots or VTK/VTI datasets in plots/, plot/, geometry/, model/, c5g7-run/, evidence/, results/, or artifacts/.</p><p>The dashboard deliberately does not replace missing files with a fabricated assembly diagram.</p></div>';
   $("geometryPreview").innerHTML='<div class="empty-state"><b>Geometry preview unavailable</b><p>Generate a plot from the validated OpenMC model inputs and click Refresh artifacts.</p><p><a href="https://docs.openmc.org/en/latest/usersguide/plots.html" target="_blank" rel="noreferrer">OpenMC geometry plotting documentation ↗</a></p></div>';
   $("geometryCaption").textContent="No external geometry artifact selected.";return;
  }
  list.innerHTML=items.map((item,i)=>'<button class="artifact-item" type="button" data-artifact-index="'+i+'"><span class="artifact-icon">'+(item.kind==="image"?"IMG":"3D")+'</span><span class="artifact-meta"><b>'+escapeHtml(item.name)+'</b><small>'+escapeHtml(item.path)+' · '+item.format+' · '+formatBytes(item.size_bytes)+'</small></span><span class="tag">'+item.kind.toUpperCase()+'</span></button>').join("");
  list.querySelectorAll("[data-artifact-index]").forEach(button=>button.addEventListener("click",()=>showGeometryArtifact(items[Number(button.dataset.artifactIndex)])));
  showGeometryArtifact(items.find(item=>item.kind==="image")||items[0]);
 }catch(error){
  $("geometryStatus").textContent="ARTIFACT SCAN FAILED";$("geometryStatus").classList.add("warning");
  $("geometryProvenance").textContent="Could not inspect geometry outputs: "+error.message;
  $("geometryArtifactList").innerHTML='<div class="loading">Artifact inventory unavailable.</div>';
 }
}
function showGeometryArtifact(item){
 if(!item)return;
 document.querySelectorAll(".artifact-item").forEach(el=>el.classList.remove("active"));
 // Mark the selected source by matching its path text, avoiding assumptions about array order after refresh.
 document.querySelectorAll(".artifact-item").forEach(el=>{if(el.textContent.includes(item.name))el.classList.add("active");});
 const preview=$("geometryPreview");
 if(item.kind==="image")preview.innerHTML='<img class="external-geometry-image" src="'+item.url+'" alt="External scientific geometry artifact: '+escapeHtml(item.name)+'" loading="lazy">';
 else preview.innerHTML='<div class="empty-state"><b>3D dataset detected: '+escapeHtml(item.format)+'</b><p>This is an externally generated 3D dataset, not a browser-native image preview.</p><p>Open it in ParaView or ParaView Glance to inspect the actual geometry and fields.</p><a href="'+item.url+'" target="_blank" rel="noreferrer">Open/download source dataset ↗</a> · <a href="https://www.paraview.org/" target="_blank" rel="noreferrer">ParaView ↗</a></div>';
 $("geometryCaption").textContent=item.path+" · "+item.format+" · "+formatBytes(item.size_bytes)+" · existing external-tool output";
}
function escapeHtml(value){return String(value).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function formatBytes(bytes){if(bytes<1024)return bytes+" B";if(bytes<1048576)return (bytes/1024).toFixed(1)+" KB";return (bytes/1048576).toFixed(2)+" MB";}


/* Assembly-integrated fission-rate proxy: direct CSV evidence, never interpreted as absolute power. */
async function initAssembly(){
 try{
  const response=await fetch("/api/assembly",{headers:{Accept:"application/json"}});
  if(!response.ok){let detail="HTTP "+response.status;try{detail=(await response.json()).error||detail}catch(_){}throw new Error(detail)}
  const payload=await response.json();
  assemblyRecords=(payload.records||[]).filter(r=>["p00_fission_rate","p01_fission_rate","p10_fission_rate","p11_fission_rate"].every(k=>Number.isFinite(Number(r[k]))));
  if(!assemblyRecords.length)throw new Error("No complete 2×2 assembly proxy records.");
  $("assemblyFieldStatus").textContent="RECORDED PROXY DATA";
  $("assemblyFieldProvenance").textContent=payload.source+" · "+payload.status_scope+". Values are recorded assembly-integrated fission-rate proxies; they are not absolute power and do not establish feasibility. Proxy seeds are independent of the candidate-summary seeds; do not compare as paired runs.";
  drawAssemblyField();
 }catch(error){
  $("assemblyFieldStatus").textContent="ASSEMBLY DATA UNAVAILABLE";
  $("assemblyFieldStatus").classList.add("warning");
  $("assemblyFieldProvenance").textContent="Could not load assembly evidence: "+error.message;
  ["assemblyMap","assemblyBar"].forEach(id=>{if($(id))$(id).innerHTML='<div class="loading">No assembly values displayed; no data are fabricated.</div>';});
 }
}
function drawAssemblyField(){
 if(!assemblyRecords.length||!$("assemblyMap")||!$("assemblyBar"))return;
 const selectedId=$("candidateSelect")?.value;
 const selected=records.find(r=>String(r.candidate_id)===String(selectedId));
 const row=selected?assemblyRecords.find(r=>String(r.candidate_id)===String(selected.candidate_id)&&String(r.layout_signature).toUpperCase()===String(selected.layout_signature).toUpperCase()):null;
 if(!row){
  $("assemblyMap").innerHTML='<div class="empty-state"><b>No matching assembly evidence</b><p>The selected candidate has no matching 2 × 2 proxy record. Values are not borrowed from another candidate.</p></div>';
 } else {
 const positions=[["p00_fission_rate","p01_fission_rate"],["p10_fission_rate","p11_fission_rate"]];
 const z=positions.map(line=>line.map(key=>Number(row[key])));
 chart("assemblyMap",[{type:"heatmap",x:["Column 0","Column 1"],y:["Row 0","Row 1"],z,customdata:[["p00","p01"],["p10","p11"]],colorscale:"Cividis",colorbar:{title:{text:"Fission-rate proxy",font:{size:10}}},hovertemplate:"Position %{customdata}<br>Proxy %{z:.6g}<extra></extra>"}],{margin:{l:65,r:20,t:10,b:45},xaxis:{...baseLayout.xaxis,title:"Recorded position index"},yaxis:{...baseLayout.yaxis,title:"Recorded position index",autorange:"reversed"},showlegend:false});
 }
 const keys=[["p00_fission_rate","p00"],["p01_fission_rate","p01"],["p10_fission_rate","p10"],["p11_fission_rate","p11"]];
 const candidates=assemblyRecords;
 chart("assemblyBar",keys.map(([key,name],i)=>({type:"bar",name,x:candidates.map(r=>String(r.candidate_id)),y:candidates.map(r=>Number(r[key])),marker:{color:[palette.cyan,palette.blue,palette.orange,"#8d9ee8"][i]},hovertemplate:"Candidate %{x}<br>Position "+name+"<br>Proxy %{y:.6g}<extra></extra>"})),{barmode:"group",margin:{l:60,r:15,t:35,b:80},legend:{orientation:"h",y:1.15,x:0},xaxis:{...baseLayout.xaxis,title:"Candidate ID"},yaxis:{...baseLayout.yaxis,title:"Recorded fission-rate proxy (units as source)"},shapes:[{type:"rect",xref:"x",yref:"paper",x0:-0.5,x1:candidates.findIndex(r=>String(r.candidate_id)===String(selectedId))+0.5,y0:0,y1:1,line:{width:0},fillcolor:"rgba(85,212,223,0.07)"}]});
}
