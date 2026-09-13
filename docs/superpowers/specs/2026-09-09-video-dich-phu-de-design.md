# Thiết kế: Hệ thống dịch phụ đề video Anh → Việt

Ngày: 2026-09-09 — bản sửa v2 theo review và yêu cầu fix.

Đồng bộ mô tả hiện trạng ngày 2026-09-12: các mã bước lịch sử được giữ để tra cứu,
nhưng thứ tự chạy hiện tại là phụ đề gốc → vùng mờ → dịch → kết xuất.
Kết quả kiểm tra cũ xem `docs/ketqua/`; bản cập nhật tài liệu này không phải lượt nghiệm thu mới.

## 1. Mục tiêu

Cho một file video tiếng Anh, sinh ra file video mới có phụ đề tiếng Việt cháy
vào hình, và phần phụ đề cứng gốc (nếu có) đã bị làm mờ.

Hệ thống phục vụ hai loại đầu vào: phim dài nhiều tập và video ngắn trên mạng
xã hội. Nhiều video có thể gom thành một **nhóm** để dùng chung bảng thuật ngữ,
khung làm mờ và kiểu chữ phụ đề.

**Sản phẩm là một web app.** Người dùng mở trình duyệt, tải video lên, theo dõi
tiến độ, khoanh vùng phụ đề cứng bằng chuột trên khung hình mẫu, rồi tải video
kết quả về. Xây theo hai giai đoạn:

1. **Backend + pipeline** (làm trước): HTTP API bọc quanh các module xử lý.
2. **Frontend web** (làm sau): trang tải lên, bảng tiến độ, canvas vẽ khung mờ,
   trang quản lý nhóm và thuật ngữ.

```
POST /api/video                tai video len, tao cong viec
GET  /api/cong-viec/{id}       trang thai, buoc dang chay, tien do
GET  /api/cong-viec/{id}/khung mot khung moi cue de ve hop
POST /api/cong-viec/{id}/hop   gui hop da ve (phan tram), chay tiep
GET  /api/cong-viec/{id}/ket-qua  tai video ket qua
GET/POST /api/nhom             nhom, thuat ngu, khung mac dinh
```

CLI `main.py` **vẫn giữ nhưng không còn là sản phẩm** — chỉ dùng nội bộ để chạy
kiểm thử, gỡ lỗi từng bước và xử lý hàng loạt khi không cần trình duyệt.

## 2. Môi trường mục tiêu (cần xác minh lại)

| Thành phần | Ghi nhận từ bản thiết kế trước |
|---|---|
| ffmpeg / ffprobe | 8.0.1-full (gyan.dev) — có `libass`, `gblur`, `overlay`, `subtitles` |
| Bộ mã hoá | `h264_nvenc`, `hevc_nvenc`, `av1_nvenc`, `libx264` |
| GPU | NVIDIA RTX 4050 Laptop, 6141 MiB VRAM, driver 610.62 |
| Python | **3.12.10** (`ctranslate2` chưa có wheel cho 3.14) |
| Trình quản lý gói | `uv` |
| `sqlite3` | Thư viện chuẩn |
| `tkinter` | **Không còn dùng** — màn đánh dấu chuyển sang canvas trong trình duyệt |
| Trình duyệt | Bất kỳ trình duyệt hiện đại hỗ trợ `<canvas>` và `fetch` |
| `DEEPSEEK_API_KEY` | Chưa có trong biến môi trường — đọc từ `.env` |

Preflight phiên sửa tài liệu: `py -0p` báo không có Python được cài. Các thông số trong bảng là ghi nhận cũ, chưa xác minh lại ở workspace này. Không coi đây là bằng chứng môi trường triển khai đã sẵn sàng. Xem PC-1–PC-5 trong plan v2.

Tesseract **không còn cần**. Khung làm mờ do người dùng đánh dấu.

## 3. Quyết định đã chốt

| Câu hỏi | Quyết định |
|---|---|
| Tách nhạc nền / giọng nói | Chỉ phục vụ nhận dạng. Mặc định ffmpeg demux; Demucs sau cờ `--separate` |
| Ngôn ngữ nguồn | Tiếng Anh (`--lang` đổi được) |
| Dịch | DeepSeek API, model `deepseek-v4-flash` |
| Sản phẩm | Web app: backend HTTP API trước, frontend sau. CLI giữ làm công cụ nội bộ |
| Khung web | FastAPI + uvicorn; upload qua `python-multipart` |
| Việc chạy lâu | Chạy nền trong tiến trình backend, trạng thái lưu ở bảng `cong_viec`, frontend hỏi tiến độ theo chu kỳ. Không Celery, không Redis, không hàng đợi ngoài |
| Vùng làm mờ | **Người dùng đánh dấu**, không tự dò. Vùng riêng theo cue lưu theo video; khung mặc định nhóm chỉ lưu khi chọn, dạng phần trăm |
| Thời điểm làm mờ | Lấy từ mốc câu trong `sub_goc.srt`, nới ±0.4 s |
| Màn đánh dấu | Canvas trong trình duyệt, một khung mỗi cue; vùng chung, vùng riêng và áp cho dải câu. Không dùng tkinter |
| Đầu ra | Chỉ phụ đề tiếng Việt burn-in |
| Trí nhớ nhiều video | SQLite, nhóm là tuỳ chọn (`nhom_id` cho phép NULL) |
| Blur mặc định video dọc | Tắt (`--blur auto`) |

## 4. Kiến trúc

```
  TRINH DUYET (giai doan sau)
  tai len . theo doi tien do . canvas ve hop . nhom & thuat ngu
    |  HTTP
    v
  api/  FastAPI          nhan file, tao cong viec, chay nen, tra tien do
    |                    KHONG tu goi ffmpeg/model, chi goi pipeline
    v
  main.py / dieu phoi    dung logic cho ca API lan CLI
    |
    v
```

