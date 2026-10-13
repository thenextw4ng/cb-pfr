const $ = (id) => document.getElementById(id);
const palette = {text:"#e8f1f7",muted:"#91a8b9",line:"#263f52",cyan:"#55d4df",blue:"#247fa0",orange:"#f5bb62"};
let records = [];
let metadata = {};
let meshData = null;
let assemblyRecords = [];
const number = (x, digits=5) => Number.isFinite(Number(x)) ? Number(x).toFixed(digits) : "—";
const has = (row,key) => {
 if(!row || typeof row!=="object")return false;
 const value=row[key];
 return value!==null && value!==undefined && !(typeof value==="string" && value.trim()==="") && Number.isFinite(Number(value));
};
function displayValue(value,fallback="Not recorded"){
 if(value===null||value===undefined||(typeof value==="string"&&value.trim()===""))return fallback;
 return String(value);
}
function normalizeLayoutSignature(signature){return String(signature??"").trim().toUpperCase();}
function isValidLayoutSignature(signature){
 const raw=normalizeLayoutSignature(signature);
 return /^[UM]{4}$/.test(raw)&&raw.split("M").length-1===2&&raw.split("U").length-1===2;
}
function label(row){return displayValue(row.candidate_id,"Candidate") + " · " + displayValue(row.layout_signature,"layout");}
function validateCandidateRecords(rows){
 if(!Array.isArray(rows)||!rows.length)throw new Error("The API returned no candidate records.");
 const seen=new Set();
 rows.forEach((row,index)=>{
  if(!row||typeof row!=="object"||Array.isArray(row))throw new Error("Candidate record "+(index+1)+" is not an object.");
  const id=String(row.candidate_id??"").trim();
  if(!id)throw new Error("Candidate record "+(index+1)+" has no candidate_id.");
  if(seen.has(id))throw new Error("Duplicate candidate_id in source data: "+id+". Selection would be ambiguous.");
  seen.add(id);
 });
 return rows;
}
function candidateOption(row){
 const id=String(row.candidate_id??"");
 return '<option value="'+escapeHtml(id)+'">'+escapeHtml(label(row))+'</option>';
}
function layoutCells(signature){
  const raw=normalizeLayoutSignature(signature);
  if(!isValidLayoutSignature(raw)){
    return '<div class="empty-state"><b>Placement unavailable</b><p>The selected candidate must contain exactly two UO₂ and two MOX positions. No default arrangement is substituted.</p></div>';
  }
  const cells=raw.split("");
  const positions=["p00","p01","p10","p11"];
  return '<div class="assembly-grid">'+cells.map((c,i)=>'<div class="assembly '+(c==="M"?"mox-cell":"")+'">'+(c==="M"?"MOX":"UO₂")+'<small>'+positions[i]+' · '+(i+1)+'</small></div>').join("")+'</div>';
}
// Pin-universe maps extracted from the archived candidate geometry.xml files (17 × 17 lattices).
// Universe IDs 1–6 map to UO2, three MOX enrichments, fission chamber, and guide tube;
// each pin's surrounding region is the water moderator defined in geometry.xml.
const pinUniverseColors={"1":"#51d2df","2":"#f4bd62","3":"#f08f62","4":"#dc6f91","5":"#c1b3ff","6":"#9cb6c8"};
let modelGeometryData=null;
let geometryArtifactActive=false;
let core3dViewer=null;
let coreGeometryMode="3d";
let core3dLoadFailed=false;
let currentGeometryRow=null;
let selectedCorePosition={row:0,col:0};
window.addEventListener("cbpfr-core3d-ready",()=>{
 core3dLoadFailed=false;
 if(currentGeometryRow&&!geometryArtifactActive)drawModelGeometry(currentGeometryRow);
});
window.addEventListener("cbpfr-core3d-failed",()=>{
 core3dLoadFailed=true;
 const status=$("core3dStatus");
 if(status)status.textContent="THREE.JS CDN UNAVAILABLE · 2D FALLBACK";
 if(currentGeometryRow&&!geometryArtifactActive)selectCoreView("2d");
});

