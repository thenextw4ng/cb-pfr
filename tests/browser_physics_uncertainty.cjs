"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const BASE_URL = process.env.CBPFR_BASE_URL || "http://127.0.0.1:8765";
const OUTPUT_DIR = path.join(process.cwd(), "artifacts", "visual-qa");
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

async function main() {
  const browser = await chromium.launch({ headless: true });
  const failures = [];
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1, acceptDownloads: true });
  page.on("pageerror", error => failures.push(error.message));

  try {
    const response = await page.goto(BASE_URL, { waitUntil: "domcontentloaded", timeout: 30000 });
    assert.ok(response && response.ok(), "HTML workstation must return HTTP 200");

    await page.waitForFunction(() => /ANALYSIS READY/.test(document.querySelector("#uncertaintyLabStatus")?.textContent || ""), { timeout: 30000 });
    for (const selector of [
      "#cmpV2aFChart.js-plotly-plot", "#cmpV2aKChart.js-plotly-plot",
      "#cmpPolicyMatchChart.js-plotly-plot", "#cmpPolicyRegretChart.js-plotly-plot",
      "#cmpT7Chart.js-plotly-plot", "#cmpT7bChart.js-plotly-plot"
    ]) await page.waitForSelector(selector, { timeout: 30000 });

    await page.selectOption("#cmpOpenMCMetric", "keff");
    await page.waitForFunction(() => /k-effective/.test(document.querySelector("#cmpV2aFTitle")?.textContent || ""));
    await page.selectOption("#cmpOpenMCMetric", "fission");
    await page.selectOption("#cmpT7Endpoint", "feasible");
    await page.waitForFunction(() => /Truly feasible selection/.test(document.querySelector("#cmpT7Chart .ytitle")?.textContent || ""));
    await page.selectOption("#cmpT7Endpoint", "primary");

    await page.locator("#axial3dPanel").scrollIntoViewIfNeeded();
    await page.waitForSelector("#axialSectionPlot.js-plotly-plot", { timeout: 60000 });
    await page.waitForSelector("#axialLineProfilePlot.js-plotly-plot", { timeout: 60000 });

    const sourceState = await page.evaluate(() => ({
      volume: window.CBPFRAxial3DData ? {
        available: window.CBPFRAxial3DData.available,
        score: window.CBPFRAxial3DData.score,
        dims: window.CBPFRAxial3DData.mesh?.dimension_xyz
      } : null,
      sliceTraceType: document.querySelector("#axialSectionPlot")?.data?.[0]?.type,
      profileTraceType: document.querySelector("#axialLineProfilePlot")?.data?.[0]?.type
    }));
    assert.ok(sourceState.volume && sourceState.volume.available === true, "orthogonal views must consume the recorded axial array");
    assert.deepEqual(sourceState.volume.dims, [51, 51, 30]);
    assert.equal(sourceState.sliceTraceType, "heatmap");
    assert.equal(sourceState.profileTraceType, "scatter");

    await page.selectOption("#axialPlaneSelect", "XZ");
    await page.waitForFunction(() => /XZ CUT/.test(document.querySelector("#axialSectionStatus")?.textContent || ""));
    assert.equal(await page.locator("#axialPlaneIndex").getAttribute("max"), "50");
    await page.locator("#axialPlaneIndex").evaluate(el => { el.value = "9"; el.dispatchEvent(new Event("input", { bubbles:true })); });

    await page.selectOption("#axialPlaneSelect", "YZ");
    await page.waitForFunction(() => /YZ CUT/.test(document.querySelector("#axialSectionStatus")?.textContent || ""));
    assert.equal(await page.locator("#axialPlaneIndex").getAttribute("max"), "50");

    await page.selectOption("#axialPlaneSelect", "XY");
    await page.waitForFunction(() => /XY CUT/.test(document.querySelector("#axialSectionStatus")?.textContent || ""));
    await page.selectOption("#axialProfileAxis", "Y");
    await page.waitForFunction(() => /Y PROFILE/.test(document.querySelector("#axialProfileStatus")?.textContent || ""));
    await page.selectOption("#axialProfileAxis", "Z");
    await page.waitForFunction(() => /Z PROFILE/.test(document.querySelector("#axialProfileStatus")?.textContent || ""));

    const inspectedVoxel = await page.locator("#axialSectionPlot").evaluate(el => {
      const record = el.data?.[0]?.customdata?.[0]?.[0];
      const inspected = Array.isArray(record) && record.length >= 9 &&
        typeof window.CBPFRShowAxialVoxel === "function" &&
        window.CBPFRShowAxialVoxel(record);
      return {
        inspected,
        text: document.querySelector("#axialVoxelReadout")?.textContent || "",
        recordedTuple: record
      };
    });
    assert.ok(inspectedVoxel.inspected, "voxel inspector must consume an actual source-bin tuple");
    assert.match(inspectedVoxel.text, /Monte Carlo standard error/, "voxel inspector should expose the recorded uncertainty label");
    assert.ok(Array.isArray(inspectedVoxel.recordedTuple) && inspectedVoxel.recordedTuple.length >= 9,
      "voxel readout must be driven by the source array's bin tuple");

    await page.locator("#axialSectionPlot").screenshot({ path:path.join(OUTPUT_DIR,"cb-pfr-desktop-axial-cross-section.png"), animations:"disabled" });
    await page.locator("#axialLineProfilePlot").screenshot({ path:path.join(OUTPUT_DIR,"cb-pfr-desktop-axial-line-profile.png"), animations:"disabled" });
    await page.locator("#uncertainty-lab").screenshot({ path:path.join(OUTPUT_DIR,"cb-pfr-desktop-uncertainty-analysis.png"), animations:"disabled" });

    // Stage 4: the figure studio renders equal-size previews and exports data/config/provenance.
    await page.locator("#figure-studio").scrollIntoViewIfNeeded();
    await page.waitForFunction(() => (document.querySelector("#figureStudioTarget")?.options.length || 0) >= 18, { timeout:15000 });
    await page.selectOption("#figureStudioTarget", "cmpV2aFChart");
    await page.fill("#figureStudioCaption", "QA figure caption: recorded C5G7 layout variability; convergence not certified.");
    await page.locator("#figureStudioRenderComparison").click();
    await page.waitForSelector("#figureComparePreviewA.js-plotly-plot", { timeout:30000 });
    await page.waitForSelector("#figureComparePreviewB.js-plotly-plot", { timeout:30000 });
    await page.waitForFunction(() => /Side-by-side comparison rendered/.test(document.querySelector("#figureStudioStatus")?.textContent || ""), { timeout:30000 });

    const [jsonDownload] = await Promise.all([
      page.waitForEvent("download", { timeout:60000 }),
      page.locator("#figureStudioExportJson").click()
    ]);
    const jsonPath = path.join(OUTPUT_DIR, "figure-studio-reproducibility.json");
    await jsonDownload.saveAs(jsonPath);
    const figureBundle = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
    assert.equal(figureBundle.schema_version, "cbpfr-figure-reproducibility-v1");
    assert.equal(figureBundle.figure.id, "cmpV2aFChart");
    assert.match(figureBundle.figure.caption, /QA figure caption/);
    assert.match(figureBundle.source.evidence_class, /OpenMC/i);
    assert.match(figureBundle.source.evidence_status, /NOT CERTIFIED|not certified/i);
    assert.equal(String(figureBundle.source.workflow_run_id), "38853860378");
    assert.ok(figureBundle.source.run_id.includes("aggregate"), "aggregate replay must not be mislabelled as one transport run");
    assert.match(figureBundle.integrity.data_sha256, /^[0-9a-f]{64}$/);
    assert.match(figureBundle.integrity.config_sha256, /^[0-9a-f]{64}$/);
    assert.ok(Array.isArray(figureBundle.visualization.trace_data) && figureBundle.visualization.trace_data.length > 0);
    assert.ok(figureBundle.visualization.layout && typeof figureBundle.visualization.layout === "object");

    const [csvDownload] = await Promise.all([
      page.waitForEvent("download", { timeout:60000 }),
      page.locator("#figureStudioExportCsv").click()
    ]);
    const csvPath = path.join(OUTPUT_DIR, "figure-studio-data.csv");
    await csvDownload.saveAs(csvPath);
    const csvText = fs.readFileSync(csvPath, "utf8");
    const csvHeader = csvText.split(/\r?\n/, 1)[0];
    for (const field of ["figure_id", "dataset_id", "source_id", "run_id", "workflow_run_id", "seed", "evidence_status", "exported_data_sha256", "visualization_config_sha256", "trace_index", "point_index"]) {
      assert.ok(csvHeader.includes(field), "CSV must retain provenance/data column " + field);
    }
    assert.ok(csvText.split(/\r?\n/).length > 5, "CSV export should contain chart point data, not only a header");
    assert.ok(csvText.includes("cmpV2aFChart"), "CSV data rows must include the figure ID, not just a column header");
    assert.ok(csvText.includes("Layout variability"), "CSV rows must retain the figure title metadata");

    const [pngDownload] = await Promise.all([
      page.waitForEvent("download", { timeout:90000 }),
      page.locator("#figureStudioExportPng").click()
    ]);
    const pngPath = path.join(OUTPUT_DIR, "figure-studio-publication.png");
    await pngDownload.saveAs(pngPath);
    const pngBytes = fs.readFileSync(pngPath);
    assert.equal(pngBytes.toString("hex", 0, 8), "89504e470d0a1a0a", "publication figure must be a PNG");
    assert.equal(pngBytes.readUInt32BE(16), 2400, "publication PNG width must be 2400 px");
    assert.equal(pngBytes.readUInt32BE(20), 1600, "publication PNG height must be 1600 px");

    await page.locator("#figure-studio").screenshot({ path:path.join(OUTPUT_DIR,"cb-pfr-desktop-figure-studio.png"), animations:"disabled" });

    const report = {
      result:"passed",
      axialDimensions:sourceState.volume.dims,
      crossSectionTrace:sourceState.sliceTraceType,
      lineProfileTrace:sourceState.profileTraceType,
      crossSectionPlanes:["XY","XZ","YZ"],
      selectableProfileAxes:["X","Y","Z"],
      voxelInspectorPopulated:Boolean((await page.locator("#axialVoxelReadout").innerText()).includes("Monte Carlo standard error")),
      comparisonCharts:["v2a F_fission / k-effective","policy match rate","paired regret","T7 endpoint","T7b interval"],
      figureStudio:{sideBySide:true,csvDownloaded:true,jsonDownloaded:true,pngDimensions:[2400,1600]},
      uncaughtJavaScriptErrors:failures
    };
    assert.deepEqual(failures, [], "no uncaught page errors");
    fs.writeFileSync(path.join(OUTPUT_DIR,"physics-analysis-qa-report.json"),JSON.stringify(report,null,2)+"\n");
    process.stdout.write(JSON.stringify(report,null,2)+"\n");
  } finally {
    await browser.close();
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
