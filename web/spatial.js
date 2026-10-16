(function(){
"use strict";
const $=(id)=>document.getElementById(id);
const palette={text:"#e6eef5",muted:"#91a5b6",line:"#203547",cyan:"#56dbe4",orange:"#f0bc67"};
const baseLayout={paper_bgcolor:"rgba(0,0,0,0)",plot_bgcolor:"rgba(0,0,0,0)",font:{family:"Manrope, sans-serif",color:palette.muted,size:10},margin:{l:55,r:18,t:15,b:55},xaxis:{gridcolor:"#1b3445",linecolor:palette.line,zerolinecolor:palette.line},yaxis:{gridcolor:"#1b3445",linecolor:palette.line,zerolinecolor:palette.line},hoverlabel:{bgcolor:"#102536",bordercolor:palette.line,font:{color:palette.text}}};
const config={displaylogo:false,responsive:true,modeBarButtonsToRemove:["lasso2d","select2d"],toImageButtonOptions:{format:"png",scale:2}};
let meshData=null;
let controlsBound=false;
let meshReloadBound=false;
function chart(id,traces,layout={}){
 const el=$(id);if(!el)return;
 if(!window.Plotly){el.innerHTML='<div class="empty-state"><b>Plotting engine unavailable</b><p>Plotly.js did not load. Check network access, then reload this page.</p></div>';return;}
 try{Promise.resolve(window.Plotly.react(el,traces,{...baseLayout,...layout},config)).catch(error=>{el.innerHTML='<div class="empty-state"><b>Chart render failed</b><p>'+escapeHtml(error?.message||error)+'</p></div>';});}
 catch(error){el.innerHTML='<div class="empty-state"><b>Chart render failed</b><p>'+escapeHtml(error?.message||error)+'</p></div>';}
}
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
  const scoreSelect=$("meshScore");const previousScore=scoreSelect.value;const availableScores=Object.keys(item.scores);scoreSelect.innerHTML=availableScores.map(k=>'<option value="'+k+'">'+k+'</option>').join("");if(availableScores.includes(previousScore))scoreSelect.value=previousScore;
  if(!controlsBound){["meshScore","meshView","meshScale","meshPalette"].forEach(id=>{const node=$(id);if(node)node.addEventListener("change",drawMesh);});controlsBound=true;}
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
async function bootSpatial(){
 if($("reloadEvidence")&&!meshReloadBound){
  $("reloadEvidence").addEventListener("click",async()=>{$("reloadEvidence").disabled=true;const old=$("reloadEvidence").textContent;$("reloadEvidence").textContent="↻ Reloading…";await initMesh();$("reloadEvidence").disabled=false;$("reloadEvidence").textContent=old||"↻ Reload spatial tally";});
  meshReloadBound=true;
 }
 ["meshScore","meshView","meshScale","meshPalette"].forEach(id=>{if($(id))$(id).disabled=false;});
 await Promise.all([loadGeometryArtifacts(),initMesh()]);
}
document.addEventListener("DOMContentLoaded",bootSpatial);
window.addEventListener("resize",()=>{if(window.Plotly)document.querySelectorAll(".js-spatial-plot").forEach(node=>{try{window.Plotly.Plots.resize(node);}catch(_){}});});
})();