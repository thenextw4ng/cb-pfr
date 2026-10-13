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
    "showCandidate, drawSelectedCandidate, drawCandidateChart, layoutCells," +
    "candidateOption, validateCandidateRecords, escapeHtml," +
    "getRecords() { return records; }" +
    "};";
  vm.runInContext(appSource + "\n" + testHooks, context, { filename: "web/app.js" });
  return { hooks: context.__testHooks, charts, $: id => document.getElementById(id) };
}

const layouts = [
  { candidate_id: "c5g7-2x2-MUMU", layout_signature: "MUMU", canonical_reference: false, seed: 620002, batches: 100, inactive: 10, particles_per_batch: 1000, keff_mean: 1.1383293452701768, keff_std_dev: 0.002785370997409737, keff_relative_sd_percent: 0.24468937825270973, aggregate_fission_score: 0.4272971392392261, aggregate_flux_score: 39.74046019706651, descriptive_keff_order: 1, mutated_preexisting_file_count: 0, mgxs_sha256_before_transport: "mgxs-same", mgxs_sha256_after_transport: "mgxs-same" },
  { candidate_id: "c5g7-2x2-MMUU", layout_signature: "MMUU", canonical_reference: false, seed: 620001, batches: 100, inactive: 10, particles_per_batch: 1000, keff_mean: 1.1481094323862011, keff_std_dev: 0.002527861986856661, keff_relative_sd_percent: 0.2201760490376616, aggregate_fission_score: 0.4278613423319014, aggregate_flux_score: 39.64155656835747, descriptive_keff_order: 2, mutated_preexisting_file_count: 0, mgxs_sha256_before_transport: "mgxs-same", mgxs_sha256_after_transport: "mgxs-same" },
  { candidate_id: "c5g7-2x2-MUUM", layout_signature: "MUUM", canonical_reference: false, seed: 620003, batches: 100, inactive: 10, particles_per_batch: 1000, keff_mean: 1.156308238717424, keff_std_dev: 0.002844248382436213, keff_relative_sd_percent: 0.24597665978675815, aggregate_fission_score: 0.4359871686226767, aggregate_flux_score: 39.83640478888248, descriptive_keff_order: 3, mutated_preexisting_file_count: 0, mgxs_sha256_before_transport: "mgxs-same", mgxs_sha256_after_transport: "mgxs-same" },
  { candidate_id: "c5g7-2x2-UMMU", layout_signature: "UMMU", canonical_reference: true, seed: 620000, batches: 100, inactive: 10, particles_per_batch: 1000, keff_mean: 1.1881792736872105, keff_std_dev: 0.003047919927246576, keff_relative_sd_percent: 0.2565202065668202, aggregate_fission_score: 0.450971318012, aggregate_flux_score: 39.838022201673304, descriptive_keff_order: 4, mutated_preexisting_file_count: 0, mgxs_sha256_before_transport: "mgxs-same", mgxs_sha256_after_transport: "mgxs-same" },
  { candidate_id: "c5g7-2x2-UUMM", layout_signature: "UUMM", canonical_reference: false, seed: 620005, batches: 100, inactive: 10, particles_per_batch: 1000, keff_mean: 1.2031326318901272, keff_std_dev: 0.0029574594585127694, keff_relative_sd_percent: 0.2458132528469938, aggregate_fission_score: 0.4650592683667839, aggregate_flux_score: 40.385021708641816, descriptive_keff_order: 5, mutated_preexisting_file_count: 0, mgxs_sha256_before_transport: "mgxs-same", mgxs_sha256_after_transport: "mgxs-same" },
  { candidate_id: "c5g7-2x2-UMUM", layout_signature: "UMUM", canonical_reference: false, seed: 620004, batches: 100, inactive: 10, particles_per_batch: 1000, keff_mean: 1.2039852128698463, keff_std_dev: 0.002731549856853567, keff_relative_sd_percent: 0.2268756981111573, aggregate_fission_score: 0.46598629907395817, aggregate_flux_score: 40.61916770603346, descriptive_keff_order: 6, mutated_preexisting_file_count: 0, mgxs_sha256_before_transport: "mgxs-same", mgxs_sha256_after_transport: "mgxs-same" }
];

const proxyRows = layouts.map((row, i) => ({
  candidate_id: row.candidate_id, layout_signature: row.layout_signature,
  p00_fission_rate: 0.1 + i * 0.01, p01_fission_rate: 0.2 + i * 0.01,
  p10_fission_rate: 0.3 + i * 0.01, p11_fission_rate: 0.4 + i * 0.01
}));

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
    assert.match($("selectedCandidateMetrics").innerHTML, /Aggregate fission score · not power/);
    assert.match($("selectedCandidateRunInfo").innerHTML, new RegExp(String(row.seed)));
    assert.match($("selectedCandidateRunInfo").innerHTML, /1000/);

    const placement = $("layoutView").innerHTML;
    const placementCells = [...placement.matchAll(/<div class="assembly[^"]*">([^<]+)<small>(p\d\d) · \d<\/small><\/div>/g)];
    assert.equal(placementCells.length, 4, row.candidate_id + " should show four cells");
    assert.deepEqual(placementCells.map(m => [m[1], m[2]]), row.layout_signature.split("").map((fuel, i) => [fuel === "M" ? "MOX" : "UO₂", ["p00", "p01", "p10", "p11"][i]]));

    const signatureCells = [...$("selectedCandidateSignature").innerHTML.matchAll(/<b>([UM])<\/b><small>(p\d\d)<\/small>/g)];
    assert.equal(signatureCells.length, 4);
    assert.deepEqual(signatureCells.map(m => [m[1], m[2]]), row.layout_signature.split("").map((fuel, i) => [fuel, ["p00", "p01", "p10", "p11"][i]]));

    assert.match($("geometryPreview").innerHTML, new RegExp("layout " + row.layout_signature));
    const comparison = charts.get("candidateChart").traces[0];
    const selectedTraceIndex = comparison.customdata.findIndex(item => item[0] === row.candidate_id);
    assert.notEqual(selectedTraceIndex, -1);
    assert.equal(comparison.marker.color[selectedTraceIndex], "#55d4df", "selected candidate should be highlighted");
    assert.equal(comparison.marker.color.filter(color => color === "#55d4df").length, 1, "only selected candidate should be highlighted");

    const proxy = proxyRows.find(item => item.candidate_id === row.candidate_id && item.layout_signature === row.layout_signature);
    assert.deepEqual(charts.get("assemblyMap").traces[0].z, [
      [proxy.p00_fission_rate, proxy.p01_fission_rate],
      [proxy.p10_fission_rate, proxy.p11_fission_rate]
    ]);
    assert.equal($("selectedRecordTag").textContent, row.canonical_reference ? "CANONICAL LAYOUT REFERENCE" : "LAYOUT VARIANT");
  }
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