function modelMaterialCell(universeId,x,y,pitch){
 const key=String(universeId),source=modelGeometryData?.materials?.pin_universes?.[key];
 if(!source)throw new Error("Unknown pin universe "+key+" in model manifest.");
 const radius=Number(modelGeometryData.pin_geometry?.pin_radius_cm),pinPitch=Number(modelGeometryData.pin_geometry?.pitch_cm?.[0]);
 if(!Number.isFinite(radius)||!Number.isFinite(pinPitch)||radius<=0||pinPitch<=0)throw new Error("Invalid source pin radius/pitch.");
 const r=pitch*radius/pinPitch,cx=x+pitch/2,cy=y+pitch/2;
 return '<rect x="'+x.toFixed(2)+'" y="'+y.toFixed(2)+'" width="'+pitch.toFixed(2)+'" height="'+pitch.toFixed(2)+'" fill="#123749" stroke="#285064" stroke-width=".38"/>'+
 '<circle cx="'+cx.toFixed(2)+'" cy="'+cy.toFixed(2)+'" r="'+r.toFixed(2)+'" fill="'+(pinUniverseColors[key]||"#c1cbd2")+'" stroke="#06111a" stroke-width=".45"><title>'+escapeHtml(source.material_name||source.name||("Universe "+key))+' · universe '+key+'</title></circle>';
}
function modelBoundaryLabel(axis,side){
 const item=(modelGeometryData?.boundary_conditions||[]).find(b=>String(b.name||"").toLowerCase().includes("core "+axis+"-"+side));
 return axis.toUpperCase()+" "+side.toUpperCase()+" · "+String(item?.condition||"not recorded").toUpperCase();
}
function renderModelGeometrySvg(row){
 if(!modelGeometryData)return '<div class="empty-state"><b>Model geometry unavailable</b><p>The OpenMC-derived manifest could not be loaded. No substitute geometry is drawn.</p></div>';
 const signature=normalizeLayoutSignature(row?.layout_signature),candidateId=String(row?.candidate_id??"");
 if(!isValidLayoutSignature(signature))return '<div class="empty-state"><b>Invalid fuel composition</b><p>A valid configuration must contain two UO₂ and two MOX positions.</p></div>';
 const source=(modelGeometryData.candidates||[]).find(c=>String(c.candidate_id)===candidateId&&normalizeLayoutSignature(c.layout_signature)===signature);
 if(!source)return '<div class="empty-state"><b>Model source not matched</b><p>No exact candidate ID and signature pair exists in the archived OpenMC manifest.</p></div>';
 if(source.source_matches_candidate_signature!==true||source.signature_derived_from_xml!==signature)return '<div class="empty-state"><b>Geometry identity check failed</b><p>The signature derived from the OpenMC core lattice differs from the selected candidate.</p></div>';
 const core=modelGeometryData.core_lattice||{},dims=core.dimensions||[],sourceGrid=source.core_universe_grid||[];
 if(dims.length!==2||sourceGrid.length!==dims[1]||sourceGrid.some(r=>!Array.isArray(r)||r.length!==dims[0]))return '<div class="empty-state"><b>Invalid source lattice</b><p>The core dimensions do not match the archived lattice rows.</p></div>';
 const assemblyMap=modelGeometryData.assemblies||{},grid=sourceGrid.map(r=>r.map(uid=>assemblyMap[String(uid)]?.code||"?"));
 if(grid.some(r=>r.some(code=>!["U","M","R"].includes(code))))return '<div class="empty-state"><b>Unknown source universe</b><p>The archived core lattice references an unmapped universe.</p></div>';
 const cols=dims[0],rows=dims[1],width=1020,height=670,x0=48,y0=92,size=Math.min(170,480/Math.max(cols,rows)),gap=2;
 const cw=cols*size+(cols-1)*gap,ch=rows*size+(rows-1)*gap,pinDims=modelGeometryData.pin_geometry?.dimensions||[];
 const extent=core.lower_left_cm&&core.pitch_cm?core.lower_left_cm.map((v,i)=>Number(v)+Number(core.pitch_cm[i])*Number(dims[i])):null;
 const xwidth=extent?extent[0]-Number(core.lower_left_cm[0]):NaN,yheight=extent?extent[1]-Number(core.lower_left_cm[1]):NaN;
 let svg='<svg class="model-geometry-svg" viewBox="0 0 '+width+' '+height+'" role="img" aria-label="OpenMC C5G7 material map for layout '+escapeHtml(signature)+' candidate '+escapeHtml(candidateId)+'">';
 svg+='<defs><linearGradient id="reflectorFill" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#13394b"/><stop offset="100%" stop-color="#0b2637"/></linearGradient><pattern id="waterPattern" width="18" height="12" patternUnits="userSpaceOnUse"><path d="M0 6 Q4 2 9 6 T18 6" fill="none" stroke="#2a637a" stroke-width="1" opacity=".5"/></pattern></defs>';
 svg+='<text x="'+x0+'" y="28" class="svg-kicker">ARCHIVED OPENMC GEOMETRY.XML · SOURCE-EXTRACTED</text><text x="'+x0+'" y="52" class="svg-title">C5G7 · '+cols+' × '+rows+' core lattice</text>';
 svg+='<text x="'+x0+'" y="72" class="svg-subtitle">'+escapeHtml(candidateId)+' · '+signature+' · '+(Number.isFinite(xwidth)?xwidth.toFixed(2):"—")+' × '+(Number.isFinite(yheight)?yheight.toFixed(2):"—")+' cm · assembly pitch '+Number(core.pitch_cm?.[0]).toFixed(2)+' cm</text>';
 svg+='<text x="'+(x0+cw/2)+'" y="'+(y0-11)+'" class="boundary-label boundary-reflective" text-anchor="middle">'+escapeHtml(modelBoundaryLabel("y","max"))+'</text>';
 svg+='<text x="'+(x0+cw/2)+'" y="'+(y0+ch+22)+'" class="boundary-label boundary-vacuum" text-anchor="middle">'+escapeHtml(modelBoundaryLabel("y","min"))+'</text>';
 svg+='<text x="'+(x0-18)+'" y="'+(y0+ch/2)+'" class="boundary-label boundary-reflective" text-anchor="middle" transform="rotate(-90 '+(x0-18)+' '+(y0+ch/2)+')">'+escapeHtml(modelBoundaryLabel("x","min"))+'</text>';
 svg+='<text x="'+(x0+cw+17)+'" y="'+(y0+ch/2)+'" class="boundary-label boundary-vacuum" text-anchor="middle" transform="rotate(90 '+(x0+cw+17)+' '+(y0+ch/2)+')">'+escapeHtml(modelBoundaryLabel("x","max"))+'</text>';
 grid.forEach((line,r)=>line.forEach((code,c)=>{
  const x=x0+c*(size+gap),y=y0+r*(size+gap);
  if(code==="R"){
   svg+='<g><rect x="'+x+'" y="'+y+'" width="'+size+'" height="'+size+'" rx="7" fill="url(#reflectorFill)" stroke="#3b7184"/><rect x="'+x+'" y="'+y+'" width="'+size+'" height="'+size+'" rx="7" fill="url(#waterPattern)"/><text x="'+(x+size/2)+'" y="'+(y+size/2-5)+'" class="reflector-title" text-anchor="middle">WATER</text><text x="'+(x+size/2)+'" y="'+(y+size/2+14)+'" class="reflector-title" text-anchor="middle">REFLECTOR</text><text x="'+(x+size/2)+'" y="'+(y+size/2+34)+'" class="reflector-sub" text-anchor="middle">'+Number(core.pitch_cm[0]).toFixed(2)+' cm pitch</text></g>';
  }else{
   const cell=assemblyMap[String(sourceGrid[r][c])],pins=modelGeometryData.pin_lattices[String(cell.lattice_id)]?.universe_grid;
   if(!Array.isArray(pins)||pins.length!==pinDims[1]||pins.some(pr=>!Array.isArray(pr)||pr.length!==pinDims[0]))throw new Error("Archived pin lattice "+cell.lattice_id+" does not match declared dimensions.");
   const color=code==="M"?"#f4bd62":"#51d2df",pp=Math.min(size-18,size-34)/pinDims[0],area=pp*pinDims[0],ix=x+(size-area)/2,iy=y+28;
   svg+='<g><rect x="'+x+'" y="'+y+'" width="'+size+'" height="'+size+'" rx="7" fill="#0a1a27" stroke="'+color+'" stroke-opacity=".72"/><rect x="'+(x+1)+'" y="'+(y+1)+'" width="'+(size-2)+'" height="24" rx="5" fill="'+color+'" fill-opacity=".12"/><text x="'+(x+8)+'" y="'+(y+16)+'" class="assembly-label" fill="'+color+'">p'+r+c+' · '+(code==="M"?"MOX":"UO₂")+'</text><text x="'+(x+size-8)+'" y="'+(y+16)+'" class="assembly-size" text-anchor="end">'+pinDims[0]+' × '+pinDims[1]+'</text>';
   pins.forEach((pr,pi)=>pr.forEach((uid,pj)=>{svg+=modelMaterialCell(uid,ix+pj*pp,iy+pi*pp,pp);}));
   svg+='<rect x="'+(ix-.6)+'" y="'+(iy-.6)+'" width="'+(area+1.2)+'" height="'+(area+1.2)+'" fill="none" stroke="#64899a" stroke-width=".7"/></g>';
  }
 }));
 const lx=624,ly=104;
 svg+='<line x1="605" y1="82" x2="605" y2="592" stroke="#29475a"/><text x="'+lx+'" y="'+ly+'" class="legend-title">PIN MATERIALS</text>';
 Object.entries(modelGeometryData.materials.pin_universes||{}).forEach(([uid,m],i)=>{
  const y=ly+27+i*29;svg+='<circle cx="'+(lx+7)+'" cy="'+(y-4)+'" r="5.2" fill="'+(pinUniverseColors[uid]||"#c1cbd2")+'"/><text x="'+(lx+22)+'" y="'+y+'" class="legend-text">'+escapeHtml(m.material_name||m.name||uid)+'</text>';
 });
 const my=ly+220,meta=[["Core lattice","ID "+core.id+" · "+dims.join(" × ")],["Fuel positions","2 × 2 · "+signature],["Pin lattice","IDs 101 (UO₂) / 103 (MOX)"],["Pin pitch / radius",Number(modelGeometryData.pin_geometry.pitch_cm[0]).toFixed(2)+" cm / "+Number(modelGeometryData.pin_geometry.pin_radius_cm).toFixed(2)+" cm"],["Assembly pitch",Number(core.pitch_cm[0]).toFixed(2)+" cm"],["Source","Archived geometry.xml"]];
 svg+='<line x1="'+lx+'" y1="'+(my-18)+'" x2="968" y2="'+(my-18)+'" stroke="#29475a"/><text x="'+lx+'" y="'+my+'" class="legend-title">SOURCE PARAMETERS</text>';
 meta.forEach((item,i)=>{const y=my+28+i*27;svg+='<text x="'+lx+'" y="'+y+'" class="meta-label">'+escapeHtml(item[0])+'</text><text x="'+lx+'" y="'+(y+13)+'" class="meta-value">'+escapeHtml(item[1])+'</text>';});
 const hash=String(source.geometry_xml_sha256||"");
 svg+='<rect x="'+lx+'" y="'+(my+195)+'" width="334" height="43" rx="7" fill="#102638" stroke="#2a4b5e"/><text x="'+(lx+12)+'" y="'+(my+212)+'" class="source-note">SOURCE SHA-256 · '+escapeHtml(hash.slice(0,16))+'…</text><text x="'+(lx+12)+'" y="'+(my+228)+'" class="source-note-secondary">XML-derived map · no transport run executed</text></svg>';
 return svg;
}
function sourceGeometryForCandidate(row){
 const signature=normalizeLayoutSignature(row?.layout_signature);
 return (modelGeometryData?.candidates||[]).find(item=>
  String(item.candidate_id)===String(row?.candidate_id)&&normalizeLayoutSignature(item.layout_signature)===signature);
}
function materialNameForUniverse(universeId){
 const material=modelGeometryData?.materials?.pin_universes?.[String(universeId)];
 return material?.material_name||material?.name||("Universe "+universeId);
}
function renderSelectedPinMapSvg(pins){
 const dims=modelGeometryData?.pin_geometry?.dimensions||[];
 if(!Array.isArray(pins)||pins.length!==17||pins.some(line=>!Array.isArray(line)||line.length!==17)){
  $("corePinLegend").innerHTML="";
  $("corePinMapBadge").textContent="NOT IN SOURCE";
  return '<div class="empty-state"><b>Pin-resolved map unavailable</b><p>The archived manifest does not provide a complete 17 × 17 pin-universe grid for this position. No pin pattern is fabricated.</p></div>';
 }
 const cell=14.2,x0=22,y0=20,size=cell*17,counts={};
 let svg='<svg class="core-pin-map-svg" viewBox="0 0 292 292" role="img" aria-label="Source-derived 17 by 17 pin universe lattice"><rect x="0" y="0" width="292" height="292" rx="9" fill="#07131e"/>';
 svg+='<text x="22" y="12" class="core-pin-map-axis">17 × 17 · SOURCE UNIVERSE GRID</text>';
 pins.forEach((line,r)=>line.forEach((uid,c)=>{
  const key=String(uid),color=pinUniverseColors[key]||"#8b9aa4";
  counts[key]=(counts[key]||0)+1;
  const x=x0+c*cell,y=y0+r*cell;
  svg+='<g><title>Pin r'+r+' c'+c+' · Universe '+escapeHtml(key)+' · '+escapeHtml(materialNameForUniverse(key))+'</title><rect x="'+(x+.5).toFixed(2)+'" y="'+(y+.5).toFixed(2)+'" width="'+(cell-1).toFixed(2)+'" height="'+(cell-1).toFixed(2)+'" rx="1.6" fill="'+color+'" stroke="#0b1b28" stroke-width=".65"/></g>';
 }));
 svg+='<rect x="'+x0+'" y="'+y0+'" width="'+size+'" height="'+size+'" fill="none" stroke="#a9c1ce" stroke-opacity=".65" stroke-width="1.2"/>';
 svg+='<text x="'+(x0+size/2)+'" y="276" text-anchor="middle" class="core-pin-map-axis">PITCH '+number(modelGeometryData.pin_geometry?.pitch_cm?.[0],2)+' cm · RADIUS '+number(modelGeometryData.pin_geometry?.pin_radius_cm,2)+' cm</text></svg>';
 $("corePinLegend").innerHTML=Object.entries(counts).map(([uid,count])=>'<span class="core-pin-legend-item"><i style="background:'+pinUniverseColors[uid]+'"></i><b>'+escapeHtml(materialNameForUniverse(uid))+'</b><small>'+count+' pins</small></span>').join("");
 $("corePinMapBadge").textContent=dims.join(" × ");
 return svg;
}
function updateCoreInspector(row,gridRow=selectedCorePosition.row,gridCol=selectedCorePosition.col){
 const title=$("coreSelectionTitle"),sub=$("coreSelectionSubtitle"),badge=$("coreAssemblyBadge"),facts=$("coreSelectedFacts"),pinMap=$("coreSelectedPinMap"),pinTitle=$("corePinMapTitle"),pinSub=$("corePinMapSubtitle");
 if(!modelGeometryData||!row||!title||!facts||!pinMap)return;
 const source=sourceGeometryForCandidate(row);
 if(!source){title.textContent="No matching source geometry";sub.textContent="Candidate identity check failed";facts.innerHTML='<div class="empty-state"><b>Geometry not matched</b><p>No exact candidate/signature pair exists in the XML-derived manifest.</p></div>';pinMap.innerHTML="";return;}
 const r=Math.max(0,Math.min(2,Number(gridRow)||0)),c=Math.max(0,Math.min(2,Number(gridCol)||0));
 selectedCorePosition={row:r,col:c};
 const uid=String(source.core_universe_grid?.[r]?.[c]??"");
 const code=String(source.assembly_grid?.[r]?.[c]||modelGeometryData.assemblies?.[uid]?.code||"");
 const assembly=modelGeometryData.assemblies?.[uid]||{};
 const position="p"+r+c, fuel=code==="M"||code==="U";
 const signature=normalizeLayoutSignature(row.layout_signature);
 const positionCode=(r<2&&c<2)?signature[r*2+c]:code;
 const material=code==="M"?"MOX fuel":code==="U"?"UO₂ fuel":"Water reflector";
 title.textContent=material+" · "+position;
 sub.textContent=String(row.candidate_id)+" · source universe "+uid;
 badge.textContent=position.toUpperCase();
 const core=modelGeometryData.core_lattice||{},pinsMeta=modelGeometryData.pin_geometry||{};
 const factsRows=[
  ["Core position",position+" · row "+r+" / col "+c],
  ["Fuel assignment",fuel?(positionCode==="M"?"MOX":"UO₂")+" · candidate signature "+signature:"Invariant reflector"],
  ["OpenMC universe",uid+" · "+displayValue(assembly.name,material)],
  ["Lattice ID",fuel?String(assembly.lattice_id??"not recorded"):"Reflector universe; no pin grid supplied"],
  ["Assembly pitch",number(core.pitch_cm?.[0],2)+" × "+number(core.pitch_cm?.[1],2)+" cm"],
  ["Pin pitch / radius",fuel?number(pinsMeta.pitch_cm?.[0],2)+" / "+number(pinsMeta.pin_radius_cm,2)+" cm":"Not resolved for reflector"],
  ["Source identity",String(source.geometry_xml_sha256||"unavailable").slice(0,18)+"…"]
 ];
 facts.innerHTML=factsRows.map(([labelText,value])=>'<div class="core-fact"><span>'+escapeHtml(labelText)+'</span><b>'+escapeHtml(value)+'</b></div>').join("");
 if(fuel){
  const lattice=modelGeometryData.pin_lattices?.[String(assembly.lattice_id)]?.universe_grid;
  pinTitle.textContent="Fuel pin material map";
  pinSub.textContent="Actual universe IDs from archived geometry.xml · categorical material map, not neutron flux";
  pinMap.innerHTML=renderSelectedPinMapSvg(lattice);
 }else{
  pinTitle.textContent="Reflector source detail";
  pinSub.textContent="The geometry manifest has no pin-resolved reflector universe grid";
  pinMap.innerHTML='<div class="core-reflector-detail"><span class="core-reflector-icon">R</span><div><b>Water / reflector universe '+escapeHtml(uid)+'</b><p>The archived manifest identifies this core position as reflector but does not provide a pin-resolved 17 × 17 grid for it. No internal material cells are invented.</p></div></div>';
  $("corePinMapBadge").textContent="SOURCE-LIMITED";
  $("corePinLegend").innerHTML='<span class="core-pin-legend-item"><i style="background:#17495d"></i><b>Water reflector</b><small>Assembly universe</small></span>';
 }
}
function setCoreGeometryMode(mode){
 if(mode==="3d"&&core3dLoadFailed)mode="2d";
 coreGeometryMode=mode==="2d"?"2d":"3d";
 const view3d=$("core3dViewport"),map2d=$("geometryPreview");
 if(view3d)view3d.hidden=coreGeometryMode!=="3d";
 if(map2d)map2d.hidden=coreGeometryMode!=="2d";
 const b3=$("coreView3d"),b2=$("coreView2d");
 if(b3){b3.classList.toggle("active",coreGeometryMode==="3d");b3.setAttribute("aria-pressed",String(coreGeometryMode==="3d"));}
 if(b2){b2.classList.toggle("active",coreGeometryMode==="2d");b2.setAttribute("aria-pressed",String(coreGeometryMode==="2d"));}
 if(coreGeometryMode==="3d"){
  if(!window.CBPFRCore3D){
   const status=$("core3dStatus");
   if(status)status.textContent=window.CBPFRCore3DError?"THREE.JS CDN UNAVAILABLE":"CONNECTING THREE.JS CDN…";
   if(window.CBPFRCore3DError){core3dLoadFailed=true;setCoreGeometryMode("2d");}
   else if($("core3dCanvas")&&!$("core3dCanvas").children.length)$("core3dCanvas").innerHTML='<div class="core3d-loading"><span></span><b>Loading Three.js scientific renderer…</b><small>The source SVG map remains available in 2D source map mode.</small></div>';
  }else if(currentGeometryRow&&!geometryArtifactActive){
   drawCore3DForCandidate(currentGeometryRow);
  }
 }else{
  const status=$("core3dStatus");
  if(status)status.textContent=core3dLoadFailed?"2D SOURCE FALLBACK":"2D XML MAP · SOURCE GEOMETRY";
 }
}
function selectCoreAssembly(cell){
 if(!cell||!Number.isFinite(Number(cell.row))||!Number.isFinite(Number(cell.col)))return;
 selectedCorePosition={row:Number(cell.row),col:Number(cell.col)};
 if(currentGeometryRow)updateCoreInspector(currentGeometryRow,selectedCorePosition.row,selectedCorePosition.col);
 if(core3dViewer)core3dViewer.highlight(selectedCorePosition.row,selectedCorePosition.col);
}
function drawCore3DForCandidate(row){
 if(!row||!modelGeometryData||coreGeometryMode!=="3d")return;
 const host=$("core3dCanvas");
 if(!host)return;
 if(!window.CBPFRCore3D){
  const status=$("core3dStatus");
  if(status)status.textContent=window.CBPFRCore3DError?"THREE.JS CDN UNAVAILABLE":"CONNECTING THREE.JS CDN…";
  return;
 }
 try{
  if(!core3dViewer)core3dViewer=window.CBPFRCore3D.createCoreViewer(host,selectCoreAssembly);
  const info=core3dViewer.update(modelGeometryData,row,selectedCorePosition);
  const status=$("core3dStatus");
  if(status){status.classList.remove("warning");status.textContent="WEBGL READY · THREE.JS R"+info.libraryVersion+" · "+info.pinCount.toLocaleString()+" PIN INSTANCES";}
  const pitch=info.corePitchCm||[21.42,21.42],dims=info.coreDimensions||[3,3];
  if($("coreModelDimensions"))$("coreModelDimensions").textContent=dims.join(" × ")+" CORE · "+number(pitch[0]*dims[0],2)+" × "+number(pitch[1]*dims[1],2)+" cm · PITCH "+number(pitch[0],2)+" cm";
  if($("coreSourceBadge"))$("coreSourceBadge").textContent="XML SOURCE · IDENTITY MATCHED";
 }catch(error){
  core3dLoadFailed=true;
  const status=$("core3dStatus");
  if(status){status.classList.add("warning");status.textContent="WEBGL UNAVAILABLE · 2D SOURCE MAP";}
  if($("core3dCanvas"))$("core3dCanvas").innerHTML='<div class="core3d-loading"><b>3D renderer unavailable</b><small>'+escapeHtml(error.message||error)+'</small><small>The source-derived SVG map is available in 2D source map mode.</small></div>';
  setCoreGeometryMode("2d");
 }
}
function setupCoreGeometryControls(){
 const b3=$("coreView3d"),b2=$("coreView2d"),reset=$("coreResetView");
 if(b3&&!b3.dataset.bound){b3.dataset.bound="true";b3.addEventListener("click",()=>{geometryArtifactActive=false;const row=records.find(item=>String(item.candidate_id)===String($("candidateSelect")?.value));if(row){currentGeometryRow=row;const preview=$("geometryPreview");if(preview)preview.innerHTML=renderModelGeometrySvg(row);updateCoreInspector(row); }setCoreGeometryMode("3d");});}
 if(b2&&!b2.dataset.bound){b2.dataset.bound="true";b2.addEventListener("click",()=>{if(currentGeometryRow&&!geometryArtifactActive){const preview=$("geometryPreview");if(preview)preview.innerHTML=renderModelGeometrySvg(currentGeometryRow);}setCoreGeometryMode("2d");});}
 if(reset&&!reset.dataset.bound){reset.dataset.bound="true";reset.addEventListener("click",()=>{if(core3dViewer)core3dViewer.reset();});}
}
function drawModelGeometry(row){
 const preview=$("geometryPreview");if(!preview||!row||geometryArtifactActive)return;
 currentGeometryRow=row;
 const sig=normalizeLayoutSignature(row.layout_signature);
 preview.innerHTML=renderModelGeometrySvg(row);
 if(!modelGeometryData){$("geometryCaption").textContent="OpenMC geometry manifest unavailable; model view not shown.";return;}
 const source=sourceGeometryForCandidate(row);
 if(!source){$("geometryCaption").textContent="No exact candidate ID and layout match exists in the source manifest.";return;}
 $("geometryCaption").textContent="SOURCE "+source.source_member+" · GEOMETRY.XML SHA-256 "+String(source.geometry_xml_sha256||"unavailable")+" · exact candidate/signature match confirmed · visualization only, not a transport result.";
 updateCoreInspector(row,selectedCorePosition.row,selectedCorePosition.col);
 if(coreGeometryMode==="3d")drawCore3DForCandidate(row);
}

