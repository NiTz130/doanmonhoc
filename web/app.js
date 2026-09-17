"use strict";
// Frontend thuan HTML/CSS/JS: khong bundler, khong framework. Backend van la noi
// quyet dinh — kiem hop o day chi de bao som cho nguoi dung.

const $ = (id) => document.getElementById(id);
const MAN = ["tai-len", "tien-do", "khung", "nhom"];

let cid = null;          // cong viec dang theo doi
let dong_ho = null;      // setTimeout cua vong hoi tien do
let khung_ds = [];       // danh sach khung mau
let khung_i = 0;
let hop = null;          // {x, y, w, h} dang ve tren khung hien tai, theo phan tram
let hop_chung = null;    // hop ap cho moi cau chua co hop rieng
let hop_rieng = new Map();   // chi so cau thoai -> hop rieng cua cau do
let pham_vi = "chung";   // hop dang ve thuoc ve "chung" hay "rieng" cua cau nay
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
  // Doi hinh ca o tha tep chu khong chi ghi mot dong mo o duoi: nguoi dung moi
  // nhin vao cai hop, hop khong doi gi thi ho tuong chua chon duoc.
  $("file-name").textContent = file
    ? `✓ Đã chọn: ${file.name} · ${(file.size / 1024 ** 2).toFixed(1)} MiB`
    : "Chưa chọn video.";
  $("file-name").classList.toggle("co-file", !!file);
  $("drop-zone").classList.toggle("da-chon", !!file);
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
    buoc_i = -1;
    ve_tien_trinh("cho", "");
    $("thanh-chay").style.width = "0%";
    $("thanh-chay").parentElement.setAttribute("aria-valuenow", "0");
    $("viec-trang-thai").textContent = "Đang lấy trạng thái công việc…";
    $("connection-status").textContent = "";
    khung_ds = []; khung_cid = null; hop = null;
    hop_chung = null; hop_rieng.clear(); pham_vi = "chung";
    $("khung-boc").hidden = true;
    $("khung-thumbnails").replaceChildren();
    $("form-toa-do").reset();
    anh_san_sang = false;
    $("toa-do-fields").disabled = true;
    $("hop-gui").disabled = $("hop-bo").disabled = true;
    $("khung-lui").disabled = $("khung-toi").disabled = true;
    $("khung-empty").hidden = false;
    $("khung-hop").textContent = "Chưa vẽ hộp nào.";
    $("hop-luu-nhom").checked = false;
    $("hop-luu-nhom").disabled = true;
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

// Stepper bam theo enum `buoc` that cua dieu_phoi.py. "canh_bao" va moi ten moi
// cho indexOf = -1; khi do giu nguyen buoc dang sang thay vi tat het den.
const BUOC = ["nhan_dien", "sub_goc", "vung_blur", "dich", "render"];
let buoc_i = -1;

function ve_tien_trinh(trang_thai, buoc) {
  if (["xong", "suy_giam"].includes(trang_thai)) buoc_i = BUOC.length;
  else buoc_i = Math.max(buoc_i, BUOC.indexOf(buoc));
  for (const li of $("tien-trinh").children) {
    const v = BUOC.indexOf(li.dataset.buoc);
    li.dataset.trangThai = v < buoc_i ? "xong"
      : v === buoc_i ? (trang_thai === "loi" ? "loi" : "dang") : "cho";
    if (li.dataset.trangThai === "dang") li.setAttribute("aria-current", "step");
    else li.removeAttribute("aria-current");
  }
}

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
    ve_tien_trinh(tt.trang_thai, tt.buoc);
    const tai = $("tai-ket-qua");
    tai.hidden = !tt.co_ket_qua;
    tai.href = "/api/cong-viec/" + cid + "/ket-qua";
    dang_xu_ly = !["xong", "suy_giam", "loi"].includes(tt.trang_thai);
    $("thanh-chay").classList.toggle("chay", dang_xu_ly);
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
    img.loading = "lazy";        // mot khung moi cue: tai het cung luc la vo, anh trong
    img.src = `/api/cong-viec/${cid}/khung/${k.i}`;
    img.addEventListener("error", () => { img.hidden = true; });
    b.append(img, `${index + 1} · ${k.giay.toFixed(1)}s`);
    b.onclick = () => { khung_i = index; ve_khung(); };
    return b;
  }));
  hien("khung");
  ve_khung();
}

// Chi so cau thoai that cua khung dang xem; /khung co the bo bot khung hong nen
// vi tri trong danh sach khong chac bang chi so cau.
function cue_i() {
  return khung_ds[khung_i] ? khung_ds[khung_i].i : 0;
}

