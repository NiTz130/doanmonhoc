"use strict";
// Frontend thuan HTML/CSS/JS: khong bundler, khong framework. Backend van la noi
// quyet dinh — kiem hop o day chi de bao som cho nguoi dung.

const $ = (id) => document.getElementById(id);
const MAN = ["tai-len", "tien-do", "khung", "nhom"];

let cid = null;          // cong viec dang theo doi
let dong_ho = null;      // setTimeout cua vong hoi tien do
let khung_ds = [];       // danh sach khung mau
let khung_i = 0;
let hop = null;          // {x, y, w, h} theo phan tram, dung chung cho moi khung
let dang_gui = false;
let dang_xu_ly = false;
let dang_hoi = false;
let dang_gui_hop = false;
let anh_san_sang = false;
let khung_cid = null;
let cho_hop = false;
let scene = null;

function cap_nhat_ui() {
  $("upload-submit").disabled = dang_gui || dang_xu_ly || dang_hoi || !$("video-file").files.length;
  $("upload-submit").textContent = dang_gui ? "Đang tải lên…" : "Bắt đầu ↗";
  $("video-file").disabled = dang_gui || dang_xu_ly;
  $("upload-note").textContent = dang_xu_ly ? "Công việc hiện tại chưa hoàn tất. Xem màn Tiến độ." : "Mỗi lần xử lý một video.";
  scene?.setBusy(dang_gui || dang_xu_ly);
}

function bao(text, ok = false) {
  const el = $("bao");
  el.textContent = text;
  el.className = ok ? "ok" : "";
  el.hidden = !text;
}

function hien(ten) {
  MAN.forEach((m) => { $(m).hidden = m !== ten; });
  document.querySelectorAll("nav a").forEach((a) => {
    a.classList.toggle("chon", a.hash === "#" + ten);
    if (a.hash === "#" + ten) a.setAttribute("aria-current", "page");
    else a.removeAttribute("aria-current");
  });
  scene?.setVisible(ten === "tai-len");
  if (ten === "khung") ve_hop();
  if (location.hash !== "#" + ten) history.replaceState(null, "", "#" + ten);
}

async function goi(duong, tuy = {}) {
  const kq = await fetch(duong, tuy);
  const text = await kq.text();
  let than = null;
  try { than = text ? JSON.parse(text) : null; } catch { than = null; }
  if (!kq.ok) {
    const detail = than?.detail;
    throw new Error(Array.isArray(detail) ? detail.map((d) => d.msg).join("; ") : detail || text || kq.status);
  }
  return than;
}

// ------------------------------------------------------------ 1. tai len

$("video-file").addEventListener("change", () => {
  const file = $("video-file").files[0];
  $("file-name").textContent = file ? `${file.name} · ${(file.size / 1024 ** 2).toFixed(1)} MiB` : "Chưa chọn video.";
  bao("");
  cap_nhat_ui();
});
for (const event of ["dragenter", "dragover", "dragleave", "drop"]) {
  $("drop-zone").addEventListener(event, (e) => {
    e.preventDefault();
    $("drop-zone").classList.toggle("dragover", event === "dragenter" || event === "dragover");
    if (event !== "drop" || dang_gui || dang_xu_ly) return;
    if (e.dataTransfer.files.length !== 1) { bao("Chọn một video mỗi lần."); return; }
    $("video-file").files = e.dataTransfer.files;
    $("video-file").dispatchEvent(new Event("change"));
  });
}

