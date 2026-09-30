# Web app dịch phụ đề video Anh → Việt

Tải video tiếng Anh lên trình duyệt → hệ thống lấy phụ đề có sẵn hoặc nhận dạng bằng
**Whisper** → dịch sang tiếng Việt bằng **DeepSeek** → làm mờ phụ đề cứng do bạn khoanh
→ trả video có phụ đề Việt cháy vào hình, **chỉ qua một lần nén**. Chạy cục bộ.

Đồ án nhóm 4 thành viên. Tài liệu: [đề cương](docs/DE_CUONG.md) ·
[phân công](docs/PHAN_CONG.md) ·
[thiết kế](docs/superpowers/specs/2026-09-09-video-dich-phu-de-design.md) ·
[kế hoạch](docs/superpowers/plans/2026-09-09-dich-phu-de-video.md) ·
[hướng dẫn Git](docs/GIT.md)

## 1. Cài đặt

Cần: **Python 3.12**, [`uv`](https://docs.astral.sh/uv/), **ffmpeg 6+** (có `libass`,
`gblur`, `overlay`, `subtitles`) trong `PATH`.

```bash
git clone https://github.com/NiTz130/doanmonhoc.git
cd doanmonhoc
uv sync
cp .env.example .env      # điền DEEPSEEK_API_KEY (dịch thật tốn tiền)
```

| Tuỳ chọn | Lệnh | Ghi chú |
|---|---|---|
| Tách giọng hát | `uv sync --extra demucs` | Kéo theo torch ~2.5 GB |
| Xuất báo cáo `.docx` | `uv sync --extra docs` | Chỉ cho `tools_md2docx.py` |

### GPU NVIDIA (nên có, không bắt buộc)

Không GPU thì Whisper chạy CPU, khoảng **2.2× thời lượng video** (mẫu đo ở
[V8](docs/ketqua/V8.md)). Có GPU: video 2 phút giảm **274 s → 56 s**.

Thấy `Library cublas64_12.dll is not found` nghĩa là thiếu CUDA runtime. Trên Windows
**phải làm cả hai bước** (thêm vào `PATH` không cứu được):

```bash
uv pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
NV=.venv/Lib/site-packages/nvidia/cublas/bin
CT=.venv/Lib/site-packages/ctranslate2
cp "$NV/cublas64_12.dll" "$NV/cublasLt64_12.dll" "$CT/"   # ctranslate2 chỉ tìm DLL cạnh nó
```

## 2. Chạy web app

```bash
.venv/Scripts/python.exe -m uvicorn api.app:app --reload   # hoặc: start_system.bat
```

Mở http://127.0.0.1:8000 — bốn màn trong một trang:

| Màn | Việc |
|---|---|
| **Tải lên** | Chọn video và tuỳ chọn, bấm Bắt đầu |
| **Tiến độ** | Thanh tiến độ hỏi backend mỗi 1.5 s |
| **Vùng làm mờ** | Vẽ hộp lên khung hình của từng câu thoại |
| **Nhóm & thuật ngữ** | Tạo nhóm, sửa bảng thuật ngữ, đặt khung mờ mặc định |

**Luồng chạy:** nhận diện → phụ đề gốc → **vùng mờ** → dịch → kết xuất.

Chưa có vùng mờ thì công việc **dừng ở trạng thái chờ** (không phải lỗi): bạn vẽ hộp,
gửi lên, nó chạy tiếp. Bấm *Bỏ qua* thì không làm mờ. Bước này đặt *trước* dịch để
người bỏ cuộc ở màn vẽ hộp chưa tốn đồng API nào.

### Vẽ vùng làm mờ

- **Kéo cạnh/góc** để chỉnh, **kéo giữa** để dời, **kéo ra ngoài** để vẽ hộp mới, rút
  hộp về gần 0 để xoá.
- Mỗi câu thoại có **một khung hình** (43 phụ đề → 43 ảnh, ~0.2 s/khung ở 640×360). Bấm
  qua lại các khung để thấy câu nào cao nhất và chỉnh hộp cho phủ hết.
- **Phụ đề nhảy chỗ:** ở khung của câu đó chọn *Riêng câu đang xem*, vẽ vùng mới, bấm
  *Áp cho dải câu* để chép sang cả cảnh. Vùng riêng **thay thế** vùng chung ở đúng những
  câu được gán. Mỗi câu có tối đa một vùng chung và một vùng riêng, vi phạm bị 400.
