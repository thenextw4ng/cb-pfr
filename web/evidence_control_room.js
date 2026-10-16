(function(){
  "use strict";
  const $ = selector => document.querySelector(selector);
  const state = { registry: null, activeId: "v2a-policy-replay", query: "", filter: "all", loading: false };
  const escapeHtml = value => String(value == null ? "" : value).replace(/[&<>"']/g, ch => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"
  }[ch]));
  const safeHref = value => {
    const raw = String(value || "");
    return /^(https:\/\/|http:\/\/|\/|#)/.test(raw) ? raw : "#evidence-control-room";
  };
  const kindName = value => ({
    candidate:"CANDIDATE RUN RECORDS",
    campaign:"CAMPAIGN / REPLAY",
    geometry:"SOURCE GEOMETRY",
    openmc:"OPENMC TALLY",
    synthetic:"SYNTHETIC METHOD"
  }[value] || String(value || "EVIDENCE").toUpperCase());
  function visibleRecords() {
    const records = state.registry && Array.isArray(state.registry.records) ? state.registry.records : [];
    const q = state.query.trim().toLowerCase();
    return records.filter(record => {
      if(state.filter !== "all" && record.classification !== state.filter) return false;
      if(!q) return true;
      const text = [
        record.title,record.domain,record.status,record.summary,record.coverage,
        ...(record.metrics || []).flatMap(item => [item.label,item.value]),
        ...(record.sources || []).flatMap(item => [item.label,item.path,item.sha256]),
        ...(record.limitations || [])
      ].join(" ").toLowerCase();
      return text.includes(q);
    });
  }
  function renderKpis() {
    const node=$("#ecrKpis");
    if(!node || !state.registry) return;
    const s=state.registry.summary || {};
    const n=(value)=>Number(value||0).toLocaleString("en-US");
    const convergence=state.registry.summary?.convergence_status || "NOT CERTIFIED";
    const cards=[
      ["Registered evidence groups",n(s.record_count),"Source types stay separated"],
      ["V2a observations",n(s.campaign_observed_runs)+" + "+n(s.high_budget_reference_runs),"Low-budget runs + high-budget references"],
      ["Source layouts",n(s.layout_count),"Candidate-specific geometry records"],
      ["Campaign convergence",convergence,"No certification inferred by this registry"]
    ];
    node.innerHTML=cards.map(([label,value,small])=>'<article class="metric"><label>'+escapeHtml(label)+'</label><strong>'+escapeHtml(value)+'</strong><small>'+escapeHtml(small)+'</small></article>').join("");
  }
  function renderCards() {
    const list=$("#ecrRecordList");
    if(!list || !state.registry) return;
    const records=visibleRecords();
    if(!records.length) {
      list.innerHTML='<div class="ecr-detail-empty"><b>No matching source records</b><p>Change the filter or remove part of the search query.</p></div>';
      renderDetail(null);
      return;
    }
    if(!records.some(record=>record.id===state.activeId)) state.activeId=records[0].id;
    list.innerHTML=records.map(record=>{
      const selected=record.id===state.activeId;
      const sources=record.sources||[];
      const available=sources.filter(item=>item.available).length;
      return '<button type="button" class="ecr-record-card" role="option" aria-selected="'+(selected?"true":"false")+'" tabindex="'+(selected?"0":"-1")+'" data-ecr-id="'+escapeHtml(record.id)+'">'+
        '<span class="ecr-card-domain">'+escapeHtml(record.domain)+'</span>'+
        '<span class="ecr-card-top"><span><h3>'+escapeHtml(record.title)+'</h3></span><span class="ecr-status '+escapeHtml(record.status_kind||"")+'">'+escapeHtml(record.status)+'</span></span>'+
        '<div class="ecr-card-coverage">'+escapeHtml(record.coverage)+'</div>'+
        '<div class="ecr-card-source-count">'+available+' / '+sources.length+' LOCAL FILE REFERENCES AVAILABLE</div>'+
      '</button>';
    }).join("");
    list.querySelectorAll("[data-ecr-id]").forEach((button,index,buttons)=>{
      button.addEventListener("click",()=>selectRecord(button.dataset.ecrId));
      button.addEventListener("keydown",event=>{
        if(event.key!=="ArrowDown"&&event.key!=="ArrowUp")return;
        event.preventDefault();
        const next=buttons[Math.max(0,Math.min(buttons.length-1,index+(event.key==="ArrowDown"?1:-1)))];
        next.focus();
        selectRecord(next.dataset.ecrId);
      });
    });
    renderDetail(records.find(record=>record.id===state.activeId));
  }
  function renderDetail(record) {
    const detail=$("#ecrDetail");
    if(!detail)return;
    if(!record) {
      detail.innerHTML='<div class="ecr-detail-empty"><b>Select an evidence record</b><p>Coverage, source files, integrity hashes, linked views and scientific limits will appear here.</p></div>';
      return;
    }
    const metrics=(record.metrics||[]).map(metric=>'<div class="ecr-fact"><label>'+escapeHtml(metric.label)+'</label><strong>'+escapeHtml(metric.value)+'</strong></div>').join("");
    const sources=(record.sources||[]).map((source,index)=>{
      const isAvailable=!!source.available;
      const hash=source.sha256 || (record.source_document&&record.source_document.sha256&&source.label==="Snapshot containing method-study results"?record.source_document.sha256:"");
      const size=source.size_bytes==null?"size not available":Number(source.size_bytes).toLocaleString("en-US")+" bytes";
      const link=source.url?'<a class="ecr-source-link" href="'+escapeHtml(safeHref(source.url))+'" target="'+(source.url.startsWith("https://")?"_blank":"_self")+'" '+(source.url.startsWith("https://")?'rel="noreferrer"':'')+'>Open source ↗</a>':"";
      const member=source.member?'<div class="ecr-source-path">Archive member: '+escapeHtml(source.member)+' ('+escapeHtml(source.member_size_bytes||0)+' bytes)</div>':"";
      return '<div class="ecr-source-row">'+
        '<div class="ecr-source-top"><span class="ecr-source-name">'+escapeHtml(source.label||source.path||"Source artifact")+'</span><span class="ecr-source-state">'+(isAvailable?"AVAILABLE":"NOT LOCAL")+'</span></div>'+
        '<div class="ecr-source-path">'+escapeHtml(source.path||"External source")+' · '+escapeHtml(size)+'</div>'+member+
        (hash?'<div class="ecr-hash-row"><code class="ecr-hash">'+escapeHtml(hash)+'</code><button class="ecr-copy-hash" type="button" data-ecr-copy="'+escapeHtml(hash)+'">COPY SHA</button></div>':"")+
        link+'</div>';
    }).join("");
    const limits=(record.limitations||[]).map(item=>"<li>"+escapeHtml(item)+"</li>").join("");
    const links=(record.links||[]).filter(item=>item.url).map(item=>{
      const href=safeHref(item.url), external=href.startsWith("https://")||href.startsWith("http://");
      return '<a href="'+escapeHtml(href)+'"'+(external?' target="_blank" rel="noreferrer"':'')+'>'+escapeHtml(item.label)+' ↗</a>';
    }).join("");
    const sourceDocument=record.source_document?'<div class="note-row"><span class="note-icon">i</span><p><b>Document provenance.</b> '+escapeHtml(record.source_document.filename||"Source document")+' · '+escapeHtml(record.source_document.pages||"unknown")+' pages · SHA-256 '+escapeHtml(record.source_document.sha256||"not recorded")+'. '+(record.source_document.committed_as_binary?"The PDF binary is stored with this repository.":"The supplied PDF binary is not committed here; transcribed tables and source hash are retained in the snapshot.")+'</p></div>':"";
    detail.innerHTML=
      '<div class="ecr-detail-head"><div><div class="ecr-detail-domain">'+escapeHtml(kindName(record.classification))+' / '+escapeHtml(record.domain)+'</div><h3>'+escapeHtml(record.title)+'</h3><div class="ecr-detail-summary">'+escapeHtml(record.summary)+'</div></div><span class="ecr-status '+escapeHtml(record.status_kind||"")+'">'+escapeHtml(record.status)+'</span></div>'+
      '<div class="ecr-fact-grid">'+metrics+'</div>'+
      '<h4>Source files &amp; integrity</h4><div class="ecr-source-list">'+(sources||"")+'</div>'+
      sourceDocument+
      '<h4>Scope and interpretation limits</h4><ul class="ecr-limitations">'+(limits||"<li>No limitations were registered.</li>")+'</ul>'+
      '<div class="ecr-link-row">'+links+'</div>';
    detail.querySelectorAll("[data-ecr-copy]").forEach(button=>button.addEventListener("click",async()=>{
      const text=button.dataset.ecrCopy;
      try{
        await navigator.clipboard.writeText(text);
        const before=button.textContent;button.textContent="COPIED";
        window.setTimeout(()=>{button.textContent=before;},1100);
      }catch(_){
        const before=button.textContent;button.textContent="SELECT HASH";
        button.title=text;
        window.setTimeout(()=>{button.textContent=before;},1500);
      }
    }));
  }
  function selectRecord(id) {
    state.activeId=id;
    renderCards();
  }
  async function loadRegistry() {
    if(state.loading)return;
    state.loading=true;
    const refresh=$("#ecrRefresh");
    const status=$("#ecrStatus");
    const message=$("#ecrMessage");
    if(refresh){refresh.disabled=true;refresh.textContent="↻ Checking…";}
    if(status){status.textContent="CHECKING SOURCE FILES…";status.className="tag";}
    if(message)message.textContent="Checking file presence, artifact sizes, SHA-256, geometry counts and snapshot coverage. Large tally arrays are not downloaded for this check.";
    try {
      const response=await fetch("/api/evidence-registry",{cache:"no-store",headers:{Accept:"application/json"}});
      if(!response.ok)throw new Error("Evidence registry HTTP "+response.status);
      const registry=await response.json();
      if(!Array.isArray(registry.records)||registry.records.length<5)throw new Error("Registry schema incomplete: expected at least five evidence records");
      state.registry=registry;
      const selected=registry.records.find(record=>record.id===state.activeId);
      if(!selected)state.activeId=registry.records[0].id;
      renderKpis();renderCards();
      if(status){status.textContent="REGISTRY READY · "+registry.records.length+" EVIDENCE GROUPS";status.className="tag success";}
      if(message)message.textContent="Snapshot "+(registry.snapshot_date||"date not declared")+" · "+(registry.summary?.available_file_count||0)+" local file references available · recorded evidence only.";
    }catch(error){
      if(status){status.textContent="REGISTRY UNAVAILABLE";status.className="tag warning";}
      if(message)message.textContent="Could not read the evidence registry: "+error.message;
      const list=$("#ecrRecordList");if(list)list.innerHTML='<div class="ecr-detail-empty"><b>Evidence registry unavailable</b><p>'+escapeHtml(error.message)+'</p><p>Check that web_server.py is running from the repository root.</p></div>';
      const detail=$("#ecrDetail");if(detail)detail.innerHTML='<div class="ecr-detail-empty"><b>Source audit could not run</b><p>No evidence records are shown until the API is reachable.</p></div>';
    }finally{
      state.loading=false;
      if(refresh){refresh.disabled=false;refresh.textContent="↻ Refresh registry";}
    }
  }
  document.addEventListener("DOMContentLoaded",()=>{
    const search=$("#ecrSearch"),filter=$("#ecrFilter"),refresh=$("#ecrRefresh");
    if(search)search.addEventListener("input",()=>{state.query=search.value;renderCards();});
    if(filter)filter.addEventListener("change",()=>{state.filter=filter.value;renderCards();});
    if(refresh)refresh.addEventListener("click",loadRegistry);
    loadRegistry();
  });
})();