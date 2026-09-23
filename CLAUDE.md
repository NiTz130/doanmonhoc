# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Bối cảnh

Web app dịch phụ đề video Anh → Việt, chạy cục bộ. Đồ án môn học 4 thành viên.
Người dùng tải video lên trình duyệt → hệ thống lấy phụ đề sẵn hoặc nhận dạng bằng
Whisper → dịch bằng DeepSeek → làm mờ vùng phụ đề cứng do người dùng khoanh → cháy
phụ đề Việt vào hình, **chỉ qua một lần nén**.

Tài liệu gốc: [README.md](README.md) (đầy đủ nhất), [spec](docs/superpowers/specs/2026-09-09-video-dich-phu-de-design.md),
[plan](docs/superpowers/plans/2026-09-09-dich-phu-de-video.md) — plan chứa toàn bộ
ràng buộc CS/IC/LD được nhắc trong comment mã nguồn.

## Lệnh

Cần Python 3.12, `uv`, ffmpeg 6+. Không có formatter/linter.

```bash
py=.venv/Scripts/python.exe          # Windows; repo dùng uv, không dùng pip trực tiếp

uv sync                              # cài môi trường
$py -m uvicorn api.app:app --reload  # chạy web app → http://127.0.0.1:8000
start_system.bat                     # tương đương, kèm mở trình duyệt

$py test_pipeline.py                 # 34 test offline, không cần mạng/GPU/ffmpeg
$py test_pipeline.py --smoke         # CHỈ test media (tests_smoke.smoke_media), cần ffmpeg
$py test/runtime_logic.py            # V-11: uvicorn + ffmpeg + SQLite thật, không nằm trong runner trên
npm ci && npx playwright install chromium          # chuẩn bị một lần
$py -m http.server 8765 --bind 127.0.0.1 --directory web   # rồi ở terminal khác:
npm run test:frontend                # Playwright + API giả lập (UI_URL đổi được cổng)
```

Dịch thật cần `DEEPSEEK_API_KEY` trong `.env` (mẫu `.env.example`) — **tốn tiền**;
mọi test ở trên đều thay `translate` bằng callable giả nên không gọi mạng.

**Chạy một test lẻ:** không có framework, `test_pipeline.py` tự quét `globals()` tìm
hàm `test_*`. Gọi trực tiếp:
`$py -c "import test_pipeline as t; t.test_vung_mo_gan_tung_cau_thoai()"`

Test offline nằm rải ở `tests_api.py` · `tests_db.py` · `tests_media.py` ·
`tests_translate.py` (mỗi thành viên một file, đánh số `V-n` trỏ về plan), được
`test_pipeline.py` gom bằng `from tests_x import *`. **Thêm file test mới phải thêm
dòng import đó**, không thì runner không thấy. Ngoại lệ có chủ ý: `tests_docx.py`
(kiểm `tools_md2docx.py`, cần `python-docx`) và `tests_smoke.py` chạy riêng.

CLI nội bộ (`main.py`) — **không phải sản phẩm**, dùng để gỡ lỗi và xử lý hàng loạt;
nó đi qua đúng `pipeline/dieu_phoi.py` như web nên cho cùng kết quả:

```bash
$py main.py phim.mp4 --nhom "Tên phim" --blur-box 0.3,0.855,0.4,0.09
$py main.py batch ./thu_muc --nhom "Tên phim"
$py main.py nhom set-term "Tên phim" "Ironhold" "Thành Sắt" --lock
```

Mã thoát: `0` xong · `1` có lỗi/có cue giữ nguyên bản gốc/còn video chờ vẽ hộp · `130` Ctrl+C.

## Kiến trúc

```
web/index.html  1 file, 4 <section> (tai-len · tien-do · khung · nhom) ẩn/hiện theo
                hash; app.js + scene.js (Three.js vendored) — không bundler, không framework
  |  HTTP (polling 1.5s)
api/            FastAPI: validate → gọi điều phối → trả JSON
                POST /api/video · GET /api/cong-viec/{cid}[/khung[/{i}]|/ket-qua]
                POST /api/cong-viec/{cid}/hop · router /nhom (nhóm + thuật ngữ + hộp)
  |
pipeline/dieu_phoi.py    luồng 6 bước, dùng chung cho cả API lẫn CLI
  |             nhận diện → phụ đề gốc → VÙNG MỜ → dịch → kết xuất
pipeline/{audio,subs,asr,translate,markbox,render,srt,db}.py
```

