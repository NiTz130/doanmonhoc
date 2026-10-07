# Tài liệu tổng hợp để viết báo cáo

**Ngày rà:** 2026-10-07 · **Nhánh:** `main` · **Nguồn duy nhất:** mã nguồn trong repo tại thời điểm rà.

**Người đọc:** thành viên nhóm viết báo cáo, slide và chuẩn bị bảo vệ.
**Mục đích:** cho mỗi con số, tên hàm, khoá JSON và chữ ký cache một chỗ tra đúng với mã.

Tài liệu này không dẫn lại `DE_CUONG.md`, `DAC_TA_YEU_CAU.md` hay thiết kế cũ. Khi có xung đột, mã thắng.
Tài liệu **không ghi số dòng** (số dòng đổi sau mỗi lần sửa): tìm theo tên hàm bằng `grep`.

---

## 1. Hệ thống làm gì

Web app chạy cục bộ. Người dùng tải một video có thoại tiếng Anh lên trình duyệt. Hệ thống:

1. lấy phụ đề gốc (file `.srt` cạnh video → track chữ nhúng → nhận dạng Whisper);
2. dừng lại để người dùng khoanh vùng phụ đề cứng trên khung hình thật;
3. dịch sang tiếng Việt **tại máy bằng NLLB-200** (không khoá API, không gửi gì ra mạng sau lần tải model đầu);
4. kết xuất video có phụ đề Việt cháy vào hình và vùng phụ đề cứng đã làm mờ — **một lần nén**, audio giữ nguyên bằng `-c:a copy`.

Bốn khối mã: `web/` (giao diện) → `api/` (HTTP) → `pipeline/dieu_phoi.py` (điều phối) → `pipeline/*.py` (xử lý).
`main.py` là CLI nội bộ để gỡ lỗi. Nó đi qua đúng `dieu_phoi.chay()` như web.

Quy mô mã (số dòng, đo ngày rà):

| Khối | Dòng | Chi tiết |
|---|---|---|
| `pipeline/` | 2 097 | `dieu_phoi` 679 · `db` 521 · `render` 206 · `translate` 196 · `srt` 161 · `markbox` 150 · `asr` 92 · `subs` 50 · `audio` 42 |
| `api/` | 662 | `app` 362 · `viec` 195 · `nhom` 105 |
| `web/` | 1 272 | `app.js` 718 · `style.css` 324 · `scene.js` 156 · `index.html` 74 |
| `main.py` | 234 | CLI nội bộ |
| Test | 3 874 | 6 file offline 2 534 · `tests_real.py` 258 · `tests_smoke.py` 204 · `tests_docx.py` 39 · `test/runtime_logic.py` 492 · `test/frontend.cjs` 347 |
| Công cụ | 118 | `tools_coverage.py` (đo độ phủ dòng, không thêm thư viện) |

Phụ thuộc Python khai trong `pyproject.toml`: `faster-whisper`, `fastapi`, `uvicorn`, `python-multipart`.
Extra `demucs` (tách giọng) và `docs` (xuất `.docx`). Bước dịch dùng `ctranslate2`, `huggingface_hub`, `tokenizers`:
cả ba đi kèm `faster-whisper`, không khai riêng. **Không còn** SDK OpenAI, `.env` hay khoá API.

---

## 2. Chức năng đã hiện thực

| # | Chức năng | Hiện thực ở | Trạng thái |
|---|---|---|---|
| F1 | Tải video lên, tạo công việc chạy nền | `api/app.py` `tai_len` | Xong |
| F2 | Hỏi trạng thái, bước, tiến độ | `api/app.py` `trang_thai` | Xong |
| F3 | Liệt kê khung mẫu kèm mốc giây và câu thoại | `api/app.py` `khung` | Xong |
| F4 | Lấy ảnh một khung | `api/app.py` `mot_khung` | Xong |
| F5 | Gửi vùng đã vẽ, chạy tiếp | `api/app.py` `nhan_hop` | Xong |
| F6 | Tải video kết quả | `api/app.py` `ket_qua` | Xong |
| F7 | Tạo, liệt kê nhóm | `api/nhom.py` `tao`, `danh_sach` | Xong |
| F8 | Đọc, ghi thuật ngữ nhóm | `api/nhom.py` `doc_thuat_ngu`, `dat_thuat_ngu` | Xong |
| F9 | Đọc, ghi vùng làm mờ mặc định của nhóm | `api/nhom.py` `doc_hop`, `dat_hop` | Xong |
| F10 | Lấy phụ đề sidecar hoặc track nhúng | `pipeline/subs.py` `tim_phu_de` | Xong |
| F11 | Nhận dạng Whisper, tách câu theo từ, lùi CPU | `pipeline/asr.py` `nhan_dang` | Xong |
| F12 | Tách giọng hát bằng Demucs | `pipeline/audio.py` `tach`, cờ `separate` | Xong (extra `demucs`) |
| F13 | Dịch theo lô tại máy, giữ đúng số cue, ép thuật ngữ | `pipeline/translate.py` `dich`, `tao_goi_cuc_bo` | Xong |
| F14 | Nhiều vùng làm mờ gắn câu thoại cụ thể | `markbox.kiem_vung` + `dieu_phoi._phan_cue` | Xong |
| F15 | Làm mờ và cháy phụ đề trong một lần encode | `pipeline/render.py` `ket_xuat` | Xong |
| F16 | Chạy lại theo chữ ký nội dung | `dieu_phoi._cache`, `_ghi_manifest` | Xong |
| F17 | CLI: một video, cả thư mục, quản lý nhóm, vận hành CSDL | `main.py` `tao_parser` | Xong (nội bộ) |
| F18 | Chặn request khác nguồn và Host lạ | `api/app.py` `chan_khac_nguon`, `TrustedHostMiddleware` | Xong |
| F19 | Danh sách công việc: lọc trạng thái, sắp xếp, phân trang | `api/app.py` `danh_sach_cong_viec` | Xong (API) |
| F20 | Tìm, sắp xếp, phân trang nhóm và thuật ngữ | `api/nhom.py` `danh_sach`, `doc_thuat_ngu`; `db.liet_ke_nhom` | Xong (API) |
| F21 | Xoá nhóm, xoá thuật ngữ (`409` khi nhóm có việc đang chạy) | `api/nhom.py` `xoa`, `xoa_thuat_ngu`; `dieu_phoi.nhom_xoa` | Xong (API, CLI) |
| F22 | Đọc nhật ký chạy từng bước và lịch sử đổi nhóm, thuật ngữ | `api/app.py` `nhat_ky`, `lich_su` | Xong (API, CLI `lich-su`) |
| F23 | Lịch sử đổi nhóm, thuật ngữ do trigger ghi | `db.SCHEMA` (6 trigger `ls_*`) | Xong |
| F24 | Sao lưu, khôi phục CSDL; tự sao lưu lúc khởi động, giữ 5 bản | `dieu_phoi.sao_luu`, `sao_luu_tu_dong`, `khoi_phuc` | Xong (khôi phục chỉ CLI) |
| F25 | Dọn kết quả và cache cũ dưới `work/tai_len/` | `dieu_phoi.don_dep` | Xong (CLI) |
| F26 | Kiểm tuỳ chọn ở một chỗ, API trả `400` | `dieu_phoi.kiem_tuy_chon` | Xong |
| F27 | Trích khung mẫu song song (4 ffmpeg cùng lúc), giữ thứ tự | `markbox.trich_khung` | Xong |
| F28 | F5 giữ công việc đang theo dõi (`sessionStorage`) | `web/app.js` `luu_viec`, `nho_viec` | Xong |

**Không có trong mã (đã xác nhận):** OCR tự dò vùng chữ, TTS lồng tiếng, đăng nhập, hàng đợi ngoài
(Celery/Redis), WebSocket, ORM, framework test, xử lý song song nhiều video cùng một nguồn.

---

## 3. Ràng buộc mà mã thực sự bảo đảm

| Ràng buộc | Bảo đảm bằng cách nào | Hàm |
|---|---|---|
| Một lần nén | Một lệnh `ffmpeg`: `crop → gblur → overlay → subtitles` trong cùng `-filter_complex`; `-c:a copy` | `render.ket_xuat` |
| Ghi nguyên tử | `mkstemp` cùng thư mục đích → ghi → kiểm → `os.replace` | `srt.file_tam` |
| Không báo xong nhầm | Manifest ghi **sau** artifact; crash giữa chừng chỉ thành cache miss | `dieu_phoi._ghi_manifest` |
| Một tiến trình cho một work dir | Lock mở bằng chế độ `"x"` (tạo độc quyền), không dùng `exists()` rồi tạo | `srt.gianh_khoa` |
| Lock sót không tự đoán là chết | Không timeout, không tự xoá; người dùng xoá tay | `srt.gianh_khoa` |
| Timestamp không phụ thuộc model | Cue kết quả dựng lại từ `bat_dau`, `ket_thuc` của cue nguồn | `dieu_phoi._buoc_dich` |
| Toạ độ độc lập độ phân giải | Hộp lưu phần trăm 0–1, đổi sang pixel lúc render | `markbox.hop_sang_pixel` |
| Một validator hình học | `kiem_hop`, `kiem_vung` phục vụ CLI, thân request, JSON trên đĩa và DB | `markbox` |
| `api/` không chứa logic xử lý | Không `subprocess`, không nạp model, không ghép filtergraph; kiểm video bằng `dieu_phoi.nhan_dien` | `api/app._nhan_file` |
| Phụ thuộc một chiều | `asr`, `audio`, `subs`, `translate`, `markbox`, `render`, `srt` không import `db`, không biết `fastapi` | kiểm: `grep -ln "import db\|fastapi" pipeline/*.py` |
| Công việc không treo sau restart | Lifespan đánh `loi` cho công việc mất chủ sở hữu | `app.vong_doi`, `db.don_cong_viec_mat_ho_so` |
| Web chỉ phục vụ máy cục bộ | Host chỉ `127.0.0.1`, `localhost`; POST khác nguồn bị `403` | `app.chan_khac_nguon` |
| Từ chối file quá lớn sớm | `Content-Length` quá 4 GiB bị `413` trước khi nhận thân request | `app.chan_khac_nguon` |
| `GET` không ghi dữ liệu | Tra nhóm không có thì `404`, không tạo; chỉ đường ghi mới dùng `lay_nhom` | `db.tim_nhom` |
| Không đường ghi nào bỏ sót lịch sử | Trigger SQLite, không phải mã ứng dụng: CLI, API, thuật ngữ học trong job, xoá dây chuyền đều ghi | `db.SCHEMA` `ls_*` |
| Khôi phục không làm mất bản đang dùng | Kiểm file (`integrity_check`, đủ bảng) **trước**, chụp bản hiện tại, rồi mới thay | `dieu_phoi.khoi_phuc`, `db._kiem_file_db` |
| Dọn dẹp không xoá nhầm | Mặc định chỉ liệt kê; chỉ xoá dưới `work/tai_len/`; bỏ qua việc đang chạy, thư mục có `.lock`, mục mới; từ chối liên kết trỏ ra ngoài `work/` | `dieu_phoi.don_dep` |