function dat_pham_vi() {
  for (const r of document.querySelectorAll("[name=pham_vi]")) r.checked = r.value === pham_vi;
  $("pham-vi-note").textContent = pham_vi === "rieng"
    ? `Chỉ câu ${cue_i() + 1} dùng vùng này.`
    : "Mọi câu chưa có vùng riêng đều dùng vùng này.";
}

function ve_khung() {
  const k = khung_ds[khung_i];
  if (!k) return;
  // Doi khung la doi sang hop cua khung do: rieng neu co, khong thi hop chung.
  pham_vi = hop_rieng.has(k.i) ? "rieng" : "chung";
  const nguon = hop_rieng.get(k.i) || hop_chung;
  hop = nguon ? { ...nguon } : null;
  dat_pham_vi();
  anh_san_sang = false;
  $("image-status").textContent = "Đang tải ảnh mẫu…";
  $("toa-do-fields").disabled = true;
  $("hop-gui").disabled = true;
  $("khung-thumbnails").querySelectorAll("button").forEach((b, i) => {
    b.setAttribute("aria-pressed", i === khung_i);
    // Vai chuc khung thi dai chuot khong tu chay theo: bam -> la mat dau khung dang xem.
    if (i === khung_i) b.scrollIntoView({ block: "nearest", inline: "nearest" });
  });
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
  $("hop-luu-nhom").disabled = true;
});

// Tam 8 tay nam, theo ti le trong hop. Ve ra thi nguoi dung moi biet hop sua duoc.
const NEO_TAY = [[0, 0], [.5, 0], [1, 0], [0, .5], [1, .5], [0, 1], [.5, 1], [1, 1]];
const BAT_PX = 10;                  // ban kinh bat canh, tinh bang pixel tren man hinh
const kep = (v, toi_da) => Math.min(toi_da, Math.max(0, v));

// Mau neo duoi con tro phong to dan len 1.3x: keo dung canh tren mot o chi cao
// vai pixel thi phai thay ro minh dang tom cai nao truoc khi bam.
const IT_DONG = matchMedia("(prefers-reduced-motion: reduce)");
let tay_hover = -1, tay_ti = 1, tay_frame = 0;

function tay_dan() {
  const dich = tay_hover >= 0 ? 1.3 : 1;
  tay_ti += (dich - tay_ti) * 0.28;
  if (Math.abs(dich - tay_ti) < 0.01) { tay_ti = dich; tay_frame = 0; }
  else tay_frame = requestAnimationFrame(tay_dan);
  ve_hop();
}

function dat_tay(i) {
  if (i === tay_hover) return;
  tay_hover = i;
  if (IT_DONG.matches) { tay_ti = i >= 0 ? 1.3 : 1; ve_hop(); return; }
  if (!tay_frame) tay_frame = requestAnimationFrame(tay_dan);
}

// Mau neo nao dang duoi con tro; khong cham cai nao thi -1.
function tay_duoi(px, py) {
  if (!hop || !canvas.width || !canvas.height) return -1;
  for (let i = 0; i < NEO_TAY.length; i++) {
    const [ax, ay] = NEO_TAY[i];
    if (Math.abs((hop.x + hop.w * ax - px) * canvas.width) <= BAT_PX &&
        Math.abs((hop.y + hop.h * ay - py) * canvas.height) <= BAT_PX) return i;
  }
  return -1;
}

function ve_hop() {
  canvas.width = anh.clientWidth;
  canvas.height = anh.clientHeight;
  const ctx = canvas.getContext("2d");
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!hop) return;
  const r = [hop.x * canvas.width, hop.y * canvas.height,
             hop.w * canvas.width, hop.h * canvas.height];
  ctx.fillStyle = "rgba(194,54,43,.18)";
  ctx.fillRect(...r);
  // Vien trang lot duoi vien do son: canh toi thi trang noi, canh sang thi do son
  // noi. Mot mau don le se chim o mot trong hai truong hop.
  ctx.strokeStyle = "rgba(255,255,255,.85)"; ctx.lineWidth = 4; ctx.strokeRect(...r);
  ctx.strokeStyle = "#c2362b"; ctx.lineWidth = 2; ctx.strokeRect(...r);
  for (let i = 0; i < NEO_TAY.length; i++) {
    const [ax, ay] = NEO_TAY[i];
    const hx = r[0] + r[2] * ax, hy = r[1] + r[3] * ay;
    const n = (i === tay_hover ? tay_ti : 1) * 4;      // nua canh mau neo
    ctx.fillStyle = "#fff"; ctx.fillRect(hx - n - 1, hy - n - 1, n * 2 + 2, n * 2 + 2);
    ctx.fillStyle = i === tay_hover ? "#e0483a" : "#c2362b";
    ctx.fillRect(hx - n, hy - n, n * 2, n * 2);
  }
}

