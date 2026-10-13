import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

export const version = "0.180.0";
const PIN_COLORS = {
  "1": "#51d2df", "2": "#f4bd62", "3": "#f08f62",
  "4": "#dc6f91", "5": "#c1b3ff", "6": "#9cb6c8"
};
const CODE_COLORS = { U: "#51d2df", M: "#f4bd62", R: "#47768a" };

function releaseObjectResources(root) {
  const geometries = new Set(), materials = new Set(), textures = new Set();
  root.traverse(object => {
    if (object.geometry) geometries.add(object.geometry);
    const list = Array.isArray(object.material) ? object.material : object.material ? [object.material] : [];
    list.forEach(material => {
      materials.add(material);
      Object.values(material).forEach(value => {
        if (value && value.isTexture) textures.add(value);
      });
    });
  });
  geometries.forEach(value => value.dispose());
  materials.forEach(value => value.dispose());
  textures.forEach(value => value.dispose());
  root.clear();
}

function makeLabel(text, color = "#e8f1f7", background = "rgba(7,17,27,0.82)") {
  const canvas = document.createElement("canvas");
  canvas.width = 512;
  canvas.height = 128;
  const context = canvas.getContext("2d");
  context.clearRect(0, 0, canvas.width, canvas.height);
  context.fillStyle = background;
  context.beginPath();
  context.roundRect(3, 8, 506, 112, 20);
  context.fill();
  context.strokeStyle = color;
  context.globalAlpha = 0.55;
  context.lineWidth = 2;
  context.stroke();
  context.globalAlpha = 1;
  context.fillStyle = color;
  context.font = "600 38px Arial, sans-serif";
  context.textAlign = "center";
  context.textBaseline = "middle";
  context.fillText(text, 256, 65, 470);
  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  const material = new THREE.SpriteMaterial({ map: texture, transparent: true, depthWrite: false });
  const sprite = new THREE.Sprite(material);
  sprite.scale.set(8.2, 2.05, 1);
  return sprite;
}

function safeDispose(material) {
  if (!material) return;
  if (Array.isArray(material)) material.forEach(safeDispose);
  else {
    Object.values(material).forEach(value => {
      if (value && value.isTexture) value.dispose();
    });
    material.dispose();
  }
}