---

## 4. Cấu trúc project

```
doanmonhoc/
├── api/                  tầng HTTP — không chứa logic xử lý (CS-6)
│   ├── app.py            router /api: tải lên · trạng thái · khung · hộp · kết quả · danh sách · nhật ký · lịch sử · sao lưu; lifespan; chặn khác nguồn
│   ├── viec.py           tác vụ nền, sổ hồ sơ cid → HoSo trong RAM, giữ và nhả claim
│   └── nhom.py           router /api/nhom: nhóm · thuật ngữ · vùng mặc định · tìm, phân trang, xoá
├── pipeline/             toàn bộ xử lý; chỉ dieu_phoi.py được biết SQLite
│   ├── dieu_phoi.py      điều phối 5 mốc, manifest, cache, quản lý nhóm, batch, sao lưu, dọn dẹp
│   ├── db.py             schema 6 bảng, 6 trigger, 4 chỉ mục và mọi truy vấn
│   ├── render.py         khoảng bật mờ, sinh ASS, filtergraph, chọn encoder
│   ├── translate.py      dịch NLLB cục bộ, phục hồi có chặn, thẻ giữ chỗ thuật ngữ
│   ├── srt.py            SRT, chữ ký nội dung, ghi nguyên tử, lock
│   ├── markbox.py        validator hình học duy nhất, trích khung mẫu
│   ├── asr.py            faster-whisper, tách câu theo từ, lùi CPU
│   ├── subs.py           tìm sidecar và track chữ nhúng
│   └── audio.py          WAV mono 16 kHz, Demucs tuỳ chọn
├── web/                  frontend thuần, không bundler, không framework
│   ├── index.html        một file, 4 <section> ẩn/hiện theo hash
│   ├── app.js · scene.js · style.css · fonts/ · vendor/three/
├── main.py               CLI nội bộ: video · batch · nhom · sao-luu · khoi-phuc · don-dep · lich-su
├── test_pipeline.py      cổng chạy duy nhất của test offline (gom 5 file tests_*.py); cờ --smoke, --real
├── tests_api.py · tests_db.py · tests_media.py · tests_translate.py · tests_van_hanh.py    test offline
├── tests_smoke.py        test media thật bằng lavfi, cần ffmpeg (chạy bằng --smoke)
├── tests_real.py         GPU + Whisper + NLLB + ffmpeg thật, không hàm giả (chạy bằng --real)
├── tools_coverage.py     đo độ phủ dòng của test offline (sys.monitoring, không thêm thư viện)
├── tests_docx.py         kiểm tools_md2docx.py, chạy riêng, cần extra docs
├── test/runtime_logic.py uvicorn + ffmpeg + SQLite thật, KHÔNG nằm trong cổng chạy
├── test/frontend.cjs     Playwright + API giả lập
├── docs/                 tài liệu và sơ đồ
├── work/                 trong .gitignore: artifact, DB, file tải lên
├── pyproject.toml · package.json · start_system.bat · .githooks/
```

**Bốn quy ước đặt tên có hiệu lực:**

1. **IC-3** — định danh nội bộ viết tiếng Việt không dấu: `dieu_phoi`, `thu_muc_lam_viec`, `vung_blur`, `cho_chon_khung`.
   Tên API và tham số đã công bố giữ nguyên.
2. Comment trong `.py` phần lớn không dấu. Chuỗi hiển thị cho người dùng có dấu (ví dụ `db.LOI_MAT_HO_SO`).
3. Hàm bắt đầu bằng `_` là nội bộ module. Ngoại lệ có chủ ý: test thay `dieu_phoi._nap` bằng bản giả.
4. File test đặt tên theo người phụ trách, không theo module được kiểm. `tests_van_hanh.py` gom test của các chức năng vận hành.

**Tài liệu trong `docs/`:**

| File | Nội dung |
|---|---|
| `BAO_CAO_TONG_HOP.md` | tài liệu này |
| `DE_CUONG.md` · `DAC_TA_YEU_CAU.md` · `PHAN_CONG.md` · `GIT.md` · `LOI_MO_DAU_KET_LUAN.md` | đề cương, đặc tả, phân công, quy trình Git, lời mở đầu và kết luận |
| `kientruc` · `usecase` · `sequence` · `luongdulieu` · `pipeline` · `erd` (`.html`, `.png`, `.json`) | sơ đồ; sửa file `.json` rồi chạy lại `archify deliver` |
| `openapi.json` | sinh từ `api.app.app.openapi()` |
| `schema.sql` | khớp `pipeline/db.py` `SCHEMA` |
| `ketqua/` · `khaosat/` | ảnh và biên bản kiểm thử; khảo sát công cụ cùng loại |
| `tuan3/` · `tuan4/` | tài liệu theo tuần, không thuộc bản rà này |
| `superpowers/` · `plans/` | thiết kế và kế hoạch ban đầu (lưu trữ, xem ghi chú đầu mỗi file) |

---

## 5. Kiến trúc và chiều phụ thuộc

```
web/index.html + app.js + scene.js + style.css
   │  fetch JSON, polling 1 500 ms
   ▼
api/app.py  (/api)            api/nhom.py  (/api/nhom)
   │  api/viec.py: BackgroundTasks, sổ hồ sơ cid → HoSo trong RAM
   ▼                              ▼
pipeline/dieu_phoi.py  ◄── chỉ file này gọi db.py
   │  _nap("ten") nạp module muộn
   ├── audio.py      ffmpeg → WAV mono 16 kHz PCM16 (+ Demucs)
   ├── asr.py        faster-whisper, CUDA → CPU một lần
   ├── subs.py       ffprobe/ffmpeg, sidecar hoặc track chữ
   ├── translate.py  NLLB-200 600M qua CTranslate2, chạy tại máy
   ├── markbox.py    validator hình học + trích khung
   ├── render.py     filtergraph + tự sinh ASS
   ├── srt.py        SRT, chữ ký, ghi nguyên tử, lock
   └── db.py         SQLite 6 bảng, trigger lịch sử
```

Ba điều cần nói trong báo cáo:

1. **`_nap(ten)`** nạp module xử lý muộn bằng `importlib`. Test thay hàm này bằng bản giả nên chạy được toàn bộ
   luồng mà không cần ffmpeg, GPU hay mạng. Đổi sang `import` thẳng ở đầu file là phá tầng test offline.
2. **Module xử lý trả dữ liệu thuần.** Không module nào biết `sqlite3` hay `fastapi`.
   CLI và web không lệch kết quả vì cùng gọi `dieu_phoi.chay()`.
3. **`api/nhom.py` không gọi `db.py`.** Nó đi qua các hàm `nhom_*` của `dieu_phoi`: `nhom_danh_sach`, `nhom_tim`,
   `nhom_tao`, `nhom_hop`, `nhom_thuat_ngu`, `nhom_thuat_ngu_tim`, `nhom_dat_thuat_ngu`, `nhom_dat_hop`, `nhom_xoa`,
   `nhom_xoa_thuat_ngu`. Các route danh sách của `api/app.py` cũng đi qua `dieu_phoi` (`cong_viec_tim`, `nhat_ky_tim`,
   `lich_su_tim`, `sao_luu`).

---

## 6. Module và hàm công khai

### 6.1 `pipeline/srt.py` — nền móng dùng chung

| Hàm | Vào → Ra | Điều cần biết |
|---|---|---|
| `Cue` | dataclass `(idx, bat_dau, ket_thuc, text)` | `frozen=True`; thời gian tính bằng giây |
| `doc_srt(path, bo_cue_hong=False)` | `Path` → `list[Cue]` | đọc `utf-8-sig`; khối hỏng là `ValueError`. `bo_cue_hong=True` chỉ dùng cho nguồn ngoài (sidecar, track nhúng) |
| `ghi_srt(cues, path)` | ghi, rồi đọc lại để kiểm | ghi `utf-8`, đi qua `file_tam` |
| `kiem_cue(cues)` | ném lỗi nếu sai | rỗng, thời gian không hữu hạn, `bat_dau >= ket_thuc`, text rỗng hoặc có dòng trống |
| `file_tam(path)` | context manager | `mkstemp` cùng thư mục → `os.replace`; lỗi thì xoá file tạm |
| `ghi_json`, `doc_json` | | `doc_json` trả `{}` khi file thiếu, hỏng hoặc không phải object |
| `bam_file(path)` | → SHA256 | `hashlib.file_digest`, không nạp cả file vào RAM |
| `chu_ky(du_lieu)` | → SHA256 | `json.dumps(sort_keys=True, allow_nan=False)`, ổn định giữa các lần chạy |
| `thu_muc_lam_viec(video)` | → `work/<stem>-<8 hex>` | băm **đường dẫn**, không băm nội dung |
| `gianh_khoa(work)` | → `Path` của `.lock` | mở `"x"`; đã có thì `FileExistsError` kèm hướng dẫn xoá tay. Caller tự nhả |
| `khoa_work(work)` | context manager | bọc `gianh_khoa`, nhả trong `finally` |

