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
    await page.locator("#coreView2d").click();
    await page.waitForSelector("#geometryPreview svg.model-geometry-svg", { timeout: 30000 });
    await page.waitForSelector("#candidateChart svg", { timeout: 30000 });
    // Stage 0/1 regression gate: preserve the interactive source registry alongside the 3D views.
    await page.waitForFunction(() =>
      /INDEX LOADED/.test(document.querySelector("#ecrStatus")?.textContent || ""),
      { timeout: 30000 }
    );
    const ecrState = await page.evaluate(() => ({
      cardCount: document.querySelectorAll("#ecrSourceGrid [data-ecr-source]").length,
      status: document.querySelector("#ecrStatus")?.textContent || "",
      detailTitle: document.querySelector("#ecrDetailTitle")?.textContent || "",
      core3dHost: Boolean(document.querySelector("#core3dCanvas")),
      axialVolumeHost: Boolean(document.querySelector("#axial3dPlot")),
      registryHasResearch: Boolean(document.querySelector("#research-evidence")),
      sourceStatusText: document.querySelector("#ecrSourceGrid")?.innerText || ""
    }));
    assert.ok(ecrState.cardCount >= 6, "control room should catalogue the separate geometry, transport, campaign and paper sources: " + JSON.stringify(ecrState));
    assert.ok(ecrState.detailTitle.trim().length > 0, "a source should be selected for provenance inspection");
    assert.ok(ecrState.core3dHost && ecrState.axialVolumeHost, "original geometry and axial visualizer mounts must remain present");
    assert.ok(ecrState.registryHasResearch, "the revised experiment/paper section must remain in the page");
    assert.match(ecrState.sourceStatusText, /source|openmc|campaign|synthetic|proxy/i, "evidence classes should be distinguishable");

    // Search/filter interactions should only change the index view, not the source data.
    await page.selectOption("#ecrFilter", "synthetic");
    await page.waitForFunction(() => {
      const cards = [...document.querySelectorAll("#ecrSourceGrid [data-ecr-source]")];
      return cards.length > 0 && cards.every(card => /synthetic/i.test(card.innerText));
    }, { timeout: 10000 });
    await page.selectOption("#ecrFilter", "all");
    await page.fill("#ecrSearch", "axial-volume");
    await page.waitForFunction(() => {
      const cards = [...document.querySelectorAll("#ecrSourceGrid [data-ecr-source]")];
      return cards.length === 1 && cards[0].dataset.ecrSource === "axial-volume";
    }, { timeout: 10000 });
    await page.locator('#ecrSourceGrid [data-ecr-source="axial-volume"]').click();
    await page.waitForFunction(() => /axial/i.test(document.querySelector("#ecrDetailTitle")?.textContent || ""));
    const axialDetailText = await page.locator("#ecrDetailBody").innerText();
    assert.match(axialDetailText, /dimension xyz|dimension|seed/i, "axial source inspector must include recorded dimensions or run metadata");
    await page.fill("#ecrSearch", "");
    await page.selectOption("#ecrFilter", "all");

    // A green browser smoke run requires the actual four spatial Plotly canvases, not just empty panels.
    for (const selector of [
      "#meshHeatmap.js-plotly-plot",
      "#meshContour.js-plotly-plot",
      "#meshProfile.js-plotly-plot",
      "#meshSurface.js-plotly-plot"
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
    // Exercise the original Three.js mode explicitly. WebGL is recorded as either
    // ready or a declared fallback; a hidden 2D SVG is not mistaken for a 3D render.
    await page.locator("#coreView3d").click();
    await page.waitForFunction(() => /WEBGL READY|WEBGL UNAVAILABLE|CDN UNAVAILABLE|2D SOURCE FALLBACK/.test(
      document.querySelector("#core3dStatus")?.textContent || ""
    ), { timeout: 30000 });

    const desktopOverflow = await page.evaluate(() => ({
      viewport: window.innerWidth,
      document: document.documentElement.scrollWidth,
      body: document.body.scrollWidth
    }));
    assert.ok(desktopOverflow.document <= desktopOverflow.viewport + 1,
      "desktop page must not create horizontal overflow: " + JSON.stringify(desktopOverflow));

    await page.screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-desktop-full.png"), fullPage: true, animations: "disabled" });
    await page.locator("#candidates").screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-desktop-candidate-inspector.png"), animations: "disabled" });
    await page.locator("#evidence-control-room").screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-desktop-evidence-control-room.png"), animations: "disabled" });
    await page.locator("#core3dViewport").screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-desktop-core-3d-viewer.png"), animations: "disabled" });
    await page.locator("#spatial").screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-desktop-spatial-field-lab.png"), animations: "disabled" });
    const geometrySection = page.locator("#geometryPreview").locator("xpath=ancestor::section[1]");
    await geometrySection.screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-desktop-model-geometry.png"), animations: "disabled" });

    // Use a fresh mobile page so Plotly dimensions are measured at the actual mobile viewport,
    // not during a desktop-to-mobile resize after desktop charts have already initialized.
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
    await mobilePage.locator("#coreView2d").click();
    await mobilePage.waitForSelector("#geometryPreview svg.model-geometry-svg", { timeout: 30000 });
    for (const selector of [
      "#meshHeatmap.js-plotly-plot",
      "#meshContour.js-plotly-plot",
      "#meshProfile.js-plotly-plot",
      "#meshSurface.js-plotly-plot"
    ]) {
      await mobilePage.waitForSelector(selector, { timeout: 30000 });
    }

    const mobileOverflow = await mobilePage.evaluate(() => {
      const overflowing = [...document.querySelectorAll("body *")].map(el => {
        const rect = el.getBoundingClientRect();
        return {
          tag: el.tagName.toLowerCase(),
          id: el.id || "",
          className: typeof el.className === "string" ? el.className.slice(0, 100) : "",
          right: Math.round(rect.right * 100) / 100,
          width: Math.round(rect.width * 100) / 100
        };
      }).filter(el => el.right > window.innerWidth + 0.1).sort((a, b) => b.right - a.right).slice(0, 16);
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
    await mobilePage.locator("#candidates").screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-mobile-candidate-inspector.png"), animations: "disabled" });
    await mobilePage.locator("#evidence-control-room").screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-mobile-evidence-control-room.png"), animations: "disabled" });
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
