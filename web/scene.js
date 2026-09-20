import * as THREE from "./vendor/three/three.module.min.js";

// Decorative only: forms never depend on the GPU or this module loading.
export function createScene(host, toggle) {
  const reduced = matchMedia("(prefers-reduced-motion: reduce)");
  const fallback = host.querySelector(".scene-fallback");
  let renderer = null;
  let world, camera, layers, vien;
  let visible = true, busy = false, paused = false, disposed = false;
  let frame = 0, previous = 0, elapsed = 0;
  let tro_x = 0, tro_y = 0, dich_x = 0, dich_y = 0;   // goc nhin hien tai va dich cua no
  const resources = new Set();

  function box(w, h, d, color, x, y, z, parent = layers, them = {}) {
    const geometry = new THREE.BoxGeometry(w, h, d);
    const material = new THREE.MeshStandardMaterial({color, roughness:0.88, metalness:0.02, ...them});
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
    // Giam chan: dai phim nghieng tu tu theo con tro chu khong giat theo chuot.
    tro_x += (dich_x - tro_x) * 0.08;
    tro_y += (dich_y - tro_y) * 0.08;
    layers.rotation.y = -0.32 + Math.sin(elapsed * 0.35) * 0.065 + tro_x * 0.26;
    layers.rotation.x = 0.2 + tro_y * 0.16;
    layers.position.y = Math.sin(elapsed * 0.55) * 0.055;
    vien.position.set(4 - tro_x * 3.5, -1.6 + tro_y * 2.4, 5);
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
      // Anh sang diu, vat lieu mo (roughness cao, metalness thap): khong bong loang.
      world.add(new THREE.AmbientLight(0xffffff, 1.5));
      const sun = new THREE.DirectionalLight(0xfff4e2, 1.4); sun.position.set(-3, 6, 7); world.add(sun);
      // Den vien: quet doc canh phim nhua theo huong nhin, cho ra khoi vat the that.
      vien = new THREE.DirectionalLight(0xfff2de, 0.9); vien.position.set(4, -1.6, 5); world.add(vien);
      // Hai dai acetate sau de trong: xep lop moi doc ra, khong thanh ba tam dac chong nhau.
      box(4.2, 2.3, 0.08, 0xd9d5c8, 0.40, 0.35, -0.65, layers, {transparent:true, opacity:0.55});
      box(4.2, 2.3, 0.08, 0xc9c4b4, 0.16, 0.12, -0.15, layers, {transparent:true, opacity:0.78});
      box(4.2, 2.3, 0.13, 0x2a2a28, -0.14, -0.14, 0.4);
      box(3.86, 1.63, 0.02, 0x141412, -0.14, 0.02, 0.48);
      for (const x of [-1.8, -1.25, -0.7, -0.15, 0.4, 0.95, 1.5]) {
        box(0.22, 0.11, 0.02, 0xf5f2e8, x, 0.87, 0.49);      // lo keo phim
      }
      // Hai thanh duoi la phu de: thanh tren mang mau nhan cua giao dien.
      box(2.65, 0.13, 0.03, 0xc2362b, -0.14, -0.56, 0.51);
      box(1.8, 0.10, 0.03, 0x8a867c, -0.14, -0.81, 0.51);
      const shape = new THREE.Shape(); shape.moveTo(-0.20, -0.22); shape.lineTo(0.24, 0.04); shape.lineTo(-0.20, 0.30); shape.closePath();
      const geo = new THREE.ShapeGeometry(shape), mat = new THREE.MeshBasicMaterial({color:0xf2efe6});
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

  // Chi doc layout khi canh dang chay that: dung, an tab hay giam chuyen dong
  // thi frame = 0, handler thoat ngay, khong ton getBoundingClientRect nao.
  function tro(event) {
    if (!renderer || !frame) return;
    const r = host.getBoundingClientRect();
    if (!r.width || !r.height) return;
    dich_x = Math.max(-1, Math.min(1, (event.clientX - r.left - r.width / 2) / r.width * 2));
    dich_y = Math.max(-1, Math.min(1, (event.clientY - r.top - r.height / 2) / r.height * 2));
  }

  const resizeObserver = new ResizeObserver(resize);
  function changeMotion() { if (reduced.matches) release(); else init(); sync(); }
  function click() { paused = !paused; sync(); }
  function pagehide(event) { if (event.persisted) stop(); else dispose(); }
  function dispose() {
    disposed = true; release();
    reduced.removeEventListener("change", changeMotion);
    window.removeEventListener("pointermove", tro);
    toggle.removeEventListener("click", click);
    document.removeEventListener("visibilitychange", sync);
    window.removeEventListener("pagehide", pagehide);
    window.removeEventListener("pageshow", sync);
  }
  reduced.addEventListener("change", changeMotion);
  window.addEventListener("pointermove", tro, {passive: true});
  toggle.addEventListener("click", click);
  document.addEventListener("visibilitychange", sync);
  window.addEventListener("pagehide", pagehide);
  window.addEventListener("pageshow", sync);
  host.dataset.scene = "static";
  init();
  return {setVisible(value) { visible = value; sync(); }, setBusy(value) { busy = value; sync(); }};
}
