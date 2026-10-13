"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const appSource = fs.readFileSync(path.join(__dirname, "..", "web", "app.js"), "utf8");

function mockElement(id) {
  const classes = new Set();
  return {
    id, value: "", innerHTML: "", textContent: "", hidden: false, disabled: false,
    attributes: {}, listeners: {},
    classList: {
      add(name) { classes.add(name); },
      remove(name) { classes.delete(name); },
      contains(name) { return classes.has(name); },
      toggle(name, force) {
        if (force === undefined) {
          if (classes.has(name)) classes.delete(name); else classes.add(name);
          return classes.has(name);
        }
        if (force) classes.add(name); else classes.delete(name);
        return classes.has(name);
      }
    },
    addEventListener(type, callback) { (this.listeners[type] ||= []).push(callback); },
    setAttribute(name, value) { this.attributes[name] = String(value); }
  };
}

function makeHarness() {
  const elements = new Map();
  const charts = new Map();
  const document = {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, mockElement(id));
      return elements.get(id);
    },
    addEventListener() {},
    querySelectorAll() { return []; },
    querySelector() { return null; }
  };
  const Plotly = {
    react(element, traces, layout, config) {
      charts.set(element.id, { traces, layout, config });
      return Promise.resolve(element);
    }
  };
  const window = { Plotly, matchMedia: () => ({ matches: false }) };
  const context = vm.createContext({ document, window, Plotly, console });
  const testHooks =
    "globalThis.__testHooks = {" +
    "setRecords(rows) { records = rows; }," +
    "setAssemblyRecords(rows) { assemblyRecords = rows; }," +
    "setModelGeometryData(data) { modelGeometryData = data; }," +
    "renderModelGeometrySvg," +
    "showCandidate, drawSelectedCandidate, drawCandidateChart, drawOtherCharts, drawAssemblyField, layoutCells," +
    "candidateOption, validateCandidateRecords, escapeHtml," +
    "getRecords() { return records; }" +
    "};";
  vm.runInContext(appSource + "\n" + testHooks, context, { filename: "web/app.js" });
  const manifestPath = path.join(__dirname, "..", "evidence", "c5g7_openmc_geometry_manifest_2026-10-13.json");
  context.__testHooks.setModelGeometryData(JSON.parse(fs.readFileSync(manifestPath, "utf8")));
  return { hooks: context.__testHooks, charts, $: id => document.getElementById(id) };
}

function parseCsvLine(line) {
  const values = [];
  let value = "";
  let quoted = false;
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    if (char === '"') {
      if (quoted && line[i + 1] === '"') { value += '"'; i++; }
      else quoted = !quoted;
    } else if (char === "," && !quoted) {
      values.push(value);
      value = "";
    } else {
      value += char;
    }
  }
  values.push(value);
  return values;
}

function readCsv(relativePath) {
  const lines = fs.readFileSync(path.join(__dirname, "..", relativePath), "utf8").trimEnd().split(/\r?\n/);
  const headers = parseCsvLine(lines.shift());
  return lines.map(line => {
    const values = parseCsvLine(line);
    return Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]));
  });
}

// Use the same repository CSVs that feed the workstation APIs, not a separate mock dataset.
const layouts = readCsv("results/c5g7_layout_smoke_2026-10-10/candidate_summary.csv");
const proxyRows = readCsv("results/c5g7_assembly_fission_proxy_smoke_2026-10-11.csv");

