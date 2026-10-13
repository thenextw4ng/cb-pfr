"use strict";
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const baseUrl = process.env.CBPFR_BASE_URL || "http://127.0.0.1:8765";
const outDir = path.join(process.cwd(), "artifacts", "stage6-visual-acceptance");
fs.mkdirSync(outDir, { recursive: true });

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: ["--enable-webgl", "--ignore-gpu-blocklist", "--use-gl=angle", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"]
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const errors = [];
  page.on("pageerror", error => errors.push(error.message));

  try {
    const response = await page.goto(baseUrl + "/", { waitUntil: "domcontentloaded", timeout: 30000 });
    assert.ok(response && response.ok(), "workstation must return HTTP 200");

    const api = await page.evaluate(async () => {
      async function get(path) {
        const response = await fetch(path, { headers: { Accept: "application/json" } });
        const payload = await response.json();
        if (!response.ok) throw new Error(path + ": " + (payload.error || response.status));
        return payload;
      }
      const values = await Promise.all([
        get("/api/health"), get("/api/candidates"), get("/api/model-geometry"),
        get("/api/assembly"), get("/api/mesh"), get("/api/axial-3d?score=flux")
      ]);
      const axial = values[5];
      return { health: values[0], candidates: values[1], geometry: values[2], assembly: values[3], mesh: values[4], axial: { available: axial.available, mesh: { dimension_xyz: axial.mesh.dimension_xyz } } };
    });

    assert.equal(api.health.status, "ok");
    assert.equal(api.candidates.records.length, 6);
    assert.equal(api.geometry.candidates.length, 6);
    assert.equal(api.assembly.records.length, 6);
    assert.deepEqual(api.mesh.mesh_tallies[0].dimensions, [51, 51, 1]);
    assert.equal(api.axial.available, true);
    assert.deepEqual(api.axial.mesh.dimension_xyz, [51, 51, 30]);

    const bySignature = new Map(api.geometry.candidates.map(item => [item.layout_signature, item]));
    for (const candidate of api.candidates.records) {
      const source = bySignature.get(candidate.layout_signature);
      assert.ok(source, "candidate geometry must match by layout signature");
      assert.equal([source.assembly_grid[0][0], source.assembly_grid[0][1], source.assembly_grid[1][0], source.assembly_grid[1][1]].join(""), candidate.layout_signature);
      assert.equal(source.assembly_grid.flat().filter(value => value === "R").length, 5);
    }

    await page.waitForFunction(() => {
      const select = document.querySelector("#candidateSelect");
      const map = document.querySelector("#assemblyMap");
      const matrix = document.querySelector("#assemblyMatrix");
      return select && [...select.options].filter(o => o.value).length === 6 &&
        map && map.data && map.data.length >= 3 && matrix && matrix.data && matrix.data.length;
    }, null, { timeout: 60000 });
    await page.waitForFunction(() => {
      const chart = document.querySelector("#candidateChart");
      return chart && Array.isArray(chart.data) && chart.data.length > 0;
    }, null, { timeout: 60000 });

    const assemblyView = await page.evaluate(() => {
      const select = document.querySelector("#candidateSelect");
      const plot = document.querySelector("#assemblyMap");
      const matrix = document.querySelector("#assemblyMatrix");
      return {
        selectedId: select.value,
        map: plot.data.map(trace => ({ type: trace.type, z: trace.z, text: trace.text, colorbar: trace.colorbar, colorscale: trace.colorscale, lineColor: trace.marker && trace.marker.line && trace.marker.line.color })),
        annotation: (plot.layout.annotations || []).map(item => item.text).join(" "),
        matrixZ: matrix.data[0].z,
        matrixShowscale: matrix.data[0].showscale,
        mapNote: document.querySelector(".assembly-map-note").innerText
      };
    });
    const current = api.candidates.records.find(row => row.candidate_id === assemblyView.selectedId);
    const sourceProxy = api.assembly.records.find(row => row.candidate_id === current.candidate_id && row.layout_signature === current.layout_signature);
    assert.ok(sourceProxy, "proxy row needs exact candidate ID and layout signature");
    assert.deepEqual(assemblyView.map[0].z, [
      [Number(sourceProxy.p00_fission_rate), Number(sourceProxy.p01_fission_rate)],
      [Number(sourceProxy.p10_fission_rate), Number(sourceProxy.p11_fission_rate)]
    ]);
    assert.match(String(assemblyView.map[0].colorbar.title.text), /unit not documented/i);
    assert.equal(assemblyView.map[0].type, "heatmap");
    assert.ok(assemblyView.map[0].colorscale, "quantitative heatmap must retain a scalar color scale");
    assert.ok(assemblyView.map.some(item => item.type === "scatter"), "material/selection frames are separate from the numeric scale");
    assert.equal(assemblyView.matrixZ.length, 6);
    assert.equal(assemblyView.matrixZ[0].length, 4);
    assert.equal(assemblyView.matrixShowscale, false);
    assert.match(assemblyView.mapNote, /not absolute power/i);
    assert.match(JSON.stringify(assemblyView.map[0].text), /P00.*P01.*P10.*P11/);
    assert.ok(!assemblyView.annotation.includes("ROW 0 (TOP)"), "dense geometry annotation should stay out of the plot canvas");
    await page.locator('#assemblyPositionPicker [data-assembly-position="P11"]').click();
    await page.waitForFunction(() => document.querySelector("#assemblyPositionTitle").textContent === "P11");
    await page.locator("#candidateSelect").selectOption("c5g7-2x2-UMMU");
    await page.waitForFunction(() => document.querySelector("#selectedCandidateId").textContent === "c5g7-2x2-UMMU");
    const ummuMap = await page.locator("#assemblyMap").evaluate(el => ({ z: el.data[0].z, selectedOutline: el.data[2].marker.line.color }));
    const ummuProxy = api.assembly.records.find(row => row.candidate_id === "c5g7-2x2-UMMU" && row.layout_signature === "UMMU");
    assert.deepEqual(ummuMap.z, [
      [Number(ummuProxy.p00_fission_rate), Number(ummuProxy.p01_fission_rate)],
      [Number(ummuProxy.p10_fission_rate), Number(ummuProxy.p11_fission_rate)]
    ]);
    assert.ok(ummuMap.selectedOutline === "#ffffff" || ummuMap.selectedOutline[0] === "#ffffff");
    await page.screenshot({ path: path.join(outDir, "assembly-proxy-map.png") });

    await page.screenshot({ path: path.join(outDir, "workstation-desktop.png"), fullPage: true });

    await page.locator('.nav-item[data-target="assembly"]').click();
    await page.locator("#coreView2d").click();
    await page.waitForFunction(() => {
      const preview = document.querySelector("#geometryPreview");
      return preview && !preview.hidden && preview.querySelector("svg.model-geometry-svg");
    }, null, { timeout: 30000 });
    const sourceMap = await page.locator("#geometryPreview svg.model-geometry-svg").evaluate(el => el.textContent || "");
    assert.match(sourceMap, /P00/);
    assert.match(sourceMap, /P11/);
    const pinMap = await page.locator("#coreSelectedPinMap").innerText();
    assert.match(pinMap, /17|pin|universe/i);
    await page.screenshot({ path: path.join(outDir, "core-geometry-source-map.png") });

    await page.locator('.nav-item[data-target="spatial"]').click();
    await page.waitForFunction(() => ["meshHeatmap", "meshContour", "meshProfile", "meshSurface"].every(id => {
      const el = document.querySelector("#" + id);
      return el && Array.isArray(el.data) && el.data.length > 0;
    }), null, { timeout: 120000 });
    const field = await page.evaluate(() => {
      const heat = document.querySelector("#meshHeatmap");
      const contour = document.querySelector("#meshContour");
      const profile = document.querySelector("#meshProfile");
      const surface = document.querySelector("#meshSurface");
      const ht = heat.data[0], ct = contour.data[0], pt = profile.data[0];
      const st = surface.data.find(trace => trace.type === "surface");
      return {
        x: ht.x, y: ht.y, z: ht.z, heatHover: ht.hovertemplate, axes: [heat.layout.xaxis.title.text, heat.layout.yaxis.title.text],
        contour: { x: ct.x, y: ct.y, z: ct.z },
        profile: { x: pt.x, y: pt.y, hover: pt.hovertemplate },
        surface: { x: st.x, y: st.y, z: st.z, hover: st.hovertemplate }
      };
    });
    assert.deepEqual(field.z, field.contour.z, "heatmap and contour must show the same field values");
    assert.deepEqual(field.z, field.surface.z, "surface must preserve the same recorded mesh values");
    assert.deepEqual(field.x, field.contour.x);
    assert.deepEqual(field.y, field.contour.y);
    assert.deepEqual(field.x, field.surface.x);
    assert.deepEqual(field.y, field.surface.y);
    assert.deepEqual(field.x, field.profile.x);
    assert.equal(field.x.length, 51);
    assert.equal(field.y.length, 51);
    assert.match(field.axes[0], /cm|bin index/i);
    assert.match(field.axes[1], /cm|bin index/i);
    assert.match(field.heatHover, /Recorded flux tally mean/i);
    assert.match(field.heatHover, /Monte Carlo standard error/i);
    assert.match(field.surface.hover, /Recorded flux tally mean/i);
    await page.locator("#meshSurface").screenshot({ path: path.join(outDir, "spatial-surface-desktop.png") });

    await page.locator("#axial3dPanel").scrollIntoViewIfNeeded();
    await page.waitForFunction(() => {
      const plot = document.querySelector("#axial3dPlot");
      return plot && Array.isArray(plot.data) && plot.data.some(trace => trace.type === "volume");
    }, null, { timeout: 120000 });
    const axial = await page.evaluate(() => {
      const plot = document.querySelector("#axial3dPlot");
      const volume = plot.data.find(trace => trace.type === "volume");
      return {
        status: document.querySelector("#axial3dStatus").textContent,
        metrics: document.querySelector("#axial3dKpis").innerText,
        provenance: document.querySelector("#axial3dProvenance").textContent,
        summary: document.querySelector("#axial3dSummary").textContent,
        pointCount: volume.x.length
      };
    });
    assert.match(axial.status, /3D STATEPOINT LOADED/i);
    assert.match(axial.metrics, /51 × 51 × 30/);
    assert.match(axial.provenance, /statepoint SHA-256 [0-9a-f]{64}/i);
    assert.match(axial.provenance, /NPZ SHA-256 [0-9a-f]{64}/i);
    assert.match(axial.provenance, /batches 7000/);
    assert.match(axial.provenance, /active realizations 6500/);
    assert.match(axial.summary, /95th percentile/i);
    assert.equal(axial.pointCount, 51 * 51 * 30);
    await page.screenshot({ path: path.join(outDir, "axial-3d-volume-desktop.png") });

    await page.setViewportSize({ width: 390, height: 844 });
    if (page.evaluate) await page.evaluate(() => {
      if (window.Plotly) document.querySelectorAll(".js-spatial-plot, #candidateChart, #distributionChart, #assemblyMap, #assemblyMatrix").forEach(el => {
        if (el.data) window.Plotly.Plots.resize(el);
      });
    });
    await page.locator("#navToggle").click();
    assert.equal(await page.locator(".sidebar").evaluate(el => el.classList.contains("nav-open")), true);
    const mobile = await page.evaluate(() => ({
      viewport: window.innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      bodyWidth: document.body.scrollWidth,
      charts: [...document.querySelectorAll(".js-spatial-plot, #candidateChart, #distributionChart, #assemblyMap, #assemblyMatrix")].map(el => {
        const r = el.getBoundingClientRect();
        return { id: el.id || el.className, right: r.right, width: r.width };
      })
    }));
    assert.ok(mobile.documentWidth <= mobile.viewport + 3, "document overflows horizontally on mobile: " + JSON.stringify(mobile));
    assert.ok(mobile.bodyWidth <= mobile.viewport + 3, "body overflows horizontally on mobile");
    for (const plot of mobile.charts) {
      assert.ok(plot.width <= mobile.viewport + 3, plot.id + " is wider than viewport");
      assert.ok(plot.right <= mobile.viewport + 5, plot.id + " extends beyond the right viewport edge");
    }
    await page.screenshot({ path: path.join(outDir, "workstation-mobile.png"), fullPage: true });
    assert.deepEqual(errors, [], "uncaught browser errors must not be present");

    const report = {
      status: "passed",
      candidates: api.candidates.records.length,
      source_geometry_layouts: api.geometry.candidates.length,
      assembly_proxy_records: api.assembly.records.length,
      source_mesh_dimensions: api.mesh.mesh_tallies[0].dimensions,
      axial_3d_dimensions: api.axial.mesh.dimension_xyz,
      axial_3d_voxels: axial.pointCount,
      selected_proxy_values_match_csv: true,
      field_heatmap_contour_surface_values_match: true,
      hover_preserves_mean_and_error: true,
      mobile: mobile,
      page_errors: errors
    };
    fs.writeFileSync(path.join(outDir, "visual-acceptance.json"), JSON.stringify(report, null, 2) + "\n");
    console.log("Stage 6 browser acceptance passed: " + JSON.stringify({ candidates: report.candidates, mesh: report.source_mesh_dimensions, axial: report.axial_3d_dimensions }));
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
