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
    "showCandidate, drawSelectedCandidate, drawCandidateChart, layoutCells," +
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
    assert.equal(JSON.stringify(charts.get("assemblyMap").traces[0].z), JSON.stringify([
      [Number(proxy.p00_fission_rate), Number(proxy.p01_fission_rate)],
      [Number(proxy.p10_fission_rate), Number(proxy.p11_fission_rate)]
    ]));
    assert.equal($("selectedRecordTag").textContent, String(row.canonical_reference).toLowerCase() === "true" ? "CANONICAL LAYOUT REFERENCE" : "LAYOUT VARIANT");
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