```
                        +---------------------------------+
                        |     work/subtitles.db           |
                        |  nhom . video . thuat_ngu       |
                        |  nhat_ky . cong_viec            |
                        +------+-------------------+------+
                          nap  |                   | ghi
                               v                   ^
 input.mp4
    |
    +--[0]   nhan_dien   ffprobe: kich thuoc, thoi luong; nap hop + style cua nhom
    |
    +--[1]   audio.py    ffmpeg demux              -> work/<ten>/audio.wav
    |                    tuy chon --separate: Demucs -> vocals.wav
    |
    +--[1.5] subs.py     tim phu de co san (sidecar .srt / track nhung dang chu)
    |                                              -> sub_goc.srt  (bo qua [2])
    |
    +--[2]   asr.py      faster-whisper large-v3   -> sub_goc.srt
    |
    +--[4]   markbox.py  mot khung moi cue + validate vung -> vung_blur.json
    |                    hop den tu nhom, API hoac CLI; GUI o frontend
    |                    cho_chon_khung neu chua co vung
    |
    +--[3]   translate.py DeepSeek + thuat ngu nhom -> sub_vi.srt
    |
    +--[5]   render.py   ffmpeg MOT lan encode      -> output.mp4
```

Nguyên tắc xuyên suốt: **mỗi bước ghi ra một file trung gian**. Artifact và metadata hợp lệ, chữ ký dependency/cấu hình khớp thì mới bỏ qua bước đó. `--force` chạy lại mọi bước; render luôn chạy. Quy tắc đầy đủ tại §9.

## 5. Ba quy tắc bất biến

1. **Hệ thống file là nguồn sự thật của việc chạy lại.** CSDL chỉ ghi nhật ký.
   Xoá `subtitles.db` làm mất nhóm, thuật ngữ, khung nhóm và nhật ký; không xóa file media. Lượt tiếp theo phải tính lại dependency theo DB mới.

   Nếu để CSDL quyết định "bước này xong rồi", sẽ có ngày CSDL nói xong mà file
   bị xoá — hoặc ngược lại — và mất cả buổi tìm xem tại sao pipeline nhảy cóc.

2. **Nhóm do người dùng chỉ định, hệ thống không đoán.** Đoán nhóm từ tên file
   video mạng xã hội sai nhiều hơn đúng.

3. **`batch` chạy tuần tự.** Thuật ngữ tích luỹ từ video trước sang video sau;
   chạy song song thì hai video cùng dịch một tên riêng theo hai kiểu rồi tranh
   nhau ghi.

## 6. Đặc tả từng bước

### Bước 0 — Nhận diện (`pipeline/dieu_phoi.py`)

```
ffprobe -v error -select_streams v:0 \
        -show_entries stream=width,height -show_entries format=duration \
        -of json input.mp4
```

**Thư mục làm việc:**

```python
stem = Path(video).stem
h    = hashlib.sha256(str(Path(video).resolve()).encode()).hexdigest()[:8]
work = Path("work") / f"{stem}-{h}"
```

Phần băm 8 ký tự là bắt buộc, không phải trang trí. Video tải từ mạng xã hội
hay tên `video.mp4`, `download.mp4`, `1.mp4`. Không có nó thì hai video khác
nhau dùng chung một thư mục và ghi đè kết quả của nhau.

**Hồ sơ hình học** theo tỉ lệ khung, chỉ dùng làm giá trị khởi tạo:

| | NGANG (`rộng/cao >= 1.2`) | DỌC |
|---|---|---|
| `--blur auto` cho ra | on | off |
| `FontSize` dự phòng | 22 | 16 |
| `MarginV` dự phòng | 30 | 90 |

Giá trị dự phòng chỉ dùng khi không có khung làm mờ. Có khung thì cả hai suy ra
từ khung (xem bước 5).

**Nhóm:** có `--nhom "tên"` thì tra hoặc tạo bản ghi, nạp thuật ngữ, khung làm
mờ và `sub_style`. Không có thì video chạy lẻ: không nạp, không ghi thuật ngữ.

### Bước 1 — Tách âm thanh (`pipeline/audio.py`)

**Vào:** `input.mp4` · **Ra:** `work/<tên>/audio.wav`

```
ffmpeg -y -i input.mp4 -vn -ac 1 -ar 16000 -c:a pcm_s16le audio.wav
```

16 kHz mono PCM là định dạng Whisper mong đợi; ép sẵn thì faster-whisper không
phải gọi lại ffmpeg lần nữa.

Có `--separate`: chạy `demucs --two-stems=vocals -n htdemucs`, bước 2 dùng
`vocals.wav`. Demucs là extra không cài mặc định (kéo theo torch khoảng 2.5 GB).
Đáng bật với video ca nhạc, nơi Whisper nghe lời hát kém hơn hẳn lời nói.

**Ghi rõ để tránh hiểu lầm:** ffmpeg không tách được nguồn nhạc khỏi giọng nói.
Chỉ Demucs mới làm được.

**Bước này bị bỏ qua hoàn toàn nếu bước 1.5 tìm được phụ đề có sẵn** — nó chỉ
tồn tại để nuôi Whisper.

### Bước 1.5 — Tìm phụ đề có sẵn (`pipeline/subs.py`)

**Vào:** `input.mp4` · **Ra:** `sub_goc.srt` hoặc không có gì

Chạy Whisper khi video đã kèm sẵn phụ đề tiếng Anh dạng chữ là lãng phí: chậm
hơn, và kém chính xác hơn bản người ta gõ tay.

**Thứ tự tìm:**

1. **File cạnh video:** ưu tiên `<stem>.en.srt`, `<stem>.eng.srt`, `<stem>.srt` trong
   cùng thư mục. Có thì parse, kiểm hợp lệ và ghi chuẩn UTF-8 không BOM sang `sub_goc.srt` theo cơ chế atomic.
