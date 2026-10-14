"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const BASE_URL = process.env.CBPFR_BASE_URL || "http://127.0.0.1:8765";
const OUTPUT_DIR = path.join(process.cwd(), "artifacts", "visual-qa");
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

async function main() {
  const browser = await chromium.launch({ headless: true, args: ["--enable-webgl", "--ignore-gpu-blocklist", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
  const failures = [];
  const context = await browser.newContext({
    viewport: { width: 1440, height: 1000 },
    deviceScaleFactor: 1
  });
  const page = await context.newPage();
  page.on("pageerror", error => failures.push("pageerror: " + error.message));

  try {
    const response = await page.goto(BASE_URL, { waitUntil: "domcontentloaded", timeout: 30000 });
    assert.ok(response && response.ok(), "workstation HTML should return HTTP 200");
    await page.waitForFunction(() => {
      const select = document.querySelector("#candidateSelect");
      return select && select.options.length === 6 && select.value;
    }, { timeout: 30000 });
    await page.waitForSelector("#selectedCandidateMetrics .candidate-stat", { timeout: 30000 });
    await page.waitForSelector("#core3dCanvas canvas.core3d-canvas", { timeout: 30000 });
    await page.waitForSelector("#geometryPreview svg.model-geometry-svg", { state: "attached", timeout: 30000 });
    await page.waitForFunction(() => /WEBGL READY/.test(document.querySelector("#core3dStatus")?.textContent || ""), { timeout: 30000 });
    await page.waitForSelector("#candidateChart svg", { timeout: 30000 });
    for (const selector of [
      "#distributionChart.js-plotly-plot",
      "#aggregateChart.js-plotly-plot",
      "#assemblyMap.js-plotly-plot",
      "#assemblyMatrix.js-plotly-plot"
    ]) {
      await page.waitForSelector(selector, { timeout: 30000 });
      await page.waitForSelector(selector + " svg.main-svg", { timeout: 30000 });
    }
    // All four real OpenMC spatial plots plus the Stage 2 scientific candidate/proxy charts must render.
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
          yAxisTitle: el?.layout?.yaxis?.title?.text || "",
          surfaceContourTraces: id === "meshSurface" ? (el?.data || []).slice(1).map(lineTrace => {
            const finiteLineZ = (lineTrace.z || []).filter(value => typeof value === "number" && Number.isFinite(value));
            return {
              type: lineTrace.type,
              mode: lineTrace.mode,
              name: lineTrace.name,
              hoverinfo: lineTrace.hoverinfo,
              pointCount: (lineTrace.x || []).filter(value => value !== null && value !== undefined).length,
              zUniqueCount: new Set(finiteLineZ).size
            };
          }) : [],
          surfaceCustomSample: id === "meshSurface" ? trace?.customdata?.[25]?.[25] || null : null,
          surfaceZSample: id === "meshSurface" ? trace?.z?.[25]?.[25] ?? null : null,
          surfaceAspectRatioZ: id === "meshSurface" ? el?.layout?.scene?.aspectratio?.z ?? null : null,
          surfaceXAxisTitle: id === "meshSurface" ? el?.layout?.scene?.xaxis?.title?.text || "" : "",
          surfaceYAxisTitle: id === "meshSurface" ? el?.layout?.scene?.yaxis?.title?.text || "" : "",
          surfaceCameraEyeX: id === "meshSurface" ? el?.layout?.scene?.camera?.eye?.x ?? null : null
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
    const terrainLines = initialSpatialData.meshSurface.surfaceContourTraces;
    assert.equal(terrainLines.length, 2, "3D terrain should overlay source-derived surface isolines and projected base-plane isolines");
    const surfaceLines = terrainLines.find(line => line.name === "Surface isolines");
    const projectedLines = terrainLines.find(line => line.name === "Projected base-plane isolines");
    assert.equal(surfaceLines?.type, "scatter3d", "surface contours should render as 3D lines computed from the selected field");
    assert.equal(surfaceLines?.mode, "lines");
    assert.ok(surfaceLines?.pointCount > 0, "surface isolines should contain contour segments derived from the tally grid");
    assert.equal(surfaceLines?.hoverinfo, "skip", "decorative contour lines must not replace source tally hover values");
    assert.equal(projectedLines?.type, "scatter3d");
    assert.ok(projectedLines?.pointCount > 0, "isolines should project to the lower reference plane");
    assert.equal(projectedLines?.zUniqueCount, 1, "base-plane contour coordinates should share one projected Z level");
    assert.match(initialSpatialData.meshSurface.surfaceXAxisTitle, /X position \(cm\)/, "3D surface should use archived physical X coordinates");
    assert.match(initialSpatialData.meshSurface.surfaceYAxisTitle, /Y position \(cm\)/, "3D surface should use archived physical Y coordinates");
    assert.ok(Array.isArray(initialSpatialData.meshSurface.surfaceCustomSample) && initialSpatialData.meshSurface.surfaceCustomSample.length === 3, "surface hover must carry mean, Monte Carlo standard error, and relative error from source data");
    assert.match(initialSpatialData.meshSurface.hovertemplate, /Monte Carlo standard error/);
    assert.match(initialSpatialData.meshSurface.hovertemplate, /Relative Monte Carlo standard error/);
    assert.ok(initialSpatialData.meshSurface.surfaceAspectRatioZ > 0 && initialSpatialData.meshSurface.surfaceAspectRatioZ <= 0.95, "surface should use an explicit display aspect ratio");

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
        coreCanvasCount: document.querySelectorAll("#core3dCanvas canvas.core3d-canvas").length,
        core3dStatus: document.querySelector("#core3dStatus")?.textContent || "",
        coreInfo: window.CBPFRCore3DInfo || null,
        coreViewMode: document.querySelector("#core3dViewport")?.hidden === false ? "3d" : "2d",
        pinMapCellCount: document.querySelectorAll("#coreSelectedPinMap svg.core-pin-map-svg rect[fill]").length,
        chartSvgCount: document.querySelectorAll("#candidateChart svg").length,
        comparisonType: document.querySelector("#candidateChart")?.data?.[0]?.type,
        comparisonErrorVisible: document.querySelector("#candidateChart")?.data?.[0]?.error_x?.visible === true,
        comparisonXTitle: document.querySelector("#candidateChart")?.layout?.xaxis?.title?.text || "",
        comparisonHasReference: (document.querySelector("#candidateChart")?.layout?.shapes || []).some(shape => shape.x0 === 1 && shape.x1 === 1),
        rankedType: document.querySelector("#distributionChart")?.data?.[0]?.type,
        rankedMode: document.querySelector("#distributionChart")?.data?.[0]?.mode,
        rankedCount: document.querySelector("#distributionChart")?.data?.[0]?.y?.length || 0,
        rankedErrorVisible: document.querySelector("#distributionChart")?.data?.[0]?.error_y?.visible === true,
        rankedSelectedColorCount: (document.querySelector("#distributionChart")?.data?.[0]?.marker?.color || []).filter(color => color === "#ffffff").length,
        rankedOrder: document.querySelector("#distributionChart")?.data?.[0]?.x || [],
        aggregateTraceCount: document.querySelector("#aggregateChart")?.data?.length || 0,
        aggregateType: document.querySelector("#aggregateChart")?.data?.[0]?.type,
        aggregateXTitle: document.querySelector("#aggregateChart")?.layout?.xaxis?.title?.text || "",
        aggregateYTitle: document.querySelector("#aggregateChart")?.layout?.yaxis?.title?.text || "",
        aggregateSelectedColorCount: (document.querySelector("#aggregateChart")?.data?.[0]?.marker?.color || []).filter(color => color === "#ffffff").length,
        assemblyMapType: document.querySelector("#assemblyMap")?.data?.[0]?.type,
        assemblyMapTraceCount: document.querySelector("#assemblyMap")?.data?.length || 0,
        assemblyMapPositions: (document.querySelector("#assemblyMap")?.data?.[0]?.customdata || []).flat().map(cell => cell?.[0]),
        assemblyMapValues: (document.querySelector("#assemblyMap")?.data?.[0]?.z || []).flat(),
        assemblyMapText: (document.querySelector("#assemblyMap")?.data?.[0]?.text || []).flat(),
        assemblyMapAxisMapping: document.querySelector("#assemblyMap")?.layout?.annotations?.[0]?.text || "",
        assemblyMapPalette: document.querySelector("#assemblyMap")?.data?.[0]?.colorscale || "",
        assemblyMapScale: [document.querySelector("#assemblyMap")?.data?.[0]?.zmin, document.querySelector("#assemblyMap")?.data?.[0]?.zmax],
        assemblyMatrixScale: [document.querySelector("#assemblyMatrix")?.data?.[0]?.zmin, document.querySelector("#assemblyMatrix")?.data?.[0]?.zmax],
        assemblyMapColorbarTitle: document.querySelector("#assemblyMap")?.data?.[0]?.colorbar?.title?.text || "",
        assemblyMapMaterialEdgeColors: document.querySelector("#assemblyMap")?.data?.[1]?.marker?.color || [],
        assemblyMapSelectedPosition: document.querySelector("#assemblyMap")?.data?.[2]?.customdata?.[0] || "",
        assemblyPositionTitle: document.querySelector("#assemblyPositionTitle")?.textContent || "",
        assemblyPositionMaterial: document.querySelector("#assemblyPositionMaterial")?.textContent || "",
        assemblyPositionValue: document.querySelector("#assemblyPositionValue")?.textContent || "",
        assemblyScaleRange: document.querySelector("#assemblyScaleRange")?.textContent || "",
        assemblyProvenanceOpen: document.querySelector(".assembly-provenance")?.open ?? null,
        assemblyMapColorbarCount: (document.querySelector("#assemblyMap")?.data || []).filter(trace => trace.colorbar || trace.showscale === true).length +
          (document.querySelector("#assemblyMatrix")?.data || []).filter(trace => trace.colorbar || trace.showscale === true).length,
        matrixType: document.querySelector("#assemblyMatrix")?.data?.[0]?.type,
        matrixColorbarVisible: document.querySelector("#assemblyMatrix")?.data?.[0]?.showscale,
        matrixRows: document.querySelector("#assemblyMatrix")?.data?.[0]?.z?.length || 0,
        matrixColumns: document.querySelector("#assemblyMatrix")?.data?.[0]?.z?.[0]?.length || 0,
        matrixPositions: document.querySelector("#assemblyMatrix")?.data?.[0]?.x || [],
        matrixTraceCount: document.querySelector("#assemblyMatrix")?.data?.length || 0,
        matrixSelectedLayout: document.querySelector("#assemblyMatrix")?.data?.[1]?.y?.[0] || "",
        keffAndSdText: document.querySelector("#selectedCandidateMetrics")?.innerText || ""
      }));
      assert.equal(details.selectedId, option.value, "selected candidate identity must update");
      assert.ok(details.signature.trim().length > 0, "candidate signature should be visible");
      assert.ok(!/Chart render failed|Candidate evidence unavailable/i.test(details.metricText), "candidate details should not show an error");
      assert.equal(details.svgCount, 1, "one candidate-linked source geometry fallback SVG should remain available");
      assert.equal(details.pinCellCount, 4 * 17 * 17, "source 2D map should preserve all four 17x17 fuel-assembly lattices");
      assert.equal(details.coreCanvasCount, 1, "external Three.js WebGL canvas should be rendered");
      assert.match(details.core3dStatus, /WEBGL READY.*THREE\.JS R0\.180\.0.*1,156 PIN INSTANCES/);
      assert.equal(details.coreViewMode, "3d", "3D core should be the default view");
      assert.equal(details.coreInfo?.candidateId, option.value, "3D core must update with the selected candidate");
      assert.equal(details.coreInfo?.fuelAssemblyCount, 4, "3D core should show four source-derived fuel assemblies");
      assert.equal(details.coreInfo?.reflectorCount, 5, "3D core should show five source-derived reflector positions");
      assert.equal(details.coreInfo?.pinCount, 1156, "all 1156 source-defined fuel pin instances should be rendered");
      assert.equal(details.coreInfo?.libraryVersion, "0.180.0", "Three.js version must be explicit in the QA evidence");
      assert.equal(details.pinMapCellCount >= 17 * 17, true, "selected pin inspector should render the source 17x17 material map");
      assert.ok(details.chartSvgCount >= 1, "candidate comparison chart should render in the browser");
      assert.equal(details.comparisonType, "scatter", "candidate comparison should use scientific point/interval marks, not baseline-zero bars");
      assert.equal(details.comparisonErrorVisible, true, "k-effective comparison must display reported SD intervals");
      assert.match(details.comparisonXTitle, /mean k-effective/i);
      assert.equal(details.comparisonHasReference, true, "point-range plot should make the k_eff=1 interpretation reference explicit");
      assert.equal(details.rankedType, "scatter", "k-effective distribution should be a ranked dot plot, not a histogram");
      assert.equal(details.rankedMode, "markers");
      assert.equal(details.rankedCount, 6, "ranked dot plot should show six actual candidate observations");
      assert.equal(details.rankedErrorVisible, true, "ranked plot should show the source-reported standard deviations");
      assert.equal(details.rankedSelectedColorCount, 1, "selected-candidate highlight should synchronize to the ranked plot");
      assert.deepEqual(details.rankedOrder, ["MUMU","MMUU","MUUM","UMMU","UUMM","UMUM"], "rank order should follow the six recorded k-effective means");
      assert.equal(details.aggregateTraceCount, 1, "flux and fission scores should not share one common y scale");
      assert.equal(details.aggregateType, "scatter", "aggregate indicators should be shown as an x-y relationship");
      assert.match(details.aggregateXTitle, /mean k-effective/i);
      assert.match(details.aggregateYTitle, /fission-rate peaking proxy/i);
      assert.equal(details.aggregateSelectedColorCount, 1, "selected-candidate highlight should synchronize to the score relationship");
      assert.equal(details.matrixType, "heatmap", "position-wise comparison should be a heatmap matrix");
      assert.equal(details.matrixRows, 6, "matrix should include all six exact candidate matches");
      assert.equal(details.matrixColumns, 4, "matrix should include all four assembly positions");
      assert.deepEqual(details.matrixPositions, ["P00","P01","P10","P11"]);
      assert.equal(details.assemblyMapType, "heatmap", "assembly proxy must remain a discrete 2 × 2 map, never a continuous contour");
      assert.equal(details.assemblyMapTraceCount, 3, "map should contain one quantitative field, one material-category outline, and one selected-position outline");
      assert.deepEqual(details.assemblyMapPositions, ["P00","P01","P10","P11"], "map labels must follow row-major geometry positions");
      const recordedAssembly = await page.evaluate(async ({candidateId, signature}) => {
        const response = await fetch("/api/assembly");
        if (!response.ok) throw new Error("Assembly evidence API unavailable for value cross-check");
        const payload = await response.json();
        const row = (payload.records || []).find(item =>
          String(item.candidate_id).trim() === candidateId.trim() &&
          String(item.layout_signature).trim().toUpperCase() === signature.trim().toUpperCase()
        );
        return {
          values: row ? ["p00_fission_rate","p01_fission_rate","p10_fission_rate","p11_fission_rate"].map(key => Number(row[key])) : null,
          pairs: (payload.records || []).map(item => [String(item.candidate_id), String(item.layout_signature)])
        };
      }, { candidateId: option.value, signature: details.coreInfo?.layoutSignature || "" });
      assert.ok(recordedAssembly.values, "the selected candidate must have an exact ID + signature proxy record; selected=" + option.value + ", signature=" + String(details.coreInfo?.layoutSignature) + ", source records=" + JSON.stringify(recordedAssembly.pairs));
      assert.deepEqual(details.assemblyMapValues.flat(), recordedAssembly.values, "all four displayed heatmap values must be the actual CSV values in P00, P01, P10, P11 order");
      assert.deepEqual(details.assemblyMapText.flat().map(text => text.split("\n")[0]), details.coreInfo.layoutSignature.split("").map((code,index) => ["P00","P01","P10","P11"][index] + " · " + (code === "M" ? "MOX" : "UO₂")), "each tile must show its matching position label and actual material category");
      assert.match(details.assemblyMapAxisMapping, /ROW 0 \(TOP\).*P00 = R0\/C0.*P11 = R1\/C1/, "the position labels must document the same row/column convention as the core map");
      assert.deepEqual(details.assemblyMapScale, details.assemblyMatrixScale, "selected map and candidate matrix must keep one shared quantitative range");
      assert.match(details.assemblyMapColorbarTitle, /CSV unit not documented/i, "do not invent a physical unit that the source CSV does not record");
      assert.deepEqual(details.assemblyMapMaterialEdgeColors, details.coreInfo?.layoutSignature?.split("").map(code => code === "M" ? "#f4bd62" : "#55d4df") || [], "material edge colours must follow selected layout signature, not fixed spatial slots");
      assert.equal(details.assemblyMapSelectedPosition, "P00", "selected position should have a synchronized outline");
      assert.equal(details.assemblyPositionTitle, "P00");
      assert.equal(details.assemblyPositionMaterial, details.coreInfo?.layoutSignature?.[0] === "M" ? "MOX" : "UO₂");
      assert.match(details.assemblyPositionValue, /^0\.\d{3,}|^\d/);
      assert.match(details.assemblyScaleRange, /Shared global colour range/);
      assert.equal(details.assemblyProvenanceOpen, false, "verbose provenance should be collapsed by default");
      assert.equal(details.assemblyMapColorbarCount, 1, "only the selected-candidate map should display the shared quantitative colorbar");
      assert.equal(details.matrixColorbarVisible, false, "candidate matrix must reuse the map scale without duplicating its colorbar");
      assert.equal(details.matrixTraceCount, 2, "matrix should have one quantitative heatmap and one selected-row outline");
      assert.equal(details.matrixSelectedLayout, details.coreInfo?.layoutSignature, "outlined matrix row should follow the selected candidate");
      assert.match(details.keffAndSdText, /Between-seed sample SD ±/);
    }

    // Position controls and click events must stay synchronized with the 2 × 2 field.
    await page.click('#assemblyPositionPicker [data-assembly-position="P11"]');
    await page.waitForFunction(() =>
      document.querySelector("#assemblyPositionTitle")?.textContent === "P11" &&
      document.querySelector("#assemblyMap")?.data?.[2]?.customdata?.[0] === "P11"
    );
    await page.evaluate(() => {
      const map = document.querySelector("#assemblyMap");
      const cell = map?.data?.[0]?.customdata?.[1]?.[0];
      map?.emit?.("plotly_click", { points: [{ curveNumber: 0, customdata: cell }] });
    });
    await page.waitForFunction(() =>
      document.querySelector("#assemblyPositionTitle")?.textContent === "P10" &&
      document.querySelector("#assemblyMap")?.data?.[2]?.customdata?.[0] === "P10"
    );

    // Prove a 3D assembly click updates the selected-position inspector.
    const coreCanvas = page.locator("#core3dCanvas canvas.core3d-canvas");
    const coreBox = await coreCanvas.boundingBox();
    assert.ok(coreBox && coreBox.width > 300 && coreBox.height > 300, "3D canvas must occupy a meaningful viewport");
    await coreCanvas.click({ position: { x: coreBox.width / 2, y: coreBox.height / 2 } });
    await page.waitForFunction(() => document.querySelector("#coreAssemblyBadge")?.textContent.trim() === "P11", { timeout: 10000 });
    assert.match(await page.locator("#coreSelectionTitle").innerText(), /p11/i, "clicking the centre lattice cell must update the inspector");
    await page.click("#coreView2d");
    await page.waitForFunction(() => document.querySelector("#geometryPreview")?.hidden === false && document.querySelector("#core3dViewport")?.hidden === true);
    await page.waitForSelector("#geometryPreview svg.model-geometry-svg", { state: "visible", timeout: 10000 });
    await page.click("#coreView3d");
    await page.waitForSelector("#core3dCanvas canvas.core3d-canvas", { timeout: 10000 });
    await page.waitForFunction(() => /WEBGL READY/.test(document.querySelector("#core3dStatus")?.textContent || ""));
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
      try {
        await page.waitForFunction(expected => {
          const el = document.querySelector("#meshHeatmap");
          return el?.data?.[0]?.hovertemplate?.includes(expected + " tally mean");
        }, score, { timeout: 15000 });
      } catch (error) {
        const state = await page.evaluate(() => ({
          selectedScore: document.querySelector("#meshScore")?.value,
          selectedView: document.querySelector("#meshView")?.value,
          meshStatus: document.querySelector("#meshStatus")?.textContent,
          hovertemplate: document.querySelector("#meshHeatmap")?.data?.[0]?.hovertemplate || "",
          chartError: document.querySelector("#meshHeatmap")?.innerText || "",
          summary: document.querySelector("#meshSummaryNote")?.textContent || ""
        }));
        throw new Error("Mesh score control did not redraw the recorded hover field for " + score + ": " + JSON.stringify(state) + "; " + error.message);
      }
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

    // Vertical exaggeration changes only the 3D scene's aspect ratio, not source tally values.
    const surfaceBeforeExaggeration = await page.evaluate(() => {
      const el = document.querySelector("#meshSurface"), trace = el?.data?.[0];
      return {
        z: trace?.z?.[25]?.[25],
        source: trace?.customdata?.[25]?.[25],
        aspect: el?.layout?.scene?.aspectratio?.z
      };
    });
    await page.selectOption("#meshExaggeration", "3");
    await page.waitForFunction(() => {
      const el = document.querySelector("#meshSurface");
      return Math.abs((el?.layout?.scene?.aspectratio?.z || 0) - 0.9) < 0.001;
    }, { timeout: 15000 });
    const surfaceAfterExaggeration = await page.evaluate(() => {
      const el = document.querySelector("#meshSurface"), trace = el?.data?.[0];
      return {
        z: trace?.z?.[25]?.[25],
        source: trace?.customdata?.[25]?.[25],
        aspect: el?.layout?.scene?.aspectratio?.z
      };
    });
    assert.equal(surfaceAfterExaggeration.z, surfaceBeforeExaggeration.z, "vertical exaggeration must not transform the 51×51 Z tally values");
    assert.deepEqual(surfaceAfterExaggeration.source, surfaceBeforeExaggeration.source, "vertical exaggeration must not change source mean/SE/relative-error hover data");
    assert.ok(surfaceAfterExaggeration.aspect > surfaceBeforeExaggeration.aspect * 2.9, "3× vertical exaggeration should change visual aspect ratio only");
    assert.match(await page.locator("#meshSummaryNote").innerText(), /display-only; source data unchanged/i);

    // Force an alternate camera, then prove the Reset camera button restores the known default.
    await page.evaluate(async () => window.Plotly.relayout(document.querySelector("#meshSurface"), {
      "scene.camera": { eye: { x: 2.3, y: 0.6, z: 0.5 }, center: { x: 0, y: 0, z: 0 }, up: { x: 0, y: 0, z: 1 } }
    }));
    await page.waitForFunction(() => Math.abs((document.querySelector("#meshSurface")?.layout?.scene?.camera?.eye?.x || 0) - 2.3) < 0.05, { timeout: 10000 });
    await page.click("#meshResetCamera");
    await page.waitForFunction(() => Math.abs((document.querySelector("#meshSurface")?.layout?.scene?.camera?.eye?.x || 0) - 1.55) < 0.05, { timeout: 10000 });
    await page.selectOption("#meshExaggeration", "1");

    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-desktop-full.png"), fullPage: true, animations: "disabled" });
    // The full-page capture above includes the map, candidate detail, and Three.js
    // canvas. Avoid per-locator screenshots of live Plotly/WebGL regions: those
    // canvases keep repainting, so Playwright's pixel-stability wait can time out
    // even though the visual smoke assertions have passed. The full-page artifact
    // provides one faithful capture without falsely failing on live canvas motion.
    await page.click("#coreView2d");
    await page.waitForFunction(() => document.querySelector("#geometryPreview")?.hidden === false && document.querySelector("#core3dViewport")?.hidden === true);
    // The source-derived SVG fallback is asserted in the DOM above. Avoid a second
    // screenshot while the UI reflows between 2D/3D modes: Chromium may report the
    // SVG as moving even when the source geometry and controls are correct. The
    // full-page screenshot above remains the primary visual QA artifact.
    await page.click("#coreView3d");
    await page.waitForFunction(() => document.querySelector("#geometryPreview")?.hidden === true && document.querySelector("#core3dViewport")?.hidden === false);

    // Reuse this explicitly-created BrowserContext so the already-loaded
    // Three.js and Plotly libraries remain cached. Open a fresh page, then set its
    // mobile viewport before navigating so charts initialise at the right width.
    const mobilePage = await context.newPage();
    await mobilePage.setViewportSize({ width: 390, height: 844 });
    const mobileFailures = [];
    mobilePage.on("pageerror", error => mobileFailures.push("pageerror: " + error.message));
    const mobileResponse = await mobilePage.goto(BASE_URL, { waitUntil: "commit", timeout: 30000 });
    assert.ok(mobileResponse && mobileResponse.ok(), "mobile workstation HTML should return HTTP 200");
    await mobilePage.waitForFunction(() => {
      const select = document.querySelector("#candidateSelect");
      return select && select.options.length === 6 && select.value;
    }, { timeout: 30000 });
    await mobilePage.waitForFunction(() => document.querySelectorAll("#selectedCandidateMetrics .candidate-stat").length === 4, { timeout: 30000 });
    await mobilePage.waitForSelector("#core3dCanvas canvas.core3d-canvas", { timeout: 30000 });
    await mobilePage.waitForSelector("#geometryPreview svg.model-geometry-svg", { state: "attached", timeout: 30000 });
    await mobilePage.waitForFunction(() => {
      const status = document.querySelector("#core3dStatus")?.textContent || "";
      const fallback = /2D SOURCE FALLBACK|WEBGL UNAVAILABLE|THREE.JS CDN UNAVAILABLE.*2D FALLBACK/i.test(status);
      const svg = document.querySelector("#geometryPreview");
      const active2d = document.querySelector("#coreView2d")?.getAttribute("aria-pressed") === "true";
      // Three.js is optional. If its CDN or WebGL is unavailable, require the
      // source SVG to be visible and the 2-D mode button to be active instead.
      return /WEBGL READY/.test(status) || (fallback && svg && svg.hidden === false && active2d);
    }, { timeout: 20000 });
    // Desktop QA above checks all four Plotly spatial views fully. On mobile,
    // focus this pass on the Stage 1 core renderer, position inspector, and overflow;
    // don't initialize/wait for a second full set of heavyweight Plotly SVGs.
    // Wait until all chart/3D initialization has settled before forcing the mobile metric into view.
    await mobilePage.evaluate(() => {
      const metric = document.querySelector("#selectedCandidateMetrics .candidate-stat");
      metric?.scrollIntoView({ block: "center", behavior: "instant" });
    });
    await mobilePage.waitForFunction(() => {
      const metric = document.querySelector("#selectedCandidateMetrics .candidate-stat");
      if (!metric) return false;
      const rect = metric.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0 && rect.bottom > 0 && rect.top < window.innerHeight;
    }, { timeout: 10000 });
    const mobileMetricsVisible = await mobilePage.evaluate(() => {
      const metric = document.querySelector("#selectedCandidateMetrics .candidate-stat");
      if (!metric) return false;
      const style = getComputedStyle(metric);
      return style.visibility !== "hidden" && style.display !== "none" && metric.getBoundingClientRect().height > 0;
    });
    assert.equal(mobileMetricsVisible, true, "candidate metrics must remain visible after chart initialization on mobile");
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
    assert.ok(await mobilePage.locator("#core3dCanvas canvas.core3d-canvas").isVisible(), "interactive Three.js core must remain visible on mobile");
    await mobilePage.evaluate(() => window.scrollTo(0, 0));
    await mobilePage.screenshot({ path: path.join(OUTPUT_DIR, "cb-pfr-mobile-top.png"), fullPage: false, animations: "disabled" });
    await mobilePage.addStyleTag({ content: "@media(max-width:680px){.sidebar{position:static!important;top:auto!important}}" });
    // The desktop full-page capture already documents every scientific plot.
    // Keep a viewport-sized mobile capture here: element-level captures of live
    // Plotly and WebGL content can time out waiting for pixel stability.
    await mobilePage.close();

    assert.deepEqual(failures, [], "desktop page must not throw uncaught JavaScript errors");
    assert.deepEqual(mobileFailures, [], "mobile page must not throw uncaught JavaScript errors");
    const coreGeometryReport = await page.evaluate(() => ({
      renderer: document.querySelector("#core3dCanvas canvas.core3d-canvas") ? "Three.js WebGL" : "fallback",
      evidence: window.CBPFRCore3DInfo || null
    }));
    const report = {
      baseUrl: BASE_URL,
      result: "passed",
      candidateCount: candidateOptions.length,
      candidateIds: candidateOptions.map(option => option.value),
      sourceGeometryPinCellCount: 4 * 17 * 17,
      spatialPlotCount: await page.locator("#meshHeatmap.js-plotly-plot, #meshContour.js-plotly-plot, #meshProfile.js-plotly-plot, #meshSurface.js-plotly-plot").count(),
      spatialDataStatus: await page.locator("#meshStatus").innerText(),
      coreGeometryRenderer: coreGeometryReport.renderer,
      coreGeometryEvidence: coreGeometryReport.evidence,
      coreGeometryStatus: await page.locator("#core3dStatus").innerText(),
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