### 6.2 `pipeline/markbox.py` — validator hình học duy nhất (LD-8)

| Hàm | Vào → Ra | Điều cần biết |
|---|---|---|
| `kiem_hop(hop, W?, H?)` | dict → dict chuẩn hoá | `x, y ∈ [0,1)`, `w, h > 0`, `x+w ≤ 1`, `y+h ≤ 1`; `bool` không phải số; có `W`, `H` thì kiểm cả làm tròn pixel |
| `kiem_vung(vung, W?, H?, so_cue?)` | dict hoặc list → `list[dict]` có khoá `cue` | tối đa một vùng chung; một câu không thuộc hai vùng riêng; chỉ số câu phải `< so_cue` |
| `hop_chinh(vung)` | → một hộp | hộp chung thắng; không có thì lấy hộp phủ nhiều câu nhất |
| `hop_sang_pixel(hop, W, H)` | → `(x, y, w, h)` pixel chẵn | dưới 2×2 là `ValueError` |
| `tach_hop("x,y,w,h")` | → dict | chỉ tách chuỗi; `kiem_hop` mới kiểm |
| `trich_khung(video, cues, work)` | → `list[Path]` | một lần `ffmpeg` seek cho **mỗi** cue, tại `bat_dau + 0,3 s` |
| `moc_khung(cues)` | → `[{i, giay, text}]` | thứ tự khớp `trich_khung` |

### 6.3 `pipeline/render.py` — kết xuất

| Hàm | Vào → Ra | Điều cần biết |
|---|---|---|
| `cue_thanh_khoang(cues, thoi_luong?, nghi, gap, toi_da)` | → `[(a, b)]` | nới ±0,4 s, gộp khoảng cách ≤ 1 s; quá 50 khoảng thì nới ngưỡng gộp gấp đôi rồi lặp |
| `khoang_mo` | bí danh của `cue_thanh_khoang` | tên `dieu_phoi` đang gọi |
| `gop_khoang(khoang)` | → `[(a, b)]` | chỉ gộp khoảng chồng hoặc chạm; không nới, không áp `TOI_DA` |
| `kieu_chu(W, H, px?, font_scale)` | → dict style | có hộp thì suy từ hộp; không thì dùng hồ sơ hình học |
| `viet_ass(cues, style, path)` | ghi `.ass` | tự ghi header để `PlayResX/Y` bằng kích thước video thật |
| `bo_ma_hoa()` | → tuple tham số ffmpeg | `lru_cache`; **encode thử thật** `h264_nvenc` |
| `ket_xuat(video, srt, vung, style, ra, loai_tru_chung?)` | → `Path` | một lệnh ffmpeg; xuất file tạm, `ffprobe` kiểm, rồi `os.replace` |

### 6.4 `translate` · `asr` · `subs` · `audio`

| Hàm | Vào → Ra | Điều cần biết |
|---|---|---|
| `translate.dich(lines, glossary, goi, lo=25)` | → `KetQua(ban, thuat_ngu_moi, giu_nguon, token_vao, token_ra)` | `goi` là callable tiêm vào; test không cần model |
| `translate.tao_goi_cuc_bo(repo)` | → callable | model `JustFrederik/nllb-200-distilled-600M-ct2-int8`, nạp ở lần dịch đầu |
| `asr.nhan_dang(wav, ra, lang, model, tao_model?, vad)` | ghi `.srt` | CUDA hỏng đúng kiểu thì lùi CPU **một lần** |
| `asr.loi_cuda(exc)` | → bool | khớp 9 chuỗi lỗi CUDA, cuDNN, cuBLAS; lỗi khác không nuốt |
| `asr.tach_cau(segment)` | → `list[Cue]` | tách một segment nhiều câu tại dấu kết câu theo mốc từng từ (bỏ qua `Mr.`, `Dr.`…) |
| `asr.gop_cau(cues, gap=1.0, toi_da=10.0)` | → `list[Cue]` | gộp mảnh liền nhau cho đến khi gặp dấu kết câu |
| `subs.tim_sidecar(video, lang)` | → `Path` hoặc `None` | thử `.en.srt`, `.eng.srt`, rồi `.srt` |
| `subs.probe_subs(video)` | → `list[dict]` | `ffprobe` liệt kê stream phụ đề |
| `subs.tim_phu_de(video, ra, lang)` | → bool | sidecar trước, rồi track chữ; track dạng ảnh coi như không có |
| `audio.tach(video, ra, separate)` | → `Path` | mono 16 kHz PCM16; `separate` mà thiếu Demucs thì báo lỗi ngay |
| `audio.kiem_wav(path)` | ném lỗi nếu sai | kênh, tần số, độ rộng mẫu, số frame phải đúng |

### 6.5 `pipeline/dieu_phoi.py` — điều phối

Công khai: `chay`, `nhan_dien`, `dich_batch`, `tao_goi`, `kiem_tuy_chon`, các hàm `nhom_*`, `cong_viec_tim`, `nhat_ky_tim`,
`lich_su_tim`, `sao_luu`, `sao_luu_tu_dong`, `khoi_phuc`, `don_dep`, `TuyChon`, `KetQua`, `ChoChonKhung`.

| Hàm | Vào → Ra |
|---|---|
| `chay(video, tuy_chon?, bao_tien_do?, con?, goi?, da_khoa?)` | → `KetQua`; `da_khoa=True` khi caller đã giữ lock |
| `nhan_dien(video)` | → `(W, H, thoi_luong)` bằng `ffprobe`; hoán đổi `W`, `H` khi video xoay 90°. Là **validator video duy nhất** |
| `dich_batch(thu_muc)` | → `[(nguồn, đích)]`; từ chối trùng đích hoặc đích trùng đầu vào trước mọi side effect |
| `tao_goi(model_dich)` | → hàm dịch NLLB cục bộ (tham số `model_dich` hiện không đổi model) |
| `kiem_tuy_chon(tc, chat=False)` | **Validator tuỳ chọn duy nhất.** CLI gọi qua `chay`, API gọi trực tiếp để trả `400`. `chat=True` (web) còn hạn chế `model`, `model_dich` vào danh sách đã biết |
| `sao_luu(con, thu_muc?, dich?)` | → đường dẫn bản sao lưu `subtitles-<thời gian>.db` |
| `sao_luu_tu_dong(con, thu_muc, giu=5)` | sao lưu lúc khởi động server, xoá bản `subtitles-*` cũ quá 5 bản; không xoá `truoc-khoi-phuc-*` |
| `khoi_phuc(con, nguon, thu_muc?)` | kiểm `nguon` trước, chụp bản hiện tại thành `truoc-khoi-phuc-*`, rồi thay; trả đường dẫn bản chụp |
| `don_dep(goc?, ngay=7, thuc_hien=False, con?)` | → `[(đường dẫn, byte)]`; chỉ xoá khi `thuc_hien=True` |

`TuyChon` (mặc định): `nhom=None`, `lang="en"`, `model="large-v3"`, `model_dich="nllb-cuc-bo"`, `blur="auto"`,
`blur_box=None`, `font_scale=0.42`, `separate=False`, `vad=True`, `force_asr=False`, `force=False`.
Ba trường `nguon_sub`, `force_dich`, `ky_cue` là trạng thái của một lượt đang tiếp tục, không phải cờ người dùng.

### 6.6 `api/`

| Hàm | Vai trò |
|---|---|
| `app.vong_doi` | lifespan lúc khởi động: `db.don_cong_viec_mat_ho_so`, `sao_luu_tu_dong`, `viec.don_khung_mo_coi` |
| `app.chan_khac_nguon` | middleware: POST có `Origin` khác `scheme://host` bị `403`; `POST /api/video` có `Content-Length` quá giới hạn bị `413` |
| `app._nhan_file(tep)` | ghi ra ngoài `work/`, tính SHA256 theo khối, `ffprobe` xong mới nhận |
| `app._canonical(bam, nhom)` | đường dẫn `nguon/<băm nhóm>/<sha256>/nguon.media` |
| `app._cong_bo(tam, dich, bam)` | đích đã có thì **phải trùng nội dung**, lệch là `409` |
| `viec.dat`, `lay`, `dat_hop`, `tra_checkpoint`, `nha_claim`, `dang_theo_doi` | sổ hồ sơ trong RAM, dưới `threading.Lock` |
| `viec.don_khung_mo_coi(tai_len)` | lúc khởi động xoá `work/tai_len/<cid>/khung/` của lượt không còn ai theo dõi |
| `viec.chay_nen(cid)` | tác vụ nền: giành lock nếu chưa có, gọi `dieu_phoi.chay`, nhả lock ở `finally` |
| `viec.tao_goi(tc)` | trả hàm dịch NLLB; model nạp muộn, chỉ tải ở lần dịch thật đầu tiên |

---

## 7. Luồng xử lý và mốc tiến độ

`dieu_phoi._chay` báo tiến độ qua `bao_tien_do(buoc, ti_le)`:

| Mốc | `buoc` | `tien_do` | Việc thật |
|---|---|---|---|
| 1 | `nhan_dien` | 0.00 | `ffprobe` lấy W, H, thời lượng |
| 2 | `sub_goc` | 0.10 | chọn nguồn phụ đề; nếu ASR thì chạy bước `audio` lồng bên trong |
| — | `canh_bao` | 0.10 | chỉ khi phụ đề ASR phủ dưới 25% thời lượng (`TI_LE_PHU_TOI_THIEU`) |
| 3 | `vung_blur` | 0.40 | vùng làm mờ; thiếu hộp thì dừng ở `cho_chon_khung` |
| 4 | `dich` | 0.50 | dịch NLLB theo lô |
| 5 | `render` | 0.85 → 1.00 | một lệnh ffmpeg |

**Vì sao vùng mờ đứng trước bước dịch:** đó là bước duy nhất cần người. Đặt sớm thì thời gian chờ của máy và của
người chồng lên nhau, và người bỏ cuộc ở màn vẽ hộp không tốn công dịch.

`KetQua.trang_thai` nhận một trong ba giá trị: `xong`, `suy_giam`, `cho_chon_khung`.
`suy_giam` nghĩa là đã xuất video nhưng còn cue giữ nguyên bản gốc, **hoặc** phụ đề ASR phủ quá ít.
`KetQua.canh_bao` giữ lý do; `viec.chay_nen` ghi lý do vào cột `cong_viec.loi`.

---

## 8. Thuật toán và xử lý quan trọng

### A1 — Gộp khoảng bật mờ, ngưỡng tự nới

Bài toán: mỗi câu cần một khoảng bật vùng mờ, nhưng chuỗi `enable` quá dài làm vỡ filtergraph.

```
nới mỗi cue ±0,4 s, kẹp trong [0, thời lượng]
lặp:
    gộp hai khoảng nếu khoảng cách ≤ gap
    nếu số khoảng ≤ 50        → trả kết quả
    nếu gap ≥ thời lượng      → trả [(0, thời lượng)]
    gap ← gap × 2
```

Nới ngưỡng thay vì cắt bớt khoảng: cắt bớt là bỏ mờ ở các câu phía sau (sai thầm lặng).
Nới ngưỡng chỉ làm mờ thừa ở quãng không có thoại.

### A2 — Chia đôi lô khi bản dịch hỏng

```
dịch(indexes, depth = 0):
    valid ← gọi model một lần cho cả lô
    nếu valid rỗng và len(indexes) > 1 và depth < 2:
        chia đôi, đệ quy hai nửa với depth + 1; dừng
    với mỗi i trong indexes:
        nếu i chưa có bản dịch → hỏi lẻ đúng cue đó
        nếu vẫn không có       → GIỮ NGUYÊN bản gốc, ghi i vào giu_nguon
```

Chặn ở `depth < 2` nên chi phí xấu nhất là hằng số. Cue nguồn không bao giờ mất; xấu nhất là không được dịch,
và điều đó nổi lên thành trạng thái `suy_giam`.

### A3 — Ép thuật ngữ bằng thẻ giữ chỗ (NLLB)

Model dịch máy không nhận glossary trong prompt. `translate` ép thuật ngữ như sau:

1. `_che`: thay mỗi thuật ngữ nguồn (cụm dài xử lý trước, khớp theo ranh giới từ, không phân biệt hoa thường)
   bằng thẻ `Zq<i>x`, nhớ bản dịch tương ứng.
2. Model dịch câu đã che.
3. `_tra`: thay thẻ bằng bản dịch thuật ngữ. Thẻ bị mất hoặc biến dạng → trả `None`.
4. Câu `None` được dịch lại **không ép thuật ngữ**, kèm cảnh báo. Thà mất thuật ngữ còn hơn để rác vào video.

`thuat_ngu_moi` luôn rỗng: model dịch máy không tự rút thuật ngữ. Thuật ngữ chỉ có khi người dùng nhập.

### A4 — Chọn hộp đại diện

```
hop_chinh(vung) = vùng đầu tiên có cue = None          (hộp chung)
                  nếu không có → vùng phủ nhiều câu nhất
```

Hai nơi dùng quy tắc này: kiểu chữ phụ đề Việt và khung mặc định lưu cho nhóm. Một quy tắc duy nhất giữ hai nơi khỏi lệch.
`dieu_phoi` chọn hộp đại diện trên danh sách **thô**, trước khi trừ cue, để việc trừ hết câu khỏi vùng chung
không làm kiểu chữ nhảy sang vùng khác.

### A5 — Phần trăm sang pixel chẵn

```
bx = ⌊x·W⌋ làm tròn xuống số chẵn            by = ⌊y·H⌋ làm tròn xuống số chẵn
bw = min(W − bx, ⌈w·W⌉ làm tròn lên chẵn) rồi làm tròn xuống chẵn
bh = min(H − by, ⌈h·H⌉ làm tròn lên chẵn) rồi làm tròn xuống chẵn
bw < 2 hoặc bh < 2 → ValueError
```

`crop` của ffmpeg đòi kích thước chẵn với màu 4:2:0. Phép `min(W − bx, …)` giữ hộp sát mép phải khỏi tràn ra ngoài.

### A6 — Phát hiện bản dịch đã sửa tay

Khi hash `sub_vi.srt` khác hash trong manifest, có hai khả năng: file hỏng, hoặc người dùng sửa lời. Phân biệt bằng **cấu trúc**:

```
_sua_tay(ra, goc) = đọc được ra thành SRT hợp lệ
                  ∧ số cue bằng số cue nguồn
                  ∧ mọi cặp (bat_dau, ket_thuc) trùng khít
```

Đúng cả ba: giữ bản sửa, ghi manifest với `sua_tay=True`. Thiếu một điều: cache miss và dịch lại.

### A7 — Đường lui CUDA → CPU

```
thử trên "cuda" (compute int8_float16)
gặp RuntimeError/OSError:
    không khớp 9 chuỗi lỗi CUDA đã biết → ném tiếp
    xoá traceback, gc.collect()              # nhả tham chiếu tới model GPU hỏng
    cảnh báo, thử lại trên "cpu" (int8) ĐÚNG MỘT LẦN
    CPU cũng hỏng → ném lỗi CPU, gắn lỗi GPU làm nguyên nhân
```

NLLB dùng cùng `loi_cuda`: nạp `device="auto"`, lỗi CUDA lúc nạp hay lúc dịch thì lùi CPU một lần.
Hai model (Whisper, NLLB) không cùng chiếm VRAM vì NLLB nạp muộn, sau khi Whisper xong.

### A8 — Chọn nguồn phụ đề

```
nếu lượt tiếp tục có nguon_sub → dùng đúng nguồn đã ghim, KHÔNG dò lại
ngược lại nếu force_asr        → "asr"
ngược lại:
    có sidecar .<lang>.srt hoặc .srt → "sidecar", phụ thuộc = sha256(sidecar)
    có track phụ đề dạng CHỮ         → "nhung",   phụ thuộc = sha256(video)
    còn lại                          → "asr",     phụ thuộc = sha256(audio)
```

Nhiều track chữ: chọn track có `tags.language` khớp alias của ngôn ngữ; không có thì lấy track chữ đầu.
Track dạng ảnh (`hdmv_pgs_subtitle`, `dvd_subtitle`) coi như không có. Chế độ nguồn nằm trong chữ ký `sub_goc`.

### A9 — Tách câu ASR

Whisper hay nhét nhiều câu vào một segment (mất dòng phụ đề, mất mốc giờ) hoặc ngắt giữa câu.
`tach_cau` tách segment tại dấu kết câu theo mốc từng từ. `gop_cau` gộp mảnh liền nhau (khoảng lặng ≤ 1 s, tổng ≤ 10 s)
cho đến khi gặp dấu kết câu. Kết quả: mỗi cue là một câu trọn, dễ dịch hơn.

### A10 — Phát hiện nhận dạng hỏng im lặng

Nguồn `asr` mà phụ đề phủ dưới 25% thời lượng video thì công việc kết thúc `suy_giam`, kèm gợi ý
tắt VAD (`--vad off`) hoặc tách giọng (`--separate`). Nguyên nhân hay gặp: Silero VAD coi nhạc nền là không phải tiếng nói.

---

## 9. Chạy lại: chữ ký nội dung, không phải DB

Manifest `work/<stem>-<8 hex>/trang_thai.json` giữ một bản ghi cho mỗi bước: `{"ver", "ky", "hash", …}`.
Cache hit đòi **cả ba** khớp: phiên bản bước, chữ ký phụ thuộc, hash artifact còn nguyên (`_cache`).

| Bước | Artifact | Chữ ký `ky` gồm |
|---|---|---|
| `audio` | `audio.wav` hoặc `vocals.wav` | `["audio", sha256(video), separate]` |
| `sub_goc` | `sub_goc.srt` | `["sub_goc", chế_độ_nguồn, sha256(phụ_thuộc), lang, model, vad]` |
| `sub_vi` | `sub_vi.srt` | `["sub_vi", sha256(sub_goc), model_dich, PROMPT_VER, glossary]` |
| `vung_blur` | `vung_blur.json` | `["vung_blur", sha256(video), W, H, ky_cue]` |

`ky_cue` là SHA256 của `sub_goc.srt` lúc chụp khung. Chỉ số câu thoại chỉ có nghĩa trên đúng bộ cue đã chụp:
đổi thứ tự cue mà giữ nguyên số lượng vẫn phải chọn lại vùng.