$("form-tai-len").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (dang_gui || dang_xu_ly || dang_hoi) return;
  bao("");
  const file = $("video-file").files[0];
  if (!file || !/\.(mp4|mkv|mov|webm|avi|ts)$/i.test(file.name) || !file.size || file.size > 4 * 1024 ** 3) {
    bao("Chọn video MP4, MKV, MOV, WEBM, AVI hoặc TS, dung lượng lớn hơn 0 và không quá 4 GiB.");
    return;
  }
  // Open advanced fields before browser validation so invalid controls can receive focus.
  if (!e.target.checkValidity()) { e.target.querySelector("details").open = true; e.target.reportValidity(); return; }
  const form = new FormData(e.target);
  for (const o of ["separate", "force_asr", "force"]) {
    form.set(o, e.target.elements[o].checked ? "true" : "false");
  }
  dang_gui = true;
  e.target.setAttribute("aria-busy", "true");
  cap_nhat_ui();
  try {
    const kq = await goi("/api/video", { method: "POST", body: form });
    cid = kq.id;
    dang_xu_ly = true;
    cho_hop = false;
    $("progress-label").textContent = "—";
    $("thanh-chay").style.width = "0%";
    $("thanh-chay").parentElement.setAttribute("aria-valuenow", "0");
    $("viec-trang-thai").textContent = "Đang lấy trạng thái công việc…";
    $("connection-status").textContent = "";
    khung_ds = []; khung_cid = null; hop = null;
    $("khung-boc").hidden = true;
    $("khung-thumbnails").replaceChildren();
    $("form-toa-do").reset();
    anh_san_sang = false;
    $("toa-do-fields").disabled = true;
    $("hop-gui").disabled = $("hop-bo").disabled = true;
    $("khung-lui").disabled = $("khung-toi").disabled = true;
    $("khung-empty").hidden = false;
    $("khung-hop").textContent = "Chưa vẽ hộp nào.";
    $("tai-ket-qua").hidden = true;
    $("video-name").textContent = file.name;
    $("viec-id").textContent = "Công việc " + cid;
    hien("tien-do");
    dang_gui = false;
    hoi_tien_do();
  } catch (err) {
    bao("Không tải lên được: " + err.message);
  } finally {
    dang_gui = false;
    e.target.setAttribute("aria-busy", "false");
    cap_nhat_ui();
  }
});

// ------------------------------------------------------------ 2. tien do

const NHAN = {
  cho: "Đang xếp hàng…",
  dang_chay: "Đang xử lý",
  cho_chon_khung: "Chờ bạn khoanh vùng phụ đề cứng",
  xong: "Xong",
  suy_giam: "Đã xuất video, nhưng còn dòng giữ nguyên tiếng nguồn. Hãy kiểm tra bản dịch.",
  loi: "Lỗi",
};

async function hoi_tien_do() {
  if (!cid || dang_hoi || dang_gui) return;
  clearTimeout(dong_ho);
  dong_ho = null;
  dang_hoi = true;
  cap_nhat_ui();
  $("poll-retry").hidden = true;
  try {
    const tt = await goi("/api/cong-viec/" + cid);
    $("connection-status").textContent = "";
    const percent = Math.round(Math.min(1, Math.max(0, Number(tt.tien_do) || 0)) * 100);
    $("thanh-chay").style.width = percent + "%";
    $("thanh-chay").parentElement.setAttribute("aria-valuenow", percent);
    $("progress-label").textContent = percent + "%";
    $("viec-trang-thai").textContent =
      (NHAN[tt.trang_thai] || tt.trang_thai) +
      (tt.buoc ? " — bước " + tt.buoc : "") + (tt.loi ? " (" + tt.loi + ")" : "");
    const tai = $("tai-ket-qua");
    tai.hidden = !tt.co_ket_qua;
    tai.href = "/api/cong-viec/" + cid + "/ket-qua";
    dang_xu_ly = !["xong", "suy_giam", "loi"].includes(tt.trang_thai);
    cho_hop = tt.trang_thai === "cho_chon_khung";
    if (tt.trang_thai === "cho_chon_khung") {
      if (khung_cid !== cid) await nap_khung();
    } else if (tt.trang_thai === "cho" || tt.trang_thai === "dang_chay") {
      dong_ho = setTimeout(hoi_tien_do, 1500);
    }
  } catch (err) {
    $("connection-status").textContent = "Không cập nhật được: " + err.message + ". Thông tin công việc vẫn được giữ.";
    $("poll-retry").hidden = false;
  } finally {
    dang_hoi = false;
    cap_nhat_ui();
  }
}
$("poll-retry").onclick = hoi_tien_do;

// ------------------------------------------------------------ 3. ve hop

