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
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 }, deviceScaleFactor: 1 });
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

    const report = {
      result:"passed",
      axialDimensions:sourceState.volume.dims,
      crossSectionTrace:sourceState.sliceTraceType,
      lineProfileTrace:sourceState.profileTraceType,
      crossSectionPlanes:["XY","XZ","YZ"],
      selectableProfileAxes:["X","Y","Z"],
      voxelInspectorPopulated:Boolean((await page.locator("#axialVoxelReadout").innerText()).includes("Monte Carlo standard error")),
      comparisonCharts:["v2a F_fission / k-effective","policy match rate","paired regret","T7 endpoint","T7b interval"],
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