**Phiên bản hiện tại:** `VER = {"audio": 1, "sub_goc": 4, "sub_vi": 1, "vung_blur": 4}`, `PROMPT_VER = 3`.
Đổi cách sinh artifact của một bước thì tăng `VER`. Đổi cách dịch thì tăng `PROMPT_VER`.
Không tăng thì manifest cũ vẫn tính là cache hit.

Ba tính chất đáng đưa vào báo cáo:

- **Glossary nằm trong chữ ký bản dịch.** Nhóm có thuật ngữ mới thì bản dịch cũ thành cache miss.
  Để việc đó không tự lặp, sau khi ghi DB, `_buoc_dich` ghi lại manifest với baseline là glossary thật của nhóm.
- **Sửa tay `sub_vi.srt` được tôn trọng** (mục A6).
- **Áp glossary là nguyên tử.** `db.ap_dung_dich` dùng `BEGIN IMMEDIATE` và `SAVEPOINT`, đánh dấu đã áp bằng một hàng
  `nhat_ky` (`buoc='translate_apply'`, `loi` = hash artifact). Crash giữa "ghi artifact" và "ghi DB" được hoàn tất nốt
  ở lần sau, không áp hai lần.

Xoá `work/subtitles.db` mất nhóm, thuật ngữ, nhật ký; **không** mất artifact.

---

## 10. Vùng làm mờ

**Cấu trúc.** Một vùng là `{"x","y","w","h","cue"}`, toạ độ phần trăm 0–1.
`cue = None` là **hộp chung** cho mọi câu. `cue = [i, …]` là hộp riêng gắn đúng các câu đó (chỉ số từ 0).
Một `dict` trần được coi là một hộp chung, nên CLI `--blur-box`, khung mặc định của nhóm và JSON cũ đi cùng một đường.

**Vùng riêng thay vùng chung** ở đúng những câu được gán. `kiem_vung` luôn áp hai ràng buộc: tối đa một vùng chung,
và một câu không thuộc hai vùng riêng. `_phan_cue` trừ câu có vùng riêng khỏi vùng chung.
Trường `che_do_vung` không còn; payload gửi trường này bị bỏ qua như mọi khoá lạ.

**Artifact của VER cũ phải chọn lại.** Khi còn vùng gắn chỉ số câu mà không chứng minh được nó ứng với bộ cue nào,
`_buoc_hop` không lặng lẽ thay bằng hộp nhóm (như thế là xoá vùng riêng bằng một hộp chung). Nó dừng ở `cho_chon_khung`.
Test canh giữ: `test_vung_blur_ver_cu_phai_chon_lai`.

**Thứ tự ưu tiên khi chọn vùng** (trong `_buoc_hop`):

1. `blur="off"`, hoặc `blur="auto"` với video có `W/H < 1.2` → không làm mờ (`{"co_blur": false}`), không xoá hộp của nhóm.
2. Có `blur_box` truyền vào (CLI hoặc `POST /hop`) → kiểm bằng `kiem_vung`; `luu_hop_nhom` thì lưu hộp chính cho nhóm.
3. Cache `vung_blur.json` hợp lệ → dùng lại.
4. Còn vùng gắn chỉ số câu nhưng chữ ký lệch → dừng chờ chọn lại.
5. Nhóm có hộp mặc định → dùng làm điểm khởi đầu.
6. Không có gì → dừng `cho_chon_khung`.

**Khung mẫu.** `trich_khung` trích **một khung cho mỗi câu thoại**, seek tại `bat_dau + 0,3 s`, không lấy mẫu thưa.
Lý do: lấy mẫu thưa thì không ai kiểm được hộp đã phủ hết chưa; câu phụ đề nhảy chỗ nằm ngoài mẫu là lọt lưới.
Chi phí: một lần ffmpeg mỗi cue, khoảng 0,2 s ở 640×360. Bản cũ chạy tuần tự (khoảng 9 s cho 43 cue).
Nay `markbox.SONG_SONG = 4` lệnh ffmpeg chạy cùng lúc trong `ThreadPoolExecutor`, kết quả vẫn đúng thứ tự cue,
và một lệnh lỗi làm cả lượt lỗi (`test_trich_khung_song_song_giu_thu_tu_va_nem_loi`). **Chưa đo lại tốc độ**
trên máy thật. Phim hai tiếng, khoảng 2 000 cue, vẫn tốn vài trăm MB PNG; lúc đó nên trích theo yêu cầu từng khung.
Khung mẫu bị xoá ngay khi công việc ra trạng thái cuối, và lúc khởi động nếu không còn ai theo dõi.

---

## 11. Kết xuất

`render.ket_xuat`:

1. **Khoảng bật.** `cue_thanh_khoang`: nới `NGHI = 0.4 s`, gộp khoảng cách `GAP = 1.0 s`, tối đa `TOI_DA = 50` khoảng (mục A1).
2. **Mặt nạ loại trừ** (khi có vùng riêng). `gop_khoang` gộp khoảng chồng hoặc chạm, không nới, không áp `TOI_DA`.
   Vùng chung nhận thêm `*not(…)` để tắt trong khoảng có vùng riêng đang bật. Cần mặt nạ vì bước nới ±0,4 s
   và gộp của vùng chung có thể bắc cầu qua đúng câu đã có vùng riêng, làm câu đó mờ cả hai chỗ.
3. **Filtergraph.** Nối tiếp từng hộp: `split` → `crop` → `gblur=sigma=25` → `overlay=…:enable=…`.
   Hộp sau nhìn thấy kết quả của hộp trước. Cuối chuỗi là `subtitles`.
4. **Kiểu chữ.** Mã tự sinh file ASS (`viet_ass`) để `PlayResX/Y` bằng kích thước video thật
   (ffmpeg đổi SRT sang ASS với PlayRes mặc định 384×288 nên công thức pixel sẽ sai). Có hộp:
   `FontSize = max(8, round(h_hộp_px × font_scale))`, `MarginV = max(0, H − y − h)`. Không có hộp:
   `FontSize` 22 hoặc 16, `MarginV` 30 hoặc 90 theo `W/H ≥ 1.2`. `font_scale` mặc định **0.42**. Font **Arial**.
   Thẻ HTML của SRT (`<i>`, `<b>`…) và khối override `{\an8}` bị loại; `{` `}` còn lại đổi thành `(` `)`.
5. **Bộ mã hoá.** `bo_ma_hoa` encode thử thật bằng `lavfi color=s=256x256:d=0.1`. Thành công:
   `h264_nvenc -preset p5 -cq 23`. Thất bại: cảnh báo và `libx264 -preset medium -crf 23`.
   Cỡ 256×256 vì dưới cỡ tối thiểu của NVENC thì phép thử tự hỏng và báo sai GPU không dùng được.
6. **Định dạng pixel.** `-pix_fmt yuv420p`: nguồn 10-bit mà rơi về libx264 sẽ ra High 10, trình duyệt và điện thoại khó phát.
7. **Kiểm đầu ra.** `_kiem_ra` hỏi `ffprobe` có luồng video và thời lượng > 0. Kích thước file không phải bằng chứng.
   Chỉ khi đó `file_tam` mới `os.replace` lên đích.

`cwd` của lệnh ffmpeg đặt tại thư mục chứa phụ đề và truyền tên tương đối, vì đường dẫn Windows tuyệt đối
trong filtergraph phải escape thành `C\:/…`.

---

## 12. Dịch

`translate.dich` chia **lô 25 cue**. Mỗi lần gọi `goi` nhận
`{"lines": {"1": …, "25": …}, "context": 5 câu liền trước lô, "glossary": {…}}`
và trả `PhanHoi(content, finish_reason, token_vao, token_ra)`.

- **Phục hồi có chặn:** lô lỗi → chia đôi tối đa 2 tầng → hỏi lẻ từng cue → giữ nguyên bản gốc (mục A2).
- **Kiểm nội dung** (`_text`): loại chuỗi rỗng, chuỗi có dòng trống, chuỗi chứa `\x00`.
  `finish_reason != "stop"` coi như lô thất bại. Khoá dư trong phản hồi bị bỏ kèm cảnh báo.
- **Model.** `JustFrederik/nllb-200-distilled-600M-ct2-int8` (khoảng 600 MB), CTranslate2, `beam_size=4`,
  tiền tố ngôn ngữ đích `vie_Latn`. Nạp **muộn** ở lần `goi` đầu tiên: công việc chờ vẽ hộp hoặc trúng cache
  dịch không phải tải model. Tải lần đầu thất bại → `RuntimeError` hướng dẫn kiểm tra mạng rồi chạy lại.
- **Giới hạn.** `context` được gửi nhưng bộ dịch cục bộ **không dùng** nó: mỗi câu dịch riêng, không thấy câu liền kề,
  nên cách xưng hô (anh/em/tôi) có thể đổi giữa các câu. Giữ CS-1 (một cue vào, một cue ra) thì không ghép câu cho model.
- **Đếm token.** NLLB không tính token ra: `token_vao` là số token đầu vào, `token_ra = 0`. Cache hit trả `0, 0`.
  Hai số này vào bảng `nhat_ky`. Không còn chi phí API.

`db.ghi_thuat_ngu` chỉ **thêm từ mới**, không bao giờ thay bản dịch đã có (`ON CONFLICT DO NOTHING`).
Chỉ `dat_thuat_ngu` (người dùng sửa tường minh) mới ghi đè.

---

## 13. Đặc tả HTTP API

`BackgroundTasks` chạy tác vụ nền **trong chính tiến trình backend**: không hàng đợi ngoài, không WebSocket.
Tệp `docs/openapi.json` sinh từ chính ứng dụng.

### 13.1 Công việc