async function nap_khung() {
  khung_ds = await goi("/api/cong-viec/" + cid + "/khung");
  if (!khung_ds.length) throw new Error("Backend chưa trích được khung nào");
  khung_cid = cid;
  khung_i = 0;
  $("khung-empty").hidden = true;
  $("khung-boc").hidden = false;
  $("khung-lui").disabled = $("khung-toi").disabled = khung_ds.length < 2;
  $("hop-bo").disabled = false;
  $("khung-thumbnails").replaceChildren(...khung_ds.map((k, index) => {
    const b = document.createElement("button"); b.type = "button";
    b.setAttribute("aria-label", `Xem khung ${index + 1} tại ${k.giay.toFixed(1)} giây`);
    const img = document.createElement("img"); img.alt = "";
    img.src = `/api/cong-viec/${cid}/khung/${k.i}`;
    img.addEventListener("error", () => { img.hidden = true; });
    b.append(img, `${index + 1} · ${k.giay.toFixed(1)}s`);
    b.onclick = () => { khung_i = index; ve_khung(); };
    return b;
  }));
  hien("khung");
  ve_khung();
}

function ve_khung() {
  const k = khung_ds[khung_i];
  if (!k) return;
  anh_san_sang = false;
  $("image-status").textContent = "Đang tải ảnh mẫu…";
  $("toa-do-fields").disabled = true;
  $("hop-gui").disabled = true;
  $("khung-thumbnails").querySelectorAll("button").forEach((b, i) => b.setAttribute("aria-pressed", i === khung_i));
  $("khung-nhan").textContent =
    `khung ${khung_i + 1}/${khung_ds.length} · ${k.giay.toFixed(1)}s · "${k.text.replace(/\n/g, " ")}"`;
  $("khung-anh").src = `/api/cong-viec/${cid}/khung/${k.i}`;
}

$("khung-lui").onclick = () => { if (khung_ds.length) { khung_i = (khung_i - 1 + khung_ds.length) % khung_ds.length; ve_khung(); } };
$("khung-toi").onclick = () => { if (khung_ds.length) { khung_i = (khung_i + 1) % khung_ds.length; ve_khung(); } };

const anh = $("khung-anh");
const canvas = $("khung-canvas");
anh.addEventListener("load", () => {
  anh_san_sang = true;
  $("image-status").textContent = "";
  $("toa-do-fields").disabled = dang_gui_hop || !cho_hop;
  cap_nhat_hop();
});
anh.addEventListener("error", () => {
  anh_san_sang = false;
  $("image-status").textContent = "Không tải được ảnh mẫu. Chọn lại ảnh để thử lại, hoặc bỏ qua làm mờ.";
  $("toa-do-fields").disabled = true;
  $("hop-gui").disabled = true;
});

function ve_hop() {
  canvas.width = anh.clientWidth;
  canvas.height = anh.clientHeight;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!hop) return;
  ctx.strokeStyle = "#f2c765";
  ctx.lineWidth = 2;
  ctx.fillStyle = "rgba(242,199,101,.25)";
  const r = [hop.x * canvas.width, hop.y * canvas.height,
             hop.w * canvas.width, hop.h * canvas.height];
  ctx.fillRect(...r);
  ctx.strokeRect(...r);
}

// Chia cho clientWidth cho ra ngay phan tram: ti le naturalWidth/clientWidth trong
// thiet ke chinh la buoc doi nguoc lai ve khung goc, va phan tram thi doc lap do phan giai.
function phan_tram(e) {
  const o = canvas.getBoundingClientRect();
  return [Math.min(1, Math.max(0, (e.clientX - o.left) / o.width)),
          Math.min(1, Math.max(0, (e.clientY - o.top) / o.height))];
}

