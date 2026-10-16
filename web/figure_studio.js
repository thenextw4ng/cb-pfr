(function(){
  "use strict";
  const $=id=>document.getElementById(id);
  const C={ink:"#17212b",muted:"#435365",line:"#dce4eb",cyan:"#117f8d",blue:"#276fbf"};
  const OUT_W=2400,OUT_H=1600;
  let SNAPSHOT=null, activeBundle=null, previewUrls=[];
  const CATALOG=[
    ["candidateChart","Candidate metric by layout","Candidate campaign","Plotly"],
    ["distributionChart","Corrected-group k-effective","Candidate campaign","Plotly"],
    ["aggregateChart","k-effective vs F_fission proxy","Candidate campaign","Plotly"],
    ["assemblyMap","Assembly-integrated fission proxy map","Assembly proxy","Plotly"],
    ["assemblyMatrix","Candidate by assembly position","Assembly proxy","Plotly"],
    ["meshHeatmap","Recorded OpenMC planar heatmap","OpenMC 2D mesh","Plotly"],
    ["meshContour","Recorded OpenMC contour field","OpenMC 2D mesh","Plotly"],
    ["meshProfile","Recorded OpenMC line profile","OpenMC 2D mesh","Plotly"],
    ["meshSurface","Recorded 2D tally as a 3D surface","OpenMC 2D mesh","Plotly"],
    ["axial3dPlot","Recorded OpenMC axial volume","OpenMC 3D mesh","Plotly"],
    ["axialSectionPlot","Recorded OpenMC orthogonal slice","OpenMC 3D mesh","Plotly"],
    ["axialLineProfilePlot","Recorded OpenMC selectable line profile","OpenMC 3D mesh","Plotly"],
    ["cmpV2aFChart","C5G7 layout variability · F_fission / k-effective","C5G7 / OpenMC","Plotly"],
    ["cmpV2aKChart","C5G7 low-budget k-effective variability","C5G7 / OpenMC","Plotly"],
    ["cmpPolicyMatchChart","Equal-budget empirical-best match rate","C5G7 policy replay","Plotly"],
    ["cmpPolicyRegretChart","Equal-budget mean-regret difference","C5G7 policy replay","Plotly"],
    ["cmpT7Chart","T7 synthetic operating envelope","Paper synthetic","Plotly"],
    ["cmpT7bChart","T7b matched-feasibility difference","Paper synthetic","Plotly"],
    ["geometryPreview","Selected core geometry · source SVG","OpenMC-derived geometry","SVG"],
    ["core3dCanvas","Selected core geometry · Three.js canvas","OpenMC-derived geometry","Canvas"]
  ];
  const FIGURES=Object.fromEntries(CATALOG.map(x=>[x[0],{id:x[0],title:x[1],group:x[2],kind:x[3]}]));
  const plain=(value,seen=new WeakSet())=>{
    if(value===null||value===undefined||typeof value==="string"||typeof value==="boolean")return value??null;
    if(typeof value==="number")return Number.isFinite(value)?value:null;
    if(typeof value==="bigint")return String(value);
    if(typeof value!=="object")return String(value);
    if(ArrayBuffer.isView(value))return Array.from(value,v=>plain(v,seen));
    if(value instanceof Date)return value.toISOString();
    if(seen.has(value))return "[circular]";
    seen.add(value);
    let out;
    if(Array.isArray(value))out=value.map(v=>plain(v,seen));
    else{
      out={};
      for(const [key,item] of Object.entries(value)){
        if(key.startsWith("_")||["parent","node","el","element","gd","_fullLayout","_context"].includes(key))continue;
        if(typeof item==="function")continue;
        out[key]=plain(item,seen);
      }
    }
    seen.delete(value);
    return out;
  };
  const safe=v=>String(v??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const slug=v=>String(v||"figure").toLowerCase().normalize("NFKD").replace(/[^a-z0-9]+/g,"-").replace(/^-|-$/g,"").slice(0,90)||"figure";
  const serial=value=>JSON.stringify(plain(value));
  const selectedText=id=>$(id)?.selectedOptions?.[0]?.textContent?.trim()||null;
  function setStatus(message,warning=false){
    const el=$("figureStudioStatus");
    if(el){el.textContent=message;el.classList.toggle("warning",warning);el.classList.toggle("success",!warning);}
  }
  function downloadBlob(blob,filename){
    const url=URL.createObjectURL(blob);
    const anchor=document.createElement("a");anchor.href=url;anchor.download=filename;anchor.style.display="none";
    document.body.appendChild(anchor);anchor.click();anchor.remove();
    setTimeout(()=>URL.revokeObjectURL(url),1500);
  }
  async function sha256(text){
    try{
      if(!window.crypto?.subtle)return "SHA-256 unavailable in this browser context";
      const digest=await crypto.subtle.digest("SHA-256",new TextEncoder().encode(text));
      return Array.from(new Uint8Array(digest),b=>b.toString(16).padStart(2,"0")).join("");
    }catch(_){return "SHA-256 unavailable in this browser context";}
  }
  function plotSource(id){
    const el=$(id);if(!el)return null;
    const fig=FIGURES[id];if(!fig)return null;
    if(fig.kind==="SVG"){
      const svg=el.querySelector("svg");
      return svg?{kind:"svg",element:el,svg,data:null,layout:null}:{kind:"svg",element:el,svg:null,data:null,layout:null};
    }
    if(fig.kind==="Canvas"){
      const canvas=el.matches("canvas")?el:el.querySelector("canvas");
      return {kind:"canvas",element:el,canvas,data:null,layout:null};
    }
    const traces=el._cbpfrFigureData||el.data;
    if(!Array.isArray(traces)||!traces.length)return {kind:"plotly",element:el,data:null,layout:null};
    const layout=el._cbpfrFigureLayout||el.layout||{};
    return {kind:"plotly",element:el,data:plain(traces),layout:plain(layout)};
  }
  function getGeometryManifest(){
    try{return typeof modelGeometryData!=="undefined"&&modelGeometryData?plain(modelGeometryData):null;}catch(_){return null;}
  }
  function getSelectedCandidate(){
    try{
      const id=String($("selectedCandidateId")?.textContent?.trim()||$("candidateSelect")?.value||"");
      const found=typeof records!=="undefined"&&Array.isArray(records)?records.find(r=>String(r.candidate_id)===id):null;
      return found?plain(found):null;
    }catch(_){return null;}
  }
  function getPlotParameters(id){
    const p={};
    const add=(key,control)=>{const v=$(control)?.value;if(v!==undefined&&v!==null&&v!=="")p[key]=v;};
    if(id.startsWith("mesh")){
      add("tally_score","meshScore");add("field_view","meshView");add("display_scale","meshScale");add("color_palette","meshPalette");add("vertical_exaggeration_display_only","meshExaggeration");
      try{p.mesh_dimensions=plain(meshData?.mesh_tallies?.[0]?.dimensions||null);p.mesh_tally_name=meshData?.mesh_tallies?.[0]?.tally_name||null;}catch(_){}
    }
    if(id==="axial3dPlot"||id==="axialSectionPlot"||id==="axialLineProfilePlot"){
      add("tally_score","axial3dScore");add("volume_view","axial3dView");add("axial_z_bin","axial3dSlice");add("volume_opacity","axial3dOpacity");add("color_palette","axial3dPalette");
      if(id==="axialSectionPlot"){add("slice_plane","axialPlaneSelect");add("slice_index","axialPlaneIndex");}
      if(id==="axialLineProfilePlot"){add("profile_axis","axialProfileAxis");add("fixed_bin_a","axialProfileFixedA");add("fixed_bin_b","axialProfileFixedB");}
      try{p.mesh_dimensions_xyz=plain(window.CBPFRAxial3DData?.mesh?.dimension_xyz||null);}catch(_){}
    }
    if(id==="candidateChart")add("metric","metricSelect");
    if(id==="cmpV2aFChart"||id==="cmpV2aKChart")add("comparison_metric","cmpOpenMCMetric");
    if(id==="cmpT7Chart")add("synthetic_endpoint","cmpT7Endpoint");
    if(["geometryPreview","core3dCanvas"].includes(id)){
      p.selected_candidate_id=$("selectedCandidateId")?.textContent?.trim()||null;
      p.layout_signature=getSelectedCandidate()?.layout_signature||null;
      p.selected_core_position=$("coreAssemblyBadge")?.textContent?.trim()||null;
    }
    return p;
  }
  async function sourceMetadata(id,parameters){
    const fig=FIGURES[id]||{id,title:id,group:"Unknown",kind:"unknown"};
    let sourceId="not recorded",sourceUri="not recorded",datasetId="not recorded",runId="not recorded",workflowRunId="not recorded",seed="not recorded";
    let sourceHashes={},evidenceClass="source classification unavailable",evidenceStatus="not recorded",limitations=[];
    let candidates=[];
    const get=(obj,key)=>obj&&Object.prototype.hasOwnProperty.call(obj,key)?obj[key]:undefined;
    if(SNAPSHOT){
      sourceUri=SNAPSHOT.repository||sourceUri;
      if(id.startsWith("cmpT7")){
        const paper=SNAPSHOT.paper||{};
        sourceId="paper-synthetic-T7";
        sourceUri="https://github.com/thenextw4ng/cb-pfr/blob/main/web/research_snapshot.json";
        datasetId="CBPFR-T7-synthetic-"+(SNAPSHOT.snapshot_date||"snapshot");
        evidenceClass="synthetic method evidence";
        evidenceStatus=id==="cmpT7bChart"?"POST HOC synthetic comparison; not physical validation":"Author-generated synthetic method study; not OpenMC";
        sourceHashes.paper_sha256=paper.source_sha256||"not recorded";
        sourceHashes.snapshot_t7_data_sha256=await awaitDigestSafe(SNAPSHOT.paper?.t7);
        limitations.push("Synthetic regimes are not neutron-transport outcomes.");
        limitations.push("T7b is post hoc.");
      }else if(id.startsWith("cmp")){
        const camp=SNAPSHOT.latestC5G7||{};
        sourceId=camp.studyId||"C5G7-policy-replay";
        sourceUri=camp.workflowUrl||camp.workflowBranch||sourceUri;
        datasetId=camp.studyId||"C5G7 replay snapshot";
        runId="aggregate / multiple OpenMC runs";workflowRunId=camp.workflowRun?String(camp.workflowRun):"not recorded";
        seed="Aggregate/common-seed pools; individual seed IDs are not embedded in this plot payload";
        evidenceClass=id.includes("Policy")||id.includes("policy")?"recorded-data policy replay":"recorded C5G7/OpenMC experiment summary";
        evidenceStatus=camp.v2a?.perRunConvergenceCertified===true?"source summary reports convergence certified":"SOURCE CONVERGENCE NOT CERTIFIED";
        limitations.push("High-budget empirical best is a noisy reference, not exact physical truth.");
        limitations.push("This offline replay launched zero new OpenMC simulations.");
        if(camp.v2a?.settings)parameters.low_budget_settings=plain(camp.v2a.settings);
        if(camp.highBudget?.settings)parameters.high_budget_settings=plain(camp.highBudget.settings);
        parameters.decision_blocks=camp.policyReplay?.decisionBlocks??null;
        parameters.calibration_pools=camp.policyReplay?.calibrationPools??null;
        parameters.held_out_pools=camp.policyReplay?.heldOutPools??null;
        parameters.evaluations_per_decision=camp.policyReplay?.budgetPerDecision??null;
        if(id.includes("T7"))limitations.push("Paper synthetic evidence must be exported separately from this C5G7/OpenMC record.");
      }else if(id.startsWith("mesh")){
        let d=null;try{d=typeof meshData!=="undefined"?meshData:null;}catch(_){}
        const prov=d?.provenance||{};
        sourceId=prov.source||"recorded OpenMC planar tally export";
        sourceUri=prov.source_url||prov.source||sourceUri;
        datasetId="OpenMC planar mesh tally";
        runId=prov.statepoint?.run_id?String(prov.statepoint.run_id):"not recorded in planar-tally metadata";
        seed="not recorded in planar-tally metadata";
        evidenceClass="recorded OpenMC 2D tally";
        evidenceStatus=prov.hash_matches===true?"statepoint member hash verified":prov.hash_matches===false?"WARNING: statepoint member hash mismatch":"hash verification unavailable";
        if(prov.sha256)sourceHashes.planar_tally_export_sha256=prov.sha256;
        if(prov.statepoint?.sha256)sourceHashes.statepoint_sha256=prov.statepoint.sha256;
        limitations.push("This is a 2D mesh tally; a 3D surface is only a display representation, not volumetric transport.");
        limitations.push("Source convergence certification is not implied by a matching file hash.");
      }else if(["axial3dPlot","axialSectionPlot","axialLineProfilePlot"].includes(id)){
        const d=window.CBPFRAxial3DData||null,prov=d?.provenance||{},sp=prov.statepoint||{},input=prov.input_manifest||{};
        sourceId=prov.source||"recorded OpenMC axial tally export";
        sourceUri=prov.source_url||prov.source||sourceUri;
        datasetId="OpenMC axial mesh tally "+(d?.mesh?.dimension_xyz||[]).join("x");
        runId=sp.run_id?String(sp.run_id):input.workflow_run?String(input.workflow_run):"not recorded in axial source metadata";
        seed=sp.seed!==undefined?String(sp.seed):input.seed!==undefined?String(input.seed):"not recorded in axial source metadata";
        evidenceClass="recorded OpenMC multi-layer tally";
        const smoke=Number(sp.n_batches||0)<=30&&Number(sp.n_particles||0)<=500;
        evidenceStatus=smoke?"SMOKE DIAGNOSTIC ONLY; not convergence-certified":"recorded multi-layer statepoint; campaign convergence remains unverified";
        if(prov.sha256)sourceHashes.axial_npz_sha256=prov.sha256;
        if(sp.sha256)sourceHashes.statepoint_sha256=sp.sha256;
        limitations.push("Tally values are source-normalised; they are not absolute reactor power.");
        limitations.push("A source tally and a schematic geometry extrusion are not one validated physical 3D solution.");
      }else if(id==="assemblyMap"||id==="assemblyMatrix"){
        sourceId="results/c5g7_assembly_fission_proxy_smoke_2026-10-11.csv";
        sourceUri="https://github.com/thenextw4ng/cb-pfr/blob/main/results/c5g7_assembly_fission_proxy_smoke_2026-10-11.csv";
        datasetId="assembly-integrated fission-rate proxy";
        evidenceClass="exploratory assembly proxy";
        evidenceStatus="SMOKE / DESCRIPTIVE ONLY";
        limitations.push("Physical units are undocumented; proxy is not absolute power.");
        limitations.push("Assembly proxy observations are not automatically paired with candidate-study observations.");
      }else if(id==="candidateChart"||id==="distributionChart"||id==="aggregateChart"){
        sourceId="results/c5g7_corrected_group_repeatability_smoke_2026-10-11";
        sourceUri="https://github.com/thenextw4ng/cb-pfr/tree/main/results/c5g7_corrected_group_repeatability_smoke_2026-10-11";
        datasetId="corrected-group repeatability smoke campaign";
        evidenceClass="exploratory OpenMC-derived candidate summary";
        evidenceStatus="18-run exploratory campaign; not a validated winner ranking";
        limitations.push("Means and between-seed SDs are descriptive, not calibrated confidence intervals.");
        limitations.push("One plotted chart may aggregate multiple candidates/runs; there may be no single run ID or seed.");
      }else if(id==="geometryPreview"||id==="core3dCanvas"){
        sourceId="evidence/c5g7_openmc_geometry_manifest_2026-10-13.json";
        sourceUri="https://github.com/thenextw4ng/cb-pfr/blob/main/evidence/c5g7_openmc_geometry_manifest_2026-10-13.json";
        datasetId="OpenMC-derived C5G7 core geometry manifest";
        evidenceClass="source geometry representation";
        evidenceStatus="geometry manifest-derived; 3D height is not an axial transport result";
        limitations.push("The core 3D viewer uses the source geometry manifest with schematic extrusion; it is not a validated 3D transport field.");
        limitations.push("Fuel/material universe identity is recorded separately from tally voxel coordinates.");
      }
    }
    if(id==="geometryPreview"||id==="core3dCanvas"){
      const row=getSelectedCandidate();
      if(row){parameters.selected_candidate_id=row.candidate_id??null;parameters.layout_signature=row.layout_signature??null;}
      parameters.selected_core_position=$("coreAssemblyBadge")?.textContent?.trim()||null;
    }
    // Seeds are only reported if the selected source exposes a seed field; do not infer one.
    const sourcePayload=(id.startsWith("mesh")?(typeof meshData!=="undefined"?meshData:null):window.CBPFRAxial3DData)||{};
    const foundSeed=findKey(sourcePayload,["seed","seed_id","random_seed","rng_seed"]);
    if(foundSeed!==null&&seed==="not recorded" )seed=String(foundSeed);
    return {
      repository:"https://github.com/thenextw4ng/cb-pfr",
      figure_id:id,figure_title:fig.title,source_id:sourceId,source_uri:sourceUri,dataset_id:datasetId,
      run_id:runId,workflow_run_id:workflowRunId,seed,evidence_class:evidenceClass,evidence_status:evidenceStatus,
      source_hashes:sourceHashes,parameters,limitations
    };
  }
  function findKey(obj,keys,depth=0){
    if(!obj||typeof obj!=="object"||depth>8)return null;
    for(const [k,v] of Object.entries(obj)){
      if(keys.includes(k.toLowerCase())&&(typeof v==="string"||typeof v==="number")&&String(v).length)return v;
    }
    for(const v of Object.values(obj)){const found=findKey(v,keys,depth+1);if(found!==null)return found;}
    return null;
  }
  async function awaitDigestSafe(value){return value===undefined? "not present":sha256(JSON.stringify(plain(value)));}
  function selectedGeometryData(){
    const manifest=getGeometryManifest(),row=getSelectedCandidate();
    if(!manifest)return {available:false,model_manifest:null,selected_candidate:row};
    const cid=String(row?.candidate_id??$("selectedCandidateId")?.textContent?.trim()??"");
    const signature=String(row?.layout_signature??"");
    const exact=(manifest.candidates||[]).find(c=>String(c.candidate_id)===cid&&String(c.layout_signature||"").toUpperCase()===signature.toUpperCase())||null;
    return {available:Boolean(exact),manifest,selected_candidate:row,matched_geometry_candidate:exact};
  }
  function geometryCsvRows(data){
    const candidate=data.matched_geometry_candidate,grid=candidate?.core_universe_grid;
    if(!Array.isArray(grid))return [{record_type:"geometry_manifest",note:"source geometry grid not available for the selected candidate"}];
    const assemblyMap=data.manifest?.assemblies||{};
    const rows=[];
    grid.forEach((row,r)=>row.forEach((universe,c)=>{
      const a=assemblyMap[String(universe)]||{};
      rows.push({record_type:"core_lattice_cell",candidate_id:candidate.candidate_id,layout_signature:candidate.layout_signature,row_index:r,col_index:c,universe_id:universe,assembly_code:a.code||"not recorded"});
    }));
    return rows;
  }
  function flattenTraceData(traces){
    const rows=[];
    const asArray=v=>v==null?[]:ArrayBuffer.isView(v)?Array.from(v):Array.isArray(v)?v:[v];
    traces.forEach((trace,traceIndex)=>{
      const x=asArray(trace.x),y=asArray(trace.y),z=asArray(trace.z),v=asArray(trace.value??trace.intensity??trace.z),custom=asArray(trace.customdata);
      const matrix=Array.isArray(trace.z)&&trace.z.length&&Array.isArray(trace.z[0]);
      const customsFor=(i,j)=>Array.isArray(trace.customdata)?(Array.isArray(trace.customdata[j])?trace.customdata[j][i]:trace.customdata[i]):trace.customdata;
      const eplus=asArray(trace.error_y?.array),eminus=asArray(trace.error_y?.arrayminus);
      if(matrix){
        trace.z.forEach((r,j)=>asArray(r).forEach((value,i)=>{
          const customValue=customsFor(i,j);
          const extras=Array.isArray(customValue)&&customValue.length>=9?{raw_tally_mean:customValue[0],monte_carlo_standard_error:customValue[1],relative_error_percent:customValue[2],bin_i:customValue[3],bin_j:customValue[4],bin_k:customValue[5],x_center_cm:customValue[6],y_center_cm:customValue[7],z_center_cm:customValue[8]}:{};
          rows.push({trace_index:traceIndex,trace_name:trace.name||"trace_"+traceIndex,trace_type:trace.type||"unknown",point_index:j*asArray(r).length+i,
            x:x.length?x[i]:i,y:y.length?y[j]:j,z:null,value,
            error_y_plus:null,error_y_minus:null,customdata:customValue,...extras});
        }));
      }else{
        const length=Math.max(x.length,y.length,z.length,asArray(trace.value).length,asArray(trace.intensity).length,custom.length,eplus.length,eminus.length);
        for(let i=0;i<length;i++){
          const valueAt=trace.value!==undefined?asArray(trace.value)[i]:trace.intensity!==undefined?asArray(trace.intensity)[i]:Array.isArray(trace.z)&&trace.z.length?z[i]:y.length?y[i]:null;
          const customValue=trace.customdata!==undefined?(Array.isArray(trace.customdata)?trace.customdata[i]:trace.customdata):null;
          const extras=Array.isArray(customValue)&&customValue.length>=9?{raw_tally_mean:customValue[0],monte_carlo_standard_error:customValue[1],relative_error_percent:customValue[2],bin_i:customValue[3],bin_j:customValue[4],bin_k:customValue[5],x_center_cm:customValue[6],y_center_cm:customValue[7],z_center_cm:customValue[8]}:{};
          rows.push({trace_index:traceIndex,trace_name:trace.name||"trace_"+traceIndex,trace_type:trace.type||"unknown",point_index:i,
            x:x.length?x[i]:null,y:y.length?y[i]:null,z:z.length?z[i]:null,value:valueAt,
            error_y_plus:eplus.length?eplus[i]:null,error_y_minus:eminus.length?eminus[i]:null,
            customdata:customValue,...extras});
        }
      }
    });
    return rows;
  }
  function csvCell(value){
    if(value===null||value===undefined)return "";
    const s=typeof value==="object"?JSON.stringify(plain(value)):String(value);
    return /[",\r\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;
  }
  function makeCsv(meta,rows){
    const base={figure_id:meta.figure_id,figure_title:meta.figure_title,caption:meta.caption||"",dataset_id:meta.source.dataset_id,
      source_id:meta.source.source_id,source_uri:meta.source.source_uri,run_id:meta.source.run_id,workflow_run_id:meta.source.workflow_run_id,seed:meta.source.seed,
      evidence_class:meta.source.evidence_class,evidence_status:meta.source.evidence_status,
      source_hashes_json:JSON.stringify(meta.source.source_hashes),exported_data_sha256:meta.integrity.data_sha256,
      visualization_config_sha256:meta.integrity.config_sha256,exported_at_utc:meta.figure.exported_at_utc};
    const fields=[...Object.keys(base),...Array.from(new Set(rows.flatMap(r=>Object.keys(r))))];
    return fields.join(",")+"\r\n"+rows.map(row=>fields.map(key=>csvCell(Object.prototype.hasOwnProperty.call(row,key)?row[key]:base[key])).join(",")).join("\r\n")+"\r\n";
  }
  function currentCaption(sourceMeta,params,id){
    if(id.startsWith("cmpT7"))return "Synthetic T7/T7b method comparison ("+(SNAPSHOT?.snapshot_date||"snapshot date not recorded")+"): "+(id==="cmpT7bChart"?"difference in the reported feasible-and-near-optimal endpoint at matched 95% feasibility. ":"selected endpoint across synthetic operating regimes. ")+"Author-generated synthetic method evidence, not an OpenMC physical result; T7b is post hoc.";
    if(id.startsWith("cmp")){
      const c=SNAPSHOT?.latestC5G7||{};
      return "C5G7/OpenMC "+(id.toLowerCase().includes("policy")?"equal-budget policy replay":"layout comparison")+" from "+(c.studyId||"the recorded C5G7 snapshot")+" (workflow run "+(c.workflowRun??"not recorded")+"). "+(id.toLowerCase().includes("policy")?"Match rate is calculated against a noisy high-budget empirical reference; no match-rate confidence interval is present in the source snapshot. ":"Error bars, where shown, are between-run standard deviations, not confidence intervals. ")+"Source convergence is not certified.";
    }
    if(id.startsWith("mesh")){
      const dims=sourceMeta.parameters.mesh_dimensions||"dimensions in source metadata";
      return "Recorded OpenMC planar mesh tally ("+dims+"), score "+(params.tally_score||"not recorded")+", view "+(params.field_view||"not recorded")+". Coordinate units follow archived regular-mesh bounds when present; relative error is a descriptive Monte Carlo statistic. A 3D surface is only a representation of 2D tally data.";
    }
    if(["axial3dPlot","axialSectionPlot","axialLineProfilePlot"].includes(id)){
      const d=window.CBPFRAxial3DData||{};
      return "Recorded OpenMC "+(params.tally_score||"not recorded")+" axial tally, mesh "+(d.mesh?.dimension_xyz||[]).join(" × ")+", run "+sourceMeta.run_id+", statepoint SHA-256 "+(sourceMeta.source_hashes.statepoint_sha256||"not recorded")+". Relative error is bin-wise Monte Carlo standard error divided by mean for positive means. Source convergence and physical validation are not implied.";
    }
    if(id==="assemblyMap"||id==="assemblyMatrix")return "Exploratory assembly-integrated fission-rate proxy from "+sourceMeta.source_id+". Physical units are undocumented; values are not absolute reactor power and are not automatically paired to candidate-study runs.";
    if(id==="geometryPreview"||id==="core3dCanvas")return "C5G7 core geometry derived from the archived OpenMC geometry manifest for candidate "+(params.selected_candidate_id||"not selected")+", layout "+(params.layout_signature||"not recorded")+". The 3D viewer uses schematic extrusion and is not a 3D transport tally; geometry identity does not establish physical validation.";
    return "Exploratory corrected-group candidate metric from "+sourceMeta.dataset_id+". State the selected metric and source campaign; run-to-run variability is descriptive and does not certify a physical winner.";
  }
  async function buildBundle(id,overrideCaption){
    const source=plotSource(id);
    if(!source)throw new Error("Unknown figure source: "+id);
    const fig=FIGURES[id];
    const params=getPlotParameters(id);
    let dataPayload,rows,layout;
    if(source.kind==="plotly"){
      if(!source.data||!source.data.length)throw new Error("The selected plot has no source trace data. Render it in the dashboard first.");
      dataPayload=source.data;layout=source.layout||{};rows=flattenTraceData(dataPayload);
    }else{
      dataPayload=selectedGeometryData();layout={render_kind:source.kind,vector_or_canvas_export:true};
      rows=source.kind==="svg"||source.kind==="canvas"?geometryCsvRows(dataPayload):[];
      if(!dataPayload.available&&source.kind==="svg")throw new Error("No exact candidate-matched source geometry is loaded.");
    }
    const meta=await sourceMetadata(id,params);
    const caption=String(overrideCaption??$("figureStudioCaption")?.value??"").trim()||currentCaption(meta,params,id);
    const dataText=JSON.stringify(plain(dataPayload));
    const configText=JSON.stringify(plain({figure_id:id,parameters:params,layout}));
    const dataHash=await sha256(dataText),configHash=await sha256(configText);
    const payload={
      schema_version:"cbpfr-figure-reproducibility-v1",
      figure:{id,title:fig.title,group:fig.group,render_kind:source.kind,caption,created_at_utc:new Date().toISOString(),png_export_pixels:[OUT_W,OUT_H]},
      source:meta,
      provenance:{source_hashes:meta.source_hashes,run_id:meta.run_id,seed:meta.seed,evidence_status:meta.evidence_status},
      visualization:{parameters:params,layout:plain(layout),trace_data:source.kind==="plotly"?dataPayload:null},
      geometry_data:source.kind!=="plotly"?dataPayload:null,
      integrity:{data_sha256:dataHash,config_sha256:configHash,hash_algorithm:"SHA-256",hash_scope:"SHA-256 of serialized exported trace/geometry payload and visualization config; does not replace upstream source-file hashes"},
      limitations:meta.limitations
    };
    // Embed the editable caption and source status in the returned bundle for exact figure reconstruction.
    meta.caption=caption;
    payload.source=meta;
    const enrichedRows=rows;
    const result={id,source,figure:fig,caption,meta,payload,rows:enrichedRows,
      csv:makeCsv({figure:{exported_at_utc:payload.figure.created_at_utc},source:meta,caption,integrity:payload.integrity},enrichedRows),
      dataText,configText};
    activeBundle=result;
    return result;
  }
  function populateSelect(select){
    const el=$(select);if(!el)return;
    el.innerHTML=CATALOG.map(([id,title,group,kind])=>'<option value="'+safe(id)+'">'+safe(group)+" · "+safe(title)+"</option>").join("");
  }
  function updateCaptionPreview(){
    const id=$("figureStudioTarget")?.value||"cmpV2aFChart",params=getPlotParameters(id);
    sourceMetadata(id,params).then(meta=>{
      const caption=currentCaption(meta,params,id);
      const input=$("figureStudioCaption");
      if(input&&!input.dataset.edited)input.value=caption;
      const status=$("figureStudioStatus");
      if(status)status.textContent="Source selected · "+meta.evidence_status+" · caption is editable";
      renderMetadataGrid(meta,caption,null);
    }).catch(e=>setStatus("Metadata lookup failed: "+e.message,true));
  }
  function renderMetadataGrid(meta,caption,integrity){
    const host=$("figureStudioMetadata");if(!host)return;
    const pairs=[
      ["Dataset ID",meta.dataset_id],["Source / path",meta.source_id],["Run / workflow ID",meta.run_id],
      ["Workflow run ID",meta.workflow_run_id],["Seed",meta.seed],["Evidence class",meta.evidence_class],["Evidence status",meta.evidence_status],
      ["Source hash(es)",JSON.stringify(meta.source_hashes)],["Parameters",JSON.stringify(meta.parameters)],
      ["Exported data SHA-256",integrity?.data_sha256||"computed during export"],["Visualization config SHA-256",integrity?.config_sha256||"computed during export"]
    ];
    host.innerHTML=pairs.map(([label,value])=>'<div class="figure-meta-item"><span>'+safe(label)+'</span><strong>'+safe(value??"not recorded")+'</strong></div>').join("");
    const boundary=$("figureStudioLimits");
    if(boundary)boundary.textContent=(meta.limitations||[]).join(" ");
    const cap=$("figureStudioAutoCaption");
    if(cap)cap.textContent=caption||"";
  }
  async function renderCompareCard(id,hostId,metaId,titleId){
    const host=$(hostId),metaHost=$(metaId),titleHost=$(titleId);
    const src=plotSource(id);
    if(!host||!src)throw new Error("Comparison source is not available: "+id);
    host.replaceChildren();
    titleHost.textContent=FIGURES[id]?.title||id;
    const bundle=await buildBundle(id,undefined);
    if(src.kind==="plotly"){
      if(!src.data?.length)throw new Error("Plot not rendered yet. Scroll to its panel and wait for the source plot to load.");
      if(!window.Plotly)throw new Error("Plotly.js is not available.");
      const data=plain(src.data),layout=plain(src.layout||{});
      layout.autosize=true;layout.height=360;
      layout.margin={l:55,r:25,t:25,b:70};
      await Plotly.newPlot(host,data,layout,{responsive:true,displayModeBar:false,displaylogo:false});
    }else if(src.kind==="svg"){
      if(!src.svg)throw new Error("Source SVG map has not rendered. Select the candidate and load its geometry first.");
      const clone=src.svg.cloneNode(true);
      clone.style.width="100%";clone.style.height="100%";clone.style.maxHeight="360px";
      host.appendChild(clone);
    }else if(src.kind==="canvas"){
      if(!src.canvas||src.canvas.width<=0||src.canvas.height<=0)throw new Error("3D canvas is not rendered. Open Core Geometry 3D before comparing it.");
      const image=document.createElement("img");
      image.alt=FIGURES[id]?.title||id;
      try{image.src=src.canvas.toDataURL("image/png");}
      catch(_){throw new Error("This WebGL canvas is not readable for export in the current renderer; use the source 2D geometry map or refresh the renderer.");}
      image.style.cssText="width:100%;height:360px;object-fit:contain;background:#06111a";
      host.appendChild(image);
    }
    const md=bundle.meta;
    if(metaHost)metaHost.textContent=[md.evidence_class,md.evidence_status,"Run: "+md.run_id,"Seed: "+md.seed,"Source hash: "+JSON.stringify(md.source_hashes)].join(" · ");
  }
  async function renderComparison(){
    const a=$("figureCompareA")?.value||"cmpV2aFChart",b=$("figureCompareB")?.value||"cmpPolicyMatchChart";
    try{
      await Promise.all([
        renderCompareCard(a,"figureComparePreviewA","figureCompareMetaA","figureCompareTitleA"),
        renderCompareCard(b,"figureComparePreviewB","figureCompareMetaB","figureCompareTitleB")
      ]);
      const notes=$("figureCompareNote");
      if(notes)notes.textContent="Both views use the same preview frame size. Each panel retains its own axes and units; do not interpret unlike metrics as a shared numerical scale. Evidence class and provenance are shown separately.";
      setStatus("Side-by-side comparison rendered · "+a+" / "+b);
    }catch(error){setStatus("Comparison unavailable: "+String(error.message||error),true);}
  }
  function imageLayout(bundle){
    const base=plain(bundle.source.kind==="plotly"?bundle.source.layout||{}:{});
    const font={...(base.font||{}),family:"Arial, Helvetica, sans-serif",size:17,color:C.ink};
    const annotations=Array.isArray(base.annotations)?base.annotations.map(a=>({...a,font:{...(a.font||{}),color:C.ink}})):[];
    const source= bundle.meta;
    const provenanceLine=[
      "Dataset: "+source.dataset_id,
      "Run ID: "+source.run_id,
      "Workflow run ID: "+source.workflow_run_id,
      "Seed: "+source.seed,
      "Evidence: "+source.evidence_status,
      "Source hash: "+JSON.stringify(source.source_hashes)
    ].join(" · ");
    annotations.push({xref:"paper",yref:"paper",x:0.01,y:1.075,xanchor:"left",yanchor:"bottom",showarrow:false,align:"left",
      text:safe(provenanceLine),font:{family:"Arial, Helvetica, sans-serif",size:12,color:C.muted}});
    annotations.push({xref:"paper",yref:"paper",x:0.01,y:-0.24,xanchor:"left",yanchor:"top",showarrow:false,align:"left",
      text:safe(bundle.caption),font:{family:"Arial, Helvetica, sans-serif",size:12,color:C.ink}});
    const out={...base,autosize:false,width:OUT_W,height:OUT_H,paper_bgcolor:"#ffffff",plot_bgcolor:"#ffffff",font,
      margin:{l:115,r:110,t:175,b:210,pad:8},
      title:{text:bundle.figure.title,x:0.01,xanchor:"left",y:0.99,yanchor:"top",font:{family:"Arial, Helvetica, sans-serif",size:29,color:"#111827"}},
      xaxis:paperAxis(base.xaxis),yaxis:paperAxis(base.yaxis),annotations,
      legend:{...(base.legend||{}),font:{...(base.legend?.font||{}),family:"Arial, Helvetica, sans-serif",size:15,color:C.ink}}
    };
    if(base.scene)out.scene={...base.scene,bgcolor:"#ffffff",xaxis:paperAxis(base.scene.xaxis),yaxis:paperAxis(base.scene.yaxis),zaxis:paperAxis(base.scene.zaxis)};
    return out;
  }
  function paperAxis(axis){
    if(!axis||typeof axis!=="object")return axis;
    const titleText=typeof axis.title==="object"?(axis.title.text||""):(axis.title||"");
    return {...axis,color:C.ink,gridcolor:C.line,linecolor:"#6b7c8c",zerolinecolor:"#9caab6",
      tickfont:{...(axis.tickfont||{}),color:C.ink,size:13},
      title:{text:titleText,font:{...(typeof axis.title==="object"?(axis.title.font||{}):{}),color:C.ink,size:16}}};
  }
  function paperTrace(trace){
    if(Array.isArray(trace))return trace.map(paperTrace);
    if(!trace||typeof trace!=="object")return trace;
    if(ArrayBuffer.isView(trace))return Array.from(trace);
    const out={};
    for(const [key,value] of Object.entries(trace)){
      if(key==="tickfont"&&value&&typeof value==="object")out[key]={...value,color:C.ink};
      else if(key==="title"&&value&&typeof value==="object")out[key]={...value,font:{...(value.font||{}),color:C.ink}};
      else out[key]=paperTrace(value);
    }
    return out;
  }
  async function exportPng(){
    const id=$("figureStudioTarget")?.value||"cmpV2aFChart";
    const button=$("figureStudioExportPng");button.disabled=true;
    let stage=null;
    try{
      const caption=$("figureStudioCaption")?.value||"";
      const b=await buildBundle(id,caption);
      const baseSource=plotSource(id);
      let imageBlob;
      if(baseSource.kind==="plotly"){
        if(!window.Plotly||!baseSource.data?.length)throw new Error("Render the selected Plotly chart first.");
        stage=document.createElement("div");stage.style.cssText="position:fixed;left:-12000px;top:0;width:"+OUT_W+"px;height:"+OUT_H+"px;opacity:.01;pointer-events:none";
        document.body.appendChild(stage);
        await Plotly.newPlot(stage,plain(baseSource.data).map(paperTrace),imageLayout(b),{displayModeBar:false,displaylogo:false,responsive:false,staticPlot:true});
        const url=await Plotly.toImage(stage,{format:"png",width:OUT_W,height:OUT_H,scale:1});
        const response=await fetch(url);imageBlob=await response.blob();
      }else{
        imageBlob=await exportGeometryPng(baseSource,b);
      }
      downloadBlob(imageBlob,"cbpfr_"+slug(id)+"_"+slug(b.meta.dataset_id)+".png");
      setStatus("PNG exported ("+OUT_W+" × "+OUT_H+" px) with caption, source, run/seed fields, evidence status and provenance hashes.");
    }catch(error){setStatus("PNG export failed: "+String(error.message||error),true);}
    finally{if(stage){try{Plotly.purge(stage);}catch(_){}stage.remove();}button.disabled=false;}
  }
  async function exportGeometryPng(source,bundle){
    const canvas=document.createElement("canvas");canvas.width=OUT_W;canvas.height=OUT_H;
    const ctx=canvas.getContext("2d");ctx.fillStyle="#fff";ctx.fillRect(0,0,OUT_W,OUT_H);
    ctx.fillStyle="#111827";ctx.font="bold 30px Arial";ctx.fillText(bundle.figure.title,80,70);
    ctx.fillStyle=C.muted;ctx.font="14px Arial";
    const p=bundle.meta;
    ctx.fillText("Dataset: "+p.dataset_id+" · Run: "+p.run_id+" · Seed: "+p.seed,80,104);
    ctx.fillText("Evidence: "+p.evidence_status,80,128);
    if(source.kind==="svg"&&source.svg){
      const clone=source.svg.cloneNode(true);
      const vb=(clone.getAttribute("viewBox")||"0 0 1000 700").split(/\s+/).map(Number);
      const w=vb[2]||1000,h=vb[3]||700;
      clone.setAttribute("xmlns","http://www.w3.org/2000/svg");clone.setAttribute("width",String(w));clone.setAttribute("height",String(h));
      const bg=document.createElementNS("http://www.w3.org/2000/svg","rect");bg.setAttribute("x",String(vb[0]||0));bg.setAttribute("y",String(vb[1]||0));bg.setAttribute("width",String(w));bg.setAttribute("height",String(h));bg.setAttribute("fill","#06111a");clone.insertBefore(bg,clone.firstChild);
      const blob=new Blob([new XMLSerializer().serializeToString(clone)],{type:"image/svg+xml;charset=utf-8"});
      const url=URL.createObjectURL(blob);
      try{
        const img=await loadImage(url),maxW=OUT_W-200,maxH=OUT_H-440,scale=Math.min(maxW/w,maxH/h);
        ctx.drawImage(img,(OUT_W-w*scale)/2,170,w*scale,h*scale);
      }finally{URL.revokeObjectURL(url);}
    }else if(source.kind==="canvas"&&source.canvas){
      let url;try{url=source.canvas.toDataURL("image/png");}catch(_){throw new Error("WebGL canvas is not readable; render the source 2D SVG map instead.");}
      const img=await loadImage(url),maxW=OUT_W-180,maxH=OUT_H-430,scale=Math.min(maxW/img.width,maxH/img.height);
      ctx.drawImage(img,(OUT_W-img.width*scale)/2,165,img.width*scale,img.height*scale);
    }
    ctx.fillStyle=C.ink;ctx.font="15px Arial";wrapText(ctx,bundle.caption,80,OUT_H-220,OUT_W-160,22);
    ctx.fillStyle=C.muted;ctx.font="12px Arial";wrapText(ctx,"Source: "+p.source_id+" · Source hashes: "+JSON.stringify(p.source_hashes)+" · Data SHA-256: "+bundle.payload.integrity.data_sha256+" · Config SHA-256: "+bundle.payload.integrity.config_sha256,80,OUT_H-115,OUT_W-160,18);
    return await new Promise((resolve,reject)=>canvas.toBlob(blob=>blob?resolve(blob):reject(new Error("Could not encode figure PNG.")),"image/png"));
  }
  function loadImage(src){return new Promise((resolve,reject)=>{const img=new Image();img.onload=()=>resolve(img);img.onerror=()=>reject(new Error("Could not rasterize the source visualization."));img.src=src;});}
  function wrapText(ctx,text,x,y,maxWidth,lineHeight){
    const words=String(text||"").split(/\s+/),lines=[];let line="";
    for(const word of words){const next=line?line+" "+word:word;if(ctx.measureText(next).width>maxWidth&&line){lines.push(line);line=word;}else line=next;}
    if(line)lines.push(line);
    lines.slice(0,6).forEach((item,index)=>ctx.fillText(item,x,y+index*lineHeight));
  }
  async function exportJson(){
    const id=$("figureStudioTarget")?.value||"cmpV2aFChart";
    const button=$("figureStudioExportJson");button.disabled=true;
    try{
      const b=await buildBundle(id,$("figureStudioCaption")?.value||"");
      const blob=new Blob([JSON.stringify(b.payload,null,2)+"\n"],{type:"application/json"});
      downloadBlob(blob,"cbpfr_"+slug(id)+"_reproducibility.json");
      renderMetadataGrid(b.meta,b.caption,b.payload.integrity);
      setStatus("Reproducibility JSON exported · data SHA-256 "+b.payload.integrity.data_sha256);
    }catch(error){setStatus("JSON export failed: "+String(error.message||error),true);}
    finally{button.disabled=false;}
  }
  async function exportCsv(){
    const id=$("figureStudioTarget")?.value||"cmpV2aFChart";
    const button=$("figureStudioExportCsv");button.disabled=true;
    try{
      const b=await buildBundle(id,$("figureStudioCaption")?.value||"");
      const blob=new Blob([b.csv],{type:"text/csv;charset=utf-8"});
      downloadBlob(blob,"cbpfr_"+slug(id)+"_data.csv");
      renderMetadataGrid(b.meta,b.caption,b.payload.integrity);
      setStatus("CSV exported · "+b.rows.length.toLocaleString()+" rows · data SHA-256 "+b.payload.integrity.data_sha256);
    }catch(error){setStatus("CSV export failed: "+String(error.message||error),true);}
    finally{button.disabled=false;}
  }
  async function exportSvg(){
    const id=$("figureStudioTarget")?.value;
    const source=plotSource(id);
    if(!source||source.kind!=="svg"||!source.svg){setStatus("The selected source is not a rendered SVG geometry map.",true);return;}
    try{
      const bundle=await buildBundle(id,$("figureStudioCaption")?.value||"");
      const clone=source.svg.cloneNode(true),viewBox=clone.getAttribute("viewBox")||"0 0 1000 700";
      const bits=viewBox.split(/\s+/).map(Number),w=bits[2]||1000,h=bits[3]||700;
      clone.setAttribute("xmlns","http://www.w3.org/2000/svg");clone.setAttribute("width",String(w));clone.setAttribute("height",String(h));
      const bg=document.createElementNS("http://www.w3.org/2000/svg","rect");bg.setAttribute("x",String(bits[0]||0));bg.setAttribute("y",String(bits[1]||0));bg.setAttribute("width",String(w));bg.setAttribute("height",String(h));bg.setAttribute("fill","#06111a");clone.insertBefore(bg,clone.firstChild);
      const blob=new Blob([new XMLSerializer().serializeToString(clone)],{type:"image/svg+xml;charset=utf-8"});
      downloadBlob(blob,"cbpfr_"+slug(id)+"_vector.svg");
      setStatus("Vector SVG geometry exported. The adjacent JSON/CSV exports retain source geometry and selected-candidate metadata.");
    }catch(error){setStatus("SVG export failed: "+String(error.message||error),true);}
  }
  async function copyCaption(){
    const text=String($("figureStudioCaption")?.value||"").trim();
    if(!text){setStatus("Caption is empty.",true);return;}
    try{await navigator.clipboard.writeText(text);setStatus("Caption copied to clipboard.");}
    catch(_){const area=$("figureStudioCaption");area.focus();area.select();setStatus("Clipboard API unavailable; caption selected for manual copying.",true);}
  }
  function bind(){
    ["figureStudioTarget","figureCompareA","figureCompareB"].forEach((id,i)=>{
      const el=$(id);if(!el)return;
      el.addEventListener("change",()=>{
        if(id==="figureStudioTarget"){if($("figureStudioCaption"))$("figureStudioCaption").dataset.edited="";updateCaptionPreview();}
        else if(id==="figureCompareA"||id==="figureCompareB")renderComparison();
      });
    });
    $("figureStudioCaption")?.addEventListener("input",e=>{e.currentTarget.dataset.edited="true";});
    $("figureStudioExportPng")?.addEventListener("click",exportPng);
    $("figureStudioExportJson")?.addEventListener("click",exportJson);
    $("figureStudioExportCsv")?.addEventListener("click",exportCsv);
    $("figureStudioExportSvg")?.addEventListener("click",exportSvg);
    $("figureStudioCopyCaption")?.addEventListener("click",copyCaption);
    $("figureStudioRenderComparison")?.addEventListener("click",renderComparison);
    $("figureStudioCompareExportA")?.addEventListener("click",()=>{$("figureStudioTarget").value=$("figureCompareA").value;updateCaptionPreview();$("figureStudioTarget").dispatchEvent(new Event("change"));});
    $("figureStudioCompareExportB")?.addEventListener("click",()=>{$("figureStudioTarget").value=$("figureCompareB").value;updateCaptionPreview();$("figureStudioTarget").dispatchEvent(new Event("change"));});
    window.addEventListener("cbpfr-axial3d-updated",()=>{if($("figureStudioTarget")?.value?.startsWith("axial"))updateCaptionPreview();});
    $("candidateSelect")?.addEventListener("change",()=>{if(["geometryPreview","core3dCanvas"].includes($("figureStudioTarget")?.value))updateCaptionPreview();});
  }
  async function init(){
    ["figureStudioTarget","figureCompareA","figureCompareB"].forEach(populateSelect);
    if($("figureStudioTarget"))$("figureStudioTarget").value="cmpV2aFChart";
    if($("figureCompareA"))$("figureCompareA").value="cmpV2aFChart";
    if($("figureCompareB"))$("figureCompareB").value="cmpPolicyMatchChart";
    try{
      const response=await fetch("./research_snapshot.json",{cache:"no-store",headers:{Accept:"application/json"}});
      if(response.ok)SNAPSHOT=await response.json();
    }catch(_){}
    bind();updateCaptionPreview();
    if($("figureStudioRenderComparison"))renderComparison();
  }
  if(document.readyState==="loading")document.addEventListener("DOMContentLoaded",init);else init();
})();