// Canh nao dang nam duoi con tro; khong cham canh nao thi null.
function canh_duoi(px, py) {
  if (!hop || !canvas.width || !canvas.height) return null;
  const bx = BAT_PX / canvas.width, by = BAT_PX / canvas.height;
  const trong_x = px >= hop.x - bx && px <= hop.x + hop.w + bx;
  const trong_y = py >= hop.y - by && py <= hop.y + hop.h + by;
  const c = { trai: trong_y && Math.abs(px - hop.x) <= bx,
              phai: trong_y && Math.abs(px - hop.x - hop.w) <= bx,
              tren: trong_x && Math.abs(py - hop.y) <= by,
              duoi: trong_x && Math.abs(py - hop.y - hop.h) <= by };
  return (c.trai || c.phai || c.tren || c.duoi) ? c : null;
}

function trong_hop(px, py) {
  return !!hop && px >= hop.x && px <= hop.x + hop.w && py >= hop.y && py <= hop.y + hop.h;
}

function con_tro(px, py) {
  if (!anh_san_sang || !cho_hop || dang_gui_hop) return "default";
  const c = canh_duoi(px, py);
  if (!c) return trong_hop(px, py) ? "move" : "crosshair";
  if ((c.trai && c.tren) || (c.phai && c.duoi)) return "nwse-resize";
  if ((c.phai && c.tren) || (c.trai && c.duoi)) return "nesw-resize";
  return (c.trai || c.phai) ? "ew-resize" : "ns-resize";
}

// Chia cho clientWidth cho ra ngay phan tram: ti le naturalWidth/clientWidth trong
// thiet ke chinh la buoc doi nguoc lai ve khung goc, va phan tram thi doc lap do phan giai.
function phan_tram(e) {
  const o = canvas.getBoundingClientRect();
  return [Math.min(1, Math.max(0, (e.clientX - o.left) / o.width)),
          Math.min(1, Math.max(0, (e.clientY - o.top) / o.height))];
}

// Keo canh/goc de chinh, keo giua hop de doi: ve lai tu dau chi vi thieu 2 pixel
// la viec phai lam di lam lai, vi con phai bao tron cau hai dong qua 8 khung.
let keo = null;          // {che_do: 'moi' | 'dich' | 'canh', tu: [x,y], canh, hop0}
canvas.addEventListener("pointerdown", (e) => {
  if (!anh_san_sang || dang_gui_hop || !cho_hop || (e.pointerType === "mouse" && e.button !== 0)) return;
  const [x, y] = phan_tram(e);
  const canh = canh_duoi(x, y);
  keo = canh ? { che_do: "canh", tu: [x, y], canh, hop0: { ...hop } }
    : trong_hop(x, y) ? { che_do: "dich", tu: [x, y], hop0: { ...hop } }
    : { che_do: "moi", tu: [x, y] };
  canvas.setPointerCapture(e.pointerId);
});
canvas.addEventListener("pointermove", (e) => {
  const [x, y] = phan_tram(e);
  if (!keo) {
    canvas.style.cursor = con_tro(x, y);
    dat_tay(anh_san_sang && cho_hop && !dang_gui_hop ? tay_duoi(x, y) : -1);
    return;
  }
  if (keo.che_do === "moi") {
    hop = { x: Math.min(keo.tu[0], x), y: Math.min(keo.tu[1], y),
            w: Math.abs(x - keo.tu[0]), h: Math.abs(y - keo.tu[1]) };
  } else if (keo.che_do === "dich") {
    const b = keo.hop0;
    hop = { ...b, x: kep(b.x + x - keo.tu[0], 1 - b.w), y: kep(b.y + y - keo.tu[1], 1 - b.h) };
  } else {
    // Doi bien roi chuan hoa lai: keo lat qua canh doi dien van ra hop hop le.
    const c = keo.canh, o = keo.hop0;
    const x0 = c.trai ? x : o.x, x1 = c.phai ? x : o.x + o.w;
    const y0 = c.tren ? y : o.y, y1 = c.duoi ? y : o.y + o.h;
    hop = { x: Math.min(x0, x1), y: Math.min(y0, y1),
            w: Math.abs(x1 - x0), h: Math.abs(y1 - y0) };
  }
  ve_hop();
});
function cap_nhat_hop() {
  const du = hop && hop.w > 0 && hop.h > 0;
  // Mot cho duy nhat ghi hop nguoc ve trang thai, nen moi duong sua hop deu di qua day.
  if (pham_vi === "rieng") {
    if (du) hop_rieng.set(cue_i(), { ...hop }); else hop_rieng.delete(cue_i());
  } else {
    hop_chung = du ? { ...hop } : null;
  }
  const co = !!hop_chung || hop_rieng.size > 0;
  const khoa = dang_gui_hop || !cho_hop;
  $("hop-gui").disabled = !co || !anh_san_sang || khoa;
  $("hop-bo").disabled = khoa;
  $("hop-luu-nhom").disabled = !co || khoa;
  $("toa-do-fields").disabled = !anh_san_sang || khoa;
  $("pham-vi-fields").disabled = !anh_san_sang || khoa;
  $("day-fields").disabled = !anh_san_sang || khoa;
  $("khung-thumbnails").querySelectorAll("button").forEach((b, i) => {
    b.classList.toggle("rieng", hop_rieng.has(khung_ds[i] ? khung_ds[i].i : -1));
  });
  const rieng = hop_rieng.size ? ` · ${hop_rieng.size} câu có vùng riêng` : "";
  $("khung-hop").textContent = du
    ? `Hộp: x=${hop.x.toFixed(3)} y=${hop.y.toFixed(3)} w=${hop.w.toFixed(3)} h=${hop.h.toFixed(3)}${rieng}`
    : "Chưa có vùng hợp lệ. Vẽ hoặc nhập tọa độ bên dưới." + rieng;
  if (du) for (const k of "xywh") $("form-toa-do").elements[k].value = hop[k];
  ve_hop();
}