2. **Track nhúng:**

   ```
   ffprobe -v error -select_streams s \
           -show_entries stream=index,codec_name \
           -show_entries stream_tags=language -of json input.mp4
   ```

   Chỉ nhận **codec dạng chữ**: `subrip`, `ass`, `ssa`, `mov_text`, `webvtt`,
   `text`. Ưu tiên track có `language` khớp `--lang`, không có thì lấy track chữ
   đầu tiên.

   ```
   ffmpeg -y -i input.mp4 -map 0:s:<i> -c:s srt sub_goc.srt
   ```

3. Không có gì → chạy bước 1 và 2 như bình thường.

**Codec dạng ảnh bị bỏ qua:** `hdmv_pgs_subtitle` (Blu-ray), `dvd_subtitle`,
`dvb_subtitle`. Chúng là ảnh bitmap, không rút ra chữ được, nên coi như không
có.

Cờ `--force-asr` ép chạy Whisper kể cả khi tìm thấy — dùng khi phụ đề có sẵn
lệch giờ hoặc sai nội dung.

Với phim mkv đầy đủ, bước này cắt bỏ khâu tốn kém nhất của cả pipeline: không
nạp model, không chiếm VRAM, không chờ vài phút.

### Bước 2 — Nhận dạng giọng nói (`pipeline/asr.py`)

**Vào:** `audio.wav` · **Ra:** `sub_goc.srt`

```python
model = WhisperModel("large-v3", device="cuda", compute_type="int8_float16")
segments, info = model.transcribe(
    audio_path, language="en", vad_filter=True,
    vad_parameters=dict(min_silence_duration_ms=500),
)
```

- `large-v3` với `int8_float16` chiếm khoảng 3.1 GB VRAM, vừa trong 6 GB.
- `vad_filter=True` cắt khoảng lặng, tránh Whisper bịa chữ trong đoạn im lặng.
- Bao phủ cả khởi tạo, transcribe và duyệt segments: chỉ lỗi CUDA/cuDNN/DLL CUDA hoặc hết VRAM mới giải phóng model và thử CPU/int8 đúng một lần. Lỗi input/model khác truyền ra; CPU vẫn lỗi thì dừng. Không hứa hệ số tốc độ chưa đo.
- Ghi SRT bằng tay (khoảng 15 dòng). Không thêm thư viện cho việc này.

### Bước 3 — Dịch (`pipeline/translate.py`)

**Vào:** `sub_goc.srt`, bảng thuật ngữ của nhóm · **Ra:** `sub_vi.srt`, thuật
ngữ mới

```python
client = OpenAI(api_key=os.environ["DEEPSEEK_API_KEY"],
                base_url="https://api.deepseek.com")
MODEL = "deepseek-v4-flash"
```

**Thông tin provider:** model và JSON Output đối chiếu tài liệu chính thức https://api-docs.deepseek.com/quick_start/pricing/. Giá và giới hạn có thể đổi; kiểm tra trước chạy thật. Không coi ước tính trong bản cũ là báo giá.

**Chia lô mặc định 25 dòng**, mỗi lô kèm 5 dòng liền trước làm ngữ cảnh, đánh dấu rõ là
không dịch lại.

Lô 400 của thiết kế ban đầu đã được giảm sau các lượt đo ghi trong
[V8](../../ketqua/V8.md): giới hạn token đầu ra khiến model chia lại lô.
Số request phụ thuộc số cue và phản hồi; đổi model cần đo lại.

Vòng lặp chia lô vẫn giữ; với một lô nó chạy đúng một vòng, không cần nhánh
riêng cho video ngắn.

**Thuật ngữ của nhóm được nạp vào prompt:**

```
Các thuật ngữ sau đã được dịch ở những video trước trong nhóm này.
Phải dùng đúng bản dịch đó, không được dịch khác:
  Shadow Realm -> Cõi Bóng Tối
  Ashfall Pass -> Đèo Tro Tàn
```

**JSON trả về** (`response_format={"type": "json_object"}`, kèm ví dụ định dạng
trong prompt và `max_tokens` đủ lớn — tài liệu DeepSeek yêu cầu cả ba):

```json
{
  "lines": { "1": "...", "2": "..." },
  "thuat_ngu_moi": { "Ironhold": "Thành Sắt" }
}
```

Thuật ngữ đi kèm ngay trong lượt dịch, không tốn thêm lời gọi API nào.

**Kiểm tra phản hồi:** object chứa `lines` object với khóa `1..N`, giá trị chuỗi không rỗng, không có block trống phá SRT; kiểm kiểu của glossary. Khóa dư cảnh báo/bỏ. Giữ dòng hợp lệ, retry lẻ dòng thiếu/hỏng một lần. Cả lô rỗng/sai cấu trúc thì chia đôi tối đa hai tầng, ở lá retry lẻ một lần; vẫn lỗi giữ nguồn, báo index và trạng thái suy giảm. Không dùng chia lô để retry lỗi auth/network. Client timeout 120 giây, tối đa 2 retry transport; hết lỗi dừng video và không ghi artifact hoàn tất. Xem LD-4/5 trong plan.

Lý do làm kỹ chỗ này: nối phụ đề thành một khối rồi tách lại theo dòng là nguồn
lỗi phổ biến nhất khi dịch phụ đề. Model gộp hai câu hoặc tách thành ba, và toàn
bộ phần sau lệch timestamp. Đánh số rồi kiểm đếm là cách rẻ nhất để chặn.