| Method | Đường dẫn | Vào | Ra | Lỗi |
|---|---|---|---|---|
| POST | `/api/video` | `multipart`: `file`, `nhom`, `lang`, `model`, `model_dich`, `blur`, `blur_box`, `font_scale`, `separate`, `vad`, `force_asr`, `force` | `202 {id, trang_thai:"cho"}` | `400` sai đuôi, rỗng, > 4 GiB khi đã nhận, ffprobe không đọc được, `blur` lạ, hộp sai, `lang` sai dạng, `model`/`model_dich` ngoài danh sách, `font_scale` ≤ 0 hoặc > 5, tên nhóm trống hoặc > 100 ký tự · `409` đang có tiến trình xử lý video này, hoặc nguồn đã lưu lệch nội dung · `413` `Content-Length` vượt 4 GiB (từ chối từ tiêu đề, chưa nhận file) |
| GET | `/api/cong-viec` | `trang_thai`, `sap_xep` (`tao_luc`, `cap_nhat_luc`, `tien_do`), `thu_tu`, `trang`, `moi_trang` | `[{id, trang_thai, buoc, tien_do, …}]` + `X-Tong-So` | `400` giá trị lọc hoặc sắp xếp lạ |
| GET | `/api/cong-viec/{cid}` | — | `{id, trang_thai, buoc, tien_do, loi, co_ket_qua}` | `404` |
| GET | `/api/cong-viec/{cid}/khung` | — | `[{i, giay, text}]` | `404` · `409` chưa có phụ đề gốc |
| GET | `/api/cong-viec/{cid}/khung/{i}` | — | `image/png` | `404` · `409` hồ sơ mất |
| POST | `/api/cong-viec/{cid}/hop` | `{co_blur, vung, luu_nhom}` | `{id, trang_thai, vung}` | `400` hình học, chỉ số câu, kiểu của `co_blur`/`luu_nhom` · `409` đang chạy, chưa tới bước chọn vùng, phụ đề gốc đã đổi, không còn khung mẫu, đã gửi vùng rồi |
| GET | `/api/cong-viec/{cid}/ket-qua` | — | `video/mp4` | `404` chưa có kết quả |

Đuôi video nhận: `.mp4 .mkv .mov .webm .avi .ts`. `trang_thai` bị khoá bằng `CHECK` trong schema:
`cho`, `dang_chay`, `cho_chon_khung`, `xong`, `suy_giam`, `loi`.

### 13.2 Nhóm

| Method | Đường dẫn | Ghi chú |
|---|---|---|
| GET | `/api/nhom` | `[{ten, blur_x, blur_y, blur_w, blur_h}]`; lọc `q` (không phân biệt dấu), `sap_xep` (`ten`, `tao_luc`), `thu_tu`, `trang`, `moi_trang` |
| POST | `/api/nhom` | `{ten}` → `201` |
| DELETE | `/api/nhom/{ten}` | `204`; xoá cả thuật ngữ của nhóm; `404` không có nhóm; `409` nhóm có việc đang chạy |
| GET, POST | `/api/nhom/{ten}/thuat-ngu` | GET nhận `q`, `sap_xep`, `thu_tu`, `trang`, `moi_trang`; POST nhận `{goc, dich}` (mỗi chuỗi ≤ 200 ký tự), trả cả bảng sau khi ghi |
| DELETE | `/api/nhom/{ten}/thuat-ngu/{goc}` | `204`; `404` không có thuật ngữ; `409` nhóm có việc đang chạy |
| GET, POST | `/api/nhom/{ten}/hop` | POST đi qua `markbox.kiem_hop`; `W`, `H` mặc định 1920×1080 |

Lỗi dữ liệu của router nhóm quy về `400`, không có đối tượng là `404`, nhóm đang bận là `409`; một hàm `loi_http` làm việc này.
`GET` chỉ đọc: tra nhóm không có trả `404`, **không tạo nhóm** (lỗi cũ: `GET` tạo nhóm rác). `web/` được `mount` ở `/` bằng `StaticFiles`.

### 13.2b Danh sách, nhật ký, lịch sử, sao lưu

| Method | Đường dẫn | Ghi chú |
|---|---|---|
| GET | `/api/nhat-ky` | lọc `video_id`, `buoc`, `ket_qua`; phân trang |
| GET | `/api/lich-su` | lọc `nhom`, `doi_tuong` (`nhom`, `thuat_ngu`), `hanh_dong` (`tao`, `sua`, `xoa`); phân trang |
| POST | `/api/sao-luu` | `201 {tep}`; chụp CSDL vào `work/sao_luu/`. Khôi phục **không** có qua API (web không thay được file đang mở) |

Mọi danh sách dùng chung một quy ước: `trang` từ 1, `moi_trang` mặc định 50 và tối đa 200 (`db.MAX_MOI_TRANG`), tổng số bản ghi
nằm ở header `X-Tong-So`, thân vẫn là mảng JSON như trước nên frontend cũ không vỡ. Giá trị lọc hoặc sắp xếp ngoài danh sách trắng là `400`.

### 13.3 Ranh giới tin cậy

- Chỉ nhận `Host` là `127.0.0.1`, `localhost` (và `testserver` cho `TestClient`).
- Request không phải `GET`, `HEAD`, `OPTIONS` mà có `Origin` khác nguồn của chính server bị `403`.
  Trình duyệt luôn gửi `Origin` với POST khác nguồn; CLI, `curl`, `TestClient` thì không.
- Không có đăng nhập: có chủ ý, vì chỉ chạy cục bộ. Đưa lên mạng chung thì phải thêm lớp xác thực trước.

### 13.4 Danh tính tài nguyên

File tải lên không được lưu theo tên người dùng gửi. `_nhan_file` ghi ra ngoài `work/`, tính SHA256 theo khối lúc ghi,
`ffprobe` xác nhận xong mới nhận. Sau đó nguồn vào đường dẫn canonical:

```
work/tai_len/nguon/<chu_ky(["nhom", tên_nhóm])[:16]>/<sha256_nội_dung>/nguon.media
```

Tên nhóm là một phần của danh tính vì thuật ngữ nhóm làm đổi bản dịch. `None` là namespace riêng.
Đuôi cố định `nguon.media`: đổi tên hay đuôi file không đổi danh tính. Cùng nội dung và cùng nhóm thì cùng work dir,
dùng lại cache. **Kết quả và khung mẫu tách riêng theo CID:**

```
work/tai_len/<cid>/<tên_gốc_đã_làm_sạch>_vi.mp4     kết quả của lượt này
work/tai_len/<cid>/khung/                           khung mẫu + bản sao sub_goc.srt của lượt này
work/<stem>-<8 hex>/                                work dir dùng chung: audio.wav, sub_goc.srt, sub_vi.srt,
                                                    vung_blur.json, trang_thai.json, .lock
```

---

## 14. Đồng thời và vòng đời công việc

Đây là phần khó nhất của hệ thống; nên có mục riêng trong báo cáo.

**(a) Claim nguyên tử.** `gianh_khoa` mở `.lock` bằng chế độ `"x"`. Kiểm `exists()` rồi tạo sau **không phải** claim:
hai upload cùng lúc sẽ cùng lọt qua khe hở. Web giành claim **trước khi** công bố nguồn và nhả ở mọi lối ra,
kể cả khi dừng chờ người vẽ hộp. `chay(da_khoa=True)` để không giành lại lock của chính mình.

**(b) Sổ hồ sơ trong RAM.** `viec._HO_SO: dict[str, HoSo]` với `HoSo(video, tc, khoa, checkpoint)`, dưới `threading.Lock`.
Backend một tiến trình nên dict là đủ. Restart server làm mất công việc đang dở; artifact trên đĩa vẫn còn.

**(c) Checkpoint, tiêu thụ nguyên tử.** Khi dừng ở `cho_chon_khung`, `dieu_phoi` trả
`checkpoint = {nguon_sub, ky_cue, force_dich}`. Đây là bản ghi phía server, **không bao giờ** nhận từ thân request.
`viec.dat_hop` tiêu thụ checkpoint dưới cùng một lock rồi xoá nó. Nhờ đó POST vùng lần hai ra `409`, không tạo tác vụ thứ hai.
Xếp lịch thất bại thì `tra_checkpoint` hoàn lại để người dùng gửi lại.

**(d) Gửi vùng không làm ASR chạy lại.** `nguon_sub` ghim nguồn đã chọn; lượt tiếp tục bỏ `force`, `force_asr`.
Ý định làm mới bản dịch giữ riêng trong `force_dich` cho đến khi bước dịch của lượt đó chạy xong.

**(e) Chặn checkpoint lệch trước mọi side effect.** `_nguon_con_nguyen` chạy **trước** `ffprobe`, trước khi ghi bảng `video`,
trước nhật ký, trước bước sub. Hash `sub_goc.srt` một mình là không đủ: sidecar đổi trên đĩa thì file sản phẩm vẫn y nguyên
cho đến khi bước sub chạy lại và ghi đè nó. Thiếu hash wav trong manifest là **không chứng minh được**, không đoán.

**(f) Dọn sau restart.** Lifespan gọi `db.don_cong_viec_mat_ho_so`: công việc ở `cho`, `dang_chay`, `cho_chon_khung`
mà không còn trong `_HO_SO` bị đánh `loi` kèm hướng dẫn tải lại. Không chạm `xong`, `suy_giam`, `loi`; không xoá `duong_dan_ra`.

**(g) Kết nối SQLite.** Một connection cho một request (`viec.ket_noi` qua `Depends`), mở `check_same_thread=False`
vì Starlette chạy route sync trong threadpool và có thể đổi thread giữa các phần của một request.

**(h) Thứ tự nhả claim và mở checkpoint** trong `chay_nen`: nhả claim **trước**, mở checkpoint **sau**.
Mở sớm thì `POST /hop` chen vào khe hở, tác vụ mới thấy khoá còn giá trị, rồi `finally` của tác vụ cũ xoá lock của nó.

