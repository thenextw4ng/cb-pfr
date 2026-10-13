"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const baseUrl = process.env.CBPFR_BASE_URL || "http://127.0.0.1:8765";
const outputDir = path.join(process.cwd(), "artifacts", "axial-3d-browser-qa");
fs.mkdirSync(outputDir, { recursive: true });

(async () => {
  const browser = await chromium.launch({
    headless: true,
    args: [
      "--enable-webgl",
      "--ignore-gpu-blocklist",
      "--use-gl=angle",
      "--use-angle=swiftshader",
      "--enable-unsafe-swiftshader"
    ]
  });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
  const pageErrors = [];
  page.on("pageerror", error => pageErrors.push(error.message));
  try {
    const response = await page.goto(baseUrl + "/#spatial", {
      waitUntil: "domcontentloaded",
      timeout: 30000
    });
    assert.ok(response && response.ok(), "workstation must return HTTP 200");

    const api = await page.evaluate(async () => {
      const response = await fetch("/api/axial-3d?score=flux");
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || "3D API failed");
      return {
        available: payload.available,
        dims: payload.mesh.dimension_xyz,
        score: payload.score,
        zCount: payload.mesh.z_centers_cm.length
      };
    });
    assert.equal(api.available, true);
    assert.deepEqual(api.dims, [51, 51, 30]);
    assert.equal(api.score, "flux");
    assert.equal(api.zCount, 30);

    await page.waitForFunction(() => {
      const el = document.getElementById("axial3dPlot");
      return el && el.data && el.data.some(trace => trace.type === "volume");
    }, null, { timeout: 120000 });

    const initial = await page.evaluate(() => {
      const plot = document.getElementById("axial3dPlot");
      return {
        status: document.getElementById("axial3dStatus").textContent,
        types: plot.data.map(trace => trace.type),
        names: plot.data.map(trace => trace.name),
        zLabel: document.getElementById("axial3dSliceLabel").textContent,
        dims: document.getElementById("axial3dKpis").innerText,
        summary: document.getElementById("axial3dSummary").textContent,
        provenance: document.getElementById("axial3dProvenance").textContent
      };
    });
    assert.match(initial.status, /3D STATEPOINT LOADED|SMOKE DIAGNOSTIC ONLY/);
    if (/SMOKE DIAGNOSTIC ONLY/.test(initial.status)) {
      assert.match(initial.status, /HIGH BINWISE RSE/, "a low-budget run must retain the high-uncertainty warning");
      assert.match(initial.summary, /smoke-profile diagnostic/i, "the summary must explicitly bound smoke data");
      assert.match(initial.provenance, /run class SMOKE DIAGNOSTIC ONLY/, "the provenance panel must identify smoke-only evidence");
    }
    assert.match(initial.dims, /214\.20 cm/, "axial span should report the full recorded Z domain, including half-bin extents");
    assert.match(initial.summary, /median 56\.3%/, "smoke uncertainty should be exposed to the reviewer, not hidden");
    assert.match(initial.provenance, /layout UMMU/, "candidate/layout provenance should be visible with the spatial view");
    assert.ok(initial.types.includes("volume"), "the plot must include a true Plotly 3-D volume trace");
    assert.ok(initial.types.includes("surface"), "the plot must include a separate selected physical Z slice");

    await page.evaluate(() => {
      const slider = document.getElementById("axial3dSlice");
      slider.value = "20";
      slider.dispatchEvent(new Event("input", { bubbles: true }));
    });
    await page.waitForFunction(() => {
      const label = document.getElementById("axial3dSliceLabel").textContent;
      const plot = document.getElementById("axial3dPlot");
      return label.includes("Z bin 20") &&
        plot.data.some(trace => String(trace.name || "").startsWith("Selected axial slice · Z="));
    }, null, { timeout: 30000 });

    await page.locator("#axial3dScore").selectOption("fission");
    await page.waitForFunction(() => {
      const plot = document.getElementById("axial3dPlot");
      return plot && plot.data && plot.data.some(trace => trace.type === "volume");
    }, null, { timeout: 30000 });

    await page.locator("#axial3dPlot").screenshot({
      path: path.join(outputDir, "physical-axial-3d-volume.png"),
      timeout: 30000
    });
    const final = await page.evaluate(() => ({
      score: document.getElementById("axial3dScore").value,
      label: document.getElementById("axial3dSliceLabel").textContent,
      status: document.getElementById("axial3dStatus").textContent,
      traces: document.getElementById("axial3dPlot").data.map(trace => trace.type)
    }));
    assert.equal(final.score, "fission");
    assert.match(final.label, /Z bin 20/);
    assert.match(final.status, /3D STATEPOINT LOADED|SMOKE DIAGNOSTIC ONLY/);
    assert.deepEqual(pageErrors, [], "the axial workstation must not raise browser page errors");

    fs.writeFileSync(
      path.join(outputDir, "axial-3d-browser-qa.json"),
      JSON.stringify({ api, initial, final, page_errors: pageErrors }, null, 2) + "\n"
    );
    console.log("Physical axial 3D browser QA passed:", JSON.stringify({ api, final }));
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