**Thuật ngữ:** truyền từ mới đã chấp nhận sang lô kế tiếp và nửa sau của lô chia đôi, không cắt tùy ý 400 mục. Giữ bản dịch của mục đã có trong suốt video; từ khóa không bị máy sửa. Lưu từ mới với metadata dịch. Ghi glossary và dấu hash artifact đã áp dụng trong cùng transaction SQLite; resume không tăng đếm lần nữa. Sau commit cập nhật baseline glossary cho cache để lần sau không tự invalidates bởi từ vừa học. Xem LD-6 và STEP-6 trong plan.

`sub_vi.srt` ghi **UTF-8 không BOM** để libass đọc đúng dấu tiếng Việt.

Usage và thời gian của các lượt mẫu thật đã được ghi trong [V8](../../ketqua/V8.md).
Đó là số đo lịch sử trên video ngắn, chưa đủ suy ra hiệu năng/chi phí phim dài.

### Bước 4 — Đánh dấu khung làm mờ (`pipeline/markbox.py`)

**Vào:** `input.mp4`, `sub_goc.srt` · **Ra:** `vung_blur.json`

**Thứ tự quyết định:**

1. `--blur off`, hoặc `--blur auto` với video dọc → ghi `{"co_blur": false}`, xong.
2. Có `--blur-box x,y,w,h` (phần trăm) → dùng luôn.
3. Có lựa chọn đã lưu hợp lệ cho đúng video/hình học và không bật `--force` → dùng lại, ưu tiên hơn khung nhóm.
4. Nhóm đã có khung → dùng luôn, **không hỏi gì**.
5. Không có box nào → **công việc dừng ở trạng thái `cho_chon_khung`**, không phải lỗi. Backend trích một khung mỗi cue; frontend hiện chúng lên canvas, người dùng vẽ vùng rồi `POST .../hop`, công việc chạy tiếp từ bước dịch. Chạy CLI thì dừng và gợi ý `--blur-box` hoặc `--blur off`; không treo chờ.

**Màn đánh dấu (frontend hiện tại):**

Lấy mọi câu thoại trong `sub_goc.srt`. Với mỗi câu,
trích một khung tại `thời_điểm_bắt_đầu + 0.3 s`:

```
ffmpeg -ss <t> -i input.mp4 -frames:v 1 -y khung_<i>.png
```

`-ss` đặt **trước** `-i` để tua nhanh.

Lấy khung tại đầu câu thoại chứ không rải đều theo thời gian, để chắc chắn khung
nào cũng đang có phụ đề trên màn hình chứ không rơi vào cảnh trống. Đây cũng là
lý do bước 4 đứng sau bước 2 chứ không phải trước.

```
+-------------------------------------------------------+
| [<]   khung 3/N   00:04:17   "I'm not going back"  [>] |
| +---------------------------------------------------+ |
| |                                                   | |
| |            anh khung hinh                         | |
| |     +---------------------------+                 | |
| |     |  keo chuot ve hop         |                 | |
| |     +---------------------------+                 | |
| +---------------------------------------------------+ |
| Ve chua cho ca cau 2 dong.            [Xong]  [Bo]    |
+-------------------------------------------------------+
```

**Vùng chung giữ nguyên khi chuyển khung; câu có vùng riêng hiện vùng riêng.** Phụ đề
2 dòng cao hơn 1 dòng, nếu vẽ trên một khung 1 dòng rồi chốt luôn thì câu 2 dòng
sẽ thòi ra ngoài vùng mờ. Bấm qua lại vài khung là thấy ngay câu nào cao nhất.

**Thu nhỏ ảnh:** để CSS lo — `<img>`/`<canvas>` với `max-width` và `max-height`
theo khung nhìn. Toạ độ chuột đổi về khung hình gốc bằng tỉ lệ
`naturalWidth / clientWidth`, không cần hằng số thu nhỏ nguyên như bản tkinter.
Backend không thu nhỏ ảnh, trả nguyên khung PNG đã trích.

**Kết quả** lưu dạng **phần trăm** (0.0–1.0), không phải pixel:

```json
{ "co_blur": true, "vung": [{ "x": 0.30, "y": 0.855, "w": 0.40, "h": 0.09, "cue": null }] }
```

Phần trăm để một nhóm có video 1080p lẫn 720p vẫn dùng chung được một khung.

Box phải gồm số hữu hạn, x/y không âm, w/h dương, x+w và y+h <=1; đổi pixel chẵn còn tối thiểu 2×2 trong ảnh. Kiểm chung tại CLI/JSON/DB/GUI. `cue: null` áp cho mọi câu chưa có vùng riêng; danh sách `cue` dùng chỉ số từ 0. Web cho phép áp vùng cho dải câu. Chỉ lưu khung mặc định nhóm khi chọn `luu_nhom`; nhóm giữ một vùng chính, không giữ chỉ số cue. CLI `--blur-box` nhận một hộp chung. Off không xóa box nhóm.

### Bước 5 — Kết xuất (`pipeline/render.py`)

**Vào:** `input.mp4`, `sub_vi.srt`, `sub_goc.srt`, `vung_blur.json`
**Ra:** `output.mp4`

**Khoảng thời gian làm mờ lấy từ mốc câu trong `sub_goc.srt`:**

Mốc cue là xấp xỉ thời gian hardsub, không đảm bảo trùng thời điểm chữ hiện. Nới biên và kiểm video thật như rủi ro §12; không cam kết xóa sạch mọi hardsub.

1. Mỗi câu thành một khoảng, nới ±0.4 s và clamp trong thời lượng video.
2. Gộp các khoảng cách nhau dưới 1.0 s.
3. Còn quá 50 khoảng thì tăng dần ngưỡng gộp cho tới khi còn tối đa 50.
4. Vẫn quá thì làm mờ toàn thời lượng.

Bước 3 và 4 sẽ kích hoạt thường xuyên với phim thoại dày — và với phim thoại dày
thì làm mờ liên tục vốn cũng gần đúng rồi. Chuỗi `enable` quá dài làm vỡ
filtergraph, nên phải chặn.