**Vùng mờ đứng trước bước dịch** dù không phải phụ thuộc của ai — nó là bước duy nhất
cần người dùng, nên đặt sớm để thời gian chờ của máy và của người chồng lên nhau, và
người bỏ cuộc ở màn vẽ hộp không tốn tiền API. Thiếu hộp → trạng thái `cho_chon_khung`,
**không phải lỗi**.

**Resume dựa trên hệ thống file, không dựa trên DB.** `work/<stem>-<hash>/trang_thai.json`
là manifest giữ chữ ký từng bước (phiên bản bước + SHA256 nội dung phụ thuộc + tham số
ảnh hưởng). Manifest luôn ghi **sau** artifact: crash ở giữa chỉ gây cache miss, không
bao giờ báo xong nhầm. Bảng `cong_viec` trong SQLite chỉ báo tiến độ cho frontend.
Xoá `work/subtitles.db` mất nhóm/thuật ngữ/nhật ký, **không** mất artifact.

Đổi cách sinh artifact của một bước → tăng số trong `VER` (`dieu_phoi.py`); đổi prompt
dịch → tăng `PROMPT_VER`. Không tăng thì manifest cũ vẫn tính là cache hit.

**Tác vụ nền chạy trong chính tiến trình backend** qua `BackgroundTasks`. `api/viec.py`
giữ ánh xạ `cid → (video, tuỳ chọn)` trong RAM; restart server làm mất tác vụ đang chạy
(artifact trên đĩa vẫn còn, tải video lại thì tái dùng được).

## Ràng buộc bất thể phá

Các mã `CS-n`/`IC-n`/`LD-n` rải trong comment trỏ về plan. Những cái hay bị vi phạm nhất:

- **CS-6 / LD-9 — `api/` không chứa logic xử lý.** Không gọi ffmpeg, không nạp model,
  không ghép filtergraph trong `api/`. Thêm đường vào mới không được sinh nhánh xử lý
  thứ hai — mọi thứ đi qua `dieu_phoi.chay()`.
- **IC-2 — phụ thuộc một chiều.** Module xử lý (`asr`, `translate`, `render`, `markbox`,
  `subs`, `audio`) không biết DB và không biết HTTP: nhận tham số, trả dữ liệu thuần.
  Chỉ `dieu_phoi.py` được gọi `db.py`; `api/nhom.py` đi qua các hàm `nhom_*` của `dieu_phoi`.
- **LD-8 — một validator hình học duy nhất.** `markbox.kiem_hop` / `kiem_vung` phục vụ
  CLI, thân request API, JSON trên đĩa và DB. Frontend kiểm thêm chỉ để báo sớm, không
  thay backend.
- **CS-1 — mỗi cue nguồn ứng đúng một cue kết quả**, giữ nguyên timestamp. Không ghép,
  không tách cue theo phản hồi model.
- **LD-2 — ghi nguyên tử.** File tạm cùng thư mục → đóng → kiểm → `os.replace`. Một
  tiến trình cho một work directory, bằng lock file tạo độc quyền (web trả 409). Lock
  sót sau crash **không tự đoán là chết**, người dùng xoá tay.
- **IC-1 — không thêm** framework test, hàng đợi ngoài (Celery/Redis), ORM, WebSocket,
  đăng nhập. Test dùng `assert` trần, callable giả, `TestClient`, SQLite `:memory:`.

## Quy ước mã

- **IC-3:** định danh nội bộ viết **tiếng Việt không dấu** (`dieu_phoi`, `thu_muc_lam_viec`,
  `bao_tien_do`, `vung_blur`). Tên API và tham số bên ngoài giữ nguyên dạng đã công bố.
  Comment tiếng Việt: trong `.py` phần lớn không dấu, chuỗi hiển thị cho người dùng có dấu.
- SRT đọc `utf-8-sig`, ghi `utf-8`.
- Hộp/vùng mờ lưu theo **phần trăm 0–1**, không theo pixel — nên dùng chung được giữa
  720p và 1080p. `blur_box` là `dict` (một hộp cho mọi câu) hoặc `list[dict]` (hộp gán
  chỉ số cue riêng).
- `_nap("ten")` trong `dieu_phoi.py` nạp module muộn — test thay hàm này bằng bản giả,
  nên đừng đổi sang `import` thẳng ở đầu file.

## Git

Hook trong `.githooks/` chỉ khoá nhánh khi đã khai báo `git config nhom.nhanh <ten>`;
chưa khai báo thì không cản. Bật bằng `git config core.hooksPath .githooks`.
Chi tiết quy trình nhóm: [docs/GIT.md](docs/GIT.md).