test("all six candidate selections update placement, detail, comparison highlight, and matching proxy", () => {
  const { hooks, charts, $ } = makeHarness();
  hooks.setRecords(layouts);
  hooks.setAssemblyRecords(proxyRows);
  $("metricSelect").value = "keff_mean";

  for (const row of layouts) {
    $("candidateSelect").value = row.candidate_id;
    hooks.showCandidate();

    assert.equal($("selectedCandidateId").textContent, row.candidate_id);
    assert.match($("layoutCaption").textContent, new RegExp(row.layout_signature + "$"));
    assert.match($("selectedCandidateMetaLine").textContent, new RegExp("Layout " + row.layout_signature));
    assert.match($("selectedCandidateMetaLine").textContent, new RegExp("Candidate " + (layouts.indexOf(row) + 1) + " of 6"));
    assert.match($("selectedCandidateMetrics").innerHTML, new RegExp(Number(row.keff_mean).toFixed(6)));
    assert.match($("selectedCandidateMetrics").innerHTML, new RegExp(Number(row.keff_std_dev).toFixed(6)));
    assert.match($("selectedCandidateMetrics").innerHTML, /Aggregate fission score/);
    assert.match($("selectedCandidateMetrics").innerHTML, /Not absolute power/);
    assert.match($("selectedCandidateMetrics").innerHTML, /Aggregate flux score/);
    assert.match($("selectedCandidateRunInfo").innerHTML, new RegExp(String(row.seed)));
    assert.match($("selectedCandidateRunInfo").innerHTML, /1000/);

    const placement = $("layoutView").innerHTML;
    assert.match(placement, /fuel-signature-summary/, row.candidate_id + " should show the compact source-recorded fuel signature");
    assert.match(placement, /P00 → P01 → P10 → P11/, "signature ordering must be explicit and consistent with the geometry map");
    assert.doesNotMatch(placement, /assembly-grid|class="assembly /, "duplicate four-tile assembly cards should be removed");
    const placementLetters = [...placement.matchAll(/class="fuel-signature-letter fuel-signature-letter-(mox|uo2)">([UM])<\/span>/g)];
    assert.deepEqual(placementLetters.map(m => m[2]), row.layout_signature.split(""), row.candidate_id + " compact signature should follow row-major source order");
    assert.match(placement, /MOX positions/);
    assert.match(placement, /UO₂ positions/);

    const signatureMarkup = $("selectedCandidateSignature").innerHTML;
    const signatureLetters = [...signatureMarkup.matchAll(/class="fuel-signature-letter fuel-signature-letter-(mox|uo2)">([UM])<\/span>/g)];
    assert.deepEqual(signatureLetters.map(m => m[2]), row.layout_signature.split(""));
    assert.match(signatureMarkup, /2 MOX · 2 UO₂/);
    assert.doesNotMatch(signatureMarkup, /signature-cell|<small>p\d\d<\/small>/, "duplicate four-box signature strip should be removed");

    assert.match($("geometryPreview").innerHTML, new RegExp("layout " + row.layout_signature));
    const comparison = charts.get("candidateChart").traces[0];
    const selectedTraceIndex = comparison.customdata.findIndex(item => item[0] === row.candidate_id);
    assert.notEqual(selectedTraceIndex, -1);
    assert.equal(comparison.marker.color[selectedTraceIndex], "#55d4df", "selected candidate should be highlighted");
    assert.equal(comparison.marker.color.filter(color => color === "#55d4df").length, 1, "only selected candidate should be highlighted");

    const proxy = proxyRows.find(item => item.candidate_id === row.candidate_id && item.layout_signature === row.layout_signature);
    assert.equal(JSON.stringify(charts.get("assemblyMap").traces[0].z), JSON.stringify([
      [Number(proxy.p00_fission_rate), Number(proxy.p01_fission_rate)],
      [Number(proxy.p10_fission_rate), Number(proxy.p11_fission_rate)]
    ]));
    const matrix = charts.get("assemblyMatrix");
    assert.equal(matrix.traces[0].type, "heatmap", "all candidates and four positions should use a shared position matrix");
    assert.equal(matrix.traces[0].z.length, 6, "matrix should include all six exact candidate-proxy matches");
    assert.equal(matrix.traces[0].z[0].length, 4, "matrix should include P00, P01, P10, and P11");
    assert.equal(matrix.traces.length, 2, "one heatmap plus one selection outline; only the heatmap carries a color scale");
    assert.equal(matrix.traces[0].showscale, true);
    assert.deepEqual(JSON.parse(JSON.stringify(matrix.traces[0].x)), ["P00","P01","P10","P11"]);
    const rankOrder = layouts.slice().sort((a,b)=>Number(a.keff_mean)-Number(b.keff_mean)).map(item=>item.layout_signature);
    assert.deepEqual(JSON.parse(JSON.stringify(matrix.traces[0].y)), rankOrder, "matrix row order should follow recorded candidate k-effective order");
    const matrixRow = rankOrder.indexOf(row.layout_signature);
    assert.deepEqual(JSON.parse(JSON.stringify(matrix.traces[0].z[matrixRow])), [
      Number(proxy.p00_fission_rate), Number(proxy.p01_fission_rate),
      Number(proxy.p10_fission_rate), Number(proxy.p11_fission_rate)
    ], "matrix values must preserve the exact matching source proxy record");
    assert.deepEqual(JSON.parse(JSON.stringify(matrix.traces[1].y)), [row.layout_signature,row.layout_signature,row.layout_signature,row.layout_signature], "selected candidate must be outlined across all four position cells");

    const ranked = charts.get("distributionChart").traces[0];
    assert.equal(ranked.type, "scatter", "six observations should use a ranked dot plot, not a histogram");
    assert.equal(ranked.error_y.visible, true, "ranked k-effective plot must show reported SD");
    assert.equal(ranked.marker.color.filter(color=>color==="#55d4df").length,1, "selected candidate highlight must sync to the ranked plot");
    const aggregate = charts.get("aggregateChart");
    assert.equal(aggregate.traces.length, 1, "aggregate indicators must not be combined on one shared scale");
    assert.equal(aggregate.traces[0].type, "scatter", "aggregate relationship should be shown as a two-metric scatter");
    assert.match(aggregate.layout.xaxis.title, /aggregate flux score/i);
    assert.match(aggregate.layout.yaxis.title, /aggregate fission score/i);
    assert.equal(aggregate.traces[0].marker.color.filter(color=>color==="#55d4df").length,1, "selected candidate highlight must sync to the aggregate relationship");
    assert.equal($("selectedRecordTag").textContent, String(row.canonical_reference).toLowerCase() === "true" ? "CANONICAL LAYOUT REFERENCE" : "LAYOUT VARIANT");
  }
});


test("Stage 2 scientific plots use ranking, uncertainty, separate score axes, and a candidate-position matrix", () => {
  const { hooks, charts, $ } = makeHarness();
  hooks.setRecords(layouts);
  hooks.setAssemblyRecords(proxyRows);
  $("candidateSelect").value = layouts[0].candidate_id;
  $("metricSelect").value = "keff_mean";
  hooks.showCandidate();
  hooks.drawOtherCharts();

  const comparison = charts.get("candidateChart");
  assert.equal(comparison.traces[0].type, "scatter");
  assert.equal(comparison.traces[0].error_x.visible, true);
  assert.ok(comparison.layout.shapes.some(shape => shape.x0 === 1 && shape.x1 === 1), "candidate point-range plot should mark k_eff=1 as an interpretive reference");
  assert.match(comparison.layout.annotations.map(a=>a.text).join(" "), /reference/i);

  const ranked = charts.get("distributionChart");
  assert.equal(ranked.traces[0].type, "scatter");
  assert.deepEqual(JSON.parse(JSON.stringify(ranked.traces[0].x)), layouts.slice().sort((a,b)=>Number(a.keff_mean)-Number(b.keff_mean)).map(row=>row.layout_signature));
  assert.equal(ranked.traces[0].y.length, 6);
  assert.equal(ranked.traces[0].error_y.array.length, 6);
  assert.ok(ranked.layout.shapes.some(shape => shape.y0 === 1 && shape.y1 === 1), "ranked plot should show the k_eff=1 reference");

  const aggregate = charts.get("aggregateChart");
  assert.equal(aggregate.traces.length, 1);
  assert.equal(aggregate.traces[0].type, "scatter");
  assert.equal(aggregate.traces[0].x.length, 6);
  assert.equal(aggregate.traces[0].y.length, 6);
  assert.match(aggregate.layout.xaxis.title, /flux score/i);
  assert.match(aggregate.layout.yaxis.title, /fission score/i);
  assert.doesNotMatch(aggregate.layout.xaxis.title, /absolute power/i);
});

test("missing numeric fields remain unavailable, not fabricated as zero", () => {
  const { hooks, $ } = makeHarness();
  const incomplete = {
    candidate_id: "candidate-missing", layout_signature: "MMUU",
    keff_mean: null, keff_std_dev: "", keff_relative_sd_percent: "   ",
    aggregate_fission_score: undefined, seed: null, batches: "",
    inactive: 0, particles_per_batch: 1000
  };
  hooks.setRecords([incomplete]);
  hooks.setAssemblyRecords([]);
  $("candidateSelect").value = incomplete.candidate_id;
  hooks.showCandidate();
  const metrics = $("selectedCandidateMetrics").innerHTML;
  assert.equal((metrics.match(/Not recorded/g) || []).length, 4);
  assert.doesNotMatch(metrics, /0\.000000|0\.0000%|0\.00000/);
  assert.match($("selectedCandidateRunInfo").innerHTML, /Not recorded/);
  assert.match($("selectedCandidateRunInfo").innerHTML, /BATCHES<\/span><b>Not recorded<\/b>/);
  assert.match($("selectedCandidateRunInfo").innerHTML, /<b>0<\/b>/, "a real zero inactive-batch count should remain visible");
});

test("invalid candidate selection clears stale details and linked views", () => {
  const { hooks, $ } = makeHarness();
  hooks.setRecords(layouts);
  hooks.setAssemblyRecords(proxyRows);
  $("candidateSelect").value = layouts[0].candidate_id;
  hooks.showCandidate();
  assert.equal($("selectedCandidateId").textContent, layouts[0].candidate_id);

  $("candidateSelect").value = "not-a-recorded-candidate";
  hooks.showCandidate();

  assert.equal($("selectedCandidateId").textContent, "No candidate selected");
  assert.match($("layoutView").innerHTML, /No candidate selected/);
  assert.doesNotMatch($("selectedCandidateMetrics").innerHTML, /1\.138329/);
  assert.match($("geometryPreview").innerHTML, /No candidate selected/);
  assert.equal($("selectedRecordTag").textContent, "NO SELECTION");
});

test("invalid candidate data is rejected when selection IDs are empty or ambiguous", () => {
  const { hooks } = makeHarness();
  assert.throws(() => hooks.validateCandidateRecords([]), /no candidate records/i);
  assert.throws(() => hooks.validateCandidateRecords([{ candidate_id: " " }]), /no candidate_id/i);
  assert.throws(() => hooks.validateCandidateRecords([{ candidate_id: "same" }, { candidate_id: "same" }]), /duplicate candidate_id/i);
  assert.equal(hooks.validateCandidateRecords(layouts).length, 6);
});

test("candidate option markup escapes IDs and labels", () => {
  const { hooks } = makeHarness();
  const option = hooks.candidateOption({ candidate_id: 'x" onfocus="alert(1)', layout_signature: "MMUU" });
  assert.doesNotMatch(option, /value="x" onfocus=/);
  assert.match(option, /&quot; onfocus=&quot;alert\(1\)/);
});


test("invalid U/M compositions fail closed in both configuration and selected-candidate status", () => {
  const { hooks, $ } = makeHarness();
  const invalid = {
    candidate_id: "candidate-invalid-layout",
    layout_signature: "MMMM",
    canonical_reference: true,
    keff_mean: 1.1,
    keff_std_dev: 0.001,
    keff_relative_sd_percent: 0.1,
    aggregate_fission_score: 0.4,
    seed: 1,
    batches: 10,
    inactive: 1,
    particles_per_batch: 100
  };
  hooks.setRecords([invalid]);
  hooks.setAssemblyRecords([]);
  $("candidateSelect").value = invalid.candidate_id;
  hooks.showCandidate();

  assert.match($("layoutView").innerHTML, /Placement unavailable/);
  assert.equal($("selectedRecordTag").textContent, "INVALID LAYOUT");
  assert.match($("selectedCandidateSignature").innerHTML, /No validated layout signature/);
  assert.match($("geometryPreview").innerHTML, /Invalid fuel composition/);
  assert.doesNotMatch($("geometryPreview").innerHTML, /<svg class="model-geometry-svg"/);
});


test("model geometry draws all four exact source pin lattices and includes source provenance for each candidate", () => {
  const { hooks } = makeHarness();
  hooks.setRecords(layouts);
  for (const row of layouts) {
    const svg = hooks.renderModelGeometrySvg(row);
    const source = JSON.parse(fs.readFileSync(path.join(__dirname, "..", "evidence", "c5g7_openmc_geometry_manifest_2026-10-13.json"), "utf8")).candidates.find(c => c.candidate_id === row.candidate_id);
    assert.ok(source);
    assert.equal(source.source_matches_candidate_signature, true);
    assert.match(svg, new RegExp("layout " + row.layout_signature + " candidate " + row.candidate_id));
    assert.ok(svg.includes(source.geometry_xml_sha256.slice(0, 16)), "the exact candidate geometry hash should be shown");
    assert.equal((svg.match(/<title>/g) || []).length, 4 * 17 * 17, "all 1,156 pin-universe cells should be present in the material map");
    assert.match(svg, /MOX 4\.3%/);
    assert.match(svg, /MOX 7\.0%/);
    assert.match(svg, /MOX 8\.7%/);
    assert.match(svg, /Fission Chamber/);
    assert.match(svg, /Guide Tube/);
    assert.match(svg, /REFLECTIVE/);
    assert.match(svg, /VACUUM/);
  }
});

test("rendering changes when a source pin-universe grid changes; the pattern is not hardcoded in JavaScript", () => {
  const { hooks } = makeHarness();
  hooks.setRecords(layouts);
  const candidate = layouts.find(row => row.layout_signature === "MUMU");
  const original = hooks.renderModelGeometrySvg(candidate);
  assert.match(original, /MOX 4\.3% · universe 2/);
  const manifestPath = path.join(__dirname, "..", "evidence", "c5g7_openmc_geometry_manifest_2026-10-13.json");
  const changed = JSON.parse(fs.readFileSync(manifestPath, "utf8"));
  changed.pin_lattices["103"].universe_grid[0][0] = 4;
  hooks.setModelGeometryData(changed);
  const rendered = hooks.renderModelGeometrySvg(candidate);
  assert.match(rendered, /MOX 8\.7% · universe 4/);
  assert.doesNotMatch(rendered.slice(0, rendered.indexOf("</svg>")), /const pinLattices/);
});