**Đổi khung phần trăm sang pixel và suy ra kiểu chữ:**

Đặt PlayResX/Y bằng kích thước video trong style để đơn vị FontSize/MarginV khớp pixel. Kiểm vị trí thực tại 720p/1080p. `font-scale` phải hữu hạn và >0.

```python
bx, by = round(x * W), round(y * H)
bw, bh = round(w * W), round(h * H)
MarginV  = H - (by + bh)          # day chu roi dung day hop
FontSize = round(bh * 0.42)       # dieu chinh bang --font-scale
```

Hệ số 0.42 suy từ: người dùng vẽ hộp vừa cho 2 dòng, chiều cao dòng khoảng 1.2
lần cỡ chữ, nên `bh ≈ 2.4 × FontSize`. Đây là con số cần chỉnh theo font thật,
nên để lộ ra thành cờ `--font-scale` chứ không chôn cứng.

Mục đích: **phụ đề tiếng Việt rơi đúng lên vệt mờ và che gần hết nó.** Nếu đặt
chỗ khác, người xem thấy cả hai — vệt nhoè lạ ở dưới, chữ Việt ở trên.

Không có khung làm mờ thì dùng `MarginV` và `FontSize` dự phòng của hồ sơ.

**Một lần encode duy nhất:**

```
ffmpeg -y -i input.mp4 -filter_complex
  [0:v]split[base][tmp];
  [tmp]crop=bw:bh:bx:by,gblur=sigma=25[blur];
  [base][blur]overlay=bx:by:enable=between(t,2.7,5.8)+between(t,9.1,12.4)[bl];
  [bl]subtitles=sub_vi.srt:force_style=FontName=Arial,FontSize=..,MarginV=..[v]
  -map [v] -map 0:a -c:v h264_nvenc -preset p5 -cq 23 -c:a copy output.mp4
```

(Trích lược; chuỗi thật cần escape dấu nháy và dấu phẩy trong `force_style`.)

Ba điểm quan trọng:

1. **Blur và burn-in nằm trong cùng một `filter_complex`**, nên chỉ encode một
   lần. Làm hai lệnh nối tiếp là mất chất lượng hai lần và chậm gấp đôi.
2. **`crop` → `gblur` → `overlay`**, không phải `gblur` thẳng. `gblur` không có
   tham số vùng; muốn mờ một hộp thì phải cắt ra, làm mờ, dán đè. `overlay` cũng
   là chỗ duy nhất nhận được `enable` để bật tắt theo thời gian.
3. **Đường dẫn `.srt`:** chạy ffmpeg với `cwd` đặt tại thư mục chứa file và
   truyền tên tương đối. Đường dẫn Windows tuyệt đối trong filtergraph phải
   escape thành `C\:/...`; sai một dấu là ffmpeg báo lỗi không liên quan gì tới
   nguyên nhân thật.

`-c:a copy` vì âm thanh không bị sửa. Audio không tương thích MP4 phải báo lỗi rõ, không tự đổi codec. Trước render kiểm NVENC thực sự encode được. Output ghi tạm cùng thư mục, ffprobe kiểm rồi os.replace; không phá output tốt cũ khi thất bại. Bước tách chỉ phục vụ nhận dạng.

`co_blur: false` thì bỏ toàn bộ nhánh `split/crop/gblur/overlay`, chỉ còn
`[0:v]subtitles=...[v]`.

## 7. Lược đồ CSDL

```sql
PRAGMA foreign_keys = ON;

CREATE TABLE nhom (
  id            INTEGER PRIMARY KEY,
  ten           TEXT NOT NULL UNIQUE,
  ngon_ngu_goc  TEXT NOT NULL DEFAULT 'en',
  sub_style     TEXT,                      -- NULL = suy tu khung blur
  blur_x REAL, blur_y REAL, blur_w REAL, blur_h REAL,   -- 0.0-1.0
  tao_luc       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE video (
  id           INTEGER PRIMARY KEY,
  nhom_id      INTEGER REFERENCES nhom(id) ON DELETE SET NULL,
  duong_dan    TEXT NOT NULL UNIQUE,
  thu_muc_work TEXT NOT NULL UNIQUE,
  rong INTEGER, cao INTEGER, thoi_luong REAL,
  them_luc     TEXT NOT NULL DEFAULT (datetime('now')),
  xong_luc     TEXT
);

CREATE TABLE thuat_ngu (
  id       INTEGER PRIMARY KEY,
  nhom_id  INTEGER NOT NULL REFERENCES nhom(id) ON DELETE CASCADE,
  goc      TEXT NOT NULL,
  dich     TEXT NOT NULL,
  loai     TEXT NOT NULL DEFAULT 'thuat_ngu'
           CHECK (loai IN ('ten_nguoi','dia_danh','thuat_ngu')),
  so_lan   INTEGER NOT NULL DEFAULT 1,
  khoa     INTEGER NOT NULL DEFAULT 0,   -- 1 = nguoi dung chot, may khong sua
  UNIQUE (nhom_id, goc)
);

CREATE TABLE nhat_ky (
  id        INTEGER PRIMARY KEY,
  video_id  INTEGER NOT NULL REFERENCES video(id) ON DELETE CASCADE,
  buoc      TEXT NOT NULL,   -- audio|subs|asr|translate|markbox|render
  ket_qua   TEXT NOT NULL,   -- xong|bo_qua|loi
  giay      REAL,
  token_vao INTEGER, token_ra INTEGER,
  loi       TEXT,
  luc       TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE cong_viec (
  id          TEXT PRIMARY KEY,           -- uuid4, frontend dung lam dia chi
  video_id    INTEGER REFERENCES video(id) ON DELETE CASCADE,
  trang_thai  TEXT NOT NULL               -- cho|dang_chay|cho_chon_khung
              CHECK (trang_thai IN ('cho','dang_chay','cho_chon_khung',
                                    'xong','suy_giam','loi')),
  buoc        TEXT,                       -- buoc dang chay
  tien_do     REAL NOT NULL DEFAULT 0.0,  -- 0.0-1.0
  duong_dan_ra TEXT,
  loi         TEXT,
  tao_luc     TEXT NOT NULL DEFAULT (datetime('now')),
  cap_nhat_luc TEXT NOT NULL DEFAULT (datetime('now'))
);
```