let neo = null;
canvas.addEventListener("pointerdown", (e) => {
  if (!anh_san_sang || dang_gui_hop || !cho_hop || (e.pointerType === "mouse" && e.button !== 0)) return;
  neo = phan_tram(e);
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener("pointermove", (e) => {
  if (!neo) return;
  const [x, y] = phan_tram(e);
  hop = { x: Math.min(neo[0], x), y: Math.min(neo[1], y),
          w: Math.abs(x - neo[0]), h: Math.abs(y - neo[1]) };
  ve_hop();
});
function cap_nhat_hop() {
  const du = hop && hop.w > 0 && hop.h > 0;
  $("hop-gui").disabled = !du || !anh_san_sang || dang_gui_hop || !cho_hop;
  $("hop-bo").disabled = dang_gui_hop || !cho_hop;
  $("toa-do-fields").disabled = !anh_san_sang || dang_gui_hop || !cho_hop;
  $("khung-hop").textContent = du
    ? `Hộp: x=${hop.x.toFixed(3)} y=${hop.y.toFixed(3)} w=${hop.w.toFixed(3)} h=${hop.h.toFixed(3)}`
    : "Chưa có vùng hợp lệ. Vẽ hoặc nhập tọa độ bên dưới.";
  if (du) for (const k of "xywh") $("form-toa-do").elements[k].value = hop[k];
  ve_hop();
}
canvas.addEventListener("pointerup", () => {
  if (!neo) return;
  neo = null;
  const du = hop && hop.w > 0.01 && hop.h > 0.01;
  if (!du) { hop = null; ve_hop(); }
  cap_nhat_hop();
});
canvas.addEventListener("pointercancel", () => { neo = null; cap_nhat_hop(); });
$("form-toa-do").addEventListener("submit", (e) => {
  e.preventDefault();
  if (!anh_san_sang || dang_gui_hop || !cho_hop) return;
  const f = e.target.elements;
  const box = Object.fromEntries([..."xywh"].map((k) => [k, Number(f[k].value)]));
  if (!hop_hop_le(box)) { bao("Vùng phải nằm trong ảnh: x + w ≤ 1, y + h ≤ 1; rộng và cao lớn hơn 0."); return; }
  hop = box; bao(""); cap_nhat_hop();
});
function hop_hop_le(box) {
  return [..."xywh"].every((k) => Number.isFinite(box[k])) && box.x >= 0 && box.y >= 0 &&
    box.w > 0 && box.h > 0 && box.x + box.w <= 1 && box.y + box.h <= 1;
}

$("hop-gui").onclick = () => gui_hop(hop);
$("hop-bo").onclick = () => gui_hop(null);

async function gui_hop(gia_tri) {
  if (!cid || !khung_ds.length || dang_gui_hop || !cho_hop) return;
  if (gia_tri !== null && (!anh_san_sang || !hop_hop_le(gia_tri))) return;
  dang_gui_hop = true;
  $("hop-gui").disabled = $("hop-bo").disabled = true;
  $("toa-do-fields").disabled = true;
  bao("");
  try {
    await goi(`/api/cong-viec/${cid}/hop`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(gia_tri === null ? { co_blur: false } : gia_tri),
    });
    cho_hop = false;
    hien("tien-do");
    hoi_tien_do();
  } catch (err) {
    bao("Hộp bị từ chối: " + err.message);
  } finally {
    dang_gui_hop = false;
    $("hop-bo").disabled = false;
    $("toa-do-fields").disabled = !anh_san_sang;
    cap_nhat_hop();
  }
}

// ------------------------------------------------------------ 4. nhom

let nhom_dang_xem = null;
let lan_nhom = 0;

function khoa_form(form, busy) {
  form.setAttribute("aria-busy", String(busy));
  form.querySelectorAll("input, button").forEach((el) => { el.disabled = busy; });
}

async function nap_nhom() {
  let ds;
  try { ds = await goi("/api/nhom"); } catch (err) { bao(err.message); return; }
  const ul = $("nhom-ds");
  $("nhom-goi-y").replaceChildren(...ds.map((n) => {
    const option = document.createElement("option"); option.value = n.ten; return option;
  }));
  ul.textContent = "";
  if (!ds.length) ul.innerHTML = '<li class="mo">Chưa có nhóm nào.</li>';
  for (const n of ds) {
    const li = document.createElement("li");
    const co_hop = n.blur_x !== null;
    li.textContent = n.ten + (co_hop
      ? ` — hộp ${[n.blur_x, n.blur_y, n.blur_w, n.blur_h].map((v) => v.toFixed(3)).join(",")}`
      : " — chưa có hộp");
    const nut = document.createElement("button");
    nut.textContent = "Xem thuật ngữ";
    nut.onclick = () => xem_nhom(n.ten);
    li.append(nut);
    ul.append(li);
  }
}

async function xem_nhom(ten) {
  if (document.querySelector('#nhom-chi-tiet form[aria-busy="true"]')) return;
  const lan = ++lan_nhom;
  nhom_dang_xem = ten;
  $("nhom-ten").textContent = ten;
  $("nhom-chi-tiet").hidden = false;
  const tbody = $("bang-thuat-ngu").tBodies[0];
  tbody.textContent = "";
  tbody.insertRow().insertCell().textContent = "Đang tải thuật ngữ…";
  try {
    const tu = await goi(`/api/nhom/${encodeURIComponent(ten)}/thuat-ngu`);
    if (lan !== lan_nhom) return;
    ve_thuat_ngu(tu);
  } catch (err) {
    if (lan !== lan_nhom) return;
    tbody.textContent = "";
    tbody.insertRow().insertCell().textContent = "Không tải được thuật ngữ. Chọn nhóm để thử lại.";
    bao(err.message);
  }
}

function ve_thuat_ngu(tu) {
  const tbody = $("bang-thuat-ngu").tBodies[0];
  tbody.textContent = "";
  for (const [goc, dich] of Object.entries(tu)) {
    const tr = tbody.insertRow();
    tr.insertCell().textContent = goc;
    tr.insertCell().textContent = dich;
  }
  if (!Object.keys(tu).length) tbody.insertRow().insertCell().textContent = "Chưa có thuật ngữ nào.";
}

$("form-nhom").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (e.target.getAttribute("aria-busy") === "true") return;
  khoa_form(e.target, true);
  try {
    await goi("/api/nhom", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ten: e.target.elements.ten.value }),
    });
    e.target.reset();
    bao("Đã tạo nhóm.", true);
    nap_nhom();
  } catch (err) { bao(err.message); }
  finally { khoa_form(e.target, false); }
});

