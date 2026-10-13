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
// Pin-universe maps extracted from the archived candidate geometry.xml files (17 × 17 lattices).
// Universe IDs 1–6 map to UO2, three MOX enrichments, fission chamber, and guide tube;
// each pin's surrounding region is the water moderator defined in geometry.xml.
const pinLattices={
 U:[
 "11111111111111111","11111111111111111","11111611611611111",
 "11161111111116111","11111111111111111","11611611611611611",
 "11111111111111111","11111111111111111","11611611511611611",
 "11111111111111111","11111111111111111","11611611611611611",
 "11111111111111111","11161111111116111","11111611611611111",
 "11111111111111111","11111111111111111"
 ],
 M:[
 "22222222222222222","23333333333333332","23333633633633332",
 "23363444444436332","23334444444443332","23644644644644632",
 "23344444444444332","23344444444444332","23644644544644632",
 "23344444444444332","23344444444444332","23644644644644632",
 "23334444444443332","23363444444436332","23333633633633332",
 "23333333333333332","22222222222222222"
 ]
};
const pinMaterials={
 "1":{name:"UO₂ fuel",color:"#51d2df"},
 "2":{name:"MOX 4.3%",color:"#f4bd62"},
 "3":{name:"MOX 7.0%",color:"#f08f62"},
 "4":{name:"MOX 8.7%",color:"#dc6f91"},
 "5":{name:"Fission chamber",color:"#c1b3ff"},
 "6":{name:"Guide tube",color:"#9cb6c8"}
};
let geometryArtifactActive=false;
function drawSelectedCandidate(row){
 const signature=String(row.layout_signature??"").trim().toUpperCase();
 const tag=$("selectedRecordTag");
 if(tag){
  const canonical=String(row.canonical_reference).toLowerCase()==="true";
  tag.textContent=canonical?"CANONICAL LAYOUT REFERENCE":"LAYOUT VARIANT";
  tag.classList.toggle("warning",!canonical);
 }
 $("selectedCandidateId").textContent=String(row.candidate_id??"Candidate not identified");
 $("selectedCandidateMetaLine").textContent="Layout "+(signature||"not recorded")+" · "+(has(row,"descriptive_keff_order")?"descriptive k-effective order "+row.descriptive_keff_order+" / "+records.length:"order not recorded");
 $("selectedCandidateSignature").innerHTML=/^[UM]{4}$/.test(signature)?signature.split("").map((code,i)=>'<div class="signature-cell '+(code==="M"?"signature-mox":"signature-uo2")+'"><b>'+code+'</b><small>'+["p00","p01","p10","p11"][i]+'</small></div>').join(""):'<span class="muted">No validated layout signature</span>';
 const metrics=[
  ["k-effective mean",has(row,"keff_mean")?number(row.keff_mean,6):"Not recorded","keff"],
  ["Reported SD",has(row,"keff_std_dev")?number(row.keff_std_dev,6):"Not recorded","sd"],
  ["Relative SD",has(row,"keff_relative_sd_percent")?number(row.keff_relative_sd_percent,4)+"%":"Not recorded","uncertainty"],
  ["Aggregate fission score",has(row,"aggregate_fission_score")?number(row.aggregate_fission_score,5):"Not recorded","proxy"]
 ];
 $("selectedCandidateMetrics").innerHTML=metrics.map(([name,value,type])=>'<div class="candidate-stat candidate-stat-'+type+'"><span>'+name+'</span><strong>'+value+'</strong></div>').join("");
 const runInfo=[
  ["SEED",row.seed??"Not recorded"],
  ["BATCHES",row.batches??"Not recorded"],
  ["INACTIVE",row.inactive??"Not recorded"],
  ["PARTICLES / BATCH",row.particles_per_batch??"Not recorded"]
 ];
 $("selectedCandidateRunInfo").innerHTML=runInfo.map(([name,value])=>'<div class="run-meta"><span>'+name+'</span><b>'+escapeHtml(value)+'</b></div>').join("");
 const unchanged=has(row,"mutated_preexisting_file_count")&&Number(row.mutated_preexisting_file_count)===0;
 const mgxsStable=row.mgxs_sha256_before_transport&&row.mgxs_sha256_before_transport===row.mgxs_sha256_after_transport;
 $("selectedCandidateChecks").innerHTML='<span class="micro-check '+(unchanged?"ok":"")+'"><i></i>'+(unchanged?"No pre-existing file mutation recorded":"Mutation check unavailable")+'</span><span class="micro-check '+(mgxsStable?"ok":"")+'"><i></i>'+(mgxsStable?"MGXS hash unchanged across recorded run":"MGXS hash comparison unavailable")+'</span>';
}
function materialCellSvg(code,x,y,pitch){
 const material=pinMaterials[code];
 const cx=x+pitch/2,cy=y+pitch/2,r=pitch*(0.54/1.26);
 const square='<rect x="'+x.toFixed(2)+'" y="'+y.toFixed(2)+'" width="'+pitch.toFixed(2)+'" height="'+pitch.toFixed(2)+'" fill="#123749" stroke="#285064" stroke-width=".38"/>';
 return square+'<circle cx="'+cx.toFixed(2)+'" cy="'+cy.toFixed(2)+'" r="'+r.toFixed(2)+'" fill="'+material.color+'" stroke="#06111a" stroke-width=".45"><title>'+material.name+' · moderator outside the 0.54 cm pin cylinder</title></circle>';
}
function renderModelGeometrySvg(signature){
 const sig=String(signature??"").trim().toUpperCase();
 if(!/^[UM]{4}$/.test(sig))return '<div class="empty-state"><b>Model geometry unavailable</b><p>The selected record does not contain a valid four-position U/M signature. No default configuration is substituted.</p></div>';
 const width=1020,height=670,x0=48,y0=92,size=170,gap=1,pinInsetX=9,pinInsetY=29,pinArea=152,pinPitch=pinArea/17,coreWidth=size*3+gap*2;
 const cells=[sig[0],sig[1],"R",sig[2],sig[3],"R","R","R","R"];
 let svg='<svg class="model-geometry-svg" viewBox="0 0 '+width+' '+height+'" role="img" aria-label="C5G7 2D material-resolved 3 by 3 lattice for selected layout '+sig+'">';
 svg+='<defs><linearGradient id="reflectorFill" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#13394b"/><stop offset="100%" stop-color="#0b2637"/></linearGradient><pattern id="waterPattern" width="18" height="12" patternUnits="userSpaceOnUse"><path d="M0 6 Q4 2 9 6 T18 6" fill="none" stroke="#2a637a" stroke-width="1" opacity=".5"/></pattern></defs>';
 svg+='<text x="'+x0+'" y="28" class="svg-kicker">ARCHIVED OPENMC GEOMETRY.XML · 2D MATERIAL MAP</text><text x="'+x0+'" y="52" class="svg-title">C5G7 · 2 × 2 fuel block + L-shaped water reflector</text>';
 svg+='<text x="'+x0+'" y="72" class="svg-subtitle">Layout '+sig+' · model extent 64.26 × 64.26 cm · assembly pitch 21.42 cm</text>';
 svg+='<text x="'+(x0+coreWidth/2)+'" y="'+(y0-11)+'" class="boundary-label boundary-reflective" text-anchor="middle">Y MAX · REFLECTIVE</text>';
 svg+='<text x="'+(x0+coreWidth/2)+'" y="'+(y0+coreWidth+22)+'" class="boundary-label boundary-vacuum" text-anchor="middle">Y MIN · VACUUM</text>';
 svg+='<text x="'+(x0-18)+'" y="'+(y0+coreWidth/2)+'" class="boundary-label boundary-reflective" text-anchor="middle" transform="rotate(-90 '+(x0-18)+' '+(y0+coreWidth/2)+')">X MIN · REFLECTIVE</text>';
 svg+='<text x="'+(x0+coreWidth+17)+'" y="'+(y0+coreWidth/2)+'" class="boundary-label boundary-vacuum" text-anchor="middle" transform="rotate(90 '+(x0+coreWidth+17)+' '+(y0+coreWidth/2)+')">X MAX · VACUUM</text>';
 cells.forEach((code,i)=>{
  const r=Math.floor(i/3),c=i%3,x=x0+c*(size+gap),y=y0+r*(size+gap);
  if(code==="R"){
   svg+='<g><rect x="'+x+'" y="'+y+'" width="'+size+'" height="'+size+'" rx="7" fill="url(#reflectorFill)" stroke="#3b7184" stroke-width="1.2"/><rect x="'+x+'" y="'+y+'" width="'+size+'" height="'+size+'" rx="7" fill="url(#waterPattern)" opacity=".9"/><text x="'+(x+size/2)+'" y="'+(y+size/2-5)+'" class="reflector-title" text-anchor="middle">WATER</text><text x="'+(x+size/2)+'" y="'+(y+size/2+14)+'" class="reflector-title" text-anchor="middle">REFLECTOR</text><text x="'+(x+size/2)+'" y="'+(y+size/2+34)+'" class="reflector-sub" text-anchor="middle">21.42 cm pitch</text></g>';
  }else{
   const matrix=pinLattices[code],color=code==="M"?"#f4bd62":"#51d2df";
   svg+='<g><rect x="'+x+'" y="'+y+'" width="'+size+'" height="'+size+'" rx="7" fill="#0a1a27" stroke="'+color+'" stroke-opacity=".72" stroke-width="1.3"/><rect x="'+(x+1)+'" y="'+(y+1)+'" width="'+(size-2)+'" height="24" rx="5" fill="'+color+'" fill-opacity=".12"/><text x="'+(x+8)+'" y="'+(y+16)+'" class="assembly-label" fill="'+color+'">'+(["p00","p01","p10","p11"][i===0?0:i===1?1:i===3?2:3])+' · '+(code==="M"?"MOX":"UO₂")+'</text>';
   const ix=x+pinInsetX,iy=y+pinInsetY;
   matrix.forEach((line,rr)=>{for(let cc=0;cc<17;cc++){svg+=materialCellSvg(line[cc],ix+cc*pinPitch,iy+rr*pinPitch,pinPitch);}});
   svg+='<rect x="'+(ix-.6)+'" y="'+(iy-.6)+'" width="'+(pinArea+1.2)+'" height="'+(pinArea+1.2)+'" fill="none" stroke="#64899a" stroke-width=".7"/><text x="'+(x+size-8)+'" y="'+(y+16)+'" class="assembly-size" text-anchor="end">17 × 17</text></g>';
  }
 });
 const lx=624,ly=104;
 svg+='<line x1="605" y1="82" x2="605" y2="592" stroke="#29475a" stroke-width="1"/><text x="'+lx+'" y="'+ly+'" class="legend-title">MATERIAL REGIONS</text>';
 const legend=[
  ["square","#123749","Moderator · water around pin"],
  ["circle",pinMaterials["1"].color,pinMaterials["1"].name],
  ["circle",pinMaterials["2"].color,pinMaterials["2"].name],
  ["circle",pinMaterials["3"].color,pinMaterials["3"].name],
  ["circle",pinMaterials["4"].color,pinMaterials["4"].name],
  ["circle",pinMaterials["5"].color,pinMaterials["5"].name],
  ["circle",pinMaterials["6"].color,pinMaterials["6"].name],
  ["square","#1b5268","Reflector · water"]
 ];
 legend.forEach((item,i)=>{
  const y=ly+27+i*29;
  if(item[0]==="circle")svg+='<circle cx="'+(lx+7)+'" cy="'+(y-4)+'" r="5.2" fill="'+item[1]+'" stroke="#b8d4df" stroke-opacity=".4"/>';
  else svg+='<rect x="'+(lx+1)+'" y="'+(y-10)+'" width="12" height="12" rx="2" fill="'+item[1]+'" stroke="#517386" stroke-width=".6"/>';
  svg+='<text x="'+(lx+22)+'" y="'+y+'" class="legend-text">'+item[2]+'</text>';
 });
 const my=ly+285;
 svg+='<line x1="'+lx+'" y1="'+(my-18)+'" x2="968" y2="'+(my-18)+'" stroke="#29475a"/><text x="'+lx+'" y="'+my+'" class="legend-title">MODEL PARAMETERS</text>';
 [
  ["Model","OECD/NEA C5G7 · 2D"],
  ["Core lattice","3 × 3 assembly sites"],
  ["Fuel assemblies","2 × 2 · selected layout"],
  ["Pin lattice","17 × 17 per fuel assembly"],
  ["Pin pitch / radius","1.26 cm / 0.54 cm"],
  ["Recorded boundary","Reflective left/top · vacuum right/bottom"]
 ].forEach((entry,i)=>{
  const y=my+28+i*25;
  svg+='<text x="'+lx+'" y="'+y+'" class="meta-label">'+entry[0]+'</text><text x="'+lx+'" y="'+(y+13)+'" class="meta-value">'+entry[1]+'</text>';
 });
 svg+='<rect x="'+lx+'" y="'+(my+194)+'" width="334" height="43" rx="7" fill="#102638" stroke="#2a4b5e"/><text x="'+(lx+12)+'" y="'+(my+211)+'" class="source-note">XML-DERIVED · MATERIAL / LATTICE VIEW</text><text x="'+(lx+12)+'" y="'+(my+227)+'" class="source-note-secondary">Visual renderer only · no transport calculation executed</text>';
 svg+='</svg>';
 return svg;
}
function drawModelGeometry(row){
 const preview=$("geometryPreview");
 if(!preview||!row)return;
 if(geometryArtifactActive)return;
 const signature=String(row.layout_signature??"").trim().toUpperCase();
 preview.innerHTML=renderModelGeometrySvg(signature);
 $("geometryCaption").textContent="Archived Actions artifact c5g7-study-640000 · "+String(row.candidate_id??"candidate")+" · layout "+signature+" · lattice/material map reconstructed from geometry.xml definitions; not an OpenMC transport result.";
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
 drawSelectedCandidate(row);
 geometryArtifactActive=false;
 drawModelGeometry(row);
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
  const list=$("geometryArtifactList");
  if(!items.length){
   $("geometryStatus").textContent="XML VIEW READY · NO PLOT FILE";
   $("geometryStatus").classList.remove("warning");
   $("geometryProvenance").textContent="The candidate-linked material map is reconstructed from archived OpenMC geometry.xml lattice/material definitions. No separate native PNG/VTK/VTI plot is checked into scanned output folders.";
   list.innerHTML='<div class="empty-state"><b>No separate OpenMC plot artifact found</b><p>The main panel still renders the archived model lattice and pin-material regions for the selected candidate.</p><p>Native PNG/VTK/VTI artifacts can be inspected here when present.</p></div>';
   geometryArtifactActive=false;
   const selected=records.find(r=>String(r.candidate_id)===$("candidateSelect")?.value);
   drawModelGeometry(selected);
   return;
  }
  $("geometryStatus").textContent=items.length+" EXTERNAL ARTIFACT(S) FOUND";
  $("geometryStatus").classList.remove("warning");
  $("geometryProvenance").textContent="Found "+items.length+" existing geometry file(s). The candidate-linked XML material map remains primary; select an item below to inspect a separate native artifact.";
  list.innerHTML=items.map((item,i)=>'<button class="artifact-item" type="button" data-artifact-index="'+i+'"><span class="artifact-icon">'+(item.kind==="image"?"IMG":"3D")+'</span><span class="artifact-meta"><b>'+escapeHtml(item.name)+'</b><small>'+escapeHtml(item.path)+' · '+item.format+' · '+formatBytes(item.size_bytes)+'</small></span><span class="tag">'+item.kind.toUpperCase()+'</span></button>').join("");
  list.querySelectorAll("[data-artifact-index]").forEach(button=>button.addEventListener("click",()=>showGeometryArtifact(items[Number(button.dataset.artifactIndex)])));
  geometryArtifactActive=false;
  const selected=records.find(r=>String(r.candidate_id)===$("candidateSelect")?.value);
  drawModelGeometry(selected);
 }catch(error){
  $("geometryStatus").textContent="ARTIFACT SCAN FAILED";$("geometryStatus").classList.add("warning");
  $("geometryProvenance").textContent="Could not inspect geometry outputs: "+error.message;
  $("geometryArtifactList").innerHTML='<div class="loading">Artifact inventory unavailable.</div>';
 }
}
function showGeometryArtifact(item){
 if(!item)return;
 geometryArtifactActive=true;
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
 const selectedAssemblyIndex=candidates.findIndex(r=>String(r.candidate_id)===String(selectedId));
 chart("assemblyBar",keys.map(([key,name],i)=>({type:"bar",name,x:candidates.map(r=>String(r.candidate_id)),y:candidates.map(r=>Number(r[key])),marker:{color:candidates.map(r=>String(r.candidate_id)===String(selectedId)?palette.cyan:[palette.blue,palette.orange,"#8d9ee8","#5f9d86"][i]),line:{color:candidates.map(r=>String(r.candidate_id)===String(selectedId)?"#e8f1f7":"rgba(0,0,0,0)"),width:candidates.map(r=>String(r.candidate_id)===String(selectedId)?1.5:0)}},hovertemplate:"Candidate %{x}<br>Position "+name+"<br>Proxy %{y:.6g}<extra></extra>"})),{barmode:"group",margin:{l:60,r:15,t:35,b:80},legend:{orientation:"h",y:1.15,x:0},xaxis:{...baseLayout.xaxis,title:"Candidate ID"},yaxis:{...baseLayout.yaxis,title:"Recorded fission-rate proxy (units as source)"},shapes:selectedAssemblyIndex>=0?[{type:"rect",xref:"x",yref:"paper",x0:selectedAssemblyIndex-0.5,x1:selectedAssemblyIndex+0.5,y0:0,y1:1,line:{color:"rgba(85,212,223,0.65)",width:1},fillcolor:"rgba(85,212,223,0.08)"}]:[]});
}