Ba ràng buộc mang ý nghĩa thiết kế, không phải trang trí:

- `UNIQUE (nhom_id, goc)` — một thuật ngữ gốc chỉ có đúng một bản dịch trong một
  nhóm. Chính ràng buộc này ép tính nhất quán, không phải code.
- `video.nhom_id` **cho phép NULL** — video lẻ không thuộc nhóm nào.
- `video.nhom_id ... ON DELETE SET NULL` chứ không phải `CASCADE` — xoá một nhóm
  thì các video vẫn còn, chỉ mất liên kết trí nhớ.

`cong_viec` là bảng **duy nhất** phục vụ web app: nó theo dõi một lượt chạy để
frontend hỏi tiến độ, không phải để quyết định bước nào đã xong. Quy tắc bất
biến số 1 vẫn giữ nguyên — `trang_thai.json` trên đĩa mới là nguồn sự thật của
việc chạy lại. Xoá `subtitles.db` làm mất lịch sử công việc, không làm mất
artifact đã sinh.

`api/app.py` đọc/tạo bản ghi công việc trực tiếp qua `db.py`; `api/viec.py`
giữ ánh xạ CID → đường dẫn video/tuỳ chọn trong RAM. Restart làm mất ánh xạ và
tác vụ đang chạy; DB và artifact còn nhưng không tự phục hồi tác vụ. Người dùng
cần tải lại video để tạo công việc mới, tái dùng artifact hợp lệ.

## 8. Giao diện và cấu trúc file

```
doanmonhoc/
+-- pyproject.toml               requires-python = ">=3.12,<3.13"
+-- .env.example                 DEEPSEEK_API_KEY=
+-- README.md
+-- main.py                      argparse, cong cu noi bo
+-- api/
|   +-- __init__.py
|   +-- app.py                   FastAPI: route + validate + tra JSON
|   +-- viec.py                  chay nen, cap nhat cong_viec, tien do
+-- web/                         GIAI DOAN SAU: frontend
+-- pipeline/
|   +-- __init__.py
|   +-- dieu_phoi.py             luong 6 buoc, dung chung cho API va CLI
|   +-- db.py                    sqlite3
|   +-- audio.py                 [1]
|   +-- subs.py                  [1.5]
|   +-- asr.py                   [2]
|   +-- translate.py             [3]
|   +-- markbox.py               [4] trich khung + validate hop
|   +-- render.py                [5]
+-- test_pipeline.py             dieu phoi + runner (diem vao)
+-- test_srt.py                  V-1
+-- test_db.py                   V-3
+-- test_asr.py                  V-4
+-- test_translate.py            V-5
+-- test_render.py               V-6 phan box/render
+-- test_api.py                  V-9 route va trang thai cong viec
+-- work/
    +-- subtitles.db
    +-- <stem>-<8 ky tu bam>/
        +-- audio.wav
        +-- sub_goc.srt
        +-- sub_vi.srt
        +-- khung_*.png
        +-- vung_blur.json
```

**Ba tầng, phụ thuộc một chiều:** `api/` → `pipeline/dieu_phoi.py` → các module
xử lý. Tầng trên gọi tầng dưới, không bao giờ ngược lại.

**Các module xử lý không biết gì về CSDL và không biết gì về HTTP.** Chúng có
thể gọi ffmpeg/ghi file nhưng không truy cập DB, không nhận `Request`, không trả
`Response`; nhận dữ liệu làm tham số và trả dữ liệu thuần. `dieu_phoi.py` và
các module API gọi `db.py`. Nhờ vậy bộ kiểm thử chạy được mà không cần dựng web
server, và cùng một luồng dùng được cho cả API lẫn CLI.

```python
subs.tim_phu_de(video, lang)            -> Path | None
translate.dich(lines, glossary)         -> (ban_dich, thuat_ngu_moi)
markbox.trich_khung(video, cues, work)   -> list[Path]
markbox.kiem_hop(hop, W, H)             -> dict            # LD-8
render.ket_xuat(video, srt, hop, khoang, style, out)
dieu_phoi.chay(video, tuy_chon, bao_tien_do) -> KetQua     # dung chung
```

`bao_tien_do` là callable `(buoc, ti_le) -> None`: API truyền hàm ghi vào
`cong_viec`, CLI truyền hàm in ra màn hình, test truyền hàm đếm. Đó là toàn bộ
chỗ khác nhau giữa hai đường chạy.

**HTTP API:**

| Phương thức và đường dẫn | Việc |
|---|---|
| `POST /api/video` | Nhận file tải lên + tuỳ chọn, tạo `cong_viec`, trả `id` |
| `GET /api/cong-viec/{id}` | `trang_thai`, `buoc`, `tien_do`, `loi` |
| `GET /api/cong-viec/{id}/khung` | Một khung mỗi cue kèm mốc thời gian và câu thoại |
| `GET /api/cong-viec/{id}/khung/{i}` | Một file PNG |
| `POST /api/cong-viec/{id}/hop` | Nhận hộp hoặc danh sách vùng theo cue, validate, chạy tiếp từ bước dịch |
| `GET /api/cong-viec/{id}/ket-qua` | Tải video kết quả |
| `GET/POST /api/nhom`, `/api/nhom/{ten}/thuat-ngu`, `/api/nhom/{ten}/hop` | Quản lý nhóm, thuật ngữ, khung mặc định |