**(i) Dọn tài nguyên.** Sổ hồ sơ trong RAM chỉ giữ `viec.GIU_XONG = 20` hồ sơ đã xong, cũ hơn thì bỏ. Khung mẫu của một lượt
bị xoá ngay khi lượt ra trạng thái cuối (`viec._ket_thuc`); lúc khởi động, `don_khung_mo_coi` xoá khung của lượt không còn ai theo dõi.
Phần còn lại dọn bằng tay: `main.py don-dep` (mặc định chỉ liệt kê).

**(j) Chạy nền tránh khoá.** Khi tác vụ nền không giành được lock, `chay_nen` báo `loi` cho công việc và dọn khung mẫu thay vì để treo.

---

## 15. Cơ sở dữ liệu

`work/subtitles.db`, 6 bảng, 4 chỉ mục, 6 trigger; schema đầy đủ ở `pipeline/db.py` (hằng `SCHEMA`) và `docs/schema.sql`
(file này sinh từ `SCHEMA`, không sửa tay). Chế độ journal là **WAL**: nhiều request đọc không chặn một request ghi.
Bảng `cong_viec` **chỉ báo tiến độ cho frontend**, không quyết định chạy lại.

| Bảng | Khoá, ràng buộc đáng nói | Dùng để làm gì |
|---|---|---|
| `nhom` | `ten` UNIQUE; `blur_x/y/w/h` | gom các tập cùng phim; giữ vùng mờ mặc định |
| `video` | `duong_dan` UNIQUE, `thu_muc_work` UNIQUE; FK `nhom_id` `ON DELETE SET NULL` | W, H, thời lượng, mốc `xong_luc` |
| `thuat_ngu` | UNIQUE `(nhom_id, goc)`; FK CASCADE | giữ tên riêng nhất quán qua nhiều tập |
| `nhat_ky` | FK `video_id` CASCADE | thời gian, token từng bước; cũng là dấu đã-áp-glossary |
| `cong_viec` | `id` TEXT (UUID4); `trang_thai` CHECK 6 giá trị | tiến độ cho frontend |
| `lich_su` | `doi_tuong` CHECK (`nhom`, `thuat_ngu`); `hanh_dong` CHECK (`tao`, `sua`, `xoa`); không FK | dấu vết đổi nhóm, thuật ngữ; chỉ trigger ghi vào |

**Chỉ mục:** `ix_nhat_ky_video(video_id, id)`, `ix_cong_viec_tt(trang_thai, tao_luc)`, `ix_lich_su_nhom(nhom_id, id)`, `ix_video_nhom(nhom_id)`.

**Trigger** (`ls_thuat_ngu_tao|sua|xoa`, `ls_nhom_tao|hop|xoa`): ghi `lich_su` ở tầng CSDL nên mọi đường ghi đều để lại dấu vết,
kể cả thuật ngữ học trong job và xoá dây chuyền khi xoá nhóm. Trigger sửa chỉ chạy khi giá trị thật sự đổi.
`lich_su` không có khoá ngoại để dòng lịch sử sống sót sau khi nhóm bị xoá.

**Sao lưu và khôi phục.** `db.sao_luu` chụp bằng API sao lưu của SQLite; `_kiem_file_db` từ chối file không phải SQLite,
không qua `integrity_check` hoặc thiếu bảng bắt buộc. `db.BANG_BAT_BUOC` có 5 bảng, không có `lich_su`: bản sao lưu cũ (trước khi có
trigger) vẫn khôi phục được, và `db.mo` tạo lại bảng, trigger còn thiếu (`test_khoi_phuc_don_cong_viec_mat_ho_so_va_ban_cu_thieu_trigger`).

`PRAGMA foreign_keys=ON` bật mỗi lần mở. `cap_nhat_cong_viec` chỉ nhận 6 cột trong danh sách trắng
(`video_id`, `trang_thai`, `buoc`, `tien_do`, `duong_dan_ra`, `loi`); cột lạ là `ValueError`.
`ghi_nhat_ky` đóng `video.xong_luc` khi và chỉ khi bước `render` thành công.
`ket_qua` của `nhat_ky` thuộc `xong`, `bo_qua`, `loi`, `suy_giam`.

---

## 16. Frontend

Một file `web/index.html` với **4 `<section>`** ẩn/hiện theo hash. Không phải 4 trang riêng.

| `id` | Màn | Nội dung chính |
|---|---|---|
| `tai-len` | Tải lên | vùng thả file, chọn nhóm, tuỳ chọn nâng cao; `scene.js` vẽ hoạt cảnh Three.js (vendored, có đường lui CSS) |
| `tien-do` | Tiến độ | thanh tiến độ ARIA, 5 bước, nút thử lại kết nối, liên kết tải kết quả |
| `khung` | Vùng làm mờ | canvas vẽ hộp, lật khung bằng ← →, phạm vi chung hoặc riêng, áp cho dải câu, tích "đặt làm mặc định cho nhóm" |
| `nhom` | Nhóm và thuật ngữ | tạo nhóm, bảng thuật ngữ, vùng mặc định |

- **Polling 1 500 ms** khi `trang_thai` là `cho` hoặc `dang_chay`. Tới `cho_chon_khung` thì tự nạp khung và dừng hỏi.
  Mất mạng thì hiện thông báo và nút thử lại, không mất thông tin công việc.
- **F5 không làm mất công việc.** `luu_viec` ghi `{id, ten}` vào `sessionStorage` của tab ngay sau khi tải lên; lúc nạp trang
  `nho_viec` đọc lại và `hoi_tien_do` khôi phục màn đúng (tiến độ hoặc vẽ hộp). Server trả `404` thì ngừng theo dõi, xoá dấu
  và báo người dùng, không hỏi mãi. Trình duyệt chặn storage thì mọi lệnh bọc `try/catch`: trang vẫn chạy, chỉ mất khả năng quay lại.
- **Chưa có màn** cho tìm kiếm, nhật ký, lịch sử, sao lưu, xoá nhóm: các chức năng này mới có ở API và CLI.
- Toạ độ tính bằng `clientWidth` nên ra thẳng phần trăm, độc lập độ phân giải.
- **Một chỗ duy nhất ghi hộp ngược về trạng thái** là `cap_nhat_hop`; kéo chuột, nhập toạ độ, áp dải câu đều đi qua đó.
- Chỉ số câu thật lấy bằng `cue_i()`, không dùng vị trí trong danh sách, vì `/khung` có thể bỏ khung hỏng.
- Frontend kiểm hộp (`hop_hop_le`) **chỉ để báo sớm**; backend quyết định.
- Khả năng tiếp cận: `aria-live` cho trạng thái, `role="progressbar"`, nhãn `sr-only`, liên kết "Đến nội dung chính",
  tôn trọng `prefers-reduced-motion`, nút dừng chuyển động, đường lui khi WebGL mất context.

---

## 17. CLI nội bộ

`main.py` **không phải sản phẩm**. Nó đi qua `dieu_phoi.chay()` như web.

```bash
py=.venv/Scripts/python.exe
$py main.py phim.mp4 --nhom "Tên phim" --blur-box 0.3,0.855,0.4,0.09
$py main.py batch ./thu_muc --nhom "Tên phim"
$py main.py nhom list | glossary <tên> | set-term <tên> <gốc> <dịch> | set-box <tên> x,y,w,h | del-term <tên> <gốc> | delete <tên>
$py main.py sao-luu [--dich FILE]        # mặc định work/sao_luu/subtitles-<thời gian>.db
$py main.py khoi-phuc FILE               # kiểm file, chụp bản hiện tại, rồi thay
$py main.py don-dep [--ngay 7] [--thuc-hien]   # mặc định chỉ liệt kê
$py main.py lich-su [--nhom TÊN] [--trang N] [--moi-trang N]
```

- `main.py <video>` không cần chữ `video`: argv được chèn lệnh con nếu đối số đầu không phải lệnh đã biết.
- `batch` **không có `-o`**. `dich_batch` tính trước mọi đích và từ chối trùng đích hoặc đích trùng đầu vào trước mọi side effect.
  File `*_vi.mp4` không được lấy làm đầu vào. Batch chạy **tuần tự** để thuật ngữ tích luỹ.
- `_preflight` kiểm `ffmpeg`, `ffprobe` trước vòng batch. Không còn kiểm khoá API.
- `stdout`, `stderr` được `reconfigure(encoding="utf-8")` vì console Windows mặc định `cp1252` làm vỡ tiếng Việt.
- CLI không có màn vẽ hộp: chưa có khung thì truyền `--blur-box` hoặc `--blur off`. Vùng riêng theo câu chỉ đặt được trên web.
- **Mã thoát:** `0` xong · `1` có lỗi, có cue giữ nguyên bản gốc, hoặc còn video chờ vẽ hộp · `130` Ctrl+C.

---

## 18. Kiểm thử — kết quả đo ngày 2026-10-07

Không framework: `assert` trần, callable giả, `TestClient`, SQLite `:memory:` (ràng buộc IC-1).

| Tầng | Lệnh | Cần gì | Kết quả |
|---|---|---|---|
| Offline | `$py test_pipeline.py` | không mạng, GPU, ffmpeg | **78/78 PASS** |
| Độ phủ | `$py tools_coverage.py --min 90` | như Offline | **91,2 %** dòng (2 039 dòng, 179 chưa chạy) |
| Media | `$py test_pipeline.py --smoke` | ffmpeg | **PASS** (`smoke media: OK`) |
| Thật | `$py test_pipeline.py --real` | GPU NVIDIA, model Whisper `base` và `large-v3`, NLLB đã tải, ffmpeg | **6/6 PASS** (RTX 4050 Laptop 6 GB) |
| Runtime | `$py test/runtime_logic.py` | uvicorn, ffmpeg, SQLite thật | **PASS** (`status: PASS`) |
| Giao diện | `npm run test:frontend` | Playwright, server tĩnh `web/` cổng 8765 | **4/4 nhóm PASS** |