$("form-thuat-ngu").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (e.target.getAttribute("aria-busy") === "true" || !nhom_dang_xem) return;
  const f = e.target.elements;
  khoa_form(e.target, true);
  // Invalidate an older group read so it cannot replace the just-saved table.
  ++lan_nhom;
  try {
    const tu = await goi(`/api/nhom/${encodeURIComponent(nhom_dang_xem)}/thuat-ngu`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goc: f.goc.value, dich: f.dich.value, khoa: f.khoa.checked }),
    });
    e.target.reset();
    ve_thuat_ngu(tu);
    bao("Đã lưu thuật ngữ.", true);
  } catch (err) { bao(err.message); }
  finally { khoa_form(e.target, false); }
});

$("form-hop-nhom").addEventListener("submit", async (e) => {
  e.preventDefault();
  if (e.target.getAttribute("aria-busy") === "true" || !nhom_dang_xem) return;
  const parts = e.target.elements.hop.value.split(",");
  const so = parts.map(Number);
  if (parts.some((p) => !p.trim()) || so.length !== 4 || !hop_hop_le({x:so[0],y:so[1],w:so[2],h:so[3]})) { bao("Hộp phải gồm bốn số x,y,w,h hợp lệ và nằm trong ảnh."); return; }
  khoa_form(e.target, true);
  try {
    await goi(`/api/nhom/${encodeURIComponent(nhom_dang_xem)}/hop`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ x: so[0], y: so[1], w: so[2], h: so[3] }),
    });
    bao("Đã lưu khung mặc định.", true);
    nap_nhom();
  } catch (err) { bao(err.message); }
  finally { khoa_form(e.target, false); }
});

// ------------------------------------------------------------ dieu huong

window.addEventListener("hashchange", dieu_huong);
function dieu_huong() {
  const ten = location.hash.slice(1);
  hien(MAN.includes(ten) ? ten : "tai-len");
  if (ten === "nhom") nap_nhom();
  if (ten === "tien-do" && cid && !dang_hoi && !dong_ho) hoi_tien_do();
}
window.addEventListener("resize", ve_hop);
dieu_huong();
cap_nhat_ui();
// Optional enhancement: an import/WebGL failure leaves the static illustration and UI intact.
import("./scene.js").then((module) => {
  scene = module.createScene($("scene"), $("scene-toggle"));
  scene?.setVisible(!$("tai-len").hidden);
  cap_nhat_ui();
}).catch((error) => { console.warn("Minh họa tĩnh được sử dụng:", error.message); });