Mọi tham số CLI dưới đây đều có trường tương ứng trong `POST /api/video`; hai
đường vào dùng chung một bộ validator, không viết kiểm tra hai lần.

**Lệnh CLI (công cụ nội bộ):**

```
main.py <video> [-o OUT] [--nhom TEN] [--lang en] [--model large-v3]
                [--blur auto|on|off] [--blur-box x,y,w,h] [--font-scale 0.42]
                [--separate] [--force-asr] [--force]
main.py batch <thu_muc> [--nhom TEN] [cac co tren]
main.py nhom list | glossary <ten> | set-term <ten> "goc" "dich" [--lock]
        | set-box <ten> x,y,w,h
```

CLI không mở được màn đánh dấu (nó nằm ở frontend), nên chạy CLI mà chưa có
khung thì phải truyền `--blur-box` hoặc `--blur off`.

`--blur auto` (mặc định): bật với video ngang, tắt với video dọc. Chữ trong video
mạng xã hội thường là nội dung — meme, caption, chú thích — che nhầm là phá video.

**Phụ thuộc:** `faster-whisper`, `openai`, `python-dotenv`, `fastapi`, `uvicorn`,
`python-multipart`. Extra `[demucs]`:
`demucs`. CUDA runtime trên Windows là phụ thuộc môi trường, cần đối chiếu tài liệu phiên bản faster-whisper/ctranslate2 được cài và xác minh DLL khi chạy; không coi cài hai gói pip là đủ. `sqlite3` nằm trong thư viện chuẩn.

## 9. Chạy lại và xử lý lỗi

`work/<stem>-<hash-path>/trang_thai.json` lưu chữ ký nội dung/dependency/cấu hình, phiên bản bước và hash artifact. File tồn tại không đủ để coi hoàn tất. Băm theo khối, mỗi file một lần/lượt. DB không quyết định resume.

- Audio phụ thuộc video + separate; sub gốc phụ thuộc nguồn/sidecar/audio thực + lang/model/mode; dịch phụ thuộc sub gốc + model/prompt/glossary. Đổi upstream làm mới downstream. Render luôn chạy.
- `--force-asr` bỏ qua cả sidecar và cache sub gốc, invalidates dịch; `--force` chạy lại mọi bước. Thay video cùng path cũng làm mới box GUI.
- Đổi blur/box/font chỉ tính lại vùng/style và render; không gọi ASR/API. Các cờ luôn được xét trước cache box. Xóa file bước trước cũng làm mới các bước phụ thuộc.
- Sửa tay `sub_vi.srt` hợp lệ được giữ nếu upstream không đổi: validate đủ cue/timestamp và ghi nhận hash override. Không học glossary từ bản sửa tay. File sai cấu trúc không dùng làm cache.
- Ghi tạm cùng thư mục → validate → os.replace; manifest ghi sau artifact bằng cùng cơ chế. Crash trước manifest gây cache miss. File tạm media giữ đuôi đúng. File tốt cũ không bị xóa trước khi output mới được xác minh.
- Một lock file tạo độc quyền cho mỗi work directory, giữ suốt lượt video. Lock còn sau crash: báo rõ và yêu cầu xác minh tiến trình đã dừng trước khi xóa, không tự thu hồi.
- Resume dịch áp dụng glossary bằng transaction có dấu hash artifact; không đếm lại cùng artifact. Sau áp dụng cập nhật baseline glossary như plan LD-6/STEP-6.

Batch từ chối `-o` trước side effect; mỗi nguồn sinh `<stem>_vi.mp4`. Hậu tố `_vi.mp4` dành cho output và bị loại khỏi quét batch. Chỉ nhận file thực; tính trước các đích, trùng đích giữa hai nguồn hoặc output trùng input thì từ chối trước ghi. Chạy tuần tự, tiếp tục sau lỗi video cục bộ, tổng kết thành công/suy giảm/lỗi. Exit 1 nếu có lỗi hoặc dòng dịch giữ nguồn, 0 khi tất cả thành công. Ctrl+C dừng và exit 130. Lỗi cấu hình chung kiểm trước vòng batch.

| Tình huống | Xử lý |
|---|---|
| Lỗi CUDA thuộc loại được hỗ trợ | Thử CPU một lần cho cả giai đoạn nhận dạng, không bắt mọi exception |
| Thiếu khóa, tool, Demucs khi bật separate | Báo cấu hình thiếu trước bước phụ thuộc; không thay model/tool |
| API auth/network lỗi sau retry hữu hạn | Dừng video; không ghi bản dịch hoàn tất |
| Dòng dịch không khôi phục được | Giữ nguồn, cảnh báo index, trạng thái suy giảm và exit khác 0 |
| Chưa có khung mờ (API) | Công việc chuyển `cho_chon_khung`, không phải lỗi; chờ frontend gửi hộp |
| Chưa có khung mờ (CLI) | Dừng, gợi ý `--blur-box` hoặc `--blur off` |
| Người dùng bỏ qua bước vẽ | Blur off, không xóa box nhóm |
| Tải lên file không phải video | 400 kèm lý do, không tạo công việc, không ghi vào `work/` |
| Hỏi công việc không tồn tại | 404, không lộ đường dẫn hệ thống |
| Box sai, SRT hỏng/rỗng | Báo lỗi rõ, không âm thầm bỏ qua |
| Không audio | Nếu có sidecar hợp lệ vẫn render; nếu cần ASR thì lỗi rõ |
| ffmpeg lỗi | In stderr nguyên văn trong cả single và batch, ghi nhật ký lỗi |

## 10. Kiểm thử

