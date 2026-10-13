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
  const page = await browser.newPage({
    viewport: { width: 1440, height: 1000 },
    deviceScaleFactor: 1
  });
  page.on("pageerror", error => failures.push("pageerror: " + error.message));

  try {
    const response = await page.goto(BASE_URL, { waitUntil: "domcontentloaded", timeout: 30000 });
    assert.ok(response && response.ok(), "workstation HTML should return HTTP 200");
    await page.waitForFunction(() => {
      const select = document.querySelector("#candidateSelect");
      return select && select.options.length === 6 && select.value;
    }, { timeout: 30000 });
    await page.waitForSelector("#selectedCandidateMetrics .candidate-stat", { timeout: 30000 });
    await page.waitForSelector("#geometryPreview svg.model-geometry-svg", { timeout: 30000 });
    await page.waitForSelector("#candidateChart svg", { timeout: 30000 });
    // All four real Plotly graphs and their source mesh matrix must be present.
    for (const selector of [
      "#meshHeatmap.js-plotly-plot",
      "#meshContour.js-plotly-plot",
      "#meshProfile.js-plotly-plot",
      "#meshSurface.js-plotly-plot"
    ]) {
      await page.waitForSelector(selector, { timeout: 30000 });
      await page.waitForSelector(selector + " svg.main-svg", { timeout: 30000 });
    }
    await page.waitForFunction(() =>
      !/SPATIAL DATA UNAVAILABLE/.test(document.querySelector("#meshStatus")?.textContent || ""),
      { timeout: 10000 }
    );
    const initialSpatialData = await page.evaluate(() => {
      const ids = ["meshHeatmap", "meshContour", "meshProfile", "meshSurface"];
      return Object.fromEntries(ids.map(id => {
        const el = document.getElementById(id);
        const trace = el?.data?.[0];
        return [id, {
          type: trace?.type,
          zRows: Array.isArray(trace?.z) ? trace.z.length : 0,
          zCols: Array.isArray(trace?.z?.[0]) ? trace.z[0].length : 0,
          xCount: Array.isArray(trace?.x) ? trace.x.length : 0,
          yCount: Array.isArray(trace?.y) ? trace.y.length : 0,
          colorscale: trace?.colorscale?.[0]?.[1] || null,
          hovertemplate: trace?.hovertemplate || "",
          contours: trace?.contours ? {
            showlabels: trace.contours.showlabels,
            start: trace.contours.start,
            end: trace.contours.end,
            size: trace.contours.size,
            labelformat: trace.contours.labelformat
          } : null,
          errorVisible: trace?.error_y?.visible === true,
          errorCount: Array.isArray(trace?.error_y?.array) ? trace.error_y.array.length : 0,
          yAxisType: el?.layout?.yaxis?.type || "linear",
          xAxisTitle: el?.layout?.xaxis?.title?.text || "",
          yAxisTitle: el?.layout?.yaxis?.title?.text || ""
        }];
      }));
    });
    assert.equal(initialSpatialData.meshHeatmap.type, "heatmap");
    assert.equal(initialSpatialData.meshContour.type, "contour");
    assert.equal(initialSpatialData.meshSurface.type, "surface");
    assert.equal(initialSpatialData.meshProfile.type, "scatter");
    for (const id of ["meshHeatmap", "meshContour", "meshSurface"]) {
      assert.equal(initialSpatialData[id].zRows, 51, id + " should use all 51 mesh rows");
      assert.equal(initialSpatialData[id].zCols, 51, id + " should use all 51 mesh columns");
    }
    assert.equal(initialSpatialData.meshProfile.xCount, 51, "central profile should include all x bins");
    assert.equal(initialSpatialData.meshProfile.yCount, 51, "central profile should include all x-bin values");
    assert.equal(initialSpatialData.meshContour.contours?.showlabels, true, "contour isolines should be numerically labeled");
    assert.ok(initialSpatialData.meshContour.contours?.size > 0, "contour levels must have an explicit interval");
    assert.ok(initialSpatialData.meshContour.contours?.end > initialSpatialData.meshContour.contours?.start, "contour interval must span the observed field");
    assert.match(initialSpatialData.meshProfile.xAxisTitle, /X position \(cm\)/, "verified regular-mesh bounds should put the profile on physical X coordinates");
    assert.match(initialSpatialData.meshProfile.yAxisTitle, /Recorded flux tally mean/);
    assert.equal(initialSpatialData.meshProfile.yAxisType, "log", "mean profile should use a true log axis instead of plotting log-transformed values");
    assert.equal(initialSpatialData.meshProfile.errorVisible, true, "central mean profile should show ±1 standard error");
    assert.equal(initialSpatialData.meshProfile.errorCount, 51, "central profile error bars must cover all bins");

    const candidateOptions = await page.locator("#candidateSelect option").evaluateAll(options =>
      options.map(option => ({ value: option.value, label: option.textContent.trim() }))
    );
    assert.equal(candidateOptions.length, 6, "all six recorded candidates must appear in the selector");
    assert.equal(new Set(candidateOptions.map(option => option.value)).size, 6, "candidate IDs must be unique");

    for (const option of candidateOptions) {
      await page.selectOption("#candidateSelect", option.value);
      await page.waitForFunction(expected => {
        const id = document.querySelector("#selectedCandidateId");
        const svg = document.querySelector("#geometryPreview svg.model-geometry-svg");
        return id && id.textContent.trim() === expected &&
          svg && svg.getAttribute("aria-label") && svg.getAttribute("aria-label").includes(expected);
      }, option.value, { timeout: 10000 });

      const details = await page.evaluate(() => ({
        selectedId: document.querySelector("#selectedCandidateId")?.textContent.trim(),
        signature: document.querySelector("#selectedCandidateSignature")?.textContent || "",
        metricText: document.querySelector("#selectedCandidateMetrics")?.innerText || "",
        pinCellCount: document.querySelectorAll("#geometryPreview svg.model-geometry-svg title").length,
        svgCount: document.querySelectorAll("#geometryPreview svg.model-geometry-svg").length,
        chartSvgCount: document.querySelectorAll("#candidateChart svg").length,
        comparisonType: document.querySelector("#candidateChart")?.data?.[0]?.type,
        comparisonErrorVisible: document.querySelector("#candidateChart")?.data?.[0]?.error_x?.visible === true,
        comparisonXTitle: document.querySelector("#candidateChart")?.layout?.xaxis?.title?.text || "",
        keffAndSdText: document.querySelector("#selectedCandidateMetrics")?.innerText || ""
      }));
      assert.equal(details.selectedId, option.value, "selected candidate identity must update");
      assert.ok(details.signature.trim().length > 0, "candidate signature should be visible");
      assert.ok(!/Chart render failed|Candidate evidence unavailable/i.test(details.metricText), "candidate details should not show an error");
      assert.equal(details.svgCount, 1, "one candidate-linked source geometry SVG should render");
      assert.equal(details.pinCellCount, 4 * 17 * 17, "pin material maps must include all four 17x17 fuel-assembly lattices");
      assert.ok(details.chartSvgCount >= 1, "candidate comparison chart should render in the browser");
      assert.equal(details.comparisonType, "scatter", "candidate comparison should use scientific point/interval marks, not baseline-zero bars");
      assert.equal(details.comparisonErrorVisible, true, "k-effective comparison must display reported SD intervals");
      assert.match(details.comparisonXTitle, /Reported k-effective mean/);
      assert.match(details.keffAndSdText, /Reported SD ±/);
    }

    // Return to the first exact recorded candidate for consistent screenshots.
    await page.selectOption("#candidateSelect", candidateOptions[0].value);
    await page.waitForFunction(expected =>
      document.querySelector("#selectedCandidateId")?.textContent.trim() === expected,
      candidateOptions[0].value
    );

    const desktopOverflow = await page.evaluate(() => ({
      viewport: window.innerWidth,
      document: document.documentElement.scrollWidth,
      body: document.body.scrollWidth
    }));
    assert.ok(desktopOverflow.document <= desktopOverflow.viewport + 1,
      "desktop page must not create horizontal overflow: " + JSON.stringify(desktopOverflow));

    // Validate control synchronization on desktop without resizing initialized Plotly SVGs.
    for (const score of ["fission", "nu-fission", "flux"]) {
      await page.selectOption("#meshScore", score);
      await page.waitForFunction(expected => {
        const el = document.querySelector("#meshHeatmap");
        return el?.data?.[0]?.hovertemplate?.includes(expected + " tally mean");
      }, score, { timeout: 15000 });
    }
    await page.selectOption("#meshView", "relative_sd");
    await page.waitForFunction(() =>
      document.querySelector("#meshHeatmap")?.data?.[0]?.hovertemplate?.toLowerCase().includes("relative monte carlo standard error"),
      { timeout: 15000 }
    );
    await page.selectOption("#meshScale", "linear");
    await page.selectOption("#meshPalette", "Cividis");
    await page.waitForFunction(() =>
      document.querySelector("#meshHeatmap")?.data?.[0]?.colorscale?.length > 2 &&
      document.querySelector("#meshContour")?.data?.[0]?.colorscale?.length > 2 &&
      document.querySelector("#meshSurface")?.data?.[0]?.colorscale?.length > 2,
      { timeout: 15000 }
    );
    await page.selectOption("#meshView", "mean");
    await page.selectOption("#meshScale", "log");
    await page.selectOption("#meshPalette", "Viridis");
    await page.waitForFunction(() =>
      document.querySelector("#meshHeatmap")?.data?.[0]?.z?.length === 51 &&
      document.querySelector("#meshSurface")?.data?.[0]?.z?.length === 51,
      { timeout: 15000 }
    );

    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-desktop-full.png"), fullPage: true, animations: "disabled" });
    await page.locator("#spatial").screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-desktop-spatial-field-lab.png"), animations: "disabled" });
    await page.locator("#candidates").screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-desktop-candidate-inspector.png"), animations: "disabled" });
    const geometrySection = page.locator("#geometryPreview").locator("xpath=ancestor::section[1]");
    await geometrySection.screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-desktop-model-geometry.png"), animations: "disabled" });

    // Use a fresh browser page so Plotly initializes at mobile width, not by shrinking desktop SVGs.
    const mobilePage = await browser.newPage({
      viewport: { width: 390, height: 844 },
      deviceScaleFactor: 1
    });
    const mobileFailures = [];
    mobilePage.on("pageerror", error => mobileFailures.push("pageerror: " + error.message));
    const mobileResponse = await mobilePage.goto(BASE_URL, { waitUntil: "domcontentloaded", timeout: 30000 });
    assert.ok(mobileResponse && mobileResponse.ok(), "mobile workstation HTML should return HTTP 200");
    await mobilePage.waitForFunction(() => {
      const select = document.querySelector("#candidateSelect");
      return select && select.options.length === 6 && select.value;
    }, { timeout: 30000 });
    await mobilePage.waitForSelector("#selectedCandidateMetrics .candidate-stat", { timeout: 30000 });
    await mobilePage.waitForSelector("#geometryPreview svg.model-geometry-svg", { timeout: 30000 });
    for (const selector of [
      "#meshHeatmap.js-plotly-plot",
      "#meshContour.js-plotly-plot",
      "#meshProfile.js-plotly-plot",
      "#meshSurface.js-plotly-plot"
    ]) {
      await mobilePage.waitForSelector(selector + " svg.main-svg", { timeout: 30000 });
    }
    const mobileOverflow = await mobilePage.evaluate(() => {
      const geometry = document.querySelector("#geometryPreview");
      const overflowing = [...document.querySelectorAll("body *")].filter(el => {
        const rect = el.getBoundingClientRect();
        return rect.right > window.innerWidth + 0.5 && !(geometry && geometry.contains(el));
      }).map(el => {
        const rect = el.getBoundingClientRect();
        return {
          tag: el.tagName.toLowerCase(), id: el.id || "",
          className: typeof el.className === "string" ? el.className.slice(0, 100) : "",
          right: Math.round(rect.right * 100) / 100, width: Math.round(rect.width * 100) / 100
        };
      }).sort((a, b) => b.right - a.right).slice(0, 16);
      return {
        viewport: window.innerWidth,
        document: document.documentElement.scrollWidth,
        body: document.body.scrollWidth,
        overflowingElements: overflowing
      };
    });
    assert.ok(mobileOverflow.document <= mobileOverflow.viewport + 1,
      "mobile page must not create more than 1px horizontal overflow: " + JSON.stringify(mobileOverflow));
    assert.ok(await mobilePage.locator("#candidateSelect").isVisible(), "candidate selector must remain visible on mobile");
    assert.ok(await mobilePage.locator("#selectedCandidateMetrics").isVisible(), "selected candidate metrics must remain visible on mobile");
    assert.ok(await mobilePage.locator("#geometryPreview svg.model-geometry-svg").isVisible(), "source geometry must remain visible on mobile");
    await mobilePage.evaluate(() => window.scrollTo(0, 0));
    await mobilePage.screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-mobile-top.png"), fullPage: false, animations: "disabled" });
    await mobilePage.addStyleTag({ content: "@media(max-width:680px){.sidebar{position:static!important;top:auto!important}}" });
    await mobilePage.locator("#spatial").screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-mobile-spatial-field-lab.png"), animations: "disabled" });
    await mobilePage.locator("#candidates").screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-mobile-candidate-inspector.png"), animations: "disabled" });
    const mobileGeometrySection = mobilePage.locator("#geometryPreview").locator("xpath=ancestor::section[1]");
    await mobileGeometrySection.screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-mobile-model-geometry.png"), animations: "disabled" });
    await mobilePage.close();

    assert.deepEqual(failures, [], "desktop page must not throw uncaught JavaScript errors");
    assert.deepEqual(mobileFailures, [], "mobile page must not throw uncaught JavaScript errors");
    const report = {
      baseUrl: BASE_URL,
      result: "passed",
      candidateCount: candidateOptions.length,
      candidateIds: candidateOptions.map(option => option.value),
      sourceGeometryPinCellCount: 4 * 17 * 17,
      spatialPlotCount: await page.locator("#meshHeatmap.js-plotly-plot, #meshContour.js-plotly-plot, #meshProfile.js-plotly-plot, #meshSurface.js-plotly-plot").count(),
      spatialDataStatus: await page.locator("#meshStatus").innerText(),
      desktopViewport: { width: 1440, height: 1000, ...desktopOverflow },
      mobileViewport: { width: 390, height: 844, ...mobileOverflow },
      uncaughtJavaScriptErrors: failures,
      screenshots: fs.readdirSync(OUTPUT_DIR).sort()
    };
    fs.writeFileSync(path.join(OUTPUT_DIR, "visual-qa-report.json"), JSON.stringify(report, null, 2) + "\n");
    process.stdout.write(JSON.stringify(report, null, 2) + "\n");
  } finally {
    await browser.close();
  }
}

main().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