async function initModelGeometry(){
 setupCoreGeometryControls();
 try{
  const response=await fetch("/api/model-geometry",{headers:{Accept:"application/json"}});
  if(!response.ok)throw new Error("HTTP "+response.status);
  const payload=await response.json();
  if(payload.schema_version!==1||!Array.isArray(payload.candidates)||payload.candidates.length!==6||!payload.core_lattice||!payload.pin_lattices)throw new Error("Incomplete or unsupported OpenMC geometry manifest.");
  modelGeometryData=payload;
  $("geometryStatus").textContent="XML SOURCE MATCHED";
  $("geometryStatus").classList.remove("warning");
  $("geometryProvenance").textContent="Manifest schema v"+payload.schema_version+" · "+payload.candidates.length+" candidate geometry.xml records · "+payload.core_lattice.dimensions.join(" × ")+" core lattice · 17 × 17 fuel-pin grids · material universe map and boundary conditions from archived input XML. Three.js "+(window.CBPFRCore3D?"loaded":"loading")+" from jsDelivr; axial dimensions are not present in this 2D manifest.";
  $("coreSourceBadge").textContent="XML-DERIVED";
  if(window.CBPFRCore3DError){core3dLoadFailed=true;setCoreGeometryMode("2d");}
  return true;
 }catch(error){
  modelGeometryData=null;
  if($("geometryStatus")){$("geometryStatus").textContent="MODEL MANIFEST UNAVAILABLE";$("geometryStatus").classList.add("warning");}
  if($("geometryProvenance"))$("geometryProvenance").textContent="Cannot load OpenMC geometry manifest: "+String(error.message||error);
  if($("geometryPreview"))$("geometryPreview").innerHTML='<div class="empty-state"><b>Model geometry unavailable</b><p>'+escapeHtml(error.message||error)+'</p><p>No substitute geometry is fabricated.</p></div>';
  if($("geometryCaption"))$("geometryCaption").textContent="Geometry not shown.";
  if($("core3dCanvas"))$("core3dCanvas").innerHTML='<div class="empty-state"><b>No source geometry</b><p>Three-dimensional geometry is blocked until the archived manifest loads.</p></div>';
  return false;
 }
}