Chạy bằng `assert`, không cần model, không cần mạng, không cần CSDL ngoài (test
DB dùng SQLite memory), không cần màn hình. Test tách theo module để bốn người
ghi song song không đụng nhau (`test_srt.py`, `test_db.py`, `test_asr.py`,
`test_translate.py`, `test_render.py`, `test_api.py`); `test_pipeline.py` giữ test điều phối,
import các file kia và là điểm vào duy nhất — `python test_pipeline.py`:

1. SRT đọc rồi ghi lại giữ nguyên timestamp và nội dung.
2. Câu → khoảng: nới ±0.4 s đúng, `[[1,2],[2.5,4]]` gộp thành `[[0.6,4.4]]`.
3. `[[1,2],[9,10]]` giữ nguyên hai khoảng.
4. 300 câu bị gộp xuống tối đa 50 khoảng.
5. Khung phần trăm ↔ pixel đi vòng về đúng giá trị cũ ở 1920×1080 và 1280×720.
6. `MarginV` và `FontSize` suy đúng từ khung.
7. Chuỗi `enable=` sinh ra đúng cú pháp `between(t,a,b)+between(t,c,d)`.
8. Chia lô: 450 dòng với mặc định 25 tạo 18 lô khi không retry; ghép lại đủ 450 dòng, đúng thứ tự, đúng index.
9. Kiểm đếm bắt được lô trả thiếu key và lô trả về rỗng.
10. Tên thư mục làm việc: hai video cùng tên file ở hai thư mục khác nhau cho ra
    hai thư mục làm việc khác nhau.
11. Phân loại codec phụ đề: `subrip` nhận, `hdmv_pgs_subtitle` bỏ.
12. API: tải file không phải video trả 400 và không tạo công việc; hỏi id không
    tồn tại trả 404; hộp sai gửi lên `POST .../hop` bị từ chối bằng đúng
    validator của CLI; công việc chưa có khung dừng ở `cho_chon_khung` chứ không
    báo lỗi. Dùng `TestClient` của FastAPI, không mở cổng mạng thật.

Cần CSDL (dùng `:memory:`):

12. Thuật ngữ có `khoa = 1` không bị lượt dịch sau ghi đè.
13. `UNIQUE (nhom_id, goc)` chặn được hai bản dịch khác nhau cho cùng một từ.
14. Xoá nhóm thì video vẫn còn với `nhom_id = NULL`.

Các test bổ sung bắt buộc theo plan V-1–V-6: cache/force/đổi input, ngắt ghi, batch đích trùng và exit code, JSON sai kiểu, glossary giữa lô/transaction resume, CUDA lỗi khi duyệt generator, box không hợp lệ. Runner luôn ở cuối file sau mọi test.

Smoke media (`--smoke`, V-7; không phải end-to-end): dùng ffmpeg lavfi testsrc và anullsrc sinh video 5
giây có audio rồi kiểm audio.tach và render có/không blur ở 720p/1080p; ffprobe kiểm kích thước, thời lượng, audio, WAV mono 16kHz. Xem frame để xác nhận chữ/blur đúng vị trí. Nghiệm thu ASR + dịch thật là V-8 riêng, chỉ chạy khi có quyền và dữ liệu; nếu chưa chạy ghi NOT RUN.

## 11. Ngoài phạm vi

Không làm, và không viết sẵn chỗ để sau này làm:

- Lồng tiếng Việt bằng TTS
- Giao diện desktop
- Tự dò vùng phụ đề bằng OCR
- Vùng làm mờ tự bám chuyển động trong một cue (vùng riêng theo cue đã có)
- Nhúng track phụ đề mềm vào đầu ra
- Tự nhận diện ngôn ngữ nguồn
- Tự đoán nhóm từ tên file
- Chạy `batch` song song

Riêng phần web, những thứ sau **không làm** dù là web app:

- Đăng nhập, phân quyền, nhiều tài khoản — chạy một người dùng trên máy cá nhân
- Hàng đợi ngoài (Celery, Redis, RabbitMQ) — chạy nền trong chính tiến trình backend
- WebSocket hay server-sent events — frontend hỏi tiến độ theo chu kỳ là đủ
- Triển khai lên máy chủ, HTTPS, Docker
- Chạy nhiều công việc nặng cùng lúc — một video một lúc, đúng như quy tắc bất biến số 3

## 12. Rủi ro đã biết

| Rủi ro | Mức | Giảm thiểu |
|---|---|---|
| cuDNN 9 cho faster-whisper trên Windows hay lỗi DLL | Cao | Fallback CPU tự động; README hướng dẫn theo phiên bản và kiểm DLL, có test CPU fallback |
| API/model và JSON có thể lỗi ở runtime | Trung bình | JSON Output đã được liệt kê chính thức; validate và retry hữu hạn, không tự đổi Pro. Test thật cần quyền |
| JSON mode thỉnh thoảng trả content rỗng (tài liệu ghi nhận) | Trung bình | Kiểm số dòng; lô rỗng thì chia đôi thử lại |
| Phụ đề cứng hiện sớm hoặc muộn hơn thoại | Trung bình | Nới ±0.4 s; chỉnh được bằng hằng số nếu thấy lệch trên video thật |
| Hệ số `FontSize = bh × 0.42` sai với font khác | Trung bình | Để lộ thành cờ `--font-scale`, chỉnh sau một lần chạy thử |
| Phụ đề có sẵn lệch giờ so với video | Thấp | `--force-asr` bỏ qua nó, chạy Whisper |
| Video không có audio và cũng không có phụ đề | Thấp | Báo lỗi rõ ở bước 1 |


## 13. Trạng thái bàn giao v2

Plan chi tiết: [2026-09-09-dich-phu-de-video.md](../plans/2026-09-09-dich-phu-de-video.md). DRAFT: tài liệu đã sửa, các test implementation và preflight media/API chưa chạy. Đọc LD-1–8 và STEP-1–7 trước triển khai; không dùng code mẫu v1. Không commit tự động.
