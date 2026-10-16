"use strict";

const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("playwright");

const BASE_URL = process.env.CBPFR_BASE_URL || "http://127.0.0.1:8765";
const OUTPUT_DIR = path.join(process.cwd(), "artifacts", "visual-qa");
fs.mkdirSync(OUTPUT_DIR, { recursive: true });

async function waitForRegistry(page) {
  await page.waitForFunction(() => {
    const status = document.querySelector("#ecrStatus")?.textContent || "";
    return status.includes("REGISTRY READY") || status.includes("REGISTRY UNAVAILABLE");
  }, { timeout: 30000 });
  const status = await page.locator("#ecrStatus").innerText();
  assert.match(status, /REGISTRY READY/, "Evidence Control Room API must load: " + status);
  await page.waitForFunction(() => document.querySelectorAll("#ecrRecordList [data-ecr-id]").length >= 6, { timeout: 10000 });
}
async function waitForCandidate(page) {
  await page.waitForFunction(() => {
    const select = document.querySelector("#candidateSelect");
    return select && select.options.length === 6 && select.value;
  }, { timeout: 30000 });
  try {
    await page.waitForSelector("#selectedCandidateMetrics .candidate-stat", { timeout: 20000 });
  } catch (error) {
    const diagnostic = await page.evaluate(() => ({
      candidateOptions: document.querySelector("#candidateSelect")?.options.length || 0,
      selectedValue: document.querySelector("#candidateSelect")?.value || "",
      selectedId: document.querySelector("#selectedCandidateId")?.textContent || "",
      metricText: document.querySelector("#selectedCandidateMetrics")?.innerText || "",
      apiError: document.querySelector("#apiError")?.innerText || "",
      sourcePath: document.querySelector("#sourcePath")?.textContent || "",
      geometryStatus: document.querySelector("#geometryStatus")?.textContent || "",
      meshStatus: document.querySelector("#meshStatus")?.textContent || ""
    }));
    throw new Error("Candidate metrics failed to remain rendered: " + JSON.stringify(diagnostic) + " · " + error.message);
  }
}
async function waitForSpatial(page) {
  await page.locator("#spatial").scrollIntoViewIfNeeded();
  for (const selector of [
    "#meshHeatmap.js-plotly-plot",
    "#meshContour.js-plotly-plot",
    "#meshProfile.js-plotly-plot",
    "#meshSurface.js-plotly-plot"
  ]) {
    await page.waitForSelector(selector, { timeout: 45000 });
  }
  const status=await page.locator("#meshStatus").innerText();
  assert.doesNotMatch(status, /UNAVAILABLE|FAILED|MISSING/i, "Planar tally data/API should be available: "+status);
}
async function waitForAxialVolume(page) {
  await page.locator("#axial3dPanel").scrollIntoViewIfNeeded();
  await page.waitForFunction(() => {
    const node = document.querySelector("#axial3dPlot");
    return Boolean(node && Array.isArray(node.data) && node.data.some(trace => trace.type === "volume"));
  }, { timeout: 60000 });
}
async function assertNoOverflow(page, viewportName) {
  const result=await page.evaluate(() => ({
    viewport:window.innerWidth,
    document:document.documentElement.scrollWidth,
    body:document.body.scrollWidth
  }));
  assert.ok(result.document <= result.viewport + 1, viewportName+" horizontal overflow: "+JSON.stringify(result));
  return result;
}
async function main() {
  const browser=await chromium.launch({
    headless:true,
    args:["--no-sandbox","--enable-webgl","--ignore-gpu-blocklist","--use-gl=angle","--use-angle=swiftshader"]
  });
  const uncaught=[];
  const results={baseUrl:BASE_URL,checks:[],screenshots:[]};
  try {
    const page=await browser.newPage({viewport:{width:1440,height:1000},deviceScaleFactor:1});
    page.on("pageerror",error=>{uncaught.push(error.message);console.error("DESKTOP PAGE ERROR:",error.message);});
    const response=await page.goto(BASE_URL,{waitUntil:"domcontentloaded",timeout:30000});
    assert.ok(response && response.ok(),"HTML must load over local API server");
    await waitForCandidate(page);
    results.checks.push("six recorded candidate layouts load");
    await waitForRegistry(page);
    const registry=await page.evaluate(async()=>{
      const response=await fetch("/api/evidence-registry",{cache:"no-store"});
      return {ok:response.ok,body:await response.json()};
    });
    assert.ok(registry.ok,"Evidence registry endpoint should return HTTP 200");
    assert.equal(registry.body.records.length,6,"Registry should list six independently scoped evidence groups");
    assert.equal(registry.body.summary.campaign_observed_runs,1200);
    assert.equal(registry.body.summary.high_budget_reference_runs,60);
    assert.equal(registry.body.summary.convergence_certified_runs,0);
    assert.match(registry.body.records.find(x=>x.id==="axial-volume").status,/HASH MATCH/);
    results.checks.push("registry shows six source groups, 1,200 + 60 campaign counts, and uncertified convergence");

    await page.locator("#coreView3d").click();
    await page.waitForSelector("#core3dCanvas canvas.core3d-canvas",{timeout:45000});
    const coreStatus=await page.locator("#core3dStatus").innerText();
    assert.doesNotMatch(coreStatus,/FAILED|UNAVAILABLE/i,"Three.js renderer must initialize: "+coreStatus);
    await page.locator("#core3dViewport").scrollIntoViewIfNeeded();
    await page.locator("#core3dViewport").screenshot({path:path.join(OUTPUT_DIR,"desktop-core-geometry-3d.png"),animations:"disabled"});
    results.screenshots.push("desktop-core-geometry-3d.png");
    await page.locator("#coreView2d").click();
    await page.waitForSelector("#geometryPreview svg.model-geometry-svg",{timeout:20000});
    await page.locator("#geometryPreview").screenshot({path:path.join(OUTPUT_DIR,"desktop-core-geometry-source-map.png"),animations:"disabled"});
    await page.locator("#coreView3d").click();
    await page.waitForSelector("#core3dCanvas canvas.core3d-canvas",{timeout:15000});
    results.checks.push("interactive 3D core renderer and inspectable 2D source-map fallback both render");

    await waitForSpatial(page);
    await page.locator("#spatial").screenshot({path:path.join(OUTPUT_DIR,"desktop-spatial-field-lab.png"),animations:"disabled"});
    results.screenshots.push("desktop-spatial-field-lab.png");
    results.checks.push("planar heatmap, contour, profile, and 3D surface render from recorded tally");

    await waitForAxialVolume(page);
    const axialInfo=await page.evaluate(()=>{
      const node=document.querySelector("#axial3dPlot");
      const volume=node.data.find(trace=>trace.type==="volume");
      return {traces:node.data.map(trace=>trace.type),x:volume.x?.length||0,mean:volume.value?.length||0};
    });
    assert.ok(axialInfo.traces.includes("volume"),"Axial viewer must contain a real Plotly volume trace");
    assert.ok(axialInfo.mean>=78030,"Axial volume should contain all 51×51×30 recorded bins");
    await page.locator("#axial3dPanel").screenshot({path:path.join(OUTPUT_DIR,"desktop-axial-3d-volume.png"),animations:"disabled"});
    results.screenshots.push("desktop-axial-3d-volume.png");
    results.checks.push("axial view contains a recorded 51×51×30 volume trace");

    await page.locator("#evidence-control-room").scrollIntoViewIfNeeded();
    await waitForRegistry(page);
    await page.locator("#evidence-control-room").screenshot({path:path.join(OUTPUT_DIR,"desktop-evidence-control-room.png"),animations:"disabled"});
    results.screenshots.push("desktop-evidence-control-room.png");
    await page.locator("#ecrSearch").fill("seed 640000");
    assert.equal(await page.locator("#ecrRecordList [data-ecr-id]").count(),1,"Search should find the single axial source record for seed 640000");
    await page.locator("#ecrSearch").fill("");
    await page.locator("#ecrFilter").selectOption("synthetic");
    assert.equal(await page.locator("#ecrRecordList [data-ecr-id]").count(),1,"Evidence class filter should isolate synthetic study");
    await page.locator("#ecrRecordList [data-ecr-id='synthetic-paper']").click();
    await page.waitForFunction(()=>document.querySelector("#ecrDetail")?.innerText.includes("SYNTHETIC METHOD"));
    assert.ok((await page.locator("#ecrDetail").innerText()).includes("has not been independently replicated"));
    await page.locator("#ecrFilter").selectOption("all");
    results.checks.push("Evidence Control Room search, class filter, source details and limits work");
    results.desktopOverflow=await assertNoOverflow(page,"desktop");
    await page.screenshot({path:path.join(OUTPUT_DIR,"desktop-workstation-overview.png"),fullPage:false,animations:"disabled"});
    results.screenshots.push("desktop-workstation-overview.png");

    const mobile=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1});
    mobile.on("pageerror",error=>{uncaught.push("mobile: "+error.message);console.error("MOBILE PAGE ERROR:",error.message);});
    const mobileResponse=await mobile.goto(BASE_URL,{waitUntil:"domcontentloaded",timeout:30000});
    assert.ok(mobileResponse && mobileResponse.ok(),"mobile HTML must load");
    await waitForCandidate(mobile);
    await waitForRegistry(mobile);
    await mobile.locator("#coreView3d").click();
    await mobile.waitForSelector("#core3dCanvas canvas.core3d-canvas",{timeout:45000});
    await mobile.locator("#evidence-control-room").scrollIntoViewIfNeeded();
    await waitForRegistry(mobile);
    await mobile.locator("#evidence-control-room").screenshot({path:path.join(OUTPUT_DIR,"mobile-evidence-control-room.png"),animations:"disabled"});
    results.screenshots.push("mobile-evidence-control-room.png");
    results.mobileOverflow=await assertNoOverflow(mobile,"mobile");
    assert.ok(await mobile.locator("#ecrSearch").isVisible(),"Evidence search should stay visible on mobile");
    results.checks.push("mobile candidate inspector, interactive 3D core and evidence registry remain accessible");
    assert.deepEqual(uncaught,[],"No uncaught JavaScript exceptions");
    results.uncaughtJavaScriptErrors=uncaught;
    results.result="passed";
    fs.writeFileSync(path.join(OUTPUT_DIR,"visual-qa-report.json"),JSON.stringify(results,null,2)+"\n");
    process.stdout.write(JSON.stringify(results,null,2)+"\n");
    await mobile.close();
    await page.close();
  } finally {
    await browser.close();
  }
}
main().catch(error=>{console.error(error);process.exitCode=1;});