function drawSelectedCandidate(row){
 const signature=normalizeLayoutSignature(row.layout_signature);
 const tag=$("selectedRecordTag");
 const layoutValid=isValidLayoutSignature(signature);
 const canonical=(row.canonical_reference===true||String(row.canonical_reference).toLowerCase()==="true")&&layoutValid;
 if(tag){
  tag.textContent=!layoutValid?"INVALID LAYOUT":canonical?"CANONICAL LAYOUT REFERENCE":"LAYOUT VARIANT";
  // A valid non-canonical layout is a candidate variant, not a failed integrity check.
  tag.classList.toggle("warning",!layoutValid);
  tag.classList.toggle("reference",canonical);
 }
 const selectedIndex=records.findIndex(item=>String(item.candidate_id)===String(row.candidate_id));
 const order=has(row,"descriptive_keff_order")?"descriptive k-effective order "+row.descriptive_keff_order+" / "+records.length:"order not recorded";
 $("selectedCandidateId").textContent=String(row.candidate_id??"Candidate not identified");
 $("selectedCandidateMetaLine").textContent="Candidate "+(selectedIndex>=0?selectedIndex+1:"—")+" of "+records.length+" · Layout "+(signature||"not recorded")+" · "+order;
 $("selectedCandidateSignature").innerHTML=isValidLayoutSignature(signature)?signature.split("").map((code,i)=>'<div class="signature-cell '+(code==="M"?"signature-mox":"signature-uo2")+'"><b>'+code+'</b><small>'+["p00","p01","p10","p11"][i]+'</small></div>').join(""):'<span class="muted">No validated layout signature</span>';
 const keffSd=has(row,"keff_std_dev")?"Reported SD ± "+number(row.keff_std_dev,6)+"; not a confidence interval":"Reported SD unavailable";
 const metrics=[
  ["k-effective mean",has(row,"keff_mean")?number(row.keff_mean,6):"Not recorded","keff",keffSd],
  ["Relative SD",has(row,"keff_relative_sd_percent")?number(row.keff_relative_sd_percent,4)+"%":"Not recorded","uncertainty","Relative spread recorded in candidate summary"],
  ["Aggregate flux score",has(row,"aggregate_flux_score")?number(row.aggregate_flux_score,5):"Not recorded","flux","Repository score; units not specified"],
  ["Aggregate fission score",has(row,"aggregate_fission_score")?number(row.aggregate_fission_score,5):"Not recorded","proxy","Not absolute power"]
 ];
 $("selectedCandidateMetrics").innerHTML=metrics.map(([name,value,type,detail])=>'<div class="candidate-stat candidate-stat-'+type+'"><span>'+name+'</span><strong>'+value+'</strong><small>'+detail+'</small></div>').join("");
 const runInfo=[
  ["SEED",displayValue(row.seed)],
  ["BATCHES",displayValue(row.batches)],
  ["INACTIVE",displayValue(row.inactive)],
  ["PARTICLES / BATCH",displayValue(row.particles_per_batch)]
 ];
 $("selectedCandidateRunInfo").innerHTML=runInfo.map(([name,value])=>'<div class="run-meta"><span>'+name+'</span><b>'+escapeHtml(value)+'</b></div>').join("");
 const unchanged=has(row,"mutated_preexisting_file_count")&&Number(row.mutated_preexisting_file_count)===0;
 const mgxsStable=Boolean(row.mgxs_sha256_before_transport&&row.mgxs_sha256_before_transport===row.mgxs_sha256_after_transport);
 $("selectedCandidateChecks").innerHTML='<span class="micro-check '+(unchanged?"ok":"")+'"><i></i>'+(unchanged?"No pre-existing file mutation recorded":"Mutation check unavailable")+'</span><span class="micro-check '+(mgxsStable?"ok":"")+'"><i></i>'+(mgxsStable?"MGXS hash unchanged across recorded run":"MGXS hash comparison unavailable")+'</span>';
}
function clearCandidateSelection(message="No candidate selected."){
 $("layoutView").innerHTML='<div class="empty-state"><b>No candidate selected</b><p>'+escapeHtml(message)+'</p></div>';
 $("layoutCaption").textContent=message;
 $("selectedRecordTag").textContent="NO SELECTION";
 $("selectedRecordTag").classList.add("warning");
 $("selectedCandidateId").textContent="No candidate selected";
 $("selectedCandidateMetaLine").textContent="Select a recorded candidate to inspect its configuration.";
 $("selectedCandidateSignature").textContent="—";
 $("selectedCandidateMetrics").innerHTML='<div class="empty-state"><b>Metrics unavailable</b><p>No candidate is selected.</p></div>';
 $("selectedCandidateRunInfo").innerHTML="";
 $("selectedCandidateChecks").innerHTML="";
 geometryArtifactActive=false;
 if($("geometryPreview"))$("geometryPreview").innerHTML='<div class="empty-state"><b>No candidate selected</b><p>Select a candidate to show its linked model view.</p></div>';
 if($("geometryCaption"))$("geometryCaption").textContent="No candidate selected.";
 if(records.length)drawCandidateChart();
 if(assemblyRecords.length)drawAssemblyField();
 else if($("assemblyMap"))$("assemblyMap").innerHTML='<div class="empty-state"><b>No candidate selected</b><p>Select a candidate to inspect recorded assembly evidence.</p></div>';
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
 const selector=$("candidateSelect");
 const id=String(selector?.value??"");
 const row=records.find(r=>String(r.candidate_id)===id);
 if(!row){clearCandidateSelection(id?"The selected identifier does not match a recorded candidate.":"Choose a candidate from the selector.");return;}
 $("selectedRecordTag").classList.remove("warning");
 $("layoutView").innerHTML=layoutCells(row.layout_signature);
 $("layoutCaption").textContent=label(row)+" · seed "+displayValue(row.seed,"not recorded")+" · signature "+displayValue(row.layout_signature,"not recorded");
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
 const isKeff=key==="keff_mean";
 const colors=valid.map(r=>String(r.candidate_id)===selected?palette.cyan:"#47758f");
 const trace={
  type:"scatter",mode:"markers",name:isKeff?"Reported k-effective mean":"Recorded aggregate score",
  x:valid.map(r=>Number(r[key])),y:valid.map(r=>String(r.layout_signature||label(r))),
  marker:{color:colors,size:valid.map(r=>String(r.candidate_id)===selected?13:9),symbol:valid.map(r=>String(r.candidate_id)===selected?"diamond":"circle"),line:{color:valid.map(r=>String(r.candidate_id)===selected?palette.text:"#102536"),width:1.2}},
  customdata:valid.map(r=>[r.candidate_id,r.layout_signature,r.seed,has(r,"keff_std_dev")?Number(r.keff_std_dev):null]),
  hovertemplate:"Candidate %{customdata[0]}<br>Layout %{customdata[1]}<br>Seed %{customdata[2]}<br>Value %{x:.7g}"+(isKeff?"<br>Reported SD %{customdata[3]:.4g}":"")+"<extra></extra>"
 };
 if(isKeff){
  trace.error_x={type:"data",array:valid.map(r=>has(r,"keff_std_dev")?Number(r.keff_std_dev):0),visible:true,color:palette.muted,thickness:1.4,width:5};
 }
 chart("candidateChart",[trace],{
  autosize:true,margin:{l:90,r:30,t:16,b:58},showlegend:false,hovermode:"closest",
  xaxis:{...baseLayout.xaxis,title:isKeff?"Reported k-effective mean (± SD)":"Recorded repository score (units not specified)",automargin:true,gridcolor:palette.line,zeroline:false,tickangle:0,tickformat:isKeff?".3f":".4g"},
  yaxis:{...baseLayout.yaxis,title:"Layout signature",type:"category",autorange:"reversed",automargin:true,tickangle:0,tickfont:{size:11,color:palette.muted},gridcolor:"rgba(38,63,82,0.55)"},
  annotations:[]
 });
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
  const payload=await response.json();records=validateCandidateRecords(payload.records);metadata=payload.metadata||{};
  $("sourcePath").textContent=metadata.source||"Source path not provided by API";
  const layouts=new Set(records.map(r=>r.layout_signature).filter(Boolean));
  const seeds=new Set(records.map(r=>String(r.seed)).filter(s=>s!=="undefined"&&s!=="null"));
  const ks=records.filter(r=>has(r,"keff_mean")).map(r=>Number(r.keff_mean));
  const metrics=[["Candidate records",records.length.toLocaleString(),"Rows in current candidate summary"],["Unique layouts",layouts.size.toLocaleString(),"Distinct recorded signatures"],["k-effective span",ks.length?number(Math.min(...ks),5)+" – "+number(Math.max(...ks),5):"—","Reported mean values"],["Recorded seeds",seeds.size.toLocaleString(),"Distinct seed values"]];
  $("metrics").innerHTML=metrics.map(m=>'<article class="metric"><label>'+m[0]+'</label><strong>'+m[1]+'</strong><small>'+m[2]+'</small></article>').join("");
  $("candidateSelect").innerHTML=records.map(candidateOption).join("");
  await initModelGeometry();
  $("candidateSelect").addEventListener("change",showCandidate);$("metricSelect").addEventListener("change",drawCandidateChart);
  showCandidate();drawOtherCharts();
  await initAssembly();
  await initGeometry();
  await initMesh();
 }catch(error){
  showError("Could not load recorded evidence: "+error.message+". Start the local Python server from the repository root and check the source CSV path.");
  clearCandidateSelection("Candidate evidence unavailable: "+error.message);
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
 const finite=values.flat().filter(v=>typeof v==="number"&&Number.isFinite(v));
 const positive=finite.filter(v=>v>0);
 return {
  finite:finite.length,positive:positive.length,
  min:finite.length?Math.min(...finite):null,
  max:finite.length?Math.max(...finite):null,
  mean:finite.length?finite.reduce((a,b)=>a+b,0)/finite.length:null
 };
}
function meshCoordinateInfo(item){
 const dims=item?.dimensions||[],geometry=item?.spatial_geometry||{};
 const lower=geometry.lower_left_cm,upper=geometry.upper_right_cm;
 const nx=Number(dims[0]),ny=Number(dims[1]);
 const physical=geometry.coordinates_available===true&&geometry.coordinate_units==="cm"&&
  Array.isArray(lower)&&Array.isArray(upper)&&lower.length>=2&&upper.length>=2&&
  Number.isFinite(Number(lower[0]))&&Number.isFinite(Number(lower[1]))&&
  Number.isFinite(Number(upper[0]))&&Number.isFinite(Number(upper[1]))&&
  Number(upper[0])>Number(lower[0])&&Number(upper[1])>Number(lower[1])&&nx>0&&ny>0;
 if(physical){
  const lx=Number(lower[0]),ly=Number(lower[1]),ux=Number(upper[0]),uy=Number(upper[1]);
  return {physical:true,
   x:Array.from({length:nx},(_,i)=>lx+(i+0.5)*(ux-lx)/nx),
   y:Array.from({length:ny},(_,i)=>ly+(i+0.5)*(uy-ly)/ny),
   xRange:[lx,ux],yRange:[ly,uy],xTitle:"X position (cm)",yTitle:"Y position (cm)",
   xHoverLabel:"X position %{x:.4g} cm",yHoverLabel:"Y position %{y:.4g} cm"};
 }
 return {physical:false,x:Array.from({length:nx},(_,i)=>i),y:Array.from({length:ny},(_,i)=>i),
  xRange:null,yRange:null,xTitle:"X mesh-bin index (0-based)",yTitle:"Y mesh-bin index (0-based)",
  xHoverLabel:"X-bin %{x}",yHoverLabel:"Y-bin %{y}"};
}
function niceAxisStep(span,target=6){
 if(!Number.isFinite(span)||span<=0)return undefined;
 const raw=span/target,power=Math.pow(10,Math.floor(Math.log10(raw))),scaled=raw/power;
 return (scaled<=1?1:scaled<=2?2:scaled<=2.5?2.5:scaled<=5?5:10)*power;
}
function currentField(){
 if(!meshData||!Array.isArray(meshData.mesh_tallies)||!meshData.mesh_tallies.length)return null;
 const score=$("meshScore").value, view=$("meshView").value, scale=$("meshScale").value;
 const item=meshData.mesh_tallies[0], record=item.scores?.[score];
 if(!record)return null;
 const coordinates=meshCoordinateInfo(item);
 const mean=record.mean;
 // "std_dev" remains as a backwards-compatible API field; in the audited reader,
 // its stored values are the Monte Carlo standard error, not sample standard deviation.
 const standardError=record.standard_error||record.std_dev;
 if(!Array.isArray(mean)||!Array.isArray(standardError)||mean.length!==item.dimensions[1]||standardError.length!==mean.length)return null;
 if(mean.some((row,i)=>!Array.isArray(row)||!Array.isArray(standardError[i])||row.length!==item.dimensions[0]||standardError[i].length!==row.length))return null;
 const relative=mean.map((row,y)=>row.map((v,x)=>
  Number.isFinite(v)&&v>0&&Number.isFinite(standardError[y][x])&&standardError[y][x]>=0
   ?100*standardError[y][x]/v:null
 ));
 const values=(view==="relative_sd"?relative:mean).map(row=>row.map(v=>{
  if(typeof v!=="number"||!Number.isFinite(v))return null;
  if(view==="mean"&&scale==="log")return v>0?Math.log10(v):null;
  return v;
 }));
 const colorTitle=view==="relative_sd"
  ?"Relative Monte Carlo standard error (%)"
  :(scale==="log"?"log₁₀(tally mean)":"Tally mean");
 const rawValues=view==="relative_sd"?relative:mean;
 return {
  item,score,view,scale,mean,standardError,sd:standardError,relative,rawValues,values,colorTitle,coordinates,
  stats:fieldStats(mean),displayStats:fieldStats(values)
 };
}
function drawMesh(){
 if(!meshData)return;
 const f=currentField();
 if(!f){
  $("meshStatus").textContent="SCORE UNAVAILABLE";
  ["meshHeatmap","meshContour","meshProfile","meshSurface"].forEach(id=>{
   $(id).innerHTML='<div class="empty-state"><b>Selected field unavailable</b><p>The requested score is not present in the recorded mesh tally.</p></div>';
  });
  return;
 }
 const paletteName=$("meshPalette").value;
 const z=f.values, raw=f.rawValues, scoreLabel=f.score;
 const nx=f.item.dimensions[0], ny=f.item.dimensions[1], coordinates=f.coordinates;
 const xs=coordinates.x, ys=coordinates.y;
 const plotTitle=f.view==="relative_sd"?"Relative Monte Carlo standard error (%)":(f.scale==="log"?"log₁₀("+scoreLabel+" tally mean)":"Recorded "+scoreLabel+" tally mean");
 const rawTitle=f.view==="relative_sd"?"Relative Monte Carlo standard error (%)":scoreLabel+" tally mean (recorded scale)";
 const hover=(title)=>coordinates.xHoverLabel+"<br>"+coordinates.yHoverLabel+"<br>"+title+" %{customdata:.6g}<extra></extra>";
 const axisStyle={...baseLayout.xaxis,gridcolor:palette.line,linecolor:palette.line,zerolinecolor:palette.line,automargin:true};
 const yAxisStyle={...baseLayout.yaxis,gridcolor:palette.line,linecolor:palette.line,zerolinecolor:palette.line,automargin:true};
 const sharedAxis={tickfont:{size:10,color:palette.muted},titlefont:{size:11,color:palette.muted}};
 const colorscale=paletteName;
 const heatLayout={
  autosize:true,margin:{l:62,r:30,t:18,b:58},showlegend:false,
  xaxis:{...axisStyle,...sharedAxis,title:{text:coordinates.xTitle,standoff:8},dtick:coordinates.physical?niceAxisStep(coordinates.xRange[1]-coordinates.xRange[0]):5,tickformat:coordinates.physical?".1f":undefined,range:coordinates.physical?coordinates.xRange:undefined,autorange:coordinates.physical?false:undefined},
  yaxis:{...yAxisStyle,...sharedAxis,title:{text:coordinates.yTitle,standoff:8},dtick:coordinates.physical?niceAxisStep(coordinates.yRange[1]-coordinates.yRange[0]):5,tickformat:coordinates.physical?".1f":undefined,range:coordinates.physical?coordinates.yRange:undefined,autorange:coordinates.physical?false:"reversed"}
 };
 const finiteZ=z.flat().filter(v=>typeof v==="number"&&Number.isFinite(v));
 const zMin=finiteZ.length?Math.min(...finiteZ):0, zMax=finiteZ.length?Math.max(...finiteZ):1;
 const zSpan=zMax-zMin;
 const rawStep=zSpan>0?zSpan/8:Math.max(Math.abs(zMin)*0.05,0.1);
 const power=Math.pow(10,Math.floor(Math.log10(rawStep)));
 const scaled=rawStep/power;
 const niceFactor=scaled<=1?1:scaled<=2?2:scaled<=2.5?2.5:scaled<=5?5:10;
 const contourStep=niceFactor*power;
 const contourStart=Math.floor(zMin/contourStep)*contourStep;
 let contourEnd=Math.ceil(zMax/contourStep)*contourStep;
 if(contourEnd<=contourStart)contourEnd=contourStart+contourStep;
 const colorbar={title:{text:plotTitle,font:{size:10,color:palette.text}},thickness:12,outlinewidth:0,tickfont:{size:9,color:palette.muted}};
 chart("meshHeatmap",[{
  type:"heatmap",x:xs,y:ys,z:z,customdata:raw,colorscale,
  colorbar:{...colorbar,title:{text:plotTitle,font:{size:10,color:palette.text}}},
  hovertemplate:hover(rawTitle),connectgaps:false,hoverongaps:false,xgap:0,ygap:0
 }],heatLayout);
 chart("meshContour",[{
  type:"contour",x:xs,y:ys,z:z,customdata:raw,colorscale,
  autocontour:false,
  contours:{
   coloring:"heatmap",showlines:true,showlabels:true,
   start:contourStart,end:contourEnd,size:contourStep,
   labelfont:{size:10,color:palette.text},
   labelformat:f.view==="relative_sd"?".1f":".2f"
  },
  line:{width:1,color:"rgba(7,17,27,0.72)"},
  colorbar:{...colorbar,title:{text:plotTitle,font:{size:10,color:palette.text}}},
  hovertemplate:hover(rawTitle),connectgaps:false,hoverongaps:false
 }],heatLayout);
 chart("meshSurface",[{
  type:"surface",x:xs,y:ys,z:z,surfacecolor:z,customdata:raw,colorscale,
  colorbar:{...colorbar,title:{text:plotTitle,font:{size:10,color:palette.text}}},
  hovertemplate:coordinates.xHoverLabel+"<br>"+coordinates.yHoverLabel+"<br>"+rawTitle+" %{customdata:.6g}<br>Displayed Z %{z:.6g}<extra></extra>",
  connectgaps:false,hoverongaps:false,showscale:true,
  lighting:{ambient:0.72,diffuse:0.78,specular:0.18,roughness:0.72,fresnel:0.08},opacity:0.98
 }],{
  autosize:true,margin:{l:8,r:8,t:8,b:8},
  scene:{
   xaxis:{title:{text:coordinates.physical?"X position (cm)":"X mesh-bin index",font:{size:11}},gridcolor:palette.line,color:palette.muted,backgroundcolor:"rgba(0,0,0,0)",showbackground:true,range:coordinates.physical?coordinates.xRange:undefined},
   yaxis:{title:{text:coordinates.physical?"Y position (cm)":"Y mesh-bin index",font:{size:11}},gridcolor:palette.line,color:palette.muted,backgroundcolor:"rgba(0,0,0,0)",showbackground:true,range:coordinates.physical?coordinates.yRange:undefined},
   zaxis:{title:{text:plotTitle,font:{size:10}},gridcolor:palette.line,color:palette.muted,backgroundcolor:"rgba(0,0,0,0)",showbackground:true},
   bgcolor:"rgba(0,0,0,0)",aspectmode:"auto",camera:{eye:{x:1.55,y:1.55,z:1.1}}
  }
 });
 const centerY=Math.floor((ny-1)/2);
 const meanRow=f.mean[centerY]||[], seRow=f.standardError[centerY]||[], relativeRow=f.relative[centerY]||[];
 const profileY=f.view==="relative_sd"?relativeRow:meanRow;
 const profileCustom=xs.map((x,i)=>[meanRow[i],seRow[i],relativeRow[i]]);
 const profileHover=f.view==="relative_sd"
  ?coordinates.xHoverLabel+"<br>Relative Monte Carlo standard error %{y:.4g}%<extra></extra>"
  :coordinates.xHoverLabel+"<br>Recorded "+scoreLabel+" tally mean %{y:.6g}<br>Monte Carlo standard error %{customdata[1]:.4g}<extra></extra>";
 const profileError=f.view==="mean"?{
  type:"data",symmetric:false,
  array:seRow.map((se,i)=>Number.isFinite(se)&&se>=0?se:0),
  arrayminus:seRow.map((se,i)=>Number.isFinite(se)&&se>=0&&Number.isFinite(meanRow[i])?Math.min(se,Math.max(0,meanRow[i]*0.999999)):0),
  visible:true,color:palette.muted,thickness:1,width:3
 }:{visible:false};
 chart("meshProfile",[{
  type:"scatter",mode:"lines+markers",name:f.view==="relative_sd"?"Relative MC standard error":"Recorded "+scoreLabel+" mean",
  x:xs,y:profileY,customdata:profileCustom,
  line:{color:palette.cyan,width:2.5,shape:"linear"},
  marker:{size:5,color:palette.orange,line:{color:palette.text,width:0.6}},
  error_y:profileError,connectgaps:false,hovertemplate:profileHover
 }],{
  autosize:true,margin:{l:76,r:24,t:20,b:60},showlegend:false,
  xaxis:{...axisStyle,...sharedAxis,title:{text:coordinates.xTitle,standoff:8},dtick:coordinates.physical?niceAxisStep(coordinates.xRange[1]-coordinates.xRange[0]):5,tickformat:coordinates.physical?".1f":undefined,range:coordinates.physical?coordinates.xRange:undefined,autorange:coordinates.physical?false:undefined},
  yaxis:{...yAxisStyle,...sharedAxis,type:f.view==="mean"&&f.scale==="log"?"log":"linear",dtick:f.view==="mean"&&f.scale==="log"?1:undefined,title:{text:f.view==="relative_sd"?"Relative Monte Carlo standard error (%)":"Recorded "+scoreLabel+" tally mean"+(f.scale==="log"?" (logarithmic axis)":""),standoff:8},exponentformat:"power"},
  annotations:[{xref:"paper",yref:"paper",x:1,y:1.12,xanchor:"right",yanchor:"bottom",showarrow:false,text:coordinates.physical?"Central cut: Y = "+coordinates.y[centerY].toFixed(3)+" cm · row "+centerY:"Central cut: Y-bin "+centerY+" (0-based)",font:{size:10,color:palette.muted}}]
 });
 if($("meshContourSubtitle"))$("meshContourSubtitle").textContent=f.view==="relative_sd"
  ?"Labelled iso-contours of relative Monte Carlo standard error (%)"
  :f.scale==="log"?"Labelled iso-contours; colour levels use log₁₀(mean), hover reports the recorded mean":"Labelled iso-contours of recorded tally mean";
 if($("meshProfileSubtitle"))$("meshProfileSubtitle").textContent=coordinates.physical?"Central cut at Y = "+coordinates.y[centerY].toFixed(3)+" cm (row "+centerY+")":"Central cut at Y-bin "+centerY+" (0-based index)";
 const st=f.stats,finiteDisplay=f.displayStats.finite,dimensionText=nx+" × "+ny;
 $("fieldKpis").innerHTML=[
  ["Mesh dimensions",dimensionText,"Archived 2D mesh bins"],
  ["Finite bins",finiteDisplay.toLocaleString(),"Valid bins in selected view"],
  ["Positive mean bins",st.positive.toLocaleString(),"Positive recorded mean values"],
  ["Maximum mean",st.max===null?"—":st.max.toExponential(4),"Recorded "+scoreLabel+" tally · source scale"]
 ].map(m=>'<article class="metric"><label>'+m[0]+'</label><strong>'+m[1]+'</strong><small>'+m[2]+'</small></article>').join("");
 const summary=[
  "Score: "+scoreLabel,
  "View: "+(f.view==="relative_sd"?"relative Monte Carlo standard error":"recorded tally mean"),
  "Scale: "+(f.view==="relative_sd"?"ratio-derived percentage":f.scale),
  "Mesh: "+dimensionText+" bins",
  "Central cut: "+(coordinates.physical?"Y = "+coordinates.y[centerY].toFixed(3)+" cm (row "+centerY+")":"Y-bin "+centerY),
  "Realizations: "+String(f.item.n_realizations??"not recorded")
 ];
 const note=$("meshSummaryNote");
 const coordinateNote=coordinates.physical
  ?"XY axes use archived regular-mesh bounds in cm; plotted coordinates are cell centres. No fuel/reflector/assembly labels are inferred."
  :"Physical XY bounds are unavailable; axes remain mesh-bin indices, not cm or assembly coordinates.";
 if(note)note.textContent=summary.join(" · ")+". "+coordinateNote+" Heatmap, contours, profile, and surface reflect the selected display scale; hover values preserve recorded tally means.";
 $("meshStatus").textContent=meshData.provenance.hash_matches===true?"SHA-256 VERIFIED":meshData.provenance.hash_matches===false?"HASH MISMATCH":"DATA LOADED · HASH NOT CHECKED";
 $("meshStatus").classList.toggle("warning",meshData.provenance.hash_matches===false);
}
async function initMesh(){
 try{
  const response=await fetch("/api/mesh",{headers:{Accept:"application/json"}});
  if(!response.ok){let detail="HTTP "+response.status;try{detail=(await response.json()).error||detail}catch(_){}throw new Error(detail)}
  const payload=await response.json();
  if(!payload.mesh_tallies||!payload.mesh_tallies.length)throw new Error("No compatible 2D mesh tally in the archived statepoint.");
  const item=payload.mesh_tallies[0];
  for(const score of Object.keys(item.scores||{})){
   const record=item.scores[score];
   if(!record.standard_error&&record.std_dev)record.standard_error=record.std_dev;
  }
  meshData=payload;
  $("meshStatus").classList.remove("warning");
  const coordinates=meshCoordinateInfo(item);
  const coordinateProvenance=coordinates.physical
   ?"Recorded regular-mesh bounds: X "+coordinates.xRange[0].toFixed(3)+" to "+coordinates.xRange[1].toFixed(3)+" cm; Y "+coordinates.yRange[0].toFixed(3)+" to "+coordinates.yRange[1].toFixed(3)+" cm. Plots use cell-centre coordinates."
   :"Physical mesh bounds unavailable; spatial plots use explicit mesh-bin indices rather than assumed centimetres.";
  $("meshProvenance").textContent=meshData.provenance.source+" · "+item.dimensions.join(" × ")+" bins · tally "+item.tally_name+" · "+String(item.n_realizations??"unknown")+" realizations · SHA-256 "+meshData.provenance.sha256+". "+(meshData.provenance.hash_matches===true?"Statepoint member hash matches the recorded baseline.":meshData.provenance.hash_matches===false?"WARNING: statepoint hash differs from the recorded baseline; verify provenance before scientific comparison.":"Baseline hash was unavailable; provenance has not been hash-verified.")+" "+coordinateProvenance+" Relative uncertainty is calculated as standard error / mean for positive tally bins.";
  const scoreSelect=$("meshScore");
  const availableScores=Object.keys(item.scores);
  scoreSelect.innerHTML=availableScores.map(k=>'<option value="'+escapeHtml(k)+'">'+escapeHtml(k)+'</option>').join("");
  if(!availableScores.includes(scoreSelect.value))scoreSelect.value=availableScores[0]||"";
  ["meshScore","meshView","meshScale","meshPalette"].forEach(id=>{
   const control=$(id);
   if(control&&!control.dataset.meshListenerBound){
    control.addEventListener("change",drawMesh);
    control.dataset.meshListenerBound="true";
   }
  });
  drawMesh();
  const resizePlots=()=>{
   if(!window.Plotly||!window.Plotly.Plots)return;
   ["meshHeatmap","meshContour","meshProfile","meshSurface"].forEach(id=>{
    const el=$(id);
    if(el&&el.classList.contains("js-plotly-plot"))try{window.Plotly.Plots.resize(el)}catch(_){}
   });
  };
  if(!window.__cbpfrMeshResizeBound){
   window.addEventListener("resize",()=>window.requestAnimationFrame(resizePlots),{passive:true});
   window.__cbpfrMeshResizeBound=true;
  }
 }catch(error){
  meshData=null;
  $("meshStatus").textContent="SPATIAL DATA UNAVAILABLE";
  $("meshStatus").classList.add("warning");
  $("meshProvenance").textContent="The archived spatial tally could not be loaded: "+error.message;
  ["meshHeatmap","meshContour","meshProfile","meshSurface"].forEach(id=>$(id).innerHTML='<div class="empty-state"><b>Spatial data unavailable</b><p>'+escapeHtml(error.message||error)+'</p><p>No scientific values have been fabricated.</p></div>');
 }
}

