const $ = (id) => document.getElementById(id);
const palette = {text:"#e8f1f7",muted:"#91a8b9",line:"#263f52",cyan:"#55d4df",blue:"#247fa0",orange:"#f5bb62"};
let records = [];
let metadata = {};
let meshData = null;
let meshDrawRevision = 0;
let axial3dData = null;
let axial3dDrawRevision = 0;
let assemblyRecords = [];
let selectedAssemblyPosition = "P00";
const assemblyPositionDefs = [
 {key:"p00_fission_rate",label:"P00",row:0,col:0,index:0},
 {key:"p01_fission_rate",label:"P01",row:0,col:1,index:1},
 {key:"p10_fission_rate",label:"P10",row:1,col:0,index:2},
 {key:"p11_fission_rate",label:"P11",row:1,col:1,index:3}
];
const materialEdgeColor = {M:"#f4bd62",U:"#55d4df"};
const formatSourceProxy = value => Number.isFinite(Number(value)) ? Number(value).toPrecision(6) : "—";
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
function signatureLettersHtml(signature){
 const raw=normalizeLayoutSignature(signature);
 return raw.split("").map(code=>'<span class="fuel-signature-letter '+(code==="M"?"fuel-signature-letter-mox":"fuel-signature-letter-uo2")+'">'+code+'</span>').join("");
}
function layoutCells(signature){
 const raw=normalizeLayoutSignature(signature);
 if(!isValidLayoutSignature(raw)){
  return '<div class="empty-state"><b>Placement unavailable</b><p>The selected candidate must contain exactly two UO₂ and two MOX positions. No default composition is substituted.</p></div>';
 }
 const mox=raw.split("").filter(code=>code==="M").length;
 const uo2=raw.split("").filter(code=>code==="U").length;
 return '<div class="fuel-signature-summary" role="img" aria-label="Fuel loading signature '+escapeHtml(raw)+' in p00, p01, p10, p11 order">'+
  '<div class="fuel-signature-kicker">LAYOUT SIGNATURE</div>'+
  '<div class="fuel-signature-code">'+signatureLettersHtml(raw)+'</div>'+
  '<div class="fuel-signature-counts"><span><b>'+mox+'</b> MOX positions</span><i></i><span><b>'+uo2+'</b> UO₂ positions</span></div>'+
  '<div class="fuel-signature-order">p00 → p01 → p10 → p11 · row-major order</div>'+
  '</div>';
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
if(typeof window.addEventListener==="function"){
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
}

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
 svg+='<defs><linearGradient id="reflectorFill" x1="0" y1="0" x2="1" y2="1"><stop offset="0%" stop-color="#4b535d"/><stop offset="100%" stop-color="#303841"/></linearGradient><pattern id="waterPattern" width="18" height="12" patternUnits="userSpaceOnUse"><path d="M0 6 Q4 2 9 6 T18 6" fill="none" stroke="#8c969f" stroke-width="1" opacity=".38"/></pattern></defs>';
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
  if(!window.CBPFRCore3DError&&host.children&&!host.children.length&&"innerHTML" in host)host.innerHTML='<div class="core3d-loading"><span></span><b>Loading Three.js scientific renderer…</b><small>The source SVG map is available in 2D source map mode.</small></div>';
  return;
 }
 try{
  if(!core3dViewer)core3dViewer=window.CBPFRCore3D.createCoreViewer(host,selectCoreAssembly);
  const info=core3dViewer.update(modelGeometryData,row,selectedCorePosition);
  window.CBPFRCore3DInfo=info;
  const status=$("core3dStatus");
  if(status){status.classList.remove("warning");status.textContent="WEBGL READY · THREE.JS R"+info.libraryVersion+" · "+info.pinCount.toLocaleString()+" PIN INSTANCES";}
  const pitch=info.corePitchCm||[21.42,21.42],dims=info.coreDimensions||[3,3];
  if($("coreModelDimensions"))$("coreModelDimensions").textContent=dims.join(" × ")+" CORE · "+number(pitch[0]*dims[0],2)+" × "+number(pitch[1]*dims[1],2)+" cm · PITCH "+number(pitch[0],2)+" cm";
  if($("coreSourceBadge"))$("coreSourceBadge").textContent="XML SOURCE · IDENTITY MATCHED";
 }catch(error){
  core3dLoadFailed=true;
  window.CBPFRCore3DInfo=null;
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
 $("selectedCandidateSignature").innerHTML=isValidLayoutSignature(signature)?'<span class="signature-summary-code">'+signatureLettersHtml(signature)+'</span><span class="signature-summary-caption">2 MOX · 2 UO₂</span>':'<span class="muted">No validated layout signature</span>';
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
 if(records.length){drawCandidateChart();drawOtherCharts();}
 if(assemblyRecords.length)drawAssemblyField();
 else if($("assemblyMap"))$("assemblyMap").innerHTML='<div class="empty-state"><b>No candidate selected</b><p>Select a candidate to inspect recorded assembly evidence.</p></div>';
}
const baseLayout={paper_bgcolor:"rgba(0,0,0,0)",plot_bgcolor:"rgba(0,0,0,0)",font:{family:"Manrope, sans-serif",color:palette.muted,size:10},margin:{l:55,r:18,t:15,b:65},xaxis:{gridcolor:"#1e3545",linecolor:palette.line,tickangle:-28},yaxis:{gridcolor:"#1e3545",linecolor:palette.line,zerolinecolor:palette.line},hoverlabel:{bgcolor:"#102536",bordercolor:palette.line,font:{color:palette.text}}};
const config={displaylogo:false,responsive:true,modeBarButtonsToRemove:["lasso2d","select2d"]};
function chart(id,traces,layout={}){
 const el=$(id);if(!el)return Promise.resolve();
 if(!window.Plotly){el.innerHTML='<div class="empty-state"><b>Plotting engine unavailable</b><p>Plotly.js could not be loaded. Check network access to the chart CDN, then reload the page.</p></div>';return Promise.resolve();}
 try{
  return Promise.resolve(Plotly.react(el,traces,{...baseLayout,...layout},config)).catch(error=>{
   const msg=String(error?.message||error).replace(/[&<>\"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
   el.innerHTML='<div class="empty-state"><b>Chart render failed</b><p>'+msg+'</p></div>';
  });
 }catch(error){el.innerHTML='<div class="empty-state"><b>Chart render failed</b><p>'+String(error.message||error)+'</p></div>';return Promise.resolve();}
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
 drawOtherCharts();
 drawAssemblyField();
}
function drawCandidateChart(){
 const key=$("metricSelect").value;
 const valid=records.filter(r=>has(r,key)).sort((a,b)=>Number(a[key])-Number(b[key]));
 const selected=String($("candidateSelect").value||"");
 if(!valid.length){$("candidateChart").innerHTML='<div class="empty-state"><b>Metric unavailable</b><p>No finite recorded values are available for the selected metric.</p></div>';return;}
 const isKeff=key==="keff_mean";
 const metricName=isKeff?"Reported k-effective mean":key==="aggregate_flux_score"?"Aggregate flux score":"Aggregate fission score";
 const colors=valid.map(r=>String(r.candidate_id)===selected?palette.cyan:"#47758f");
 const trace={
  type:"scatter",mode:"markers",name:metricName,
  x:valid.map(r=>Number(r[key])),y:valid.map(r=>String(r.layout_signature||label(r))),
  marker:{color:colors,size:valid.map(r=>String(r.candidate_id)===selected?13:9),symbol:valid.map(r=>String(r.candidate_id)===selected?"diamond":"circle"),line:{color:valid.map(r=>String(r.candidate_id)===selected?palette.text:"#102536"),width:1.2}},
  customdata:valid.map(r=>[r.candidate_id,r.layout_signature,r.seed,has(r,"keff_std_dev")?Number(r.keff_std_dev):null]),
  hovertemplate:"Candidate %{customdata[0]}<br>Layout %{customdata[1]}<br>Seed %{customdata[2]}<br>"+metricName+" %{x:.7g}"+(isKeff?"<br>Reported SD ±%{customdata[3]:.4g}":"")+"<extra></extra>"
 };
 const shapes=[],annotations=[];
 let min= Math.min(...valid.map(r=>Number(r[key]))), max=Math.max(...valid.map(r=>Number(r[key])));
 const spread=max-min, pad=spread>0?spread*0.14:Math.max(Math.abs(max)*0.01,0.001);
 if(isKeff){
  trace.error_x={type:"data",array:valid.map(r=>has(r,"keff_std_dev")?Number(r.keff_std_dev):0),visible:true,color:palette.muted,thickness:1.4,width:5};
  // Keep the k_eff=1 reference visible, but explicitly label it as interpretive rather than a safety limit.
  min=Math.min(1,min-pad); max+=pad;
  shapes.push({type:"line",xref:"x",yref:"paper",x0:1,x1:1,y0:0,y1:1,line:{color:palette.orange,width:1,dash:"dash"}});
  annotations.push({xref:"x",yref:"paper",x:1,y:1.02,text:"k_eff = 1 · reference only",showarrow:false,xanchor:"left",yanchor:"bottom",font:{size:9,color:palette.orange},bgcolor:"rgba(7,17,27,0.82)",borderpad:2});
 } else { min-=pad; max+=pad; }
 chart("candidateChart",[trace],{
  autosize:true,margin:{l:70,r:25,t:isKeff?34:16,b:54},showlegend:false,hovermode:"closest",shapes,annotations,
  xaxis:{...baseLayout.xaxis,title:isKeff?"Reported k-effective mean (± reported SD)":"Recorded "+metricName.toLowerCase()+" (source units unspecified)",automargin:true,gridcolor:palette.line,zeroline:false,tickangle:0,tickformat:isKeff?".3f":".4g",range:[min,max]},
  yaxis:{...baseLayout.yaxis,title:"Candidate layout",type:"category",autorange:"reversed",automargin:true,tickangle:0,tickfont:{size:11,color:palette.muted},gridcolor:"rgba(38,63,82,0.55)"}
 });
}
function drawOtherCharts(){
 const selected=String($("candidateSelect")?.value||"");
 const vals=records.filter(r=>has(r,"keff_mean")).sort((a,b)=>Number(a.keff_mean)-Number(b.keff_mean));
 if(!vals.length){
  $("distributionChart").innerHTML='<div class="empty-state"><b>k-effective data unavailable</b><p>No finite recorded means are available.</p></div>';
 } else {
  const keffColors=vals.map(r=>String(r.candidate_id)===selected?palette.cyan:"#47758f");
  const spread=Math.max(...vals.map(r=>Number(r.keff_mean)))-Math.min(...vals.map(r=>Number(r.keff_mean)));
  const pad=spread>0?spread*0.12:0.002;
  const trace={type:"scatter",mode:"markers",name:"Ranked candidate k-effective",x:vals.map(r=>String(r.layout_signature||label(r))),y:vals.map(r=>Number(r.keff_mean)),customdata:vals.map(r=>[r.candidate_id,r.layout_signature,r.seed,has(r,"keff_std_dev")?Number(r.keff_std_dev):null]),marker:{color:keffColors,size:vals.map(r=>String(r.candidate_id)===selected?12:9),symbol:vals.map(r=>String(r.candidate_id)===selected?"diamond":"circle"),line:{color:vals.map(r=>String(r.candidate_id)===selected?palette.text:"#102536"),width:1.1}},error_y:{type:"data",array:vals.map(r=>has(r,"keff_std_dev")?Number(r.keff_std_dev):0),visible:true,color:palette.muted,thickness:1.2,width:4},hovertemplate:"Ranked layout %{x}<br>Candidate %{customdata[0]}<br>Seed %{customdata[2]}<br>k-effective mean %{y:.7f}<br>Reported SD ±%{customdata[3]:.4g}<extra></extra>"};
  chart("distributionChart",[trace],{autosize:true,margin:{l:62,r:20,t:18,b:42},showlegend:false,hovermode:"closest",xaxis:{...baseLayout.xaxis,title:"Candidate layout · sorted by recorded k-effective",type:"category",tickangle:0,automargin:true,gridcolor:"rgba(38,63,82,0.4)"},yaxis:{...baseLayout.yaxis,title:"Reported k-effective mean (± SD)",range:[Math.min(1,Math.min(...vals.map(r=>Number(r.keff_mean)))-pad),Math.max(...vals.map(r=>Number(r.keff_mean)))+pad],automargin:true},shapes:[{type:"line",xref:"paper",yref:"y",x0:0,x1:1,y0:1,y1:1,line:{color:palette.orange,width:1,dash:"dash"}}],annotations:[{xref:"paper",yref:"y",x:1,y:1,xanchor:"right",yanchor:"bottom",text:"k_eff = 1 · reference only",showarrow:false,font:{size:9,color:palette.orange},bgcolor:"rgba(7,17,27,0.82)",borderpad:2}]});
 }
 const pairs=records.filter(r=>has(r,"aggregate_flux_score")&&has(r,"aggregate_fission_score"));
 if(!pairs.length){
  $("aggregateChart").innerHTML='<div class="empty-state"><b>Score relationship unavailable</b><p>No candidates have both a finite aggregate flux score and aggregate fission score. The two metrics are not combined on a shared scale.</p></div>';
  return;
 }
 const isSelected=r=>String(r.candidate_id)===selected;
 const aggTrace={type:"scatter",mode:"markers+text",name:"Candidate score pair",x:pairs.map(r=>Number(r.aggregate_flux_score)),y:pairs.map(r=>Number(r.aggregate_fission_score)),text:pairs.map(r=>String(r.layout_signature||"")),textposition:"top center",textfont:{size:9,color:palette.muted},customdata:pairs.map(r=>[r.candidate_id,r.layout_signature,r.seed]),marker:{color:pairs.map(r=>isSelected(r)?palette.cyan:"#e0ad58"),size:pairs.map(r=>isSelected(r)?13:10),symbol:pairs.map(r=>isSelected(r)?"diamond":"circle"),line:{color:pairs.map(r=>isSelected(r)?palette.text:"#102536"),width:1.2}},hovertemplate:"Candidate %{customdata[0]}<br>Layout %{customdata[1]}<br>Seed %{customdata[2]}<br>Aggregate flux score %{x:.7g}<br>Aggregate fission score %{y:.7g}<extra></extra>"};
 const xValues=pairs.map(r=>Number(r.aggregate_flux_score)),yValues=pairs.map(r=>Number(r.aggregate_fission_score));
 const xSpan=Math.max(...xValues)-Math.min(...xValues),ySpan=Math.max(...yValues)-Math.min(...yValues);
 const xPad=xSpan>0?xSpan*0.12:Math.max(Math.abs(xValues[0])*0.02,0.001),yPad=ySpan>0?ySpan*0.14:Math.max(Math.abs(yValues[0])*0.02,0.001);
 chart("aggregateChart",[aggTrace],{autosize:true,margin:{l:66,r:24,t:18,b:58},showlegend:false,hovermode:"closest",xaxis:{...baseLayout.xaxis,title:"Aggregate flux score (source units unspecified)",range:[Math.min(...xValues)-xPad,Math.max(...xValues)+xPad],automargin:true,gridcolor:"rgba(38,63,82,0.55)",tickformat:".4g"},yaxis:{...baseLayout.yaxis,title:"Aggregate fission score (source units unspecified)",range:[Math.min(...yValues)-yPad,Math.max(...yValues)+yPad],automargin:true,gridcolor:"rgba(38,63,82,0.55)",tickformat:".4g"}});
}
function showError(message){const el=$("apiError");el.hidden=false;el.textContent=message;}
async function init(){
 setupNavigation();
 const reloadButton=$("reloadEvidence");
 if(reloadButton)reloadButton.addEventListener("click",async()=>{reloadButton.disabled=true;reloadButton.textContent="↻ Reloading…";meshData=null;await initMesh();await initAxial3D();reloadButton.disabled=false;reloadButton.textContent="↻ Reload spatial tally";});
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
  await initAxial3D();
 }catch(error){
  showError("Could not load recorded evidence: "+error.message+". Start the local Python server from the repository root and check the source CSV path.");
  clearCandidateSelection("Candidate evidence unavailable: "+error.message);
  $("sourcePath").textContent="API unavailable";
  await initGeometry();
  await initMesh();
  await initAxial3D();
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
function buildSurfaceContourLines(z,xs,ys,levels,baseZ){
 const surface={x:[],y:[],z:[]},base={x:[],y:[],z:[]};
 const rows=z.length,cols=z[0]?.length||0;
 const append=(a,b)=>{
  surface.x.push(a.x,b.x,null);surface.y.push(a.y,b.y,null);surface.z.push(a.z,b.z,null);
  base.x.push(a.x,b.x,null);base.y.push(a.y,b.y,null);base.z.push(baseZ,baseZ,null);
 };
 const interpolate=(a,b,level)=>{
  const delta=b.v-a.v;
  const t=delta===0?0.5:Math.max(0,Math.min(1,(level-a.v)/delta));
  return {x:a.x+t*(b.x-a.x),y:a.y+t*(b.y-a.y),z:level};
 };
 for(const level of levels){
  if(!Number.isFinite(level))continue;
  for(let row=0;row<rows-1;row++){
   for(let col=0;col<cols-1;col++){
    const corners=[
     {x:xs[col],y:ys[row],v:z[row][col]},
     {x:xs[col+1],y:ys[row],v:z[row][col+1]},
     {x:xs[col+1],y:ys[row+1],v:z[row+1][col+1]},
     {x:xs[col],y:ys[row+1],v:z[row+1][col]}
    ];
    if(corners.some(p=>typeof p.v!=="number"||!Number.isFinite(p.v)))continue;
    const edges=[[0,1],[1,2],[2,3],[3,0]],points=[];
    for(const [ai,bi] of edges){
     const a=corners[ai],b=corners[bi];
     if((a.v<level&&b.v>=level)||(a.v>=level&&b.v<level)){
      const point=interpolate(a,b,level);
      if(!points.some(p=>Math.abs(p.x-point.x)<1e-10&&Math.abs(p.y-point.y)<1e-10))points.push(point);
     }
    }
    if(points.length===2)append(points[0],points[1]);
    else if(points.length===4){
     const center=(corners[0].v+corners[1].v+corners[2].v+corners[3].v)/4;
     if(center>=level){append(points[0],points[1]);append(points[2],points[3]);}
     else {append(points[0],points[3]);append(points[1],points[2]);}
    }
   }
  }
 }
 return {surface,base,segments:surface.z.filter(value=>value!==null).length/2};
}
function waitForCoreGeometryReady(timeoutMs=3000){
 const status=$("core3dStatus")?.textContent||"";
 const canvas=$("core3dCanvas")?.querySelector("canvas.core3d-canvas");
 if(canvas||core3dLoadFailed||/WEBGL READY|2D FALLBACK|UNAVAILABLE/i.test(status))return Promise.resolve();
 return new Promise(resolve=>{
  let done=false;
  let timer=null;
  const finish=()=>{
   if(done)return;
   done=true;
   if(timer!==null)window.clearTimeout(timer);
   window.removeEventListener("cbpfr-core3d-ready",finish);
   window.removeEventListener("cbpfr-core3d-failed",finish);
   resolve();
  };
  window.addEventListener("cbpfr-core3d-ready",finish,{once:true});
  window.addEventListener("cbpfr-core3d-failed",finish,{once:true});
  timer=window.setTimeout(finish,timeoutMs);
 });
}
const meshDefaultCamera={eye:{x:1.55,y:1.55,z:1.1},center:{x:0,y:0,z:0},up:{x:0,y:0,z:1}};
async function drawMesh(){
 if(!meshData)return;
 const drawRevision=++meshDrawRevision;
 const f=currentField();
 if(!f){
  $("meshStatus").textContent="SCORE UNAVAILABLE";
  ["meshHeatmap","meshContour","meshProfile","meshSurface"].forEach(id=>{
   $(id).innerHTML='<div class="empty-state"><b>Selected field unavailable</b><p>The requested score is not present in the recorded mesh tally.</p></div>';
  });
  return;
 }
 const paletteName=$("meshPalette").value;
 const z=f.values, scoreLabel=f.score;
 const nx=f.item.dimensions[0], ny=f.item.dimensions[1], coordinates=f.coordinates;
 const xs=coordinates.x, ys=coordinates.y;
 const exaggeration=Math.max(0.5,Math.min(3,Number($("meshExaggeration")?.value||1)));
 const plotTitle=f.view==="relative_sd"?"Relative Monte Carlo standard error (%)":(f.scale==="log"?"log₁₀("+scoreLabel+" tally mean)":"Recorded "+scoreLabel+" tally mean");
 const rawTitle=f.view==="relative_sd"?"Relative Monte Carlo standard error (%)":scoreLabel+" tally mean (recorded scale)";
 const sourceCustomData=f.mean.map((row,y)=>row.map((mean,x)=>[
  Number.isFinite(mean)?mean:null,
  Number.isFinite(f.standardError[y]?.[x])?f.standardError[y][x]:null,
  Number.isFinite(f.relative[y]?.[x])?f.relative[y][x]:null
 ]));
 const sourceHover=f.view==="relative_sd"
  ?"<br>Relative Monte Carlo standard error %{customdata[2]:.4g}%<br>Recorded tally mean %{customdata[0]:.6g}<br>Monte Carlo standard error %{customdata[1]:.4g}"
  :"<br>Recorded "+scoreLabel+" tally mean %{customdata[0]:.6g}<br>Monte Carlo standard error %{customdata[1]:.4g}<br>Relative Monte Carlo standard error %{customdata[2]:.4g}%";
 const displayHover=f.view==="mean"&&f.scale==="log"
  ?"<br>Display Z: log₁₀(mean) = %{z:.5g}"
  :f.view==="relative_sd"
   ?"<br>Display Z: relative MC standard error = %{z:.4g}%"
   :"<br>Display Z: recorded mean = %{z:.6g}";
 const hover=(title)=>coordinates.xHoverLabel+"<br>"+coordinates.yHoverLabel+title+sourceHover+"<extra></extra>";
 const axisStyle={...baseLayout.xaxis,gridcolor:palette.line,linecolor:palette.line,zerolinecolor:palette.line,automargin:true};
 const yAxisStyle={...baseLayout.yaxis,gridcolor:palette.line,linecolor:palette.line,zerolinecolor:palette.line,automargin:true};
 const sharedAxis={tickfont:{size:10,color:palette.muted},titlefont:{size:11,color:palette.muted}};
 const colorscale=paletteName;
 const spanX=coordinates.xRange?coordinates.xRange[1]-coordinates.xRange[0]:Math.max(1,nx-1);
 const spanY=coordinates.yRange?coordinates.yRange[1]-coordinates.yRange[0]:Math.max(1,ny-1);
 const xySpan=Math.max(spanX,spanY,1);
 const aspectX=spanX/xySpan,aspectY=spanY/xySpan;
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
 await chart("meshHeatmap",[{
  type:"heatmap",x:xs,y:ys,z:z,customdata:sourceCustomData,colorscale,
  colorbar:{...colorbar,title:{text:plotTitle,font:{size:10,color:palette.text}}},
  hovertemplate:hover(""),connectgaps:false,hoverongaps:false,xgap:0,ygap:0
}],heatLayout);
 if(drawRevision!==meshDrawRevision)return;
 await chart("meshContour",[{
  type:"contour",x:xs,y:ys,z:z,customdata:sourceCustomData,colorscale,
  autocontour:false,
  contours:{
   coloring:"heatmap",showlines:true,showlabels:true,
   start:contourStart,end:contourEnd,size:contourStep,
   labelfont:{size:10,color:palette.text},
   labelformat:f.view==="relative_sd"?".1f":".2f"
  },
  line:{width:1,color:"rgba(7,17,27,0.72)"},
  colorbar:{...colorbar,title:{text:plotTitle,font:{size:10,color:palette.text}}},
  hovertemplate:hover(""),connectgaps:false,hoverongaps:false
}],heatLayout);
 if(drawRevision!==meshDrawRevision)return;
 const centerY=Math.floor((ny-1)/2);
 const meanRow=f.mean[centerY]||[], seRow=f.standardError[centerY]||[], relativeRow=f.relative[centerY]||[];
 const profileY=f.view==="relative_sd"?relativeRow:meanRow;
 const profileCustom=xs.map((x,i)=>[meanRow[i],seRow[i],relativeRow[i]]);
 const profileHover=f.view==="relative_sd"
  ?coordinates.xHoverLabel+"<br>Relative Monte Carlo standard error %{y:.4g}%<br>Recorded tally mean %{customdata[0]:.6g}<br>Monte Carlo standard error %{customdata[1]:.4g}<extra></extra>"
  :coordinates.xHoverLabel+"<br>Recorded "+scoreLabel+" tally mean %{y:.6g}<br>Monte Carlo standard error %{customdata[1]:.4g}<br>Relative Monte Carlo standard error %{customdata[2]:.4g}%<extra></extra>";
 const profileError=f.view==="mean"?{
  type:"data",symmetric:false,
  array:seRow.map((se,i)=>Number.isFinite(se)&&se>=0?se:0),
  arrayminus:seRow.map((se,i)=>Number.isFinite(se)&&se>=0&&Number.isFinite(meanRow[i])?Math.min(se,Math.max(0,meanRow[i]*0.999999)):0),
  visible:true,color:palette.muted,thickness:1,width:3
 }:{visible:false};
 await chart("meshProfile",[{
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
 if(drawRevision!==meshDrawRevision)return;
  const surfaceContourCount=Math.min(6,Math.max(0,Math.floor(zSpan/Math.max(contourStep,1e-12))));
 const contourLevels=zSpan>0
  ?Array.from({length:surfaceContourCount},(_,index)=>zMin+(index+1)*zSpan/(surfaceContourCount+1))
  :finiteZ.length?[zMin]:[];
 const baseZ=zMin-Math.max(zSpan*0.08,Math.abs(zMin)*0.001,1e-6);
 const contourLines=buildSurfaceContourLines(z,xs,ys,contourLevels,baseZ);
 const surfaceTraces=[{
  type:"surface",x:xs,y:ys,z:z,surfacecolor:z,customdata:sourceCustomData,colorscale,
  colorbar:{...colorbar,title:{text:plotTitle,font:{size:10,color:palette.text}}},
  hovertemplate:coordinates.xHoverLabel+"<br>"+coordinates.yHoverLabel+sourceHover+displayHover+"<extra></extra>",
  connectgaps:false,hoverongaps:false,showscale:true,
  lighting:{ambient:0.42,diffuse:0.92,specular:0.26,roughness:0.46,fresnel:0.12},
  lightposition:{x:1200,y:1000,z:1800},opacity:1
 }];
 const surfaceLayout={
  autosize:true,margin:{l:8,r:8,t:8,b:8},
  scene:{
   uirevision:"cbpfr-neutron-field-camera-v1",
   xaxis:{title:{text:coordinates.physical?"X position (cm)":"X mesh-bin index (0-based)",font:{size:11}},gridcolor:"#365064",color:palette.muted,backgroundcolor:"#091724",showbackground:true,showspikes:false,zerolinecolor:palette.line,range:coordinates.physical?coordinates.xRange:undefined},
   yaxis:{title:{text:coordinates.physical?"Y position (cm)":"Y mesh-bin index (0-based)",font:{size:11}},gridcolor:"#365064",color:palette.muted,backgroundcolor:"#091724",showbackground:true,showspikes:false,zerolinecolor:palette.line,range:coordinates.physical?coordinates.yRange:undefined},
   zaxis:{title:{text:plotTitle,font:{size:10}},gridcolor:"#365064",color:palette.muted,backgroundcolor:"#091724",showbackground:true,showspikes:false,zerolinecolor:palette.line},
   bgcolor:"rgba(0,0,0,0)",aspectmode:"manual",aspectratio:{x:aspectX,y:aspectY,z:Math.min(0.95,0.30*exaggeration)},camera:JSON.parse(JSON.stringify(meshDefaultCamera))
  }
 };
 if(contourLines.segments>0){
  surfaceTraces.push({
   type:"scatter3d",mode:"lines",name:"Surface isolines",x:contourLines.surface.x,y:contourLines.surface.y,z:contourLines.surface.z,
   line:{color:"rgba(232,241,247,0.88)",width:2},hoverinfo:"skip",showlegend:false,connectgaps:false
  });
  surfaceTraces.push({
   type:"scatter3d",mode:"lines",name:"Projected base-plane isolines",x:contourLines.base.x,y:contourLines.base.y,z:contourLines.base.z,
   line:{color:"rgba(85,212,223,0.56)",width:2},hoverinfo:"skip",showlegend:false,connectgaps:false
  });
 }
 await waitForCoreGeometryReady();
 if(drawRevision!==meshDrawRevision)return;
 await chart("meshSurface",surfaceTraces,surfaceLayout);
 if(drawRevision!==meshDrawRevision)return;
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
  "Vertical exaggeration: "+exaggeration.toFixed(1)+"× (display-only; source data unchanged)",
  "Mesh: "+dimensionText+" bins",
  "Central cut: "+(coordinates.physical?"Y = "+coordinates.y[centerY].toFixed(3)+" cm (row "+centerY+")":"Y-bin "+centerY),
  "Realizations: "+String(f.item.n_realizations??"not recorded")
 ];
 const note=$("meshSummaryNote");
 const coordinateNote=coordinates.physical
  ?"XY axes use archived regular-mesh bounds in cm; plotted coordinates are cell centres. No fuel/reflector/assembly labels are inferred."
  :"Physical XY bounds are unavailable; axes remain mesh-bin indices, not cm or assembly coordinates.";
 if(note)note.textContent=summary.join(" · ")+". "+coordinateNote+" The Z dimension is vertically exaggerated through plot aspect ratio only; the tally matrix and hover values are unchanged. Contour projection on the lower reference plane is a display aid.";
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
  ["meshScore","meshView","meshScale","meshPalette","meshExaggeration"].forEach(id=>{
   const control=$(id);
   if(control&&!control.dataset.meshListenerBound){
    control.addEventListener("change",drawMesh);
    control.dataset.meshListenerBound="true";
   }
  });
  const resetCamera=$("meshResetCamera");
  if(resetCamera&&!resetCamera.dataset.meshListenerBound){
   resetCamera.addEventListener("click",()=>{
    const plot=$("meshSurface");
    if(!window.Plotly||!plot?.data)return;
    window.Plotly.relayout(plot,{"scene.camera":JSON.parse(JSON.stringify(meshDefaultCamera))});
   });
   resetCamera.dataset.meshListenerBound="true";
  }
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


/* Stage 4: render only a recorded multi-layer OpenMC statepoint mesh. */
async function initAxial3D(){
 const panel=$("axial3dPanel");
 if(!panel)return;
 const updateButton=$("reloadAxial3d");
 if(updateButton&&!updateButton.dataset.bound){
  updateButton.dataset.bound="true";
  updateButton.addEventListener("click",async()=>{
   updateButton.disabled=true;updateButton.textContent="↻ Loading…";
   await loadAxial3D();
   updateButton.disabled=false;updateButton.textContent="↻ Reload 3D tally";
  });
 }
 const score=$("axial3dScore"),view=$("axial3dView"),slice=$("axial3dSlice"),opacity=$("axial3dOpacity"),paletteSelect=$("axial3dPalette");
 if(score&&!score.dataset.bound){score.dataset.bound="true";score.addEventListener("change",loadAxial3D);}
 [view,slice,opacity,paletteSelect].forEach(control=>{
  if(control&&!control.dataset.bound){
   control.dataset.bound="true";
   control.addEventListener("input",drawAxial3D);
   control.addEventListener("change",drawAxial3D);
  }
 });
 await loadAxial3D();
}
async function loadAxial3D(){
 try{
  const score=$("axial3dScore")?.value||"flux";
  const response=await fetch("/api/axial-3d?score="+encodeURIComponent(score),{headers:{Accept:"application/json"}});
  let payload;
  try{payload=await response.json();}catch(_){payload={error:"API returned a non-JSON response"};}
  if(!response.ok)throw new Error(payload.error||("HTTP "+response.status));
  const dims=payload.mesh?.dimension_xyz||[];
  if(!payload.available||dims.length!==3||dims[2]<=1||!Array.isArray(payload.mean)||!Array.isArray(payload.standard_error)||!Array.isArray(payload.relative_error_percent)){
   throw new Error("The source does not contain a verified multi-layer 3D tally.");
  }
  if(payload.mean.length!==dims[2]||payload.mean.some(layer=>layer.length!==dims[1]||layer.some(row=>row.length!==dims[0]))){
   throw new Error("3D tally arrays do not match the declared mesh dimensions.");
  }
  axial3dData=payload;
  const scoreQuality=payload.provenance?.score_summary||{};
  const medianRse=Number(scoreQuality.relative_error_percent_median_positive_bins);
  const p95Rse=Number(scoreQuality.relative_error_percent_p95_positive_bins);
  const hasHighLocalRse=Number.isFinite(medianRse)&&medianRse>25;
  $("axial3dStatus").textContent="3D STATEPOINT LOADED"+(hasHighLocalRse?" · HIGH BINWISE RSE":"");
  $("axial3dStatus").classList.toggle("warning",hasHighLocalRse);
  const state=payload.provenance?.statepoint||{};
  const sha=payload.provenance?.sha256||"not recorded";
  const inputAudit=payload.provenance?.input_audit||{};
  const inputManifest=payload.provenance?.input_manifest||{};
  const sourceCandidate=inputManifest.candidate_id||inputAudit.candidate_id||"candidate not recorded";
  const layoutSignature=inputManifest.layout_signature||"layout not recorded";
  const auditText=inputAudit.status||"input XML audit sidecar not installed";
  $("axial3dProvenance").textContent=payload.provenance?.source+" · candidate "+sourceCandidate+" · layout "+layoutSignature+" · input audit: "+auditText+" · mesh "+dims.join(" × ")+" · statepoint SHA-256 "+(state.sha256||"not recorded")+" · NPZ SHA-256 "+sha+". The plotted field comes from recorded 3D tally bins, not the 2D surface.";
  const zs=payload.mesh.z_centers_cm||[];
  const slider=$("axial3dSlice");
  slider.max=String(zs.length-1);
  slider.value=String(Math.min(Number(slider.value)||0,zs.length-1));
  const lower=payload.mesh.lower_left_cm_xyz,upper=payload.mesh.upper_right_cm_xyz;
  const zCell=zs.length>1?Math.abs(zs[1]-zs[0]):0;
  const zSpan=Array.isArray(lower)&&Array.isArray(upper)&&Number.isFinite(Number(lower[2]))&&Number.isFinite(Number(upper[2]))
   ?Math.abs(Number(upper[2])-Number(lower[2]))
   :(zs.length?Math.abs(zs[zs.length-1]-zs[0])+zCell:0);
  const meanActive=state.n_realizations??"not recorded";
  $("axial3dKpis").innerHTML=[
   ["Mesh dimensions",dims.join(" × "),"51 × 51 × "+dims[2]+" source tally bins"],
   ["Axial span",zSpan.toFixed(2)+" cm","From recorded Z cell centres"],
   ["Axial bins",String(dims[2]),"Recorded independent mesh layers"],
   ["Active realisations",String(meanActive),"OpenMC statepoint metadata"]
  ].map(m=>'<article class="metric"><label>'+m[0]+'</label><strong>'+m[1]+'</strong><small>'+m[2]+'</small></article>').join("");
  const rseNote=Number.isFinite(medianRse)
   ?" Positive-mean voxel relative MC standard error: median "+medianRse.toFixed(1)+"%"+(Number.isFinite(p95Rse)?", 95th percentile "+p95Rse.toFixed(1)+"%":"")+". These are descriptive spatial uncertainty statistics, not a formal acceptance threshold."
   :" Spatial relative-error summary is not present in the sidecar.";
  $("axial3dSummary").textContent="Selected score: "+score+". Axial layers: "+dims[2]+". The volume is an OpenMC mesh-tally estimate; each voxel retains Monte Carlo uncertainty. Relative standard errors in zero-mean bins are undefined and shown as missing."+rseNote+" Input/model hashes and the full statepoint summary are retained in the artifact.";
  drawAxial3D();
 }catch(error){
  axial3dData=null;
  $("axial3dStatus").textContent="3D DATA UNAVAILABLE";
  $("axial3dStatus").classList.add("warning");
  $("axial3dProvenance").textContent=error.message||String(error);
  $("axial3dKpis").innerHTML=[
   ["Mesh dimensions","—","Awaiting 3D statepoint"],
   ["Axial span","—","No verified physical Z data"],
   ["Axial bins","—","No multi-layer tally installed"],
   ["Active realisations","—","Statepoint unavailable"]
  ].map(m=>'<article class="metric"><label>'+m[0]+'</label><strong>'+m[1]+'</strong><small>'+m[2]+'</small></article>').join("");
  $("axial3dSummary").textContent="No volumetric data are fabricated. Install axial_tally_3d.npz and its AXIAL_3D_STATEPOINT_SUMMARY.json sidecar from the CB-PFR axial-3D Actions artifact under evidence/cbpfr_axial_3d/, or set CBPFR_AXIAL_TALLY_NPZ to the NPZ path and restart the local server.";
  $("axial3dPlot").innerHTML='<div class="empty-state"><b>Recorded 3D tally not installed</b><p>The physical axial volume will appear here when a true multi-layer OpenMC statepoint export is available. The 2D terrain above is intentionally not used as a fallback.</p><p><a href="https://github.com/thenextw4ng/cb-pfr/actions/workflows/c5g7-axial-3d.yml" target="_blank" rel="noreferrer">Open the axial 3D transport workflow ↗</a></p></div>';
 }
}
function drawAxial3D(){
 if(!axial3dData||!window.Plotly)return;
 const revision=++axial3dDrawRevision;
 const payload=axial3dData,mean=payload.mean,se=payload.standard_error,rel=payload.relative_error_percent;
 const xs=payload.mesh.x_centers_cm,ys=payload.mesh.y_centers_cm,zs=payload.mesh.z_centers_cm;
 const nz=zs.length,ny=ys.length,nx=xs.length;
 const zIndex=Math.min(nz-1,Math.max(0,Number($("axial3dSlice")?.value||0)));
 const view=$("axial3dView")?.value||"mean";
 const score=payload.score;
 const colorscale=$("axial3dPalette")?.value||"Viridis";
 const opacity=Math.max(0.04,Math.min(0.4,Number($("axial3dOpacity")?.value||0.14)));
 const flatDisplay=[],flatMean=[],flatSE=[],flatRelative=[],flatX=[],flatY=[],flatZ=[],positiveDisplay=[];
 const rawDisplay=(m,r)=>{
  if(view==="relative_error")return m>0&&Number.isFinite(r)?r:null;
  return m>0&&Number.isFinite(m)?Math.log10(m):null;
 };
 for(let k=0;k<nz;k++)for(let j=0;j<ny;j++)for(let i=0;i<nx;i++){
  const m=mean[k][j][i],s=se[k][j][i],r=rel[k][j][i],v=rawDisplay(m,r);
  flatX.push(xs[i]);flatY.push(ys[j]);flatZ.push(zs[k]);
  flatMean.push(m);flatSE.push(s);flatRelative.push(r);
  flatDisplay.push(v);
  if(v!==null&&Number.isFinite(v))positiveDisplay.push(v);
 }
 if(!positiveDisplay.length){
  $("axial3dPlot").innerHTML='<div class="empty-state"><b>No finite voxels for this view</b><p>The selected tally score has no positive means or finite relative errors.</p></div>';
  return;
 }
 const sorted=positiveDisplay.slice().sort((a,b)=>a-b);
 const quantile=q=>sorted[Math.min(sorted.length-1,Math.max(0,Math.floor((sorted.length-1)*q)))];
 let isomin=quantile(0.12),isomax=quantile(0.92);
 if(!(isomax>isomin))isomax=isomin+Math.max(Math.abs(isomin)*0.02,1e-6);
 const floor=isomin-Math.max(1,Math.abs(isomin)*0.05);
 const values=flatDisplay.map(v=>v===null||!Number.isFinite(v)?floor:v);
 const volumeTrace={
  type:"volume",name:"Recorded 3D tally volume",
  x:flatX,y:flatY,z:flatZ,value:values,
  isomin,isomax,surface_count:10,opacity,
  colorscale,showscale:true,
  colorbar:{title:{text:view==="relative_error"?"Relative MC SE (%)":"log₁₀ tally mean",font:{size:10,color:palette.text}},thickness:12,outlinewidth:0,tickfont:{size:9,color:palette.muted}},
  caps:{x:{show:false},y:{show:false},z:{show:false}},
  customdata:flatMean.map((m,i)=>[m,flatSE[i],flatRelative[i]]),
  hovertemplate:"X %{x:.2f} cm<br>Y %{y:.2f} cm<br>Z %{z:.2f} cm<br>Recorded "+escapeHtml(score)+" mean %{customdata[0]:.6g}<br>Monte Carlo standard error %{customdata[1]:.4g}<br>Relative MC SE %{customdata[2]:.4g}%<extra>3D tally voxel</extra>"
 };
 const sliceMean=mean[zIndex],sliceSE=se[zIndex],sliceRel=rel[zIndex];
 const sliceDisplay=sliceMean.map((row,j)=>row.map((m,i)=>{
  const v=rawDisplay(m,sliceRel[j][i]);
  return v===null||!Number.isFinite(v)?null:v;
 }));
 const sliceCustom=sliceMean.map((row,j)=>row.map((m,i)=>[m,sliceSE[j][i],sliceRel[j][i]]));
 const planeZ=zs[zIndex];
 const sliceTrace={
  type:"surface",name:"Selected axial slice · Z="+planeZ.toFixed(2)+" cm",
  x:xs,y:ys,z:Array.from({length:ny},()=>Array(nx).fill(planeZ)),
  surfacecolor:sliceDisplay,colorscale,cmin:isomin,cmax:isomax,
  showscale:false,opacity:0.94,connectgaps:false,
  customdata:sliceCustom,
  hovertemplate:"X %{x:.2f} cm<br>Y %{y:.2f} cm<br>Z "+planeZ.toFixed(2)+" cm<br>Recorded "+escapeHtml(score)+" mean %{customdata[0]:.6g}<br>Monte Carlo standard error %{customdata[1]:.4g}<br>Relative MC SE %{customdata[2]:.4g}%<extra>Selected Z bin</extra>"
 };
 const traceLayout={
  autosize:true,margin:{l:0,r:8,t:8,b:8},showlegend:false,
  scene:{
   xaxis:{title:{text:"X position (cm)"},color:palette.muted,gridcolor:palette.line,backgroundcolor:"#091724",showbackground:true,range:[xs[0]-(xs[1]-xs[0])/2,xs[nx-1]+(xs[1]-xs[0])/2]},
   yaxis:{title:{text:"Y position (cm)"},color:palette.muted,gridcolor:palette.line,backgroundcolor:"#091724",showbackground:true,range:[ys[0]-(ys[1]-ys[0])/2,ys[ny-1]+(ys[1]-ys[0])/2]},
   zaxis:{title:{text:"Physical Z (cm)"},color:palette.muted,gridcolor:palette.line,backgroundcolor:"#091724",showbackground:true,range:[zs[0]-(zs[1]-zs[0])/2,zs[nz-1]+(zs[1]-zs[0])/2]},
   aspectmode:"manual",aspectratio:{x:1,y:1,z:Math.max(0.5,(zs[nz-1]-zs[0])/(xs[nx-1]-xs[0]))},
   camera:{eye:{x:1.6,y:1.7,z:1.45},center:{x:0,y:0,z:0},up:{x:0,y:0,z:1}}
  },
  uirevision:"cbpfr-physical-axial-volume-v1"
 };
 if(revision!==axial3dDrawRevision)return;
 chart("axial3dPlot",[volumeTrace,sliceTrace],traceLayout);
 $("axial3dSliceLabel").textContent="Z bin "+zIndex+" · "+planeZ.toFixed(2)+" cm";
 const quality=payload.provenance?.score_summary||{};
 const medianRse=Number(quality.relative_error_percent_median_positive_bins);
 const p95Rse=Number(quality.relative_error_percent_p95_positive_bins);
 const uncertaintyText=Number.isFinite(medianRse)
  ?" Positive-mean voxel relative MC standard error: median "+medianRse.toFixed(1)+"%"+(Number.isFinite(p95Rse)?", 95th percentile "+p95Rse.toFixed(1)+"%":"")+". These statistics describe sampling uncertainty spatially; they are not a formal acceptance threshold."
  :" Spatial relative-error summary is not present in the sidecar.";
 $("axial3dSummary").textContent="Score: "+score+" · view: "+(view==="relative_error"?"relative Monte Carlo standard error (%)":"log₁₀ of recorded mean for volume colour")+" · selected plane Z = "+planeZ.toFixed(2)+" cm · volume iso-range "+isomin.toPrecision(4)+" to "+isomax.toPrecision(4)+" · opacity "+opacity.toFixed(2)+". Voxel means and errors remain the recorded values; only the displayed colour variable is transformed."+uncertaintyText;
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
   $("geometryProvenance").textContent="Manifest schema v1 · "+(modelGeometryData?.candidates?.length||0)+" candidate geometry.xml records · "+(modelGeometryData?.core_lattice?.dimensions||[]).join(" × ")+" core lattice · pin-material universe maps and boundary conditions source-extracted from archived XML. No separate native PNG/VTK/VTI plot is checked into scanned output folders.";
   list.innerHTML='<div class="empty-state"><b>No separate OpenMC plot artifact found</b><p>The main panel still renders the archived model lattice and pin-material regions for the selected candidate.</p><p>Native PNG/VTK/VTI artifacts can be inspected here when present.</p></div>';
   geometryArtifactActive=false;
   const selected=records.find(r=>String(r.candidate_id)===$("candidateSelect")?.value);
   drawModelGeometry(selected);
   return;
  }
  $("geometryArtifactStatus").textContent=items.length+" FILE(S) FOUND";
  $("geometryArtifactStatus").classList.remove("warning");
  $("geometryProvenance").textContent="Manifest schema v1 · "+(modelGeometryData?.candidates?.length||0)+" candidate geometry.xml records · found "+items.length+" existing native geometry file(s). Select a file below to inspect that external artifact.";
  list.innerHTML=items.map((item,i)=>'<button class="artifact-item" type="button" data-artifact-index="'+i+'"><span class="artifact-icon">'+(item.kind==="image"?"IMG":"3D")+'</span><span class="artifact-meta"><b>'+escapeHtml(item.name)+'</b><small>'+escapeHtml(item.path)+' · '+item.format+' · '+formatBytes(item.size_bytes)+'</small></span><span class="tag">'+item.kind.toUpperCase()+'</span></button>').join("");
  list.querySelectorAll("[data-artifact-index]").forEach(button=>button.addEventListener("click",()=>showGeometryArtifact(items[Number(button.dataset.artifactIndex)])));
  geometryArtifactActive=false;
  const selected=records.find(r=>String(r.candidate_id)===$("candidateSelect")?.value);
  drawModelGeometry(selected);
 }catch(error){
  $("geometryArtifactStatus").textContent="SCAN FAILED";$("geometryArtifactStatus").classList.add("warning");
  $("geometryProvenance").textContent="OpenMC geometry manifest was loaded separately. Could not inspect additional native artifacts: "+error.message;
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
  assemblyRecords=(payload.records||[]).filter(r=>assemblyPositionDefs.every(position=>has(r,position.key)));
  if(!assemblyRecords.length)throw new Error("No complete 2×2 assembly proxy records.");
  $("assemblyFieldStatus").textContent="RECORDED PROXY DATA";
  $("assemblyFieldProvenance").textContent=payload.source+" · "+payload.status_scope+". Values are recorded assembly-integrated fission-rate proxies; they are not absolute power and do not establish feasibility. Proxy seeds are independent of the candidate-summary seeds; do not compare as paired runs.";
  drawAssemblyField();
 }catch(error){
  $("assemblyFieldStatus").textContent="ASSEMBLY DATA UNAVAILABLE";
  $("assemblyFieldStatus").classList.add("warning");
  $("assemblyFieldProvenance").textContent="Could not load assembly evidence: "+error.message;
  ["assemblyMap","assemblyMatrix"].forEach(id=>{if($(id))$(id).innerHTML='<div class="loading">No assembly values displayed; no data are fabricated.</div>';});
 }
}
function drawAssemblyField(){
 if(!assemblyRecords.length||!$("assemblyMap")||!$("assemblyMatrix"))return;
 const selectedId=String($("candidateSelect")?.value||"");
 const selected=records.find(r=>String(r.candidate_id)===selectedId);
 const row=selected?assemblyRecords.find(item=>
  String(item.candidate_id)===String(selected.candidate_id)&&
  String(item.layout_signature).toUpperCase()===String(selected.layout_signature).toUpperCase()
 ):null;
 const matrixRows=records.slice().sort((a,b)=>{
  const av=has(a,"keff_mean")?Number(a.keff_mean):Number.POSITIVE_INFINITY;
  const bv=has(b,"keff_mean")?Number(b.keff_mean):Number.POSITIVE_INFINITY;
  return av-bv;
 }).map(candidate=>{
  const proxy=assemblyRecords.find(item=>
   String(item.candidate_id)===String(candidate.candidate_id)&&
   String(item.layout_signature).toUpperCase()===String(candidate.layout_signature).toUpperCase()
  );
  if(!proxy||!assemblyPositionDefs.every(position=>has(proxy,position.key)))return null;
  return {candidate,proxy,values:assemblyPositionDefs.map(position=>Number(proxy[position.key]))};
 }).filter(Boolean);

 // A common min/max is used by both views. Changing candidates must not rescale
 // the colour field and visually exaggerate otherwise comparable proxy values.
 const globalValues=matrixRows.flatMap(item=>item.values).filter(Number.isFinite);
 if(!globalValues.length){
  $("assemblyMatrix").innerHTML='<div class="empty-state"><b>Quantitative scale unavailable</b><p>No finite, exact ID-and-layout-matched proxy values are available.</p></div>';
  $("assemblyMap").innerHTML='<div class="empty-state"><b>Assembly data unavailable</b><p>No numerical field is drawn without recorded values.</p></div>';
  return;
 }
 const observedMin=Math.min(...globalValues),observedMax=Math.max(...globalValues);
 const scaleMin=observedMin,scaleMax=observedMax>observedMin?observedMax:observedMin+Math.max(Math.abs(observedMin)*0.01,1e-9);
 const mid=(scaleMin+scaleMax)/2;
 const colorbar={
  title:{text:"Fission-rate proxy<br>(source units not specified)",font:{size:10,color:palette.text}},
  thickness:13,outlinewidth:0,tickfont:{size:9,color:palette.muted},
  tickmode:"array",tickvals:[scaleMin,mid,scaleMax],
  ticktext:[formatSourceProxy(scaleMin),formatSourceProxy(mid),formatSourceProxy(scaleMax)],
  ticks:"outside",len:0.78
 };

 if(!row){
  $("assemblyMap").innerHTML='<div class="empty-state"><b>No exact candidate proxy record</b><p>The selected candidate ID and layout signature have no matching assembly run. Values are not borrowed from another layout.</p></div>';
  $("assemblyPositionTitle").textContent=selectedAssemblyPosition;
  $("assemblyPositionMaterial").textContent="NO MATCH";
  $("assemblyPositionValue").textContent="—";
  $("assemblyPositionPicker").innerHTML="";
 }else{
  if(!assemblyPositionDefs.some(position=>position.label===selectedAssemblyPosition))selectedAssemblyPosition="P00";
  const signature=normalizeLayoutSignature(row.layout_signature);
  const positionFor=(position)=>({
   ...position,
   value:Number(row[position.key]),
   material:signature[position.index]==="M"?"MOX":"UO₂",
   materialCode:signature[position.index]
  });
  const cells=assemblyPositionDefs.map(positionFor);
  const selectedPosition=cells.find(position=>position.label===selectedAssemblyPosition)||cells[0];
  $("assemblyPositionTitle").textContent=selectedPosition.label;
  $("assemblyPositionMaterial").textContent=selectedPosition.material;
  $("assemblyPositionMaterial").className="material-chip "+(selectedPosition.materialCode==="M"?"material-chip-mox":"material-chip-uo2");
  $("assemblyPositionValue").textContent=formatSourceProxy(selectedPosition.value);
  $("assemblyPositionPicker").innerHTML=cells.map(position=>
   '<button type="button" class="assembly-position-option '+(position.label===selectedAssemblyPosition?"selected":"")+'" data-assembly-position="'+position.label+'" aria-pressed="'+String(position.label===selectedAssemblyPosition)+'">'+
    '<span>'+position.label+'</span><b>'+position.material+'</b><strong>'+formatSourceProxy(position.value)+'</strong>'+
   '</button>'
  ).join("");
  $("assemblyPositionPicker").querySelectorAll("[data-assembly-position]").forEach(button=>button.addEventListener("click",()=>{
   selectedAssemblyPosition=button.dataset.assemblyPosition;
   drawAssemblyField();
  }));

  const z=[
   [cells[0].value,cells[1].value],
   [cells[2].value,cells[3].value]
  ];
  const customdata=[
   [cells[0],cells[1]],
   [cells[2],cells[3]]
  ].map(line=>line.map(position=>[
   position.label,position.material,row.candidate_id,signature,row.seed,row.status
  ]));
  const textValues=cells.map(position=>position.label+" · "+(position.materialCode==="M"?"M":"U")+"\n"+formatSourceProxy(position.value));
  const heatmap={
   type:"heatmap",name:"Assembly-integrated fission-rate proxy",
   x:["Column 0","Column 1"],y:["Row 0","Row 1"],
   z,text:[[textValues[0],textValues[1]],[textValues[2],textValues[3]]],
   texttemplate:"%{text}",textfont:{size:11,color:"#f0f3f5"},
   customdata,colorscale:"Cividis",zmin:scaleMin,zmax:scaleMax,zauto:false,
   colorbar,
   xgap:4,ygap:4,hoverongaps:false,connectgaps:false,
   hovertemplate:"Position %{customdata[0]} · %{customdata[1]}<br>Candidate %{customdata[2]}<br>Layout %{customdata[3]}<br>Recorded fission-rate proxy %{z:.8g}<br>Source unit: not specified · not absolute power<br>Proxy-run seed %{customdata[4]}<extra></extra>"
  };
  const materialOutline={
   type:"scatter",mode:"markers",name:"Material category outline",
   x:cells.map(position=>position.col===0?"Column 0":"Column 1"),
   y:cells.map(position=>position.row===0?"Row 0":"Row 1"),
   customdata:cells.map(position=>position.label),
   marker:{
    symbol:"square-open",size:49,
    color:cells.map(position=>materialEdgeColor[position.materialCode]),
    line:{width:2.6,color:cells.map(position=>materialEdgeColor[position.materialCode])}
   },
   hoverinfo:"skip",showlegend:false
  };
  const highlighted=cells.find(position=>position.label===selectedAssemblyPosition)||cells[0];
  const selectionOutline={
   type:"scatter",mode:"markers",name:"Selected spatial position",
   x:[highlighted.col===0?"Column 0":"Column 1"],
   y:[highlighted.row===0?"Row 0":"Row 1"],
   customdata:[highlighted.label],
   marker:{symbol:"square-open",size:62,color:"#ffffff",line:{width:3.2,color:"#ffffff"}},
   hoverinfo:"skip",showlegend:false
  };
  const mapEl=$("assemblyMap");
  chart("assemblyMap",[heatmap,materialOutline,selectionOutline],{
   autosize:true,margin:{l:58,r:112,t:14,b:52},
   showlegend:false,hovermode:"closest",
   xaxis:{...baseLayout.xaxis,title:{text:"Core-map column",standoff:9},type:"category",categoryorder:"array",categoryarray:["Column 0","Column 1"],tickangle:0,automargin:true,gridcolor:"rgba(38,63,82,0.35)"},
   yaxis:{...baseLayout.yaxis,title:{text:"Core-map row · row 0 at top",standoff:8},type:"category",categoryorder:"array",categoryarray:["Row 0","Row 1"],autorange:"reversed",tickangle:0,automargin:true,gridcolor:"rgba(38,63,82,0.35)"},
   annotations:[{xref:"paper",yref:"paper",x:0,y:1.08,xanchor:"left",yanchor:"bottom",showarrow:false,text:"P00 → P01 / P10 → P11 · row-major",font:{size:9,color:palette.muted}}]
  }).then(()=>{
   if(!mapEl||typeof mapEl.on!=="function"||mapEl.dataset.positionClickBound)return;
   mapEl.on("plotly_click",event=>{
    const point=(event?.points||[]).find(item=>item?.curveNumber===0)|| (event?.points||[])[0];
    const raw=point?.customdata;
    const position=Array.isArray(raw)?raw[0]:raw;
    if(assemblyPositionDefs.some(item=>item.label===position)&&position!==selectedAssemblyPosition){
     selectedAssemblyPosition=position;
     drawAssemblyField();
    }
   });
   mapEl.dataset.positionClickBound="true";
  });
 }
 if(!matrixRows.length){
  $("assemblyMatrix").innerHTML='<div class="empty-state"><b>Position matrix unavailable</b><p>No complete exact candidate-ID and layout-signature matches exist in the proxy file.</p></div>';
  return;
 }
 const matrixTrace={
  type:"heatmap",name:"Recorded assembly fission-rate proxy",
  x:assemblyPositionDefs.map(position=>position.label),
  y:matrixRows.map(item=>String(item.candidate.layout_signature||label(item.candidate))),
  z:matrixRows.map(item=>item.values),
  text:matrixRows.map(item=>item.values.map(formatSourceProxy)),
  texttemplate:"%{text}",textfont:{size:10,color:"#f0f3f5"},
  colorscale:"Cividis",zmin:scaleMin,zmax:scaleMax,zauto:false,showscale:false,
  xgap:3,ygap:2,
  customdata:matrixRows.map(item=>item.values.map((value,index)=>[
   item.candidate.candidate_id,item.candidate.layout_signature,
   assemblyPositionDefs[index].label,item.proxy.seed,item.proxy.status
  ])),
  hovertemplate:"Candidate %{customdata[0]}<br>Layout %{customdata[1]}<br>Position %{customdata[2]}<br>Recorded fission-rate proxy %{z:.8g}<br>Source unit: not specified · not absolute power<br>Proxy-run seed %{customdata[3]}<br>Status %{customdata[4]}<extra></extra>"
 };
 const selectedRow=matrixRows.find(item=>String(item.candidate.candidate_id)===selectedId&&String(item.candidate.layout_signature).toUpperCase()===String(selected?.layout_signature||"").toUpperCase());
 const traces=[matrixTrace];
 if(selectedRow)traces.push({
  type:"scatter",mode:"markers",name:"Selected candidate",
  x:assemblyPositionDefs.map(position=>position.label),
  y:assemblyPositionDefs.map(()=>String(selectedRow.candidate.layout_signature||label(selectedRow.candidate))),
  marker:{symbol:"square-open",size:34,color:"#ffffff",line:{width:1.8,color:"#ffffff"}},
  hoverinfo:"skip",showlegend:false
 });
 chart("assemblyMatrix",traces,{
  autosize:true,margin:{l:62,r:20,t:16,b:50},showlegend:false,hovermode:"closest",
  xaxis:{...baseLayout.xaxis,title:{text:"Fuel position · row-major",standoff:10},type:"category",categoryorder:"array",categoryarray:["P00","P01","P10","P11"],tickangle:0,automargin:true,gridcolor:"rgba(38,63,82,0.3)"},
  yaxis:{...baseLayout.yaxis,title:{text:"Candidate layout · descriptive k-effective order",standoff:8},type:"category",autorange:"reversed",automargin:true,tickangle:0,tickfont:{size:11,color:palette.muted},gridcolor:"rgba(38,63,82,0.25)"},
  annotations:[{xref:"paper",yref:"paper",x:1,y:1.07,xanchor:"right",yanchor:"bottom",showarrow:false,text:selectedRow?"Outlined row = selected candidate":"No matching candidate selected",font:{size:9,color:palette.muted}}]
 });
}