Số 78 gồm: `test_pipeline.py` 11 · `tests_api.py` 20 · `tests_media.py` 12 · `tests_translate.py` 6 · `tests_db.py` 2 · `tests_van_hanh.py` 27.
Số 6 của `--real` là các hàm `real_*` trong `tests_real.py`, không thuộc 78 test offline.

Lưu ý khi chạy:

- `--smoke` **chỉ** chạy `tests_smoke.smoke_media()` rồi thoát; không chạy 78 test kia. Nó ghi `smoke_*.png` (bị `.gitignore`).
- `--real` cũng chạy riêng rồi thoát. Thiếu GPU, model hoặc ffmpeg thì từng test báo `NOT RUN` kèm lý do, **không tự pass**
  và **không tự tải model** (`large-v3` nặng khoảng 3 GB). Test ép Whisper và NLLB chạy trên GPU; lùi về CPU là lỗi.
- Khi chạy offline, dòng `WARNING … CUDA không sẵn sàng; thử CPU/int8` là test cố ý giả lập lỗi CUDA để kiểm đường lùi, không phải GPU hỏng.
- `test/runtime_logic.py` không nằm trong cổng chạy. Đầu ra nay tự đặt `utf-8` nên không còn lỗi `UnicodeEncodeError` (cp1252);
  lỗi cũ làm test thoát mã 1 dù kết quả `PASS`.
- `tools_coverage.py` chỉ đo **dòng** trong tiến trình test offline: không đo nhánh, không đo tiến trình con. `pipeline/audio.py` (0 %)
  và `render.py` (78 %) cần ffmpeg thật nên bộ offline ít chạm tới; `--smoke`, `--real` kiểm hai file này nhưng không vào con số 91,2 %.
- `npm run test:frontend` ghi đè các ảnh `docs/ketqua/B-*.png`; xem `git status` trước khi commit.
- `tests_docx.py` chạy riêng, cần `uv sync --extra docs`.

`test_pipeline.py` quét `globals()` tìm hàm `test_*`, chạy **hết** rồi mới báo. Thêm file test mới phải thêm dòng
`from tests_x import *`. Chạy một test lẻ:
`$py -c "import test_pipeline as t; t.test_vung_mo_gan_tung_cau_thoai()"`.

### 18.1 Ranh giới giả lập

| Tầng | Thật cái gì | Giả cái gì |
|---|---|---|
| Offline | điều phối, manifest trên đĩa, SQLite, tầng HTTP, `BackgroundTasks` | `_nap()` trả module giả cho `audio`, `asr`, `subs`, `translate`, `render`, `markbox`; callable dịch giả |
| Smoke, runtime | ffmpeg và ffprobe thật, uvicorn thật, SQLite và lock trên đĩa thật | ASR và bộ dịch (hai thành phần không tất định hoặc nặng) |
| Thật (`--real`) | GPU, faster-whisper (`base`, `large-v3`), NLLB qua CTranslate2, ffmpeg, điều phối đầu-cuối trên video mẫu 30 giây | không giả gì; chỉ video đầu vào là một clip mẫu |
| Giao diện | Chromium thật, mã `web/` thật | API (giả lập bằng Playwright route) |

**Chưa được kiểm tự động:** chất lượng dịch và nhận dạng (WER, BLEU), tải model NLLB lần đầu qua mạng,
chạy video dài cả một phim, bộ nhớ GPU của `large-v3` khi chạy lâu (`--real` chỉ chạy 30 giây), tốc độ trích khung song song. Số đo thật cũ ở `ketqua/V8.md` đo trên bộ dịch DeepSeek đã bỏ (xem ghi chú đầu file).

### 18.2 Ánh xạ test → tính chất

| Tính chất | Test canh giữ |
|---|---|
| Vùng riêng thay vùng chung | `test_vung_rieng_thay_vung_chung`, `test_vung_mo_gan_tung_cau_thoai` |
| Artifact VER cũ phải chọn lại | `test_vung_blur_ver_cu_phai_chon_lai` |
| Chữ ký vùng theo nội dung | `test_vung_cue_signature_tracks_content_not_count` |
| Chặn checkpoint lệch trước side effect | `test_vung_cue_source_invalidation_before_side_effect` |
| Lock nguyên tử, không lộ đường dẫn | `test_atomic_write_and_lock`, `test_lock_khong_lo_duong_dan_ngoai_work` |
| Một người thắng claim | `test_api_upload_and_resume_claim_is_single_winner`, `test_api_resume_claim_is_single_winner` |
| Restart chỉ đánh lỗi công việc mồ côi | `test_api_restart_marks_only_orphans_and_keeps_completed_output` |
| API và CLI cùng kết quả | `test_api_va_cli_cung_ket_qua` |
| Từ chối `Origin`, `Host` lạ | `test_api_tu_choi_origin_va_host_la` |
| Dịch cục bộ: nạp muộn, lùi CPU, thẻ hỏng | `test_dich_cuc_bo_nap_model_muon`, `test_dich_cuc_bo_lui_ve_cpu_khi_loi_cuda`, `test_dich_cuc_bo_the_hong_thi_dich_lai_khong_the` |
| Tách câu ASR | `test_asr_tach_segment_nhieu_cau_theo_tu`, `test_gop_cau_asr` |
| Phụ đề phủ quá ít → `suy_giam` | `test_api_suy_giam_bao_ly_do_phu_de_thieu` |
| `GET` không tạo nhóm, độ dài tên bị chặn | `test_get_khong_tao_nhom_va_gioi_han_do_dai`, `test_api_get_khong_tao_nhom_va_404_409` |
| Trigger ghi lịch sử mọi đường | `test_trigger_lich_su_moi_duong_ghi`, `test_hop_nhom_ghi_roi_xoa_khong_vo_trigger_khi_hop_rong` |
| Tìm, lọc, sắp xếp, phân trang | `test_liet_ke_nhom_tim_khong_dau_sap_xep_phan_trang`, `test_api_tim_loc_sap_xep_phan_trang_va_header_tong` |
| Xoá nhóm, thuật ngữ; `409` khi đang chạy | `test_xoa_nhom_thuat_ngu_va_chan_khi_dang_chay`, `test_api_xoa_nhom_thuat_ngu_va_409_khi_dang_chay` |
| Sao lưu, khôi phục, từ chối file hỏng | `test_sao_luu_khoi_phuc_va_tu_choi_file_hong`, `test_khoi_phuc_tu_choi_khi_thieu_file_hoac_dang_co_giao_dich`, `test_sao_luu_tu_dong_giu_5_ban_va_khong_xoa_ban_an_toan` |
| Dọn dẹp không xoá nhầm | `test_don_dep_chi_xoa_cu_khong_xoa_dang_chay_va_ngoai_work`, `test_don_dep_tu_choi_xoa_qua_lien_ket_ra_ngoai_work`, `test_don_dep_nguon_cu_khong_lock_bi_don_con_lock_hoac_moi_thi_giu` |
| Tuỳ chọn sai → `400`, không để rác | `test_kiem_tuy_chon_cua_web_va_cli`, `test_api_tuy_chon_sai_la_400_khong_de_rac` |
| File quá lớn bị từ chối từ tiêu đề | `test_api_tu_choi_file_qua_lon_tu_tieu_de`, `test_api_content_length_rac_khong_lam_sap_middleware` |
| Trích khung song song giữ thứ tự | `test_trich_khung_song_song_giu_thu_tu_va_nem_loi` |
| GPU, Whisper, NLLB, đầu-cuối thật | `real_gpu_ctranslate2_cuda`, `real_whisper_base_tren_gpu`, `real_whisper_large_v3_tren_gpu`, `real_nllb_dich_tren_gpu_va_ep_thuat_ngu`, `real_dich_giu_dung_so_cue_khi_goi_model_that`, `real_dau_cuoi_whisper_nllb_ffmpeg` |
| F5 giữ công việc, `404` dừng theo dõi, storage bị chặn | `test/frontend.cjs` (nhóm kịch bản thứ ba) |

---

## 19. Giới hạn đã biết

- Bước dịch không thấy câu liền kề, nên xưng hô có thể đổi giữa câu (mục 12).
- Model không tự rút thuật ngữ; thuật ngữ chỉ có khi người dùng nhập.
- Lần dịch đầu tiên tải khoảng 600 MB; thanh tiến độ đứng ở bước `dich` đến khi tải xong.
- Vùng làm mờ là hình chữ nhật, đứng yên trong mỗi câu.
- Trích khung mẫu chạy 4 luồng nhưng vẫn một ffmpeg mỗi cue: phim dài vẫn tốn thời gian và dung lượng; chưa đo lại (mục 10).
- Tìm kiếm, nhật ký, lịch sử, sao lưu và xoá nhóm chưa có giao diện web; khôi phục CSDL chỉ có ở CLI.
- Chưa đo bộ nhớ GPU của Whisper `large-v3` trên phim dài; `--real` mới chạy video 30 giây.
- SQLite ở chế độ WAL chịu được vài request đồng thời của một người dùng; chưa thiết kế cho nhiều người dùng.
- Khởi động lại server làm mất công việc đang chạy; công việc chuyển `loi` kèm hướng dẫn, artifact trên đĩa còn.
- Chưa đo chất lượng tự động (WER, BLEU).
