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
      const axialSampleIndices = [[0, 0, 0], [15, 25, 25], [29, 50, 50]];
      const axialSamples = axialSampleIndices.map(([k, j, i]) => ({
        k, j, i,
        x: axial.mesh.x_centers_cm[i], y: axial.mesh.y_centers_cm[j], z: axial.mesh.z_centers_cm[k],
        mean: axial.mean[k][j][i],
        standard_error: axial.standard_error[k][j][i],
        relative_error_percent: axial.relative_error_percent[k][j][i]
      }));
      return {
        health: values[0], candidates: values[1], geometry: values[2], assembly: values[3], mesh: values[4],
        axial: {
          available: axial.available,
          score: axial.score,
          mesh: {
            dimension_xyz: axial.mesh.dimension_xyz,
            axis_samples: {
              x: [axial.mesh.x_centers_cm[0], axial.mesh.x_centers_cm[25], axial.mesh.x_centers_cm[50]],
              y: [axial.mesh.y_centers_cm[0], axial.mesh.y_centers_cm[25], axial.mesh.y_centers_cm[50]],
              z: [axial.mesh.z_centers_cm[0], axial.mesh.z_centers_cm[15], axial.mesh.z_centers_cm[29]]
            }
          },
          provenance: {
            npz_sha256: axial.provenance.sha256,
            statepoint_sha256: axial.provenance.statepoint && axial.provenance.statepoint.sha256,
            statepoint: axial.provenance.statepoint,
            score_summary: axial.provenance.score_summary
          },
          samples: axialSamples
        }
      };
    });

    assert.equal(api.health.status, "ok");
    assert.equal(api.candidates.records.length, 6);
    assert.equal(api.candidates.metadata.campaign_status, "EXPLORATORY_DESCRIPTIVE_ONLY");
    assert.equal(api.candidates.metadata.run_count, 18);
    assert.equal(api.candidates.metadata.runs_per_layout, 3);
    assert.equal(api.candidates.metadata.records_validated_against_run_level_data, true);
    assert.match(api.candidates.metadata.source, /c5g7_corrected_group_repeatability_smoke_2026-10-11/);
    assert.match(api.candidates.metadata.acceptance_status, /BLOCKED_NO_DESIGN_SPECIFIC_KEFF_BAND/);
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
      const distribution = document.querySelector("#distributionChart");
      return chart && Array.isArray(chart.data) && chart.data.length > 0 &&
        distribution && Array.isArray(distribution.data) && distribution.data.length > 0;
    }, null, { timeout: 60000 });

    const candidateStats = await page.locator("#distributionChart").evaluate(el => {
      const trace = el.data[0];
      return {
        x: trace.x || [],
        y: trace.y || [],
        sd: trace.error_y && trace.error_y.array || [],
        hover: trace.hovertemplate || "",
        xTitle: String(el.layout.xaxis.title && (el.layout.xaxis.title.text || el.layout.xaxis.title) || ""),
        yTitle: String(el.layout.yaxis.title && (el.layout.yaxis.title.text || el.layout.yaxis.title) || "")
      };
    });
    assert.equal(candidateStats.x.length, 6, "six candidate layouts must appear in the comparative chart");
    assert.equal(new Set(candidateStats.x).size, 6, "candidate labels must be unique");
    assert.equal(candidateStats.y.length, 6, "each plotted candidate needs one recorded k-effective mean");
    assert.equal(candidateStats.sd.length, 6, "each plotted candidate needs an explicit SD bar (zero only when missing)");
    assert.ok(candidateStats.y.every(value => Number.isFinite(Number(value))), "candidate values must be finite");
    assert.ok(candidateStats.sd.every(value => value === null || (Number.isFinite(Number(value)) && Number(value) >= 0)), "recorded SD values must be nonnegative; absent SD remains missing");
    const candidateBySignature = new Map(api.candidates.records.map(row => [String(row.layout_signature), row]));
    for (let index = 0; index < candidateStats.x.length; index++) {
      const source = candidateBySignature.get(String(candidateStats.x[index]));
      assert.ok(source, "comparative chart label must match a recorded layout signature");
      assert.equal(Number(candidateStats.y[index]), Number(source.keff_mean), "plotted mean must equal the candidate CSV mean");
      if (source.keff_std_dev === null || source.keff_std_dev === undefined || source.keff_std_dev === "") {
        assert.equal(candidateStats.sd[index], null, "missing source SD must not be represented as zero");
      } else {
        assert.equal(Number(candidateStats.sd[index]), Number(source.keff_std_dev), "plotted SD must equal the candidate CSV SD");
      }
    }
    assert.match(candidateStats.hover, /k-effective mean/i);
    assert.match(candidateStats.hover, /Between-seed sample SD/i);
    assert.match(candidateStats.xTitle, /k-effective/i);
    assert.match(candidateStats.yTitle, /between-seed sample SD/i);

    // Verify the paper export renders a publication-sized image, offers explicit
    // user-initiated downloads, and writes a JSON provenance sidecar.
    const paperExportButton = page.locator('[data-figure-target="distributionChart"]');
    assert.equal(await paperExportButton.count(), 1, "paper export control for corrected-group k-effective must exist");
    await paperExportButton.click();
    await page.waitForFunction(() => {
      const status = document.querySelector("#paperExportStatus")?.textContent || "";
      return status.includes("JSON provenance/interpretation sidecar are ready to download");
    }, null, { timeout: 60000 });
    const [paperPng] = await Promise.all([
      page.waitForEvent("download", { timeout: 30000 }),
      page.locator('#paperExportStatus a[data-export-kind="png"]').click()
    ]);
    const [paperJson] = await Promise.all([
      page.waitForEvent("download", { timeout: 30000 }),
      page.locator('#paperExportStatus a[data-export-kind="json"]').click()
    ]);
    assert.match(paperPng.suggestedFilename(), /\.png$/i);
    assert.match(paperJson.suggestedFilename(), /\.json$/i);
    const pngPath = await paperPng.path();
    const jsonPath = await paperJson.path();
    assert.ok(fs.statSync(pngPath).size > 10000, "exported PNG must contain rendered figure data");
    const sidecar = JSON.parse(fs.readFileSync(jsonPath, "utf8"));
    assert.equal(sidecar.schema_version, "cbpfr-paper-figure-export-v1");
    assert.equal(sidecar.figure.target_id, "distributionChart");
    assert.equal(sidecar.image.pixel_width, 4400);
    assert.equal(sidecar.image.pixel_height, 2800);
    assert.match(sidecar.interpretation_boundary, /smoke-budget|descriptive/i);

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
        pickerValues: [...document.querySelectorAll("#assemblyPositionPicker strong")].map(el => el.textContent.trim()),
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
    assert.equal(assemblyView.pickerValues.length, 4);
    assert.ok(assemblyView.pickerValues.every(value => value.length <= 7), "position picker values must remain on one readable line");
    assert.match(assemblyView.mapNote, /not absolute power/i);
    assert.match(JSON.stringify(assemblyView.map[0].text), /P00.*P01.*P10.*P11/);
    assert.ok(!assemblyView.annotation.includes("ROW 0 (TOP)"), "dense geometry annotation should stay out of the plot canvas");
    await page.locator('#assemblyPositionPicker [data-assembly-position="P11"]').click();
    await page.waitForFunction(() => document.querySelector("#assemblyPositionTitle").textContent === "P11");
    await page.locator("#candidateSelect").selectOption("c5g7-2x2-UMMU");
    await page.waitForFunction(() => document.querySelector("#selectedCandidateId").textContent === "c5g7-2x2-UMMU");
    const ummuMap = await page.locator("#assemblyMap").evaluate(el => ({ z: el.data[0].z, selectedOutline: el.data[2].marker.line.color }));
    const matrixSelection = await page.locator("#assemblyMatrix").evaluate(el => ({ types: el.data.map(trace => trace.type), labels: el.data[0].y, values: el.data[0].z, annotation: (el.layout.annotations || []).map(item => item.text).join(" ") }));
    assert.deepEqual(matrixSelection.types, ["heatmap"], "selected candidate highlight must not cover numerical matrix cells");
    assert.ok(matrixSelection.labels.some(label => /UMMU\s+◂/.test(label)), "selected candidate should be identified at its row label");
    assert.match(matrixSelection.annotation, /Selected layout: UMMU/);
    const ummuProxy = api.assembly.records.find(row => row.candidate_id === "c5g7-2x2-UMMU" && row.layout_signature === "UMMU");
    assert.deepEqual(ummuMap.z, [
      [Number(ummuProxy.p00_fission_rate), Number(ummuProxy.p01_fission_rate)],
      [Number(ummuProxy.p10_fission_rate), Number(ummuProxy.p11_fission_rate)]
    ]);
    assert.ok(ummuMap.selectedOutline === "#ffffff" || ummuMap.selectedOutline[0] === "#ffffff");
    await page.locator(".assembly-evidence-grid").screenshot({ path: path.join(outDir, "assembly-proxy-map.png") });

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
    await page.locator(".core-geometry-layout").screenshot({ path: path.join(outDir, "core-geometry-source-map.png") });

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
        score: document.querySelector("#meshScore").value,
        view: document.querySelector("#meshView").value,
        scale: document.querySelector("#meshScale").value,
        status: document.querySelector("#meshStatus").textContent,
        provenance: document.querySelector("#meshProvenance").textContent,
        contour: { x: ct.x, y: ct.y, z: ct.z },
        profile: { x: pt.x, y: pt.y, hover: pt.hovertemplate },
        surface: { x: st.x, y: st.y, z: st.z, customdata: st.customdata, hover: st.hovertemplate, camera: surface.layout.scene.camera, aspectRatioZ: surface.layout.scene.aspectratio.z }
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
    assert.match(field.heatHover, /Recorded .* tally mean/i);
    assert.match(field.heatHover, /Monte Carlo standard error/i);
    assert.match(field.surface.hover, /Recorded .* tally mean/i);
    const recordedMesh = api.mesh.mesh_tallies[0];
    const recordedScore = recordedMesh.scores[field.score];
    const sourceGeometry = recordedMesh.spatial_geometry;
    if (sourceGeometry && sourceGeometry.coordinates_available === true && sourceGeometry.coordinate_units === "cm") {
      const [lx, ly] = sourceGeometry.lower_left_cm;
      const [ux, uy] = sourceGeometry.upper_right_cm;
      const nx = recordedMesh.dimensions[0], ny = recordedMesh.dimensions[1];
      const expectedX = Array.from({ length: nx }, (_, i) => lx + (i + 0.5) * (ux - lx) / nx);
      const expectedY = Array.from({ length: ny }, (_, j) => ly + (j + 0.5) * (uy - ly) / ny);
      for (let i = 0; i < nx; i++) assert.ok(Math.abs(Number(field.x[i]) - expectedX[i]) < 1e-12, "X coordinate must be the recorded mesh cell centre");
      for (let j = 0; j < ny; j++) assert.ok(Math.abs(Number(field.y[j]) - expectedY[j]) < 1e-12, "Y coordinate must be the recorded mesh cell centre");
    } else {
      assert.match(field.axes[0], /bin index/i);
      assert.match(field.axes[1], /bin index/i);
    }
    const sourceMean = recordedScore.mean;
    const sourceSE = recordedScore.standard_error || recordedScore.std_dev;
    for (let j = 0; j < 51; j++) for (let i = 0; i < 51; i++) {
      const mean = Number(sourceMean[j][i]);
      const se = Number(sourceSE[j][i]);
      let expected = null;
      if (field.view === "relative_sd") expected = mean > 0 && Number.isFinite(se) ? 100 * se / mean : null;
      else if (field.scale === "log") expected = mean > 0 ? Math.log10(mean) : null;
      else expected = Number.isFinite(mean) ? mean : null;
      const actual = field.z[j][i];
      if (expected === null || !Number.isFinite(expected)) assert.ok(actual === null || actual === undefined, "missing / non-positive value must not be transformed into a peak");
      else assert.ok(Number.isFinite(Number(actual)) && Math.abs(Number(actual) - expected) <= Math.max(1e-12, Math.abs(expected) * 1e-12), "mesh display value must derive from source tally mean/uncertainty");
      const surfaceCustom = field.surface.customdata[j][i];
      assert.ok(Array.isArray(surfaceCustom) && surfaceCustom.length >= 3, "surface must retain source mean/SE/relative-SE for hover");
      assert.equal(Number(surfaceCustom[0]), mean, "surface hover mean must match the source mesh");
      assert.equal(Number(surfaceCustom[1]), se, "surface hover Monte Carlo SE must match the source mesh");
      const expectedRelative = mean > 0 && Number.isFinite(se) && se >= 0 ? 100 * se / mean : null;
      if (expectedRelative === null) assert.ok(surfaceCustom[2] === null || surfaceCustom[2] === undefined, "missing relative error must not be fabricated");
      else assert.ok(Number.isFinite(Number(surfaceCustom[2])) && Math.abs(Number(surfaceCustom[2]) - expectedRelative) <= Math.max(1e-12, Math.abs(expectedRelative) * 1e-12), "surface hover relative error must match the source tally");
    }
    assert.match(field.surface.hover, /customdata\[0\]/);
    assert.match(field.surface.hover, /customdata\[1\]/);
    assert.match(field.surface.hover, /customdata\[2\]/);
    if (api.mesh.provenance.hash_matches === true) {
      assert.equal(field.status, "SHA-256 VERIFIED");
      assert.match(field.provenance, /matches the recorded baseline/i);
    } else if (api.mesh.provenance.hash_matches === false) {
      assert.equal(field.status, "HASH MISMATCH");
      assert.match(field.provenance, /differs from the recorded baseline/i);
    } else {
      assert.equal(field.status, "DATA LOADED · HASH NOT CHECKED");
      assert.match(field.provenance, /Baseline hash was unavailable/i);
      assert.match(field.provenance, /has not been hash-verified/i);
    }
    await page.locator("#meshSurface").screenshot({ path: path.join(outDir, "spatial-surface-desktop.png") });

    // Exercise actual Plotly 3D interaction and confirm display controls never change source data.
    const surfacePlot = page.locator("#meshSurface");
    const surfaceBefore = await surfacePlot.evaluate(el => {
      const trace = el.data.find(item => item.type === "surface");
      return {
        z: trace.z,
        customdata: trace.customdata,
        camera: el.layout.scene.camera,
        aspectRatioZ: el.layout.scene.aspectratio.z
      };
    });
    assert.ok(Math.abs(Number(surfaceBefore.aspectRatioZ) - 0.3) < 1e-8, "1× display exaggeration must start at its declared aspect ratio");
    // Plotly's WebGL layer may be nested in a canvas that is intentionally transparent
    // or not exposed as a visible element by headless Chromium. Drag the plot's own hit area,
    // which is the public interactive surface container, rather than depending on canvas CSS.
    await surfacePlot.waitFor({ state: "visible", timeout: 15000 });
    const surfaceBounds = await surfacePlot.boundingBox();
    assert.ok(surfaceBounds && surfaceBounds.width > 100 && surfaceBounds.height > 100, "interactive 3D surface plot must have a usable hit area");
    await page.mouse.move(surfaceBounds.x + surfaceBounds.width * 0.48, surfaceBounds.y + surfaceBounds.height * 0.52);
    await page.mouse.down();
    await page.mouse.move(surfaceBounds.x + surfaceBounds.width * 0.61, surfaceBounds.y + surfaceBounds.height * 0.43, { steps: 8 });
    await page.mouse.up();
    await page.waitForFunction(original => {
      const plot = document.querySelector("#meshSurface");
      const camera = plot && plot.layout && plot.layout.scene && plot.layout.scene.camera;
      return !!camera && ["x", "y", "z"].some(axis => Math.abs(Number(camera.eye[axis]) - Number(original.eye[axis])) > 1e-4);
    }, surfaceBefore.camera, { timeout: 15000 });
    const draggedCamera = await surfacePlot.evaluate(el => el.layout.scene.camera);
    assert.notDeepEqual(draggedCamera, surfaceBefore.camera, "mouse drag must rotate the interactive surface camera");
    await page.locator("#meshResetCamera").click();
    await page.waitForFunction(original => {
      const camera = document.querySelector("#meshSurface")?.layout?.scene?.camera;
      return !!camera && ["x", "y", "z"].every(axis => Math.abs(Number(camera.eye[axis]) - Number(original.eye[axis])) < 1e-3);
    }, surfaceBefore.camera, { timeout: 10000 });
    await page.locator("#meshExaggeration").selectOption("3");
    await page.waitForFunction(() => Math.abs(Number(document.querySelector("#meshSurface")?.layout?.scene?.aspectratio?.z) - 0.9) < 1e-6, null, { timeout: 15000 });
    const exaggeratedSurface = await surfacePlot.evaluate(el => {
      const trace = el.data.find(item => item.type === "surface");
      return { z: trace.z, customdata: trace.customdata, aspectRatioZ: el.layout.scene.aspectratio.z };
    });
    assert.deepEqual(exaggeratedSurface.z, surfaceBefore.z, "vertical exaggeration must not change source-derived surface Z values");
    assert.deepEqual(exaggeratedSurface.customdata, surfaceBefore.customdata, "vertical exaggeration must not change source mean/uncertainty hover data");
    assert.ok(Math.abs(Number(exaggeratedSurface.aspectRatioZ) - 0.9) < 1e-6, "3× exaggeration may change scene aspect ratio only");
    await page.locator("#meshExaggeration").selectOption("1");
    await page.waitForFunction(() => Math.abs(Number(document.querySelector("#meshSurface")?.layout?.scene?.aspectratio?.z) - 0.3) < 1e-6, null, { timeout: 15000 });

    await page.locator("#axial3dPanel").scrollIntoViewIfNeeded();
    await page.waitForFunction(() => {
      const plot = document.querySelector("#axial3dPlot");
      return plot && Array.isArray(plot.data) && plot.data.some(trace => trace.type === "volume");
    }, null, { timeout: 120000 });
    const axial = await page.evaluate(() => {
      const plot = document.querySelector("#axial3dPlot");
      const volume = plot.data.find(trace => trace.type === "volume");
      const sampleIndices = [[0, 0, 0], [15, 25, 25], [29, 50, 50]];
      return {
        status: document.querySelector("#axial3dStatus").textContent,
        metrics: document.querySelector("#axial3dKpis").innerText,
        provenance: document.querySelector("#axial3dProvenance").textContent,
        summary: document.querySelector("#axial3dSummary").textContent,
        view: document.querySelector("#axial3dView").value,
        pointCount: volume.x.length,
        points: sampleIndices.map(([k, j, i]) => {
          const index = (k * 51 + j) * 51 + i;
          return {
            x: volume.x[index], y: volume.y[index], z: volume.z[index],
            value: volume.value[index], customdata: volume.customdata[index]
          };
        })
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
    assert.equal(api.axial.score, "flux");
    assert.match(axial.provenance, new RegExp("NPZ SHA-256 " + api.axial.provenance.npz_sha256));
    assert.match(axial.provenance, new RegExp("statepoint SHA-256 " + api.axial.provenance.statepoint_sha256));
    const expectedAxisSamples = api.axial.mesh.axis_samples;
    for (let i = 0; i < axial.points.length; i++) {
      const actual = axial.points[i], source = api.axial.samples[i];
      assert.equal(Number(actual.x), Number(source.x), "3D voxel X must match recorded physical coordinate");
      assert.equal(Number(actual.y), Number(source.y), "3D voxel Y must match recorded physical coordinate");
      assert.equal(Number(actual.z), Number(source.z), "3D voxel Z must match recorded physical coordinate");
      assert.equal(Number(actual.customdata[0]), Number(source.mean), "3D hover mean must match source NPZ mean");
      assert.equal(Number(actual.customdata[1]), Number(source.standard_error), "3D hover error must match source NPZ uncertainty");
      assert.equal(Number(actual.customdata[2]), Number(source.relative_error_percent), "3D hover relative error must match source NPZ uncertainty");
      if (Number(source.mean) > 0 && Number.isFinite(Number(source.mean)) && axial.view !== "relative_error") {
        assert.ok(Math.abs(Number(actual.value) - Math.log10(Number(source.mean))) < 1e-12, "3D volume scalar must be derived from the recorded mean");
      } else if (axial.view === "relative_error" && Number.isFinite(Number(source.relative_error_percent))) {
        assert.equal(Number(actual.value), Number(source.relative_error_percent), "relative-error volume must use recorded relative uncertainty");
      }
    }
    assert.ok(expectedAxisSamples.x[0] < expectedAxisSamples.x[1] && expectedAxisSamples.x[1] < expectedAxisSamples.x[2]);
    assert.ok(expectedAxisSamples.y[0] < expectedAxisSamples.y[1] && expectedAxisSamples.y[1] < expectedAxisSamples.y[2]);
    assert.ok(expectedAxisSamples.z[0] < expectedAxisSamples.z[1] && expectedAxisSamples.z[1] < expectedAxisSamples.z[2]);
    await page.locator("#axial3dPanel").screenshot({ path: path.join(outDir, "axial-3d-volume-desktop.png") });

    const desktop = await page.evaluate(() => ({
      viewport: window.innerWidth,
      documentWidth: document.documentElement.scrollWidth,
      bodyWidth: document.body.scrollWidth,
      charts: [...document.querySelectorAll(".js-spatial-plot, #candidateChart, #distributionChart, #assemblyMap, #assemblyMatrix")]
        .filter(el => el.getClientRects().length)
        .map(el => { const r = el.getBoundingClientRect(); return { id: el.id || el.className, right: r.right, width: r.width }; }),
      layoutBlocks: [...document.querySelectorAll(".panel-head, .section-head, .field-controls, .topbar, .renderer-stack-strip")]
        .filter(el => el.getClientRects().length)
        .map(el => ({ className: el.className, clientWidth: el.clientWidth, scrollWidth: el.scrollWidth }))
    }));
    assert.ok(desktop.documentWidth <= desktop.viewport + 3, "desktop document overflows horizontally: " + JSON.stringify(desktop));
    assert.ok(desktop.bodyWidth <= desktop.viewport + 3, "desktop body overflows horizontally");
    for (const plot of desktop.charts) {
      assert.ok(plot.width <= desktop.viewport + 3, "desktop " + plot.id + " is wider than viewport");
      assert.ok(plot.right <= desktop.viewport + 5, "desktop " + plot.id + " extends beyond viewport edge");
    }
    for (const block of desktop.layoutBlocks) {
      assert.ok(block.scrollWidth <= block.clientWidth + 4, "desktop labels/controls overflow their panel: " + JSON.stringify(block));
    }

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
      }),
      layoutBlocks: [...document.querySelectorAll(".panel-head, .section-head, .field-controls, .topbar, .renderer-stack-strip")]
        .filter(el => el.getClientRects().length)
        .map(el => ({ className: el.className, clientWidth: el.clientWidth, scrollWidth: el.scrollWidth }))
    }));
    assert.ok(mobile.documentWidth <= mobile.viewport + 3, "document overflows horizontally on mobile: " + JSON.stringify(mobile));
    assert.ok(mobile.bodyWidth <= mobile.viewport + 3, "body overflows horizontally on mobile");
    for (const plot of mobile.charts) {
      assert.ok(plot.width <= mobile.viewport + 3, plot.id + " is wider than viewport");
      assert.ok(plot.right <= mobile.viewport + 5, plot.id + " extends beyond the right viewport edge");
    }
    for (const block of mobile.layoutBlocks) {
      assert.ok(block.scrollWidth <= block.clientWidth + 4, "mobile labels/controls overflow their panel: " + JSON.stringify(block));
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
      candidate_chart_values_match_source: true,
      paper_png_and_json_sidecar_export_passed: true,
      spatial_field_values_match_source: true,
      spatial_coordinates_match_recorded_mesh: true,
      spatial_hash_status: api.mesh.provenance.hash_matches === true ? "verified" : api.mesh.provenance.hash_matches === false ? "mismatch" : "not-checked",
      surface_camera_drag_and_reset_passed: true,
      exaggeration_preserves_source_surface_values: true,
      desktop: desktop,
      axial_voxel_hover_and_coordinates_match_source: true,
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