- Vùng lấy thời gian từ các câu gán cho nó, nới ±0.4 s, gộp khoảng gần nhau. Mỗi vùng
  là một nhánh `crop → gblur → overlay` trong **cùng một filtergraph**.
- Phụ đề Việt chỉ vẽ ở một chỗ; cỡ chữ và lề bám theo *vùng chính* (`markbox.hop_chinh`).
- Hộp chỉ thuộc video đó. Muốn dùng chung cho nhóm thì tích *Đặt làm vùng mặc định cho
  nhóm* (nhóm chỉ giữ **một** hộp). Hộp riêng của video luôn thắng khung của nhóm.

## 3. Dòng lệnh (nội bộ)

`main.py` **không phải sản phẩm**: dùng để gỡ lỗi và xử lý hàng loạt, đi qua đúng
`pipeline/dieu_phoi.py` như web nên cho cùng kết quả.

```bash
py=.venv/Scripts/python.exe
$py main.py phim.mp4 --nhom "Tên phim" --blur-box 0.3,0.855,0.4,0.09
$py main.py batch ./thu_muc --nhom "Tên phim"     # tuần tự, thuật ngữ tích luỹ
$py main.py nhom list
$py main.py nhom glossary "Tên phim"
$py main.py nhom set-term "Tên phim" "Ironhold" "Thành Sắt"
$py main.py nhom set-box "Tên phim" 0.3,0.855,0.4,0.09
```

| Cờ | Ý nghĩa |
|---|---|
| `--nhom TEN` | Dùng chung thuật ngữ, khung mờ, kiểu chữ trong nhóm |
| `--blur auto\|on\|off` | `auto` (mặc định): bật với video ngang, tắt với video dọc |
| `--blur-box x,y,w,h` | Một hộp cho mọi câu, theo **phần trăm 0–1** (dùng chung 720p/1080p) |
| `--font-scale 0.42` | `FontSize = chiều_cao_hộp × hệ_số` |
| `--vad on\|off` | Mặc định `on`. **Tắt với video ca nhạc** (VAD coi nhạc nền là im lặng) |
| `--separate` | Tách giọng bằng Demucs trước khi nhận dạng (cần extra `demucs`) |
| `--force-asr` | Bỏ qua phụ đề có sẵn, chạy Whisper |
| `--force` | Chạy lại mọi bước |
| `--lang`, `--model`, `--model-dich` | Ngôn ngữ nguồn (`en`), model Whisper (`large-v3`), model dịch (`deepseek-v4-flash`) |
| `-o OUT` | Đường dẫn ra (một video; `batch` từ chối) |

CLI không có màn vẽ hộp: chưa có khung thì phải truyền `--blur-box` hoặc `--blur off`.
Vùng riêng theo từng câu chỉ đặt được trên web.

**Mã thoát:** `0` xong · `1` có lỗi / có cue giữ nguyên bản gốc / còn video chờ vẽ hộp ·
`130` Ctrl+C. `batch` sinh `<tên>_vi.mp4` và bỏ qua đuôi `_vi.mp4` khi quét.

## 4. Chạy lại và sửa tay

Kết quả nằm trong `work/`. **Hệ thống file là nguồn sự thật**; xoá `work/subtitles.db`
chỉ mất nhóm, thuật ngữ, nhật ký — không mất artifact.

| Thư mục | Nội dung |
|---|---|
| `work/<tên>-<băm>/` | File trung gian; `vung_blur.json` (vùng + chỉ số câu), `trang_thai.json` (chữ ký từng bước) |
| `work/tai_len/nguon/<băm nhóm>/<sha256>/` | Video tải lên, cất theo **nội dung và nhóm**, không theo tên file |
| `work/tai_len/<id công việc>/` | Kết quả và khung mẫu của từng lượt (mỗi lần tải lên = công việc mới) |

- Đổi `--blur`, hộp, cỡ chữ → chỉ tính lại vùng mờ và kết xuất, **không** gọi lại
  Whisper hay API dịch.
