(function () {
  "use strict";

  var currentScript = document.currentScript;
  var dataUrl = new URL("./computational_run_results.json", currentScript.src).href;
  var esc = function (value) {
    return String(value == null ? "" : value).replace(/[&<>"']/g, function (ch) {
      return ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[ch];
    });
  };
  var fmt = function (value, digits) { return Number(value).toFixed(digits == null ? 6 : digits); };
  var signed = function (value, digits) { return (Number(value) > 0 ? "+" : "") + Number(value).toFixed(digits == null ? 5 : digits); };
  var chartBase = {
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: { family: "Manrope, sans-serif", color: "#b7c8d6", size: 10 },
    margin: { l: 60, r: 16, t: 24, b: 56 },
    xaxis: { gridcolor: "#1b3445", linecolor: "#294455", tickfont: { size: 9 } },
    yaxis: { gridcolor: "#1b3445", linecolor: "#294455", tickfont: { size: 9 } },
    legend: { orientation: "h", y: -0.24, font: { size: 9 } }
  };
  var sectionMarkup = [
    '<section class="section cr-section" id="computational-results">',
    ' <div class="section-head"><div><div class="eyebrow">COMPUTATIONAL RUN RECORD / T8</div><h2>Computational Run Results</h2><p>Auditable summary of the paper-reported C5G7 transport campaign: recorded OpenMC runs, deterministic S_N comparison, and the selector decision replay. This panel reads archived values; it does not launch simulations.</p></div><span class="tag warning" id="crStatusTag">SOURCE SUMMARY</span></div>',
    ' <div class="notice cr-notice"><b>INTERPRETATION BOUNDARY</b><span>Statepoint integrity checks passed, but source/eigenvalue convergence is not certified. These aggregate values are transcribed from the paper draft, not raw statepoint payloads. No physical validation, reactor safety, or CB-PFR superiority is claimed.</span></div>',
    ' <div class="cr-summary-grid" id="crSummaryCards"></div>',
    ' <div class="grid two cr-chart-grid">',
    '  <article class="panel cr-panel"><div class="panel-head"><div><h3>Assembly-integrated fission proxy</h3><p>Mean from three seeds per layout; P4 is screening and P5 is held-out.</p></div><span class="tag">LOWER PROXY ≠ SAFETY</span></div><div id="crProxyChart" class="cr-chart"><div class="loading">Loading recorded series…</div></div><p class="panel-footnote">F_fission = maximum assembly-integrated fission rate divided by the mean over the four fuel assemblies. It is a shape proxy, not absolute thermal power or pin-power peaking.</p></article>',
    '  <article class="panel cr-panel"><div class="panel-head"><div><h3>k-effective by layout</h3><p>OpenMC screening mean versus held-out mean.</p></div><span class="tag">P4 / P5</span></div><div id="crKeffChart" class="cr-chart"><div class="loading">Loading recorded series…</div></div><p class="panel-footnote">Run-to-run dispersion and source-convergence bias limit interpretation. Values are means of the recorded three-seed phase, not exact eigenvalue truth.</p></article>',
    ' </div>',
    ' <article class="panel cr-panel"><div class="panel-head"><div><h3>Layout-level results and cross-code comparison</h3><p>All six enumerated two-MOX/two-UO₂ layouts; values transcribed from the paper tables.</p></div><span class="tag">6 LAYOUTS · 4 INFERRED CLASSES</span></div><div id="crLayoutTable" class="table-scroller"><div class="loading">Loading layout data…</div></div><p class="panel-footnote">S_N columns are deterministic outputs. The reported spatial RMS mismatch (7.53–7.91%) is too large to support a physical-validation claim. Symmetry grouping remains an inference pending confirmation against the repository position map.</p></article>',
    ' <article class="panel cr-panel"><div class="panel-head"><div><h3>Run phases and computational budget</h3><p>Run settings reported in Table 6 of the paper. b/i/p = batches / inactive batches / particles per batch.</p></div><span class="tag">46 OPENMC CASES</span></div><div id="crPhaseTable" class="table-scroller"><div class="loading">Loading run-phase register…</div></div><p class="panel-footnote">The 4.0905 × 10⁹ total refers to configured active neutron histories summed across run plans, not independent layout observations.</p></article>',
    ' <div class="grid two cr-findings-grid"><article class="panel cr-panel"><div class="panel-head"><div><h3>What the recorded runs show</h3><p>Results and decision implications within this campaign only.</p></div></div><div id="crFindings" class="cr-findings"></div></article>',
    '  <article class="panel cr-panel"><div class="panel-head"><div><h3>Evidence boundaries</h3><p>Conditions a reviewer should retain when interpreting the charts.</p></div><span class="tag warning">NOT VALIDATED</span></div><ul id="crLimitations" class="cr-limitations"></ul><div class="cr-canonical" id="crCanonical"></div></article></div>',
    ' <article class="panel cr-panel cr-source-panel"><div class="panel-head"><div><h3>Source and provenance</h3><p>Machine-readable, versioned record of the aggregates shown above.</p></div><a class="action-button" id="crDownloadData" href="./computational_run_results.json" download>Download JSON</a></div><div id="crSourceMeta" class="cr-source-meta"></div><p class="panel-footnote">The attached PDF fingerprint identifies the source draft; it is not a fingerprint of OpenMC statepoints. Raw HDF5/statepoint archives remain the preferred evidence source when available. The existing “Experiments &amp; paper” section contains a separate archived 1,200-observation / 60-reference-run offline replay; do not merge the two campaigns.</p></article>',
    '</section>'
  ].join("");

  function mount() {
    if (!document.getElementById("computational-results")) {
      var before = document.getElementById("research-evidence");
      if (before) before.insertAdjacentHTML("beforebegin", sectionMarkup);
    }
    if (!document.querySelector('.sidebar .nav-item[data-target="computational-results"]')) {
      var navAnchor = document.querySelector('.sidebar .nav-item[data-target="research-evidence"]');
      if (navAnchor) navAnchor.insertAdjacentHTML("beforebegin", '<a class="nav-item" href="#computational-results" data-target="computational-results"><span>▤</span> Computational run results</a>');
    }
    fetch(dataUrl, { cache: "no-store" })
      .then(function (response) {
        if (!response.ok) throw new Error("Run-summary data request returned HTTP " + response.status);
        return response.json();
      })
      .then(render)
      .catch(function (error) {
        var status = document.getElementById("crStatusTag");
        if (status) { status.textContent = "DATA LOAD FAILED"; status.className = "tag warning"; }
        var host = document.getElementById("crSummaryCards");
        if (host) host.innerHTML = '<div class="cr-empty">Recorded computational results could not be loaded. Check the JSON asset path and serve the workstation over HTTP(S). (' + esc(error.message || error) + ')</div>';
      });
  }

  function plot(id, traces, layout) {
    var node = document.getElementById(id);
    if (!node) return;
    if (!window.Plotly) {
      node.innerHTML = '<div class="cr-empty">Plotly did not load. The full numeric table below remains available.</div>';
      return;
    }
    try {
      Promise.resolve(window.Plotly.react(node, traces, Object.assign({}, chartBase, layout || {}, { autosize: true }), {
        responsive: true, displaylogo: false, modeBarButtonsToRemove: ["lasso2d", "select2d"]
      })).catch(function (error) {
        node.innerHTML = '<div class="cr-empty">Chart render failed: ' + esc(error.message || error) + '</div>';
      });
    } catch (error) {
      node.innerHTML = '<div class="cr-empty">Chart render failed: ' + esc(error.message || error) + '</div>';
    }
  }

  function render(data) {
    var c = data.campaign;
    var cards = [
      ["46", "OpenMC cases", "P1–P5 transport campaign"],
      ["4.0905 × 10⁹", "Configured active histories", "Not independent design observations"],
      ["7", "Deterministic S_N runs", "One canonical reference + six layouts"],
      ["6 → 4*", "Layout labels / inferred classes", "*Symmetry mapping needs confirmation"]
    ];
    document.getElementById("crSummaryCards").innerHTML = cards.map(function (card) {
      return '<div class="cr-metric"><span class="cr-metric-label">' + esc(card[1]) + '</span><strong>' + esc(card[0]) + '</strong><small>' + esc(card[2]) + '</small></div>';
    }).join("");
    var status = document.getElementById("crStatusTag");
    if (status) { status.textContent = "PAPER-TRANSCRIBED · CONVERGENCE OPEN"; status.className = "tag warning"; }

    var layouts = data.layouts;
    plot("crProxyChart", [
      {type:"bar", name:"P4 · screening", x:layouts.map(function(x){return x.layout;}), y:layouts.map(function(x){return x.fP4;}), marker:{color:"#d8a75b"}, hovertemplate:"%{x}<br>P4 mean F_fission: %{y:.6f}<extra></extra>"},
      {type:"bar", name:"P5 · held-out", x:layouts.map(function(x){return x.layout;}), y:layouts.map(function(x){return x.fP5;}), marker:{color:"#56dbe4"}, hovertemplate:"%{x}<br>P5 mean F_fission: %{y:.6f}<extra></extra>"}
    ], {barmode:"group", yaxis:{title:"F_fission proxy", range:[1.2,1.95]}, xaxis:{title:"Layout", tickfont:{size:9}}, legend:{orientation:"h",y:-0.24}, margin:{l:62,r:14,t:22,b:62}});
    plot("crKeffChart", [
      {type:"scatter", mode:"lines+markers", name:"P4 · screening", x:layouts.map(function(x){return x.layout;}), y:layouts.map(function(x){return x.keffP4;}), marker:{size:8,color:"#d8a75b"}, line:{color:"#d8a75b",width:1.5}, hovertemplate:"%{x}<br>P4 mean k_eff: %{y:.6f}<extra></extra>"},
      {type:"scatter", mode:"lines+markers", name:"P5 · held-out", x:layouts.map(function(x){return x.layout;}), y:layouts.map(function(x){return x.keffP5;}), marker:{size:8,color:"#56dbe4"}, line:{color:"#56dbe4",width:1.5}, hovertemplate:"%{x}<br>P5 mean k_eff: %{y:.6f}<extra></extra>"}
    ], {yaxis:{title:"Mean k_eff", range:[1.13,1.22]}, xaxis:{title:"Layout", tickfont:{size:9}}, legend:{orientation:"h",y:-0.24}, margin:{l:62,r:14,t:22,b:62}});

    document.getElementById("crLayoutTable").innerHTML =
      '<table><thead><tr><th>Layout</th><th>Inferred class</th><th>k_eff P4</th><th>k_eff P5</th><th>F P4</th><th>F P5</th><th>ΔF P4−P5</th><th>k_eff S_N</th><th>Δk S_N−OMC (pcm)</th><th>S_N max pin</th><th>Spatial RMS</th><th>Max Δ</th></tr></thead><tbody>' +
      layouts.map(function(x) {
        return '<tr><td><b>' + esc(x.layout) + '</b>' + (x.layout === data.campaign.heldOutLowestProxyLayout ? '<br><span class="cr-lowest">LOWEST P5 PROXY</span>' : '') + '</td><td>' + esc(x.symmetryLabel) + '</td><td class="numeric">' + fmt(x.keffP4,6) + '</td><td class="numeric">' + fmt(x.keffP5,6) + '</td><td class="numeric">' + fmt(x.fP4,6) + '</td><td class="numeric">' + fmt(x.fP5,6) + '</td><td class="numeric">' + signed(x.deltaF,5) + '</td><td class="numeric">' + fmt(x.keffSN,6) + '</td><td class="numeric">' + signed(x.deltaKpcm,1) + '</td><td class="numeric">' + fmt(x.snPinMax,6) + '</td><td class="numeric">' + fmt(x.spatialRmsPct,2) + '%</td><td class="numeric">' + fmt(x.maxRelativePct,2) + '%</td></tr>';
      }).join("") +
      '</tbody></table><p class="caption">F = assembly-integrated fission-rate proxy. “Inferred class” follows the paper’s symmetry interpretation; it is not independently certified by this display.</p>';

    document.getElementById("crPhaseTable").innerHTML =
      '<table><thead><tr><th>Phase</th><th>Cases</th><th>b / i / p</th><th>Active histories / case</th><th>Total active histories</th><th>Role</th></tr></thead><tbody>' +
      data.phases.map(function(x) {
        return '<tr><td><b>' + esc(x.phase) + '</b></td><td class="numeric">' + x.cases + '</td><td class="numeric">' + esc(x.settings) + '</td><td class="numeric">' + esc(x.activePerCase) + '</td><td class="numeric">' + esc(x.totalActive) + '</td><td>' + esc(x.role) + '</td></tr>';
      }).join("") +
      '</tbody><tfoot><tr><th>TOTAL</th><th>46</th><th>—</th><th>—</th><th>4,090,500,000</th><th>Reported configured active histories</th></tr></tfoot></table>';

    document.getElementById("crFindings").innerHTML = data.findings.map(function(x, i) {
      return '<div class="cr-finding"><div class="cr-finding-top"><span class="cr-finding-index">0' + (i + 1) + '</span><span class="cr-finding-status">' + esc(x.status) + '</span></div><h4>' + esc(x.title) + '</h4><p>' + esc(x.body) + '</p></div>';
    }).join("");
    document.getElementById("crLimitations").innerHTML = data.limitations.map(function(x) {
      return '<li>' + esc(x) + '</li>';
    }).join("");
    var ref = data.canonicalReference;
    document.getElementById("crCanonical").innerHTML =
      '<div class="cr-subhead">CANONICAL C5G7 CHECK</div><div class="cr-canonical-values"><strong>' + fmt(ref.openmcKeff,6) + '</strong><span>OpenMC k_eff</span><strong>' + fmt(ref.referenceKeff,5) + '</strong><span>Reference</span><strong>' + signed(ref.deltaPcm,1) + ' pcm</strong><span>Difference · z = ' + fmt(ref.zScore,2) + '</span></div><p>' + esc(ref.verdict) + '</p>';

    var source = data.source;
    document.getElementById("crSourceMeta").innerHTML =
      '<div><span>Source document</span><strong>' + esc(source.document) + '</strong></div>' +
      '<div><span>Source tables / pages</span><strong>' + esc(source.locations) + '</strong></div>' +
      '<div><span>Data type</span><strong>' + esc(source.kind) + '</strong></div>' +
      '<div><span>Record updated</span><strong>' + esc(data.updated) + '</strong></div>' +
      '<div class="cr-hash"><span>Source PDF SHA-256</span><code>' + esc(source.sha256) + '</code></div>' +
      '<p class="cr-source-note">' + esc(source.limitation) + '</p>';
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", mount, {once:true});
  else mount();
})();