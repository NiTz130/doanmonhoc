import * as THREE from "./vendor/three/three.module.min.js";

// Decorative only: forms never depend on the GPU or this module loading.
export function createScene(host, toggle) {
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const fallback = host.querySelector(".scene-fallback");
  let renderer = null;
  let world, camera, layers;
  let visible = true, busy = false, paused = false, disposed = false;
  let frame = 0, previous = 0, elapsed = 0;
  const resources = new Set();

  function box(w, h, d, color, x, y, z, parent = layers) {
    const geometry = new THREE.BoxGeometry(w, h, d);
    const material = new THREE.MeshStandardMaterial({color, roughness:0.75, metalness:0.08});
    resources.add(geometry); resources.add(material);
    const mesh = new THREE.Mesh(geometry, material);
    mesh.position.set(x, y, z); parent.add(mesh);
    return mesh;
  }

  function stop() {
    cancelAnimationFrame(frame); frame = 0; previous = 0;
    host.dataset.motion = "stopped";
  }

  function release() {
    stop();
    resizeObserver.disconnect();
    if (renderer) {
      renderer.domElement.removeEventListener("webglcontextlost", lost);
      renderer.dispose();
      renderer.domElement.remove();
      renderer = null;
    }
    resources.forEach(resource => resource.dispose()); resources.clear();
    fallback.hidden = false; toggle.hidden = true;
    host.dataset.scene = "static";
  }

  function lost(event) {
    event.preventDefault();
    release(); // A context loss keeps the stable 2D illustration; no retry loop.
  }

  function resize() {
    if (!renderer || !host.clientWidth || !host.clientHeight) return;
    const width = host.clientWidth, height = host.clientHeight;
    renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 1.5));
    renderer.setSize(width, height, false);
    const aspect = width / height;
    camera.left = -2.35 * aspect; camera.right = 2.35 * aspect;
    camera.top = 2.35; camera.bottom = -2.35; camera.updateProjectionMatrix();
    renderer.render(world, camera);
  }

  function tick(time) {
    if (!renderer) return;
    frame = requestAnimationFrame(tick);
    if (previous && time - previous < 1000 / 30) return;
    elapsed += previous ? Math.min((time - previous) / 1000, 0.1) : 0;
    previous = time;
    layers.rotation.y = -0.32 + Math.sin(elapsed * 0.35) * 0.065;
    layers.position.y = Math.sin(elapsed * 0.55) * 0.055;
    renderer.render(world, camera);
  }

  function sync() {
    if (disposed) return;
    toggle.textContent = paused ? "Bật chuyển động" : "Dừng chuyển động";
    toggle.setAttribute("aria-pressed", String(paused));
    if (!renderer || !visible || busy || paused || document.hidden || reduced.matches) stop();
    else if (!frame) { frame = requestAnimationFrame(tick); host.dataset.motion = "running"; }
  }

  function init() {
    if (renderer || disposed || reduced.matches) return;
    try {
      renderer = new THREE.WebGLRenderer({alpha:true, antialias:true, powerPreference:"low-power"});
      renderer.setClearColor(0x000000, 0);
      world = new THREE.Scene();
      camera = new THREE.OrthographicCamera(-4, 4, 2.35, -2.35, 0.1, 30);
      camera.position.set(0, 0, 10);
      layers = new THREE.Group(); layers.rotation.set(0.2, -0.32, -0.11); world.add(layers);
      world.add(new THREE.AmbientLight(0xffffff, 2));
      const sun = new THREE.DirectionalLight(0xfff3d7, 3); sun.position.set(-3, 6, 7); world.add(sun);
      box(4.2, 2.3, 0.08, 0xd8dec9, 0.40, 0.35, -0.65);
      box(4.2, 2.3, 0.08, 0xa1b493, 0.16, 0.12, -0.15);
      box(4.2, 2.3, 0.13, 0x315d48, -0.14, -0.14, 0.4);
      box(3.86, 1.63, 0.02, 0x284b3b, -0.14, 0.02, 0.48);
      for (const x of [-1.8, -1.25, -0.7, -0.15, 0.4, 0.95, 1.5]) {
        box(0.22, 0.11, 0.02, 0xbbc9a7, x, 0.87, 0.49);
      }
      box(2.65, 0.13, 0.03, 0xf0e8d1, -0.14, -0.56, 0.51);
      box(1.8, 0.10, 0.03, 0xc0cdb3, -0.14, -0.81, 0.51);
      const shape = new THREE.Shape(); shape.moveTo(-0.20, -0.22); shape.lineTo(0.24, 0.04); shape.lineTo(-0.20, 0.30); shape.closePath();
      const geo = new THREE.ShapeGeometry(shape), mat = new THREE.MeshBasicMaterial({color:0xe6cc92});
      resources.add(geo); resources.add(mat);
      const play = new THREE.Mesh(geo, mat); play.position.set(-0.13, 0.1, 0.52); layers.add(play);
      host.append(renderer.domElement);
      renderer.domElement.addEventListener("webglcontextlost", lost);
      resize();
      resizeObserver.observe(host);
      fallback.hidden = true; toggle.hidden = false;
      host.dataset.scene = "webgl";
      sync();
    } catch (error) {
      release();
      console.warn("WebGL không khả dụng; dùng minh họa tĩnh:", error.message);
    }
  }

  const resizeObserver = new ResizeObserver(resize);
  function changeMotion() { if (reduced.matches) release(); else init(); sync(); }
  function click() { paused = !paused; sync(); }
  function pagehide(event) { if (event.persisted) stop(); else dispose(); }
  function dispose() {
    disposed = true; release();
    reduced.removeEventListener("change", changeMotion);
    toggle.removeEventListener("click", click);
    document.removeEventListener("visibilitychange", sync);
    window.removeEventListener("pagehide", pagehide);
    window.removeEventListener("pageshow", sync);
  }
  reduced.addEventListener("change", changeMotion);
  toggle.addEventListener("click", click);
  document.addEventListener("visibilitychange", sync);
  window.addEventListener("pagehide", pagehide);
  window.addEventListener("pageshow", sync);
  host.dataset.scene = "static";
  init();
  return {setVisible(value) { visible = value; sync(); }, setBusy(value) { busy = value; sync(); }, dispose};
}