- Băm theo nội dung: đổi tên file vẫn dùng lại cache; đổi nội dung thì làm mới.
- Sửa tay `sub_vi.srt` rồi chạy lại: bản sửa **được giữ** nếu còn đủ cue, đúng mốc giờ.
- Ngắt giữa chừng chỉ gây tính lại, không sinh file dở bị hiểu là hoàn tất.
- Phụ đề gốc đổi trong lúc bạn vẽ hộp → web trả **409**, cần tải lại video.
- **Lock sót sau khi máy treo:** xoá tay `work/<tên>-<băm>/.lock` khi chắc chắn không
  còn tiến trình nào chạy. Hệ thống không tự đoán lock đã chết.
- **Khởi động lại server:** công việc dở được đánh dấu **lỗi** kèm hướng dẫn tải lại;
  công việc đã xong giữ nguyên và tải được.

## 5. Kiểm thử

```bash
py=.venv/Scripts/python.exe
$py test_pipeline.py             # 41 test offline (= npm test), không cần mạng/GPU/ffmpeg
$py test_pipeline.py --smoke     # test media, cần ffmpeg; ghi smoke_*.png để nhìn tận mắt
$py test/runtime_logic.py        # uvicorn + ffmpeg + SQLite thật

npm ci && npx playwright install chromium                     # một lần
$py -m http.server 8765 --bind 127.0.0.1 --directory web      # terminal 1
npm run test:frontend                                         # terminal 2
```

Bộ offline dùng `assert` trần, callable giả, `TestClient`, SQLite `:memory:`; không gọi
API dịch. `--smoke` **không phải** end-to-end. Số đo ASR/dịch thật ở
[V8](docs/ketqua/V8.md), kiểm giao diện ở [B-frontend](docs/ketqua/B-frontend.md) —
đều là bằng chứng của lượt đo được ghi lại, không phải cam kết cho phiên bản hiện tại.

## 6. Kiến trúc

```
web/            4 màn HTML/CSS/JS thuần (Three.js vendored), không bundler
  |  HTTP (polling 1.5 s)
api/            FastAPI: validate → gọi điều phối → trả JSON (KHÔNG gọi ffmpeg/model)
  |
pipeline/dieu_phoi.py    luồng dùng chung cho API và CLI
  |
pipeline/{audio,subs,asr,translate,markbox,render,srt,db}.py
```

| Đường API | Việc |
|---|---|
| `POST /api/video` | Tải video, tạo công việc |
| `GET /api/cong-viec/{cid}` | Tiến độ (`/khung`, `/khung/{i}`, `/ket-qua`) |
| `POST /api/cong-viec/{cid}/hop` | Gửi vùng mờ, chạy tiếp |
| `/nhom` | Nhóm, thuật ngữ, khung mặc định |

Nguyên tắc chính:

- **Phụ thuộc một chiều:** module xử lý không biết DB lẫn HTTP, chỉ `dieu_phoi.py` gọi `db.py`.
- **Tác vụ nền chạy trong chính tiến trình backend** (không Celery, Redis, WebSocket).
  Ánh xạ công việc nằm trong RAM nên restart server làm mất tác vụ đang chạy.
- **Một tiến trình cho một thư mục làm việc**, giành nguyên tử bằng `.lock` ngay lúc nhận
  upload, và nhả ra trong lúc chờ người vẽ hộp.
- **Ghi nguyên tử** (file tạm → kiểm → `os.replace`); manifest ghi *sau* artifact nên
  crash chỉ gây cache miss.
- **Mỗi cue nguồn ứng đúng một cue kết quả**, giữ nguyên timestamp.

**Lô dịch phụ thuộc model:** mặc định 25 cue/request, đo trên `deepseek-v4-flash`. Đổi
model thì đo lại rồi chỉnh `lo` trong `pipeline/translate.py` — lô quá lớn bị cắt và rơi
vào chia đôi, đắt gấp ~4 lần.

## 7. Chưa làm

Lồng tiếng TTS · tự dò vùng chữ bằng OCR · giao diện desktop · phụ đề mềm · đăng nhập
· hàng đợi ngoài · WebSocket · triển khai máy chủ · chạy nhiều video song song · vùng
mờ bám chuyển động trong một câu (vùng vẫn đứng yên trong mỗi câu) · benchmark video
dài / chi phí API cho cả một phim.
