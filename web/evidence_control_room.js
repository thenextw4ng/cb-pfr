(function(){
  "use strict";
  const byId = id => document.getElementById(id);
  const state = { sources: [], selectedId: null, filter: "all", query: "" };
  const escapeHtml = value => String(value == null ? "" : value).replace(/[&<>"']/g, char => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;", "'":"&#39;"
  }[char]));
  const pretty = value => {
    if (value === null || value === undefined || value === "") return "Not recorded";
    if (typeof value === "object") return JSON.stringify(value);
    return String(value);
  };
  function statusClass(status) {
    const s=String(status||"").toLowerCase();
    if (/unavailable|mismatch|review|required|not certified|blocked|no baseline/.test(s)) return "status-warn";
    if (/synthetic|exploratory/.test(s)) return "status-neutral";
    if (/hash match|source matched|integrity pass/.test(s)) return "status-good";
    return "status-neutral";
  }
  function classLabel(value) {
    return ({
      "openmc-candidates":"OpenMC · candidate study",
      "geometry":"Model geometry",
      "openmc-planar-tally":"OpenMC · planar tally",
      "openmc-axial-volume":"OpenMC · axial volume",
      "exploratory-proxy":"Exploratory proxy",
      "campaign-replay":"Campaign replay",
      "synthetic-method":"Synthetic method evidence"
    })[value] || String(value||"Evidence source");
  }
  function filterGroup(item) {
    if (item.evidence_class === "geometry") return "geometry";
    if (item.evidence_class === "campaign-replay" || item.evidence_class === "openmc-candidates") return "campaign";
    if (item.evidence_class === "synthetic-method") return "synthetic";
    if (item.evidence_class === "exploratory-proxy") return "exploratory";
    if (String(item.evidence_class||"").startsWith("openmc-")) return "openmc";
    return "other";
  }
  function searchableText(item) {
    return [
      item.id,item.title,item.evidence_class,item.status,item.summary,item.source_path,
      item.sha256,JSON.stringify(item.metadata||{})
    ].join(" ").toLowerCase();
  }
  function visibleSources() {
    return state.sources.filter(item =>
      (state.filter === "all" || filterGroup(item) === state.filter) &&
      (!state.query || searchableText(item).includes(state.query))
    );
  }
  function renderMetrics() {
    const sources=state.sources;
    const hashMatched=sources.filter(item => /hash match|source matched/i.test(item.status||"")).length;
    const review=sources.filter(item => /unavailable|mismatch|review|required|not certified|no baseline|exploratory/i.test(item.status||"")).length;
    const classes=new Set(sources.map(item=>item.evidence_class));
    byId("ecrSourceCount").textContent=String(sources.length);
    byId("ecrHashCount").textContent=String(hashMatched);
    byId("ecrReviewCount").textContent=String(review);
    byId("ecrClassCount").textContent=String(classes.size);
  }
  function renderCards() {
    const host=byId("ecrSourceGrid");
    const sources=visibleSources();
    byId("ecrFilterCount").textContent=sources.length+" / "+state.sources.length+" sources";
    if (!sources.length) {
      host.innerHTML='<div class="panel ecr-empty"><div class="empty-state"><b>No matching source</b><p>Change the evidence-class filter or search terms. The underlying source index has not been modified.</p></div></div>';
      return;
    }
    host.innerHTML=sources.map(item=>{
      const bytes=Number.isFinite(Number(item.bytes))?formatBytes(Number(item.bytes)):"size n/r";
      const count=item.record_count===null||item.record_count===undefined?"":" · n="+Number(item.record_count).toLocaleString("en-US");
      return '<button type="button" class="ecr-source-card" data-ecr-source="'+escapeHtml(item.id)+'" aria-pressed="'+String(item.id===state.selectedId)+'">'+
        '<span class="ecr-source-top"><span><span class="ecr-source-title">'+escapeHtml(item.title)+'</span><span class="ecr-source-class">'+escapeHtml(classLabel(item.evidence_class))+'</span></span>'+
        '<span class="ecr-source-status '+statusClass(item.status)+'">'+escapeHtml(item.status)+'</span></span>'+
        '<p class="ecr-source-summary">'+escapeHtml(item.summary)+'</p>'+
        '<span class="ecr-source-bottom"><span class="ecr-source-path">'+escapeHtml(item.source_path||"Source path not recorded")+'<br>'+escapeHtml(bytes)+'</span><span class="ecr-source-count">'+escapeHtml(count||"OPEN ↗")+'</span></span></button>';
    }).join("");
    host.querySelectorAll("[data-ecr-source]").forEach(button=>button.addEventListener("click",()=>{
      state.selectedId=button.dataset.ecrSource;
      renderCards();
      renderDetail(state.sources.find(item=>item.id===state.selectedId));
    }));
  }
  function renderDetail(item) {
    const title=byId("ecrDetailTitle"), subtitle=byId("ecrDetailSubtitle"), badge=byId("ecrDetailStatus"), body=byId("ecrDetailBody");
    if(!item) {
      title.textContent="Select an evidence source";
      subtitle.textContent="Source path, fingerprint, run metadata and interpretation boundary.";
      badge.textContent="NO SELECTION"; badge.className="tag";
      body.innerHTML='<div class="empty-state"><b>No source selected</b><p>Choose a source card to inspect its recorded provenance and follow it to the corresponding workspace panel.</p></div>';
      return;
    }
    title.textContent=item.title;
    subtitle.textContent=classLabel(item.evidence_class);
    badge.textContent=item.status; badge.className="tag "+statusClass(item.status);
    const entries=[
      ["Evidence ID",item.id],
      ["Class",classLabel(item.evidence_class)],
      ["Source path",item.source_path],
      ["SHA-256",item.sha256],
      ["Artifact size",Number.isFinite(Number(item.bytes))?formatBytes(Number(item.bytes)):"Not recorded"],
      ["Record / bin count",item.record_count],
      ...Object.entries(item.metadata||{})
    ];
    body.innerHTML='<p class="ecr-detail-summary">'+escapeHtml(item.summary)+'</p>'+
      '<div class="ecr-detail-block"><div class="ecr-detail-label">SOURCE AND RECORDED METADATA</div>'+
      '<dl class="ecr-detail-meta">'+entries.map(([key,value])=>'<dt>'+escapeHtml(key.replace(/_/g," "))+'</dt><dd>'+escapeHtml(pretty(value))+'</dd>').join("")+'</dl></div>'+
      (item.error?'<div class="ecr-detail-block"><div class="ecr-detail-label">SOURCE ERROR</div><div class="ecr-detail-value">'+escapeHtml(item.error)+'</div></div>':"")+
      (item.destination?'<a class="ecr-source-link" href="'+escapeHtml(item.destination)+'">Open related workspace panel ↗</a>':"");
  }
  function render() {
    renderMetrics();
    renderCards();
    renderDetail(state.sources.find(item=>item.id===state.selectedId));
  }
  async function loadIndex() {
    const status=byId("ecrStatus"), refresh=byId("ecrRefresh");
    if(!status||!refresh)return;
    refresh.disabled=true;
    status.textContent="READING LOCAL SOURCES…";
    status.className="tag";
    try {
      const response=await fetch("/api/evidence-index",{headers:{Accept:"application/json"},cache:"no-store"});
      const payload=await response.json();
      if(!response.ok)throw new Error(payload.error||("HTTP "+response.status));
      if(payload.mode!=="recorded-evidence-only"||!Array.isArray(payload.sources))throw new Error("Evidence index schema or mode is unexpected.");
      state.sources=payload.sources;
      if(!state.sources.some(item=>item.id===state.selectedId))state.selectedId=state.sources[0]?.id||null;
      status.textContent="INDEX LOADED · "+payload.source_count+" SOURCES";
      status.className="tag success";
      render();
    } catch(error) {
      status.textContent="INDEX UNAVAILABLE";
      status.className="tag warning";
      byId("ecrFilterCount").textContent="Registry request failed";
      byId("ecrSourceGrid").innerHTML='<div class="panel ecr-empty"><div class="empty-state"><b>Could not load the evidence index</b><p>'+escapeHtml(error.message||error)+'</p><p>Other workstation panels remain separate; this registry does not synthesize substitute records.</p></div></div>';
    } finally {
      refresh.disabled=false;
    }
  }
  function formatBytes(bytes) {
    if(bytes<1024)return bytes+" B";
    if(bytes<1048576)return (bytes/1024).toFixed(1)+" KB";
    return (bytes/1048576).toFixed(2)+" MB";
  }
  document.addEventListener("DOMContentLoaded",()=>{
    const filter=byId("ecrFilter"), search=byId("ecrSearch"), refresh=byId("ecrRefresh");
    if(filter)filter.addEventListener("change",()=>{state.filter=filter.value;renderCards();});
    if(search)search.addEventListener("input",()=>{state.query=search.value.trim().toLowerCase();renderCards();});
    if(refresh)refresh.addEventListener("click",loadIndex);
    loadIndex();
  });
})();