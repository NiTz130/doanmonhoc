# Web app dịch phụ đề video Anh → Việt

Tải video tiếng Anh lên trình duyệt, hệ thống lấy phụ đề có sẵn hoặc nhận dạng bằng
Whisper, dịch sang tiếng Việt bằng DeepSeek, làm mờ vệt phụ đề cứng do bạn khoanh bằng
chuột, rồi trả về video có phụ đề Việt cháy vào hình — **chỉ qua một lần nén**.

Đồ án nhóm 4 thành viên. Tài liệu: [đề cương](docs/DE_CUONG.md) ·
[phân công](docs/PHAN_CONG.md) ·
[thiết kế](docs/superpowers/specs/2026-09-09-video-dich-phu-de-design.md) ·
[kế hoạch](docs/superpowers/plans/2026-09-09-dich-phu-de-video.md) ·
[hướng dẫn Git](docs/GIT.md).

## 1. Cài đặt

Cần sẵn: **Python 3.12**, [`uv`](https://docs.astral.sh/uv/), và **ffmpeg 6+** có
`libass`, `gblur`, `overlay`, `subtitles` trong `PATH`.

```bash
git clone https://github.com/NiTz130/doanmonhoc.git
cd doanmonhoc
uv sync
cp .env.example .env          # rồi mở .env, điền DEEPSEEK_API_KEY
```

**GPU NVIDIA là tuỳ chọn nhưng nên có.** Không có thì Whisper chạy CPU ở khoảng
**2.2× thời lượng video** — phim hai tiếng mất 4–5 tiếng; ffmpeg cũng lui về `libx264`.

### Bật GPU trên Windows

Thấy dòng `Library cublas64_12.dll is not found or cannot be loaded` thì card không
thiếu, chỉ thiếu CUDA runtime. Hai bước, **phải làm cả hai**:

```bash
uv pip install nvidia-cublas-cu12 nvidia-cudnn-cu12

# ctranslate2.dll chi tim phu thuoc trong chinh thu muc no, nen dat cublas canh no:
NV=.venv/Lib/site-packages/nvidia/cublas/bin
CT=.venv/Lib/site-packages/ctranslate2
cp "$NV/cublas64_12.dll" "$NV/cublasLt64_12.dll" "$CT/"
```

Bước hai là bắt buộc trên Windows. Chỉ cài gói pip thôi thì DLL nằm trong
`site-packages/nvidia/` và `ctranslate2` **không** tìm thấy — thêm vào `PATH` hay
`os.add_dll_directory` đều không cứu được, đã thử.

Kiểm lại bằng một video ngắn: hết dòng cảnh báo là GPU đã được dùng. Đo trên video
2 phút của nhóm: **274 s xuống 56 s**.

Tách giọng hát (tuỳ chọn, kéo theo torch ~2.5 GB): `uv sync --extra demucs`.

Kiểm nhanh môi trường:

```bash
ffmpeg -version
.venv/Scripts/python.exe test_pipeline.py      # 13 test offline, không cần mạng/GPU
```

## 2. Chạy web app

```bash
.venv/Scripts/python.exe -m uvicorn api.app:app --reload
```

Mở http://127.0.0.1:8000 — bốn màn trong một trang:

| Màn | Việc |
|---|---|
| **Tải lên** | Chọn video và tuỳ chọn, bấm Bắt đầu |
| **Tiến độ** | Thanh tiến độ hỏi backend mỗi 1.5 giây |
| **Vùng làm mờ** | Kéo chuột vẽ hộp trên 8 khung mẫu; hộp giữ nguyên khi chuyển khung |
| **Nhóm & thuật ngữ** | Tạo nhóm, xem/sửa bảng thuật ngữ, khoá bản dịch, đặt khung mặc định |

Khi video chưa có vùng làm mờ, công việc **dừng ở trạng thái chờ** chứ không báo lỗi:
bạn sang màn vẽ hộp, gửi lên, nó chạy tiếp từ bước kết xuất. Bấm *Bỏ qua* thì không
làm mờ nhưng **không xoá** khung mặc định của nhóm.

Hộp giữ nguyên khi chuyển khung là có chủ đích: phụ đề hai dòng cao hơn một dòng, vẽ
trên khung một dòng rồi chốt luôn thì câu hai dòng thòi ra ngoài vùng mờ. Bấm qua lại
vài khung là thấy câu nào cao nhất.

## 3. Công cụ dòng lệnh

`main.py` **không phải sản phẩm** — nó là công cụ nội bộ để kiểm thử, gỡ lỗi từng bước
và xử lý hàng loạt khi không cần trình duyệt. Dùng chung `pipeline/dieu_phoi.py` với
web nên hai đường vào cho **cùng một kết quả**.

```bash
py=.venv/Scripts/python.exe

$py main.py phim.mp4 --nhom "Tên phim" --blur-box 0.3,0.855,0.4,0.09
$py main.py batch ./thu_muc --nhom "Tên phim"
$py main.py nhom list
$py main.py nhom glossary "Tên phim"
$py main.py nhom set-term "Tên phim" "Ironhold" "Thành Sắt" --lock
$py main.py nhom set-box "Tên phim" 0.3,0.855,0.4,0.09
```

| Cờ | Ý nghĩa |
|---|---|
| `--nhom TEN` | Dùng chung thuật ngữ, khung mờ và kiểu chữ với các video khác trong nhóm |
| `--blur auto\|on\|off` | `auto` (mặc định): bật với video ngang, tắt với video dọc |
| `--blur-box x,y,w,h` | Vùng mờ theo **phần trăm** 0–1, dùng chung được cho 720p lẫn 1080p |
| `--font-scale 0.42` | `FontSize = chiều_cao_hộp × hệ_số`; chỉnh sau một lần chạy thử |
| `--vad on\|off` | `on` (mặc định) cắt khoảng lặng để Whisper khỏi bịa chữ. **Tắt với video ca nhạc** — Silero VAD coi nhạc nền là không phải tiếng nói và vứt gần hết audio |
| `--separate` | Tách giọng hát bằng Demucs trước khi nhận dạng (cần extra `demucs`) |
| `--force-asr` | Bỏ qua phụ đề có sẵn, chạy Whisper — dùng khi phụ đề sẵn lệch giờ |
| `--force` | Chạy lại mọi bước |
| `-o OUT` | Đường dẫn ra (chỉ cho một video; `batch` từ chối cờ này) |

CLI không mở được màn vẽ hộp — nó nằm ở frontend. Chạy CLI mà chưa có khung thì phải
truyền `--blur-box` hoặc `--blur off`.

**Mã thoát:** `0` tất cả thành công · `1` có lỗi, có dòng giữ nguyên bản gốc, hoặc còn
video chờ vẽ hộp · `130` bị Ctrl+C.

`batch` chạy **tuần tự** để thuật ngữ tích luỹ từ video trước sang video sau, mỗi nguồn
sinh `<tên>_vi.mp4`. Đuôi `_vi.mp4` bị loại khỏi lượt quét nên chạy lại không nhận
output làm input. Hai nguồn trùng đích thì nó từ chối **trước khi ghi gì**.

## 4. Chạy lại và sửa tay

`work/<tên>-<8 ký tự băm>/` giữ file trung gian của từng video; `trang_thai.json` lưu
chữ ký nội dung và cấu hình của từng bước. **Hệ thống file là nguồn sự thật** — xoá
`work/subtitles.db` làm mất nhóm, thuật ngữ và nhật ký, không làm mất artifact.

- Đổi `--blur`, hộp hay cỡ chữ → chỉ tính lại vùng mờ và kết xuất, **không** gọi lại
  Whisper hay API dịch.
- Thay nội dung video tại cùng đường dẫn → làm mới mọi bước phụ thuộc. Băm theo nội
  dung, không theo đường dẫn.
- Sửa tay `work/<...>/sub_vi.srt` rồi chạy lại: bản sửa **được giữ** nếu còn đủ cue và
  đúng mốc thời gian. Máy không học thuật ngữ từ bản sửa tay.
- Ngắt giữa chừng chỉ gây tính lại, không tạo file dở bị hiểu nhầm là hoàn tất, và
  không phá output tốt của lần trước.

**Lock sót sau khi máy treo:** mỗi thư mục làm việc có một `.lock`; tiến trình thứ hai
bị từ chối (web trả 409). Nếu chắc chắn không còn tiến trình nào đang chạy thì xoá tay
`work/<tên>-<băm>/.lock`. Hệ thống **không tự đoán** lock đã chết.

## 5. Kiểm thử

```bash
.venv/Scripts/python.exe test_pipeline.py            # 13 test offline
.venv/Scripts/python.exe test_pipeline.py --smoke    # thêm media, cần ffmpeg
```

Bộ offline không cần mạng, GPU, cổng mạng hay màn hình: `assert` trần, callable giả,
`TestClient` của FastAPI, SQLite `:memory:`. `test_pipeline.py` là điểm vào duy nhất:
nó giữ test SRT và điều phối, rồi import `tests_db`, `tests_media`, `tests_translate`
và `tests_api`.

`--smoke` sinh video bằng `ffmpeg lavfi`, chạy tách audio và kết xuất có/không blur ở
720p và 1080p, rồi ghi ra `smoke_*.png` để **nhìn tận mắt** chữ Việt và vùng mờ.
Đây **không phải** end-to-end: nghiệm thu ASR và dịch thật là V-8, chỉ chạy khi nhóm
đã thống nhất tài khoản và ngân sách.

Đã chạy thật với ASR và API dịch trên video có tiếng: kết quả, chi phí đo được và
một lỗi tìm ra nhờ nó ở [docs/ketqua/V8.md](docs/ketqua/V8.md).

Luồng web đã chạy thật trên Chromium — tải lên, kéo chuột vẽ hộp, tải kết quả về —
không lỗi JavaScript nào. Ảnh và kết luận ở [docs/ketqua](docs/ketqua/).

## 6. Kiến trúc

```
web/            4 màn HTML/CSS/JS thuần, không bundler
  |  HTTP
api/            FastAPI: validate, gọi điều phối, trả JSON — KHÔNG gọi ffmpeg/model
  |
pipeline/dieu_phoi.py    luồng 6 bước, dùng chung cho cả API lẫn CLI
  |
pipeline/{audio,subs,asr,translate,markbox,render}.py
```

Phụ thuộc **một chiều**. Các module xử lý không biết CSDL và không biết HTTP: nhận dữ
liệu làm tham số, trả dữ liệu thuần. Chỉ `dieu_phoi.py` gọi `db.py`. Khác biệt duy nhất
giữa web và CLI là callable `bao_tien_do` — web ghi vào bảng `cong_viec`, CLI in ra
màn hình. Đó cũng là lý do bộ kiểm thử chạy được mà không cần dựng CSDL lẫn web server.

Việc chạy lâu chạy nền **trong chính tiến trình backend**, không Celery, không Redis,
không WebSocket. Một video một lúc. Khởi động lại server thì công việc đang dở mất,
nhưng artifact trên đĩa còn nguyên nên tải lại là chạy tiếp từ chỗ đã xong.

## 7. Chưa làm

Lồng tiếng TTS · tự dò vùng chữ bằng OCR · giao diện desktop · vùng mờ di chuyển theo
cảnh · nhúng phụ đề mềm · đăng nhập và phân quyền · hàng đợi ngoài · WebSocket ·
triển khai máy chủ · chạy nhiều video song song.

Chưa đo trên video thật nên README **không nêu** con số hiệu năng hay chi phí API.
