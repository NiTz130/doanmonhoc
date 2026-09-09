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
  });
  if (location.hash !== "#" + ten) location.hash = ten;
}

async function goi(duong, tuy = {}) {
  const kq = await fetch(duong, tuy);
  const text = await kq.text();
  let than = null;
  try { than = text ? JSON.parse(text) : null; } catch { than = null; }
  if (!kq.ok) throw new Error((than && than.detail) || text || kq.status);
  return than;
}

// ------------------------------------------------------------ 1. tai len

$("form-tai-len").addEventListener("submit", async (e) => {
  e.preventDefault();
  bao("");
  const form = new FormData(e.target);
  for (const o of ["separate", "force_asr", "force"]) {
    form.set(o, e.target.elements[o].checked ? "true" : "false");
  }
  try {
    const kq = await goi("/api/video", { method: "POST", body: form });
    cid = kq.id;
    $("viec-id").textContent = "Công việc " + cid;
    hien("tien-do");
    hoi_tien_do();
  } catch (err) {
    bao("Không tải lên được: " + err.message);
  }
});

// ------------------------------------------------------------ 2. tien do

const NHAN = {
  cho: "Đang xếp hàng…",
  dang_chay: "Đang xử lý",
  cho_chon_khung: "Chờ bạn khoanh vùng phụ đề cứng",
  xong: "Xong",
  suy_giam: "Xong, nhưng có cue giữ nguyên bản gốc",
  loi: "Lỗi",
};

async function hoi_tien_do() {
  clearTimeout(dong_ho);
  if (!cid) return;
  let tt;
  try {
    tt = await goi("/api/cong-viec/" + cid);
  } catch (err) {
    bao("Không hỏi được tiến độ: " + err.message);
    return;
  }
  $("thanh-chay").style.width = Math.round((tt.tien_do || 0) * 100) + "%";
  $("viec-trang-thai").textContent =
    (NHAN[tt.trang_thai] || tt.trang_thai) +
    (tt.buoc ? " — bước " + tt.buoc : "") +
    (tt.loi ? " (" + tt.loi + ")" : "");
  const tai = $("tai-ket-qua");
  tai.hidden = !tt.co_ket_qua;
  tai.href = "/api/cong-viec/" + cid + "/ket-qua";

  if (tt.trang_thai === "cho_chon_khung") { await nap_khung(); return; }
  if (tt.trang_thai === "cho" || tt.trang_thai === "dang_chay") {
    dong_ho = setTimeout(hoi_tien_do, 1500);   // hoi theo chu ky, khong WebSocket
  }
}

// ------------------------------------------------------------ 3. ve hop

async function nap_khung() {
  try {
    khung_ds = await goi("/api/cong-viec/" + cid + "/khung");
  } catch (err) {
    bao("Không lấy được khung mẫu: " + err.message);
    return;
  }
  if (!khung_ds.length) { bao("Backend chưa trích được khung nào."); return; }
  khung_i = 0;
  hien("khung");
  ve_khung();
}

function ve_khung() {
  const k = khung_ds[khung_i];
  $("khung-nhan").textContent =
    `khung ${khung_i + 1}/${khung_ds.length} · ${k.giay.toFixed(1)}s · "${k.text.replace(/\n/g, " ")}"`;
  $("khung-anh").src = `/api/cong-viec/${cid}/khung/${k.i}`;
}

$("khung-lui").onclick = () => { khung_i = (khung_i - 1 + khung_ds.length) % khung_ds.length; ve_khung(); };
$("khung-toi").onclick = () => { khung_i = (khung_i + 1) % khung_ds.length; ve_khung(); };

const anh = $("khung-anh");
const canvas = $("khung-canvas");
anh.addEventListener("load", ve_hop);          // hop giu nguyen khi chuyen khung

function ve_hop() {
  canvas.width = anh.clientWidth;
  canvas.height = anh.clientHeight;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!hop) return;
  ctx.strokeStyle = "#6aa6ff";
  ctx.lineWidth = 2;
  ctx.fillStyle = "rgba(106,166,255,.18)";
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
canvas.addEventListener("pointerup", () => {
  neo = null;
  const du = hop && hop.w > 0.01 && hop.h > 0.01;
  if (!du) { hop = null; ve_hop(); }
  $("hop-gui").disabled = !du;
  $("khung-hop").textContent = du
    ? `Hộp: x=${hop.x.toFixed(3)} y=${hop.y.toFixed(3)} w=${hop.w.toFixed(3)} h=${hop.h.toFixed(3)}`
    : "Hộp quá nhỏ, vẽ lại.";
});

$("hop-gui").onclick = () => gui_hop(hop);
$("hop-bo").onclick = () => gui_hop(null);

async function gui_hop(gia_tri) {
  bao("");
  try {
    await goi(`/api/cong-viec/${cid}/hop`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(gia_tri === null ? { co_blur: false } : gia_tri),
    });
    hien("tien-do");
    hoi_tien_do();
  } catch (err) {
    bao("Hộp bị từ chối: " + err.message);
  }
}

// ------------------------------------------------------------ 4. nhom

let nhom_dang_xem = null;

async function nap_nhom() {
  let ds;
  try { ds = await goi("/api/nhom"); } catch (err) { bao(err.message); return; }
  const ul = $("nhom-ds");
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
  nhom_dang_xem = ten;
  $("nhom-ten").textContent = ten;
  $("nhom-chi-tiet").hidden = false;
  const tbody = $("bang-thuat-ngu").tBodies[0];
  tbody.textContent = "";
  const tu = await goi(`/api/nhom/${encodeURIComponent(ten)}/thuat-ngu`);
  for (const [goc, dich] of Object.entries(tu)) {
    const tr = tbody.insertRow();
    tr.insertCell().textContent = goc;
    tr.insertCell().textContent = dich;
  }
  if (!Object.keys(tu).length) tbody.insertRow().insertCell().textContent = "Chưa có thuật ngữ nào.";
}

$("form-nhom").addEventListener("submit", async (e) => {
  e.preventDefault();
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
});

$("form-thuat-ngu").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = e.target.elements;
  try {
    await goi(`/api/nhom/${encodeURIComponent(nhom_dang_xem)}/thuat-ngu`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ goc: f.goc.value, dich: f.dich.value, khoa: f.khoa.checked }),
    });
    e.target.reset();
    xem_nhom(nhom_dang_xem);
  } catch (err) { bao(err.message); }
});

$("form-hop-nhom").addEventListener("submit", async (e) => {
  e.preventDefault();
  const so = e.target.elements.hop.value.split(",").map(Number);
  if (so.length !== 4 || so.some((n) => !isFinite(n))) { bao("Hộp phải gồm bốn số x,y,w,h"); return; }
  try {
    await goi(`/api/nhom/${encodeURIComponent(nhom_dang_xem)}/hop`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ x: so[0], y: so[1], w: so[2], h: so[3] }),
    });
    bao("Đã lưu khung mặc định.", true);
    nap_nhom();
  } catch (err) { bao(err.message); }
});

// ------------------------------------------------------------ dieu huong

window.addEventListener("hashchange", dieu_huong);
function dieu_huong() {
  const ten = location.hash.slice(1);
  hien(MAN.includes(ten) ? ten : "tai-len");
  if (ten === "nhom") nap_nhom();
  if (ten === "tien-do" && cid) hoi_tien_do();
}
window.addEventListener("resize", ve_hop);
dieu_huong();
