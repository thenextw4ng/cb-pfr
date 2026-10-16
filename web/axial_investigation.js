(function(){
  "use strict";
  const $ = id => document.getElementById(id);
  const state = { data:null, plane:"XY", profileAxis:"X", selected:null };
  const colorscaleName = () => $("axial3dPalette")?.value || "Viridis";
  const currentView = () => $("axial3dView")?.value || "mean";
  const fmt = (v,n=5) => Number.isFinite(Number(v)) ? Number(v).toFixed(n) : "not recorded";
  const safe = v => String(v == null ? "" : v).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  const empty = (title,message) => '<div class="empty-state"><b>'+safe(title)+'</b><p>'+safe(message)+'</p></div>';
  function axes(){
    const m=state.data?.mesh||{};
    return {x:Array.isArray(m.x_centers_cm)?m.x_centers_cm:[],y:Array.isArray(m.y_centers_cm)?m.y_centers_cm:[],z:Array.isArray(m.z_centers_cm)?m.z_centers_cm:[]};
  }
  function dims(){const a=axes();return {nx:a.x.length,ny:a.y.length,nz:a.z.length};}
  function displayed(mean,rse){return currentView()==="relative_error"?(Number.isFinite(rse)?rse:null):(Number.isFinite(mean)&&mean>0?Math.log10(mean):null);}
  function rangeFor(values){
    const finite=values.flat(Infinity).filter(v=>Number.isFinite(v));
    if(!finite.length)return {min:0,max:1};
    let min=Math.min(...finite),max=Math.max(...finite);
    if(!(max>min)){const d=Math.max(Math.abs(min)*0.02,1e-6);min-=d;max+=d;}
    return {min,max};
  }
  function customVoxel(i,j,k){
    const d=state.data,a=axes(),m=d.mean[k][j][i],se=d.standard_error[k][j][i],r=d.relative_error_percent[k][j][i];
    return [m,se,r,i,j,k,a.x[i],a.y[j],a.z[k]];
  }
  function axisTitle(axis){return axis+" position (cm)";}
  function hoverTemplate(){
    return "Recorded "+safe(state.data?.score||"tally")+" voxel<br>X %{customdata[6]:.4f} cm · bin %{customdata[3]}<br>Y %{customdata[7]:.4f} cm · bin %{customdata[4]}<br>Z %{customdata[8]:.4f} cm · bin %{customdata[5]}<br>Mean %{customdata[0]:.7g}<br>Monte Carlo standard error %{customdata[1]:.5g}<br>Relative MC standard error %{customdata[2]:.4g}%<extra></extra>";
  }
  function updatePlaneControl(){
    const d=dims(),plane=$("axialPlaneSelect")?.value||"XY";state.plane=plane;
    const slider=$("axialPlaneIndex"),label=$("axialPlaneIndexLabel");if(!slider)return;
    const max=plane==="XY"?d.nz-1:plane==="XZ"?d.ny-1:d.nx-1;
    slider.max=String(Math.max(0,max));
    const current3dZ=Number($("axial3dSlice")?.value||0);
    if(plane==="XY"&&d.nz)slider.value=String(Math.min(current3dZ,d.nz-1));
    else slider.value=String(Math.min(Number(slider.value)||0,Math.max(0,max)));
    const idx=Number(slider.value||0),a=axes(),normal=plane==="XY"?"Z":plane==="XZ"?"Y":"X";
    const coord=plane==="XY"?a.z[idx]:plane==="XZ"?a.y[idx]:a.x[idx];
    if(label)label.textContent=normal+" bin "+idx+(Number.isFinite(coord)?" · "+coord.toFixed(3)+" cm":"");
    renderPlane();
  }
  function currentPlaneIndex(){return Math.max(0,Number($("axialPlaneIndex")?.value||0));}
  function renderPlane(){
    const host=$("axialSectionPlot");if(!host||!state.data)return;
    const d=state.data,a=axes(),{nx,ny,nz}=dims(),plane=state.plane,index=currentPlaneIndex();
    if(!nx||!ny||!nz){host.innerHTML=empty("Coordinates unavailable","The source tally has no coordinate centers for the selected mesh.");return;}
    let x=[],y=[],raw=[],custom=[],xName="",yName="",normal="",normalCoord=0;
    const mean=d.mean,se=d.standard_error,rse=d.relative_error_percent;
    if(plane==="XY"){
      normal="Z";normalCoord=a.z[index];x=a.x;y=a.y;xName=axisTitle("X");yName=axisTitle("Y");
      raw=mean[index].map((row,j)=>row.map((m,i)=>displayed(m,rse[index][j][i])));
      custom=mean[index].map((row,j)=>row.map((m,i)=>customVoxel(i,j,index)));
    }else if(plane==="XZ"){
      normal="Y";normalCoord=a.y[index];x=a.x;y=a.z;xName=axisTitle("X");yName=axisTitle("Z");
      raw=Array.from({length:nz},(_,k)=>Array.from({length:nx},(_,i)=>displayed(mean[k][index][i],rse[k][index][i])));
      custom=Array.from({length:nz},(_,k)=>Array.from({length:nx},(_,i)=>customVoxel(i,index,k)));
    }else{
      normal="X";normalCoord=a.x[index];x=a.y;y=a.z;xName=axisTitle("Y");yName=axisTitle("Z");
      raw=Array.from({length:nz},(_,k)=>Array.from({length:ny},(_,j)=>displayed(mean[k][j][index],rse[k][j][index])));
      custom=Array.from({length:nz},(_,k)=>Array.from({length:ny},(_,j)=>customVoxel(index,j,k)));
    }
    const scale=rangeFor(raw),trace={type:"heatmap",name:plane+" source tally slice",x,y,z:raw,customdata:custom,colorscale:colorscaleName(),zmin:scale.min,zmax:scale.max,connectgaps:false,
      colorbar:{title:{text:currentView()==="relative_error"?"Relative MC SE (%)":"log₁₀ mean",font:{size:10,color:"#d6e2eb"}},tickfont:{size:9,color:"#9bb0bf"},thickness:10},
      hovertemplate:hoverTemplate()};
    const status=$("axialSectionStatus");if(status)status.textContent=plane+" CUT · "+normal+"="+fmt(normalCoord,3)+" cm";
    if(!window.Plotly){host.innerHTML=empty("Plotly unavailable","This orthogonal slice needs Plotly.js. Source arrays remain untouched.");return;}
    window.Plotly.react(host,[trace],{
      paper_bgcolor:"rgba(0,0,0,0)",plot_bgcolor:"rgba(0,0,0,0)",font:{family:"Manrope, sans-serif",color:"#b7c8d6",size:10},
      margin:{l:64,r:25,t:15,b:56},xaxis:{title:xName,gridcolor:"#1b3445",linecolor:"#294455",automargin:true},
      yaxis:{title:yName,gridcolor:"#1b3445",linecolor:"#294455",automargin:true,autorange:"reversed"},uirevision:"cbpfr-axial-plane-"+plane
    },{responsive:true,displaylogo:false,modeBarButtonsToRemove:["lasso2d","select2d"]}).then(()=>bindVoxelReadout(host)).catch(err=>{host.innerHTML=empty("Slice render failed",err.message||err);});
  }
  function updateProfileLabels(){
    const d=dims(),axis=$("axialProfileAxis")?.value||"X";state.profileAxis=axis;
    const a=$("axialProfileFixedA"),b=$("axialProfileFixedB"),labelA=$("axialProfileFixedALabel"),labelB=$("axialProfileFixedBLabel");
    let cfg;
    if(axis==="X")cfg={aAxis:"Y",aMax:d.ny-1,bAxis:"Z",bMax:d.nz-1};
    else if(axis==="Y")cfg={aAxis:"X",aMax:d.nx-1,bAxis:"Z",bMax:d.nz-1};
    else cfg={aAxis:"X",aMax:d.nx-1,bAxis:"Y",bMax:d.ny-1};
    if(a){a.max=String(Math.max(0,cfg.aMax));a.value=String(Math.min(Number(a.value)||0,Math.max(0,cfg.aMax)));}
    if(b){b.max=String(Math.max(0,cfg.bMax));b.value=String(Math.min(Number(b.value)||0,Math.max(0,cfg.bMax)));}
    if(labelA)labelA.textContent="FIXED "+cfg.aAxis+" BIN";if(labelB)labelB.textContent="FIXED "+cfg.bAxis+" BIN";
    const coords=axes(),ai=Number(a?.value||0),bi=Number(b?.value||0);
    const ca=cfg.aAxis==="X"?coords.x[ai]:cfg.aAxis==="Y"?coords.y[ai]:coords.z[ai];
    const cb=cfg.bAxis==="X"?coords.x[bi]:cfg.bAxis==="Y"?coords.y[bi]:coords.z[bi];
    const status=$("axialProfileIndexLabel");if(status)status.textContent=cfg.aAxis+"["+ai+"] "+fmt(ca,3)+" cm · "+cfg.bAxis+"["+bi+"] "+fmt(cb,3)+" cm";
    renderProfile();
  }
  function renderProfile(){
    const host=$("axialLineProfilePlot");if(!host||!state.data)return;
    const a=axes(),d=state.data,dn=dims(),axis=$("axialProfileAxis")?.value||"X";
    const fi=Number($("axialProfileFixedA")?.value||0),fj=Number($("axialProfileFixedB")?.value||0);
    const x=[],values=[],errors=[],custom=[],mean=d.mean,se=d.standard_error,rse=d.relative_error_percent;
    let fixedText="";
    if(axis==="X"){
      fixedText="Y bin "+fi+", Z bin "+fj;
      for(let i=0;i<dn.nx;i++){x.push(a.x[i]);values.push(displayed(mean[fj][fi][i],rse[fj][fi][i]));errors.push(se[fj][fi][i]);custom.push(customVoxel(i,fi,fj));}
    }else if(axis==="Y"){
      fixedText="X bin "+fi+", Z bin "+fj;
      for(let j=0;j<dn.ny;j++){x.push(a.y[j]);values.push(displayed(mean[fj][j][fi],rse[fj][j][fi]));errors.push(se[fj][j][fi]);custom.push(customVoxel(fi,j,fj));}
    }else{
      fixedText="X bin "+fi+", Y bin "+fj;
      for(let k=0;k<dn.nz;k++){x.push(a.z[k]);values.push(displayed(mean[k][fj][fi],rse[k][fj][fi]));errors.push(se[k][fj][fi]);custom.push(customVoxel(fi,fj,k));}
    }
    const trace={type:"scatter",mode:"lines+markers",name:currentView()==="relative_error"?"Relative MC standard error":"Recorded tally mean",x,y:values,customdata:custom,connectgaps:false,
      line:{color:"#56dbe4",width:2},marker:{size:5,color:"#f0bc67"},
      error_y:currentView()==="mean"?{type:"data",array:errors.map(v=>Number.isFinite(v)&&v>=0?v:0),visible:true,color:"#90a7b7",thickness:1,width:2}:{visible:false},
      hovertemplate:hoverTemplate()};
    const status=$("axialProfileStatus");if(status)status.textContent=axis+" PROFILE · "+fixedText;
    if(!window.Plotly){host.innerHTML=empty("Plotly unavailable","Line-profile plots require Plotly.js.");return;}
    window.Plotly.react(host,[trace],{
      paper_bgcolor:"rgba(0,0,0,0)",plot_bgcolor:"rgba(0,0,0,0)",font:{family:"Manrope, sans-serif",color:"#b7c8d6",size:10},
      margin:{l:70,r:24,t:15,b:58},showlegend:false,
      xaxis:{title:axisTitle(axis),gridcolor:"#1b3445",linecolor:"#294455",automargin:true},
      yaxis:{title:currentView()==="relative_error"?"Relative MC standard error (%)":"Recorded mean tally · log axis",type:currentView()==="mean"?"log":"linear",gridcolor:"#1b3445",linecolor:"#294455",automargin:true},
      uirevision:"cbpfr-axial-profile-"+axis
    },{responsive:true,displaylogo:false,modeBarButtonsToRemove:["lasso2d","select2d"]}).then(()=>bindVoxelReadout(host)).catch(err=>{host.innerHTML=empty("Profile render failed",err.message||err);});
  }
  function bindVoxelReadout(host){
    if(!host||typeof host.on!=="function"||host.dataset.voxelReadoutBound)return;
    const show=event=>{
      const p=(event?.points||[])[0],v=p?.customdata;if(!Array.isArray(v)||v.length<9)return;
      state.selected=v;const node=$("axialVoxelReadout");if(!node)return;
      node.innerHTML='<span class="voxel-readout-tag">RECORDED VOXEL</span><div class="voxel-readout-grid">'+[
        ["Bin index","i="+v[3]+", j="+v[4]+", k="+v[5]],
        ["Physical position","X "+fmt(v[6],4)+" · Y "+fmt(v[7],4)+" · Z "+fmt(v[8],4)+" cm"],
        ["Tally mean",fmt(v[0],8)],
        ["Monte Carlo standard error",fmt(v[1],7)],
        ["Relative MC standard error",fmt(v[2],5)+"%"],
        ["Score / view",(state.data?.score||"unknown")+" / "+currentView()]
      ].map(pair=>'<div><span>'+safe(pair[0])+'</span><strong>'+safe(pair[1])+'</strong></div>').join("")+'</div>';
    };
    host.on("plotly_hover",show);host.on("plotly_click",show);host.dataset.voxelReadoutBound="true";
  }
  function handleNewData(){
    const d=window.CBPFRAxial3DData;if(!d||d.available!==true||!Array.isArray(d.mean))return;
    state.data=d;
    const status=$("axialInvestigationStatus");if(status){status.textContent="SOURCE ARRAYS CONNECTED · "+(d.mesh?.dimension_xyz||[]).join(" × ");status.className="tag success";}
    updatePlaneControl();updateProfileLabels();
  }
  document.addEventListener("DOMContentLoaded",()=>{
    $("axialPlaneSelect")?.addEventListener("change",updatePlaneControl);
    $("axialPlaneIndex")?.addEventListener("input",()=>{
      if(($("axialPlaneSelect")?.value||"XY")==="XY"&&$("axial3dSlice")){
        $("axial3dSlice").value=$("axialPlaneIndex").value;
        $("axial3dSlice").dispatchEvent(new Event("input",{bubbles:true}));
      }
      renderPlane();
    });
    $("axialProfileAxis")?.addEventListener("change",updateProfileLabels);
    ["axialProfileFixedA","axialProfileFixedB"].forEach(id=>$(id)?.addEventListener("input",updateProfileLabels));
    ["axial3dView","axial3dPalette"].forEach(id=>$(id)?.addEventListener("change",()=>{renderPlane();renderProfile();}));
    $("axial3dSlice")?.addEventListener("input",()=>{
      if(($("axialPlaneSelect")?.value||"XY")==="XY"){const s=$("axialPlaneIndex");if(s)s.value=$("axial3dSlice").value;updatePlaneControl();}
    });
    window.addEventListener("cbpfr-axial3d-updated",handleNewData);
    if(window.CBPFRAxial3DData)handleNewData();
  });
})();