for (const r of document.querySelectorAll("[name=pham_vi]")) {
  r.addEventListener("change", () => {
    if (!cho_hop || dang_gui_hop) return;
    pham_vi = r.value;
    if (pham_vi === "chung") {
      hop_rieng.delete(cue_i());              // bo hop rieng, quay ve dung hop chung
      if (hop_chung) hop = { ...hop_chung };
    }
    cap_nhat_hop();
    dat_pham_vi();
  });
}

// Phu de nhay cho thuong nhay ca mot canh, khong phai mot cau le.
$("form-day").addEventListener("submit", (e) => {
  e.preventDefault();
  if (!cho_hop || dang_gui_hop) return;
  if (!hop || !hop_hop_le(hop)) { bao("Vẽ một vùng hợp lệ trước khi áp cho dải câu."); return; }
  const f = e.target.elements;
  const tu = Number(f.tu.value) - 1, den = Number(f.den.value) - 1;
  const het = khung_ds.length ? khung_ds[khung_ds.length - 1].i + 1 : 0;
  if (!Number.isInteger(tu) || !Number.isInteger(den) || tu < 0 || den < tu || den >= het) {
    bao(`Dải câu phải nằm trong 1–${het}, và câu đầu không lớn hơn câu cuối.`);
    return;
  }
  for (const k of khung_ds) if (k.i >= tu && k.i <= den) hop_rieng.set(k.i, { ...hop });
  pham_vi = hop_rieng.has(cue_i()) ? "rieng" : "chung";
  bao(`Đã áp vùng cho câu ${tu + 1}–${den + 1}.`, true);
  cap_nhat_hop();
  dat_pham_vi();
});
canvas.addEventListener("pointerup", () => {
  if (!keo) return;
  keo = null;
  const du = hop && hop.w > 0.01 && hop.h > 0.01;
  if (!du) { hop = null; ve_hop(); }     // co rut hop ve gan 0 cung la cach xoa
  cap_nhat_hop();
});
canvas.addEventListener("pointercancel", () => { keo = null; cap_nhat_hop(); });
canvas.addEventListener("pointerleave", () => dat_tay(-1));
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

// Hop chung mang cue: null (moi cau); cac cau cung mot hop rieng duoc gop lai.
function xay_vung() {
  const ra = hop_chung ? [{ ...hop_chung, cue: null }] : [];
  const gom = new Map();
  for (const i of [...hop_rieng.keys()].sort((a, b) => a - b)) {
    const h = hop_rieng.get(i);
    const khoa = `${h.x}|${h.y}|${h.w}|${h.h}`;
    if (!gom.has(khoa)) gom.set(khoa, { ...h, cue: [] });
    gom.get(khoa).cue.push(i);
  }
  return [...ra, ...gom.values()];
}

$("hop-gui").onclick = () => gui_hop(xay_vung());
$("hop-bo").onclick = () => gui_hop(null);

async function gui_hop(gia_tri) {
  if (!cid || !khung_ds.length || dang_gui_hop || !cho_hop) return;
  if (gia_tri !== null && (!anh_san_sang || !gia_tri.length || !gia_tri.every(hop_hop_le))) return;
  dang_gui_hop = true;
  $("hop-gui").disabled = $("hop-bo").disabled = true;
  $("toa-do-fields").disabled = true;
  bao("");
  try {
    await goi(`/api/cong-viec/${cid}/hop`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      // che_do_vung tuong minh: backend mac dinh cong_them cho payload cu, nen
      // frontend moi phai tu noi no dung nghia thay the ma man hinh nay mo ta.
      body: JSON.stringify(gia_tri === null ? { co_blur: false }
        : { co_blur: true, che_do_vung: "thay_the", vung: gia_tri,
            luu_nhom: $("hop-luu-nhom").checked }),
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