/* Displays existing external geometry artifacts only; never synthesizes a reactor layout. */
async function initGeometry(){
 const refresh=$("reloadGeometry");
 if(refresh&&!refresh.dataset.bound){refresh.dataset.bound="true";refresh.addEventListener("click",async()=>{
  refresh.disabled=true;refresh.textContent="↻ Refreshing…";
  const ok=await initModelGeometry();
  const selected=records.find(item=>String(item.candidate_id)===String($("candidateSelect")?.value));
  if(ok&&selected){geometryArtifactActive=false;drawModelGeometry(selected);}
  await loadGeometryArtifacts();
  refresh.disabled=false;refresh.textContent="↻ Refresh source";
 });}
 await loadGeometryArtifacts();
}
async function loadGeometryArtifacts(){
 try{
  const response=await fetch("/api/geometry-artifacts",{headers:{Accept:"application/json"}});
  if(!response.ok)throw new Error("HTTP "+response.status);
  const payload=await response.json(),items=payload.artifacts||[];
  const list=$("geometryArtifactList");
  if(!items.length){
   $("geometryArtifactStatus").textContent="NO FILES FOUND";
   $("geometryArtifactStatus").classList.remove("warning");
   $("geometryProvenance").textContent="The candidate-linked material map is reconstructed from archived OpenMC geometry.xml lattice/material definitions. No separate native PNG/VTK/VTI plot is checked into scanned output folders.";
   list.innerHTML='<div class="empty-state"><b>No separate OpenMC plot artifact found</b><p>The main panel still renders the archived model lattice and pin-material regions for the selected candidate.</p><p>Native PNG/VTK/VTI artifacts can be inspected here when present.</p></div>';
   geometryArtifactActive=false;
   const selected=records.find(r=>String(r.candidate_id)===$("candidateSelect")?.value);
   drawModelGeometry(selected);
   return;
  }
  $("geometryArtifactStatus").textContent=items.length+" FILE(S) FOUND";
  $("geometryArtifactStatus").classList.remove("warning");
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
 setCoreGeometryMode("2d");
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
