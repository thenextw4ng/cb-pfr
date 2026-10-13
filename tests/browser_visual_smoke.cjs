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
    // A green browser smoke run requires the actual four spatial Plotly canvases, not just empty panels.
    for (const selector of [
      "#meshHeatmap .js-plotly-plot",
      "#meshContour .js-plotly-plot",
      "#meshProfile .js-plotly-plot",
      "#meshSurface .js-plotly-plot"
    ]) {
      await page.waitForSelector(selector, { timeout: 30000 });
    }
    await page.waitForFunction(() =>
      !/SPATIAL DATA UNAVAILABLE/.test(document.querySelector("#meshStatus")?.textContent || ""),
      { timeout: 10000 }
    );

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
        chartSvgCount: document.querySelectorAll("#candidateChart svg").length
      }));
      assert.equal(details.selectedId, option.value, "selected candidate identity must update");
      assert.ok(details.signature.trim().length > 0, "candidate signature should be visible");
      assert.ok(!/Chart render failed|Candidate evidence unavailable/i.test(details.metricText), "candidate details should not show an error");
      assert.equal(details.svgCount, 1, "one candidate-linked source geometry SVG should render");
      assert.equal(details.pinCellCount, 4 * 17 * 17, "pin material maps must include all four 17x17 fuel-assembly lattices");
      assert.ok(details.chartSvgCount >= 1, "candidate comparison chart should render in the browser");
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

    await page.screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-desktop-full.png"), fullPage: true, animations: "disabled" });
    await page.locator("#candidates").screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-desktop-candidate-inspector.png"), animations: "disabled" });
    await page.locator("#spatial").screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-desktop-spatial-field-lab.png"), animations: "disabled" });
    const geometrySection = page.locator("#geometryPreview").locator("xpath=ancestor::section[1]");
    await geometrySection.screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-desktop-model-geometry.png"), animations: "disabled" });

    // Repeat viewport and rendering checks at a common narrow-phone width.
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForTimeout(300);
    const mobileOverflow = await page.evaluate(() => {
      const overflowing = [...document.querySelectorAll("body *")].map(el => {
        const rect = el.getBoundingClientRect();
        return {
          tag: el.tagName.toLowerCase(),
          id: el.id || "",
          className: typeof el.className === "string" ? el.className.slice(0, 100) : "",
          right: Math.round(rect.right * 100) / 100,
          width: Math.round(rect.width * 100) / 100
        };
      }).filter(el => el.right > window.innerWidth + 0.1).sort((a, b) => b.right - a.right).slice(0, 12);
      return {
        viewport: window.innerWidth,
        document: document.documentElement.scrollWidth,
        body: document.body.scrollWidth,
        overflowingElements: overflowing
      };
    });
    assert.ok(mobileOverflow.document <= mobileOverflow.viewport + 1,
      "mobile page must not create more than 1px horizontal overflow: " + JSON.stringify(mobileOverflow));
    assert.ok(await page.locator("#candidateSelect").isVisible(), "candidate selector must remain visible on mobile");
    assert.ok(await page.locator("#selectedCandidateMetrics").isVisible(), "selected candidate metrics must remain visible on mobile");
    assert.ok(await page.locator("#geometryPreview svg.model-geometry-svg").isVisible(), "source geometry must remain visible on mobile");

    // Take the top viewport at scroll origin. The mobile navigation is sticky during normal use.
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-mobile-top.png"), fullPage: false, animations: "disabled" });

    // Sticky navigation can be painted over tall element screenshots by Chromium. Disable only
    // its sticky positioning for content cut-outs; the real mobile viewport screenshot above keeps it.
    await page.addStyleTag({ content: "@media(max-width:680px){.sidebar{position:static!important;top:auto!important}}" });
    await page.locator("#candidates").screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-mobile-candidate-inspector.png"), animations: "disabled" });
    await geometrySection.screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-mobile-model-geometry.png"), animations: "disabled" });

    assert.deepEqual(failures, [], "page must not throw uncaught JavaScript errors");
    const report = {
      baseUrl: BASE_URL,
      result: "passed",
      candidateCount: candidateOptions.length,
      candidateIds: candidateOptions.map(option => option.value),
      sourceGeometryPinCellCount: 4 * 17 * 17,
      spatialPlotCount: await page.locator("#meshHeatmap .js-plotly-plot, #meshContour .js-plotly-plot, #meshProfile .js-plotly-plot, #meshSurface .js-plotly-plot").count(),
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