export function createCoreViewer(container, onAssemblySelect) {
  if (!container) throw new Error("Core 3D viewport element was not found.");
  const scene = new THREE.Scene();
  scene.background = new THREE.Color("#07131e");
  scene.fog = new THREE.Fog("#07131e", 100, 190);

  const camera = new THREE.PerspectiveCamera(37, 1, 0.1, 500);
  camera.position.set(72, 65, 88);
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "high-performance" });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.8));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.12;
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.domElement.className = "core3d-canvas";
  renderer.domElement.setAttribute("role", "img");
  renderer.domElement.setAttribute("aria-label", "Interactive Three.js rendering of the archived C5G7 OpenMC core lattice");
  container.replaceChildren(renderer.domElement);

  scene.add(new THREE.HemisphereLight("#c7ecff", "#102230", 2.0));
  const keyLight = new THREE.DirectionalLight("#ffffff", 3.0);
  keyLight.position.set(-36, 70, 48);
  keyLight.castShadow = true;
  keyLight.shadow.mapSize.set(1024, 1024);
  scene.add(keyLight);
  const fillLight = new THREE.DirectionalLight("#55d4df", 1.15);
  fillLight.position.set(42, 34, -42);
  scene.add(fillLight);
  const rimLight = new THREE.PointLight("#f4bd62", 70, 150, 1.8);
  rimLight.position.set(0, 25, 38);
  scene.add(rimLight);

  const world = new THREE.Group();
  scene.add(world);
  const model = new THREE.Group();
  world.add(model);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.075;
  controls.enablePan = true;
  controls.minDistance = 32;
  controls.maxDistance = 150;
  controls.minPolarAngle = 0.2;
  controls.maxPolarAngle = 1.49;
  controls.target.set(0, 0, 0);

  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();
  let modelManifest = null;
  let candidateRow = null;
  let selectedCell = { row: 0, col: 0 };
  let clickStart = null;
  let resizeObserver = null;
  let animationFrame = 0;
  let disposed = false;
  let lastInfo = null;
  let selectedOutline = null;
  const selectable = [];
  let pinMeshes = [];
  let assemblyIndex = {};

  function resize() {
    if (disposed) return;
    const rect = container.getBoundingClientRect();
    const width = Math.max(1, Math.round(rect.width));
    const height = Math.max(1, Math.round(rect.height || 520));
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height, false);
  }

  function animate() {
    if (disposed) return;
    animationFrame = window.requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }

  function addLine(points, color, opacity = 1) {
    const geometry = new THREE.BufferGeometry().setFromPoints(points.map(point => new THREE.Vector3(...point)));
    const material = new THREE.LineBasicMaterial({ color, transparent: opacity < 1, opacity });
    const line = new THREE.Line(geometry, material);
    model.add(line);
    return line;
  }

  function addBoundaryLabel(text, x, z, color) {
    const sprite = makeLabel(text, color, "rgba(7,19,30,0.93)");
    sprite.position.set(x, 0.18, z);
    sprite.scale.set(10.3, 2.55, 1);
    model.add(sprite);
  }

  function addSelectionOutline(row, col, pitch) {
    if (selectedOutline) {
      model.remove(selectedOutline);
      safeDispose(selectedOutline.material);
      selectedOutline.geometry.dispose();
      selectedOutline = null;
    }
    const center = assemblyIndex[row + "," + col];
    if (!center) return;
    const shape = new THREE.Shape();
    const half = pitch * 0.47;
    shape.moveTo(-half, -half);
    shape.lineTo(half, -half);
    shape.lineTo(half, half);
    shape.lineTo(-half, half);
    shape.lineTo(-half, -half);
    const points = shape.getPoints(4).map(point => new THREE.Vector3(center.x + point.x, 2.35, center.z + point.y));
    const geometry = new THREE.BufferGeometry().setFromPoints(points);
    const material = new THREE.LineBasicMaterial({ color: "#ffffff", transparent: true, opacity: 0.96 });
    selectedOutline = new THREE.Line(geometry, material);
    selectedOutline.renderOrder = 10;
    model.add(selectedOutline);
  }

  function update(manifest, row, focusCell = selectedCell) {
    if (!manifest || !row) throw new Error("The source geometry manifest and selected candidate are required.");
    const signature = String(row.layout_signature || "").trim().toUpperCase();
    if (!/^[UM]{4}$/.test(signature) || (signature.match(/M/g) || []).length !== 2 || (signature.match(/U/g) || []).length !== 2) {
      throw new Error("The selected candidate does not contain exactly two MOX and two UO₂ positions.");
    }
    const source = (manifest.candidates || []).find(item =>
      String(item.candidate_id) === String(row.candidate_id) &&
      String(item.layout_signature || "").toUpperCase() === signature
    );
    if (!source || source.source_matches_candidate_signature !== true || source.signature_derived_from_xml !== signature) {
      throw new Error("The exact candidate/signature pair did not pass the source geometry identity check.");
    }

    releaseObjectResources(model);
    selectable.length = 0;
    pinMeshes = [];
    assemblyIndex = {};
    selectedOutline = null;
    modelManifest = manifest;
    candidateRow = row;

    const core = manifest.core_lattice || {};
    const dims = core.dimensions || [];
    const lower = core.lower_left_cm || [];
    const pitchValues = core.pitch_cm || [];
    const grid = source.core_universe_grid || [];
    const codeGrid = source.assembly_grid || [];
    const cols = Number(dims[0]), rows = Number(dims[1]);
    const pitchX = Number(pitchValues[0]), pitchZ = Number(pitchValues[1]);
    if (cols !== 3 || rows !== 3 || grid.length !== rows || grid.some(line => !Array.isArray(line) || line.length !== cols)) {
      throw new Error("The source model does not contain the declared 3 × 3 core lattice.");
    }
    const assemblyMap = manifest.assemblies || {};
    const pinDims = manifest.pin_geometry?.dimensions || [];
    const pinPitch = Number(manifest.pin_geometry?.pitch_cm?.[0]);
    const pinRadius = Number(manifest.pin_geometry?.pin_radius_cm);
    const pinLower = manifest.pin_geometry?.lower_left_cm || [];
    if (pinDims[0] !== 17 || pinDims[1] !== 17 || !Number.isFinite(pinPitch) || !Number.isFinite(pinRadius)) {
      throw new Error("The archived pin geometry does not match the declared 17 × 17 lattice metadata.");
    }

    const width = cols * pitchX;
    const depth = rows * pitchZ;
    const leftX = Number(lower[0]);
    const bottomY = Number(lower[1]);
    if (![width, depth, leftX, bottomY].every(Number.isFinite) || pitchX <= 0 || pitchZ <= 0) {
      throw new Error("The source core bounds or assembly pitches are invalid.");
    }

    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(width + 26, depth + 26),
      new THREE.MeshStandardMaterial({ color: "#091925", metalness: 0.3, roughness: 0.92 })
    );
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = -0.95;
    floor.receiveShadow = true;
    model.add(floor);

    const gridHelper = new THREE.GridHelper(Math.max(width, depth) + 20, 22, "#2c6075", "#18384a");
    gridHelper.position.y = -0.9;
    gridHelper.material.transparent = true;
    gridHelper.material.opacity = 0.32;
    model.add(gridHelper);

    const baseMaterials = {
      M: new THREE.MeshStandardMaterial({ color: "#704d2d", metalness: 0.35, roughness: 0.45 }),
      U: new THREE.MeshStandardMaterial({ color: "#174657", metalness: 0.34, roughness: 0.42 }),
      R: new THREE.MeshStandardMaterial({ color: "#0d2b3a", metalness: 0.5, roughness: 0.34 })
    };
    const baseGeometry = new THREE.BoxGeometry(pitchX * 0.985, 0.48, pitchZ * 0.985);
    const reflectorTopGeometry = new THREE.BoxGeometry(pitchX * 0.97, 0.16, pitchZ * 0.97);
    const pinGeometry = new THREE.CylinderGeometry(pinRadius * 0.79, pinRadius * 0.79, 1.25, 10, 1);
    const pinMaterialPool = {};
    Object.entries(PIN_COLORS).forEach(([universe, color]) => {
      pinMaterialPool[universe] = new THREE.MeshStandardMaterial({
        color, metalness: 0.28, roughness: 0.42, emissive: color, emissiveIntensity: 0.07
      });
    });

    let fuelAssemblyCount = 0, reflectorCount = 0, renderedPinCount = 0;
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const universeId = String(grid[r][c]);
        const sourceAssembly = assemblyMap[universeId];
        const code = String(codeGrid[r]?.[c] || sourceAssembly?.code || "");
        if (!sourceAssembly || !["U", "M", "R"].includes(code)) throw new Error("Unknown core-lattice universe " + universeId + ".");
        const x = leftX + (c + 0.5) * pitchX;
        const yCoordinate = bottomY + (rows - r - 0.5) * pitchZ;
        const z = yCoordinate;
        const positionKey = r + "," + c;
        const position = "p" + r + c;
        assemblyIndex[positionKey] = { x, z, code, universeId, position, latticeId: sourceAssembly.lattice_id };
        const base = new THREE.Mesh(baseGeometry, baseMaterials[code]);
        base.position.set(x, -0.13, z);
        base.castShadow = true;
        base.receiveShadow = true;
        model.add(base);

        if (code === "R") {
          reflectorCount++;
          const top = new THREE.Mesh(
            reflectorTopGeometry,
            new THREE.MeshStandardMaterial({ color: "#17495d", metalness: 0.42, roughness: 0.38, emissive: "#0a2a38", emissiveIntensity: 0.5 })
          );
          top.position.set(x, 0.19, z);
          top.castShadow = true;
          top.receiveShadow = true;
          model.add(top);
          const wavePoints = [];
          for (let line = -8; line <= 8; line += 2) {
            const offset = line * 1.08;
            wavePoints.push([x - pitchX * 0.34, 0.29, z + offset], [x + pitchX * 0.34, 0.29, z + offset]);
            wavePoints.push([x + offset, 0.29, z - pitchZ * 0.34], [x + offset, 0.29, z + pitchZ * 0.34]);
          }
          for (let i = 0; i < wavePoints.length; i += 2) addLine([wavePoints[i], wavePoints[i + 1]], "#347b91", 0.58);
          const label = makeLabel("REFLECTOR · " + position, "#9bd8eb");
          label.position.set(x, 1.7, z);
          label.scale.set(9.6, 2.4, 1);
          model.add(label);
        } else {
          fuelAssemblyCount++;
          const materialTop = new THREE.Mesh(
            reflectorTopGeometry,
            new THREE.MeshStandardMaterial({ color: code === "M" ? "#b78042" : "#32869a", metalness: 0.32, roughness: 0.4, emissive: code === "M" ? "#643c20" : "#103946", emissiveIntensity: 0.28 })
          );
          materialTop.position.set(x, 0.18, z);
          materialTop.receiveShadow = true;
          model.add(materialTop);

          const lattice = manifest.pin_lattices?.[String(sourceAssembly.lattice_id)]?.universe_grid;
          if (!Array.isArray(lattice) || lattice.length !== pinDims[1] || lattice.some(line => !Array.isArray(line) || line.length !== pinDims[0])) {
            throw new Error("Pin lattice " + sourceAssembly.lattice_id + " is missing or does not match 17 × 17.");
          }
          const matrices = {};
          const counts = {};
          Object.keys(PIN_COLORS).forEach(universe => { matrices[universe] = []; counts[universe] = 0; });
          for (let pr = 0; pr < pinDims[1]; pr++) {
            for (let pc = 0; pc < pinDims[0]; pc++) {
              const pinUniverse = String(lattice[pr][pc]);
              if (!PIN_COLORS[pinUniverse]) throw new Error("Unmapped pin universe " + pinUniverse + " in source lattice.");
              const px = x + Number(pinLower[0] || -pinPitch * pinDims[0] / 2) + (pc + 0.5) * pinPitch;
              const pz = z + (pinDims[1] / 2 - pr - 0.5) * pinPitch;
              const matrix = new THREE.Matrix4().compose(
                new THREE.Vector3(px, 0.86, pz),
                new THREE.Quaternion(),
                new THREE.Vector3(1, 1, 1)
              );
              matrices[pinUniverse].push(matrix);
              counts[pinUniverse]++;
            }
          }
          Object.keys(matrices).forEach(universe => {
            if (!counts[universe]) return;
            const instances = new THREE.InstancedMesh(pinGeometry, pinMaterialPool[universe], counts[universe]);
            instances.castShadow = true;
            instances.receiveShadow = true;
            instances.userData.coreCell = { row: r, col: c, position, code, universeId, latticeId: sourceAssembly.lattice_id };
            matrices[universe].forEach((matrix, index) => instances.setMatrixAt(index, matrix));
            instances.instanceMatrix.needsUpdate = true;
            pinMeshes.push(instances);
            model.add(instances);
            renderedPinCount += counts[universe];
          });
          const fuelLabel = makeLabel((code === "M" ? "MOX" : "UO₂") + " · " + position, code === "M" ? "#f4bd62" : "#70e6f2");
          fuelLabel.position.set(x, 2.0, z);
          model.add(fuelLabel);
        }

        const clickTarget = new THREE.Mesh(
          new THREE.BoxGeometry(pitchX * 0.91, 0.04, pitchZ * 0.91),
          new THREE.MeshBasicMaterial({ transparent: true, opacity: 0, colorWrite: false, depthWrite: false, side: THREE.DoubleSide })
        );
        clickTarget.position.set(x, 1.63, z);
        clickTarget.userData.coreCell = { row: r, col: c, position, code, universeId, latticeId: sourceAssembly.lattice_id };
        model.add(clickTarget);
        selectable.push(clickTarget);
      }
    }

    const xMin = leftX, xMax = leftX + width, zMin = bottomY, zMax = bottomY + depth;
    addLine([[xMin, 0.01, zMin], [xMax, 0.01, zMin]], "#f4bd62");
    addLine([[xMin, 0.01, zMax], [xMax, 0.01, zMax]], "#55d4df");
    addLine([[xMin, 0.01, zMin], [xMin, 0.01, zMax]], "#55d4df");
    addLine([[xMax, 0.01, zMin], [xMax, 0.01, zMax]], "#f4bd62");
    addBoundaryLabel("Y− VACUUM", 0, zMin - 6.5, "#f4bd62");
    addBoundaryLabel("Y+ REFLECTIVE", 0, zMax + 6.5, "#55d4df");
    addBoundaryLabel("X− REFLECTIVE", xMin - 7.6, 0, "#55d4df");
    addBoundaryLabel("X+ VACUUM", xMax + 7.6, 0, "#f4bd62");

    const originLabel = makeLabel("C5G7 · 3×3 CORE · " + signature, "#e8f1f7", "rgba(7,19,30,0.92)");
    originLabel.position.set(0, 5.0, zMax + 12.3);
    originLabel.scale.set(18, 4.5, 1);
    model.add(originLabel);
    const extrusionLabel = makeLabel("DISPLAY EXTRUSION ONLY · NO AXIAL DIMENSION IN SOURCE", "#f4bd62", "rgba(42,27,18,0.93)");
    extrusionLabel.position.set(0, -0.85, zMin - 13.2);
    extrusionLabel.scale.set(26, 6.3, 1);
    model.add(extrusionLabel);

    const safeRow = Math.max(0, Math.min(rows - 1, Number(focusCell?.row ?? 0)));
    const safeCol = Math.max(0, Math.min(cols - 1, Number(focusCell?.col ?? 0)));
    selectedCell = { row: safeRow, col: safeCol };
    lastInfo = {
      candidateId: String(row.candidate_id),
      layoutSignature: signature,
      sourceMember: source.source_member,
      geometryXmlSha256: source.geometry_xml_sha256,
      coreDimensions: [cols, rows],
      corePitchCm: [pitchX, pitchZ],
      coreLowerLeftCm: [leftX, bottomY],
      fuelAssemblyCount,
      reflectorCount,
      pinCount: renderedPinCount,
      universeIdGrid: grid,
      assemblyCodeGrid: codeGrid,
      libraryVersion: version
    };
    addSelectionOutline(safeRow, safeCol, Math.max(pitchX, pitchZ));
    resize();
    return { ...lastInfo };
  }

  function selectFromPointer(event) {
    if (!clickStart || Math.hypot(event.clientX - clickStart.x, event.clientY - clickStart.y) > 5) return;
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects(selectable, false);
    const hit = hits[0]?.object;
    if (!hit?.userData?.coreCell) return;
    selectedCell = { row: hit.userData.coreCell.row, col: hit.userData.coreCell.col };
    addSelectionOutline(selectedCell.row, selectedCell.col, Math.max(...(modelManifest?.core_lattice?.pitch_cm || [21.42, 21.42])));
    onAssemblySelect?.({ ...hit.userData.coreCell });
  }

  renderer.domElement.addEventListener("pointerdown", event => { clickStart = { x: event.clientX, y: event.clientY }; });
  renderer.domElement.addEventListener("pointerup", selectFromPointer);
  renderer.domElement.addEventListener("pointercancel", () => { clickStart = null; });
  renderer.domElement.addEventListener("pointerleave", () => { clickStart = null; });
  if ("ResizeObserver" in window) {
    resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(container);
  } else {
    window.addEventListener("resize", resize, { passive: true });
  }
  resize();
  animate();

  return {
    update,
    reset() {
      controls.reset();
      controls.target.set(0, 0, 0);
      camera.position.set(72, 65, 88);
      controls.update();
    },
    highlight(row, col) {
      selectedCell = { row: Number(row), col: Number(col) };
      addSelectionOutline(selectedCell.row, selectedCell.col, Math.max(...(modelManifest?.core_lattice?.pitch_cm || [21.42, 21.42])));
    },
    info() { return lastInfo ? { ...lastInfo } : null; },
    dispose() {
      disposed = true;
      window.cancelAnimationFrame(animationFrame);
      if (resizeObserver) resizeObserver.disconnect();
      else window.removeEventListener("resize", resize);
      controls.dispose();
      releaseObjectResources(model);
      releaseObjectResources(world);
      renderer.dispose();
      container.replaceChildren();
    }
  };
}
