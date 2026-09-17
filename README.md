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
**2.2× thời lượng video trong mẫu đã đo ở [V8](docs/ketqua/V8.md)**; chưa đo phim hai tiếng.
ffmpeg cũng có đường lui về `libx264`.

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

**Kích thước lô dịch phụ thuộc model.** Mặc định là 25 cue một request, đo trên
`deepseek-v4-flash`: model này sinh 500–1100 token *ra* mỗi cue vì viết phần suy luận
trước khi trả JSON, nên `max_tokens=16000` chỉ chứa nổi khoảng 30 cue. Đổi sang model
khác thì đo lại rồi chỉnh `lo` trong `pipeline/translate.py` — để quá lớn thì mọi lô
đều bị cắt và rơi vào chia đôi, đắt gấp 4 lần cho cùng một video.

Kiểm nhanh môi trường:

```bash
ffmpeg -version
.venv/Scripts/python.exe test_pipeline.py      # 17 test offline, không cần mạng/GPU
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
| **Vùng làm mờ** | Vẽ hộp, kéo cạnh/góc để chỉnh; **một khung cho mỗi câu thoại**, và câu nào phụ đề nhảy chỗ thì gán vùng riêng |
| **Nhóm & thuật ngữ** | Tạo nhóm, xem/sửa bảng thuật ngữ, khoá bản dịch, đặt khung mặc định |

Khi video chưa có vùng làm mờ, công việc **dừng ở trạng thái chờ** chứ không báo lỗi:
bạn sang màn vẽ hộp, gửi lên, nó chạy tiếp từ bước dịch. Bấm *Bỏ qua* thì không làm mờ
nhưng **không xoá** khung mặc định của nhóm.

Chỗ dừng đó nằm **ngay sau nhận dạng, trước bước dịch**. Vẽ hộp chỉ cần khung hình chứ
không cần bản dịch, nên đặt nó sau bước dịch chỉ tổ bắt người dùng ngồi chờ thêm — và
nếu họ bỏ cuộc ở màn vẽ hộp thì tiền gọi API dịch đã mất rồi. Giờ chưa vẽ hộp là chưa
tốn đồng nào.

Hộp **kéo cạnh hoặc góc để chỉnh, kéo giữa hộp để dời**; kéo ra ngoài hộp thì vẽ hộp
mới. Rút hộp về gần bằng không là cách xoá nó.

Hộp giữ nguyên khi chuyển khung là có chủ đích: phụ đề hai dòng cao hơn một dòng, vẽ
trên khung một dòng rồi chốt luôn thì câu hai dòng thòi ra ngoài vùng mờ. Bấm qua lại
vài khung là thấy câu nào cao nhất — đó cũng là lý do hộp phải sửa được tại chỗ thay
vì vẽ lại từ đầu mỗi lần lệch vài pixel.

Màn vẽ hộp trích **một khung cho mỗi câu thoại**, không lấy mẫu. Video 43 phụ đề thì
có 43 ảnh. Lấy mẫu 8 khung thì đúng những câu nhảy chỗ — câu cần nhìn nhất — lại lọt
lưới, và bạn không có cách nào biết hộp đã phủ hết hay chưa. Chi phí: một lần ffmpeg
seek mỗi câu, đo được **~0,2 s mỗi khung ở 640×360**, tức ~9 s cho 43 câu. Ảnh nhỏ tải
lười nên vài chục khung không làm nghẽn trình duyệt.

### Phụ đề nhảy chỗ: vùng riêng cho từng câu

Mặc định một vùng dùng cho mọi câu. Khi phụ đề cứng nhảy lên đỉnh trong một cảnh, sang
khung của câu đó, chọn **Riêng câu đang xem**, vẽ vùng mới, rồi bấm *Áp cho dải câu* để
chép sang cả cảnh. Vùng chung của những câu còn lại không đổi. Ảnh nhỏ của câu có vùng
riêng được đánh dấu `riêng`.

Vùng riêng **thay thế** vùng chung ở đúng những câu được gán: câu 12 có vùng riêng
trên đỉnh thì lúc câu 12 hiện, chỉ vùng trên mờ, vùng dưới tắt. Phép trừ đó diễn ra ở
hai tầng — trừ theo câu, rồi trừ theo thời gian — vì bước nới ±0,4 s và gộp khoảng có
thể bắc cầu từ câu bên cạnh sang đúng lúc câu 12 đang chiếu; thiếu tầng thứ hai thì
câu đó mờ cả hai chỗ. Vùng riêng thắng ở cả hai biên của khoảng.

Ở chế độ thay thế, một câu chỉ thuộc **một** vùng riêng và chỉ có **một** vùng chung;
gửi lên hai vùng chung, hoặc một câu nằm trong hai vùng riêng, bị từ chối 400 trước khi
đụng tới công việc hay nhóm. Cỡ chữ và khung mặc định của nhóm vẫn lấy *vùng chính* từ
danh sách **thô**, trước khi trừ câu — trừ hết câu khỏi vùng chung không làm chữ nhảy
sang chỗ khác.

**Dữ liệu cũ giữ nguyên nghĩa cũ.** Payload và `vung_blur.json` không có trường
`che_do_vung` là hàng legacy và vẫn **cộng dồn** như trước; chúng không bị đọc lại bằng
nghĩa mới, cũng không bị migrate. Trường này chỉ nhận đúng hai giá trị `cong_them` và
`thay_the`, phân biệt chữ hoa thường; vắng mặt là `cong_them`, giá trị lạ là 400. Giao
diện web luôn gửi `thay_the`. Vùng đã lưu mang chế độ nào thì lần chạy sau đọc lại đúng
chế độ đó.

Mỗi vùng lấy thời gian từ các câu gán cho nó, nới ±0.4 s rồi gộp các khoảng gần nhau;
vì vậy có thể làm mờ cả khoảng trống ngắn giữa câu. Kết xuất vẫn **một lần nén**: mỗi vùng thêm một nhánh `crop → gblur →
overlay` nối tiếp trong cùng một filtergraph.

Phụ đề Việt chỉ vẽ ở **một chỗ**, nên cỡ chữ và lề dưới bám theo *vùng chính* — vùng
áp cho mọi câu, hoặc nếu không có thì vùng phủ nhiều câu nhất. `markbox.hop_chinh` giữ
quy tắc này, và cả bước kết xuất lẫn khung mặc định của nhóm đều gọi nó, nên hai chỗ
không thể chọn lệch nhau.

Hộp vẽ cho một video **chỉ thuộc về video đó**. Muốn nó thành khung mặc định dùng
chung cho cả nhóm thì tích ô *Đặt làm vùng mặc định cho nhóm* trước khi gửi — khung
mặc định của nhóm là **một** hộp (vùng chính), vì chỉ số câu thoại không dùng chung
được giữa các video. Hộp riêng của video luôn thắng khung mặc định của nhóm ở những
lần chạy sau, vì nó được vẽ trên đúng khung hình này.

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
| `--blur-box x,y,w,h` | Vùng mờ theo **phần trăm** 0–1, dùng chung được cho 720p lẫn 1080p. Chỉ áp cho video này; đặt khung mặc định cho nhóm bằng `nhom set-box` |
| `--font-scale 0.42` | `FontSize = chiều_cao_hộp × hệ_số`; chỉnh sau một lần chạy thử |
| `--vad on\|off` | `on` (mặc định) cắt khoảng lặng để Whisper khỏi bịa chữ. **Tắt với video ca nhạc** — Silero VAD coi nhạc nền là không phải tiếng nói và vứt gần hết audio |
| `--separate` | Tách giọng hát bằng Demucs trước khi nhận dạng (cần extra `demucs`). Đo được: với video ca nhạc thì `--vad off` hiệu quả hơn nhiều, `--separate` chỉ thêm chút |
| `--force-asr` | Bỏ qua phụ đề có sẵn, chạy Whisper — dùng khi phụ đề sẵn lệch giờ |
| `--force` | Chạy lại mọi bước |
| `-o OUT` | Đường dẫn ra (chỉ cho một video; `batch` từ chối cờ này) |

CLI không mở được màn vẽ hộp — nó nằm ở frontend. Chạy CLI mà chưa có khung thì phải
truyền `--blur-box` hoặc `--blur off`. `--blur-box` chỉ nhận **một** hộp dùng cho mọi
câu; vùng riêng theo từng câu chỉ đặt được trên web, vì phải nhìn khung hình mới gán được.

**Mã thoát:** `0` tất cả thành công · `1` có lỗi, có dòng giữ nguyên bản gốc, hoặc còn
video chờ vẽ hộp · `130` bị Ctrl+C.

`batch` chạy **tuần tự** để thuật ngữ tích luỹ từ video trước sang video sau, mỗi nguồn
sinh `<tên>_vi.mp4`. Đuôi `_vi.mp4` bị loại khỏi lượt quét nên chạy lại không nhận
output làm input. Hai nguồn trùng đích thì nó từ chối **trước khi ghi gì**.

## 4. Chạy lại và sửa tay

Video tải lên web được cất theo **nội dung và nhóm**, không theo tên file:
`work/tai_len/nguon/<băm nhóm>/<sha256 video>/nguon.media`. Tải lại cùng một video —
kể cả sau khi đổi tên — vẫn dùng lại được phụ đề, bản dịch và vùng mờ đã tính; tải nó
lên dưới nhóm khác thì là tài nguyên khác, vì thuật ngữ của nhóm làm đổi bản dịch. Mỗi
lần tải lên vẫn là một **công việc mới** với id riêng: kết quả và khung mẫu nằm trong
`work/tai_len/<id công việc>/`, nên hai lượt cùng một video không ghi đè nhau. Dữ liệu
tải lên từ trước bản này **giữ nguyên tại chỗ**, không tự chuyển sang cách sắp xếp mới;
lần đầu tải lại chúng có thể phải xử lý lại một lượt. CLI không đổi gì.

`work/<tên>-<8 ký tự băm>/` giữ file trung gian của từng video; `vung_blur.json` giữ
danh sách vùng kèm chỉ số câu của từng vùng; `trang_thai.json` lưu
chữ ký nội dung và cấu hình của từng bước. **Hệ thống file là nguồn sự thật** — xoá
`work/subtitles.db` làm mất nhóm, thuật ngữ và nhật ký, không làm mất artifact.

- Đổi `--blur`, hộp hay cỡ chữ → chỉ tính lại vùng mờ và kết xuất, **không** gọi lại
  Whisper hay API dịch. Vùng mờ chạy trước bước dịch, nhưng bản dịch đã có thì vẫn
  là cache hit.
- Thay nội dung video tại cùng đường dẫn → làm mới mọi bước phụ thuộc. Băm theo nội
  dung, không theo đường dẫn.
- Sửa tay `work/<...>/sub_vi.srt` rồi chạy lại: bản sửa **được giữ** nếu còn đủ cue và
  đúng mốc thời gian. Máy không học thuật ngữ từ bản sửa tay.
- Ngắt giữa chừng chỉ gây tính lại, không tạo file dở bị hiểu nhầm là hoàn tất, và
  không phá output tốt của lần trước.

- Gửi vùng mờ lên là **chạy tiếp đúng lượt đang chờ**, không phải mở một lượt mới:
  nguồn phụ đề đã chọn được giữ nguyên, nên `--force-asr` của lượt đó không làm Whisper
  chạy lại lần nữa, còn ý định làm mới bản dịch thì vẫn giữ cho tới khi bước dịch của
  chính lượt đó xong. Nếu phụ đề gốc đã đổi trong lúc bạn vẽ, web trả 409 và yêu cầu
  tải lại video — chỉ số câu thoại của vùng cũ không còn ứng với câu nào nữa.

**Lock sót sau khi máy treo:** mỗi thư mục làm việc có một `.lock`; tiến trình thứ hai
bị từ chối (web trả 409). Nếu chắc chắn không còn tiến trình nào đang chạy thì xoá tay
`work/<tên>-<băm>/.lock`. Hệ thống **không tự đoán** lock đã chết, và tải video lên lại
cũng không tự xoá lock giúp bạn.

**Khởi động lại server:** công việc còn dở của tiến trình cũ không còn ai theo dõi, nên
lúc khởi động chúng được đánh dấu **lỗi** kèm hướng dẫn tải lại, thay vì treo mãi ở
`đang chạy`. Công việc đã xong giữ nguyên kết quả và vẫn tải xuống được.

## 5. Kiểm thử

```bash
.venv/Scripts/python.exe test_pipeline.py            # 17 test offline
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

Các lượt chạy trước đã dùng ASR và API dịch thật trên video có tiếng: kết quả, usage đo được và
một lỗi tìm ra nhờ nó ở [docs/ketqua/V8.md](docs/ketqua/V8.md).

Báo cáo [B-frontend](docs/ketqua/B-frontend.md) ghi kiểm tra Chromium với API giả lập;
đó là bằng chứng giao diện của lượt kiểm tra được ghi nhận, không phải nghiệm thu
ASR/dịch thật qua web hay xác nhận mọi thay đổi hiện tại.

## 6. Kiến trúc

```
web/            4 màn HTML/CSS/JS thuần, không bundler
  |  HTTP
api/            FastAPI: validate, gọi điều phối, trả JSON — KHÔNG gọi ffmpeg/model
  |
pipeline/dieu_phoi.py    luồng 6 bước, dùng chung cho cả API lẫn CLI
  |             nhận diện → phụ đề gốc → vùng mờ → dịch → kết xuất
pipeline/{audio,subs,asr,translate,markbox,render}.py
```

Vùng mờ đứng **trước** bước dịch dù nó không phải phụ thuộc của ai: nó là bước duy nhất
cần người dùng, nên đặt nó sớm nhất có thể thì thời gian chờ của máy và của người chồng
lên nhau thay vì nối tiếp nhau.

Phụ thuộc **một chiều**. Các module xử lý không biết CSDL và không biết HTTP: nhận dữ
liệu làm tham số, trả dữ liệu thuần. `dieu_phoi.py` dùng `db.py` cho dữ liệu pipeline;
`api/app.py`, `api/viec.py` và API nhóm cũng truy cập DB. Web ghi tiến độ vào bảng
`cong_viec` qua callable `bao_tien_do`, còn CLI in ra màn hình.

Việc chạy lâu chạy nền **trong chính tiến trình backend**, không Celery, không Redis,
không WebSocket. `api/viec.py` giữ ánh xạ CID → video/tuỳ chọn/claim/checkpoint trong
RAM; khởi động lại server làm mất ánh xạ và tác vụ đang chạy. Bản ghi `cong_viec` và
artifact trên đĩa còn, nhưng không tự khôi phục tác vụ; lúc khởi động các công việc mất
hồ sơ được đánh dấu lỗi, cần tải video lại để tạo công việc mới, tái dùng artifact nào
còn hợp lệ.

Quyền ghi vào một thư mục làm việc được **giành nguyên tử ngay lúc nhận upload** bằng
chính `.lock` đó, chứ không phải kiểm tra file có tồn tại rồi tạo sau — hai lượt tải
lên cùng lúc đều lọt qua cách kiểm đó. Claim được trao thẳng cho tác vụ nền, và được
**nhả ra trong lúc chờ người vẽ vùng** rồi giành lại khi nhận vùng: không giữ khoá độc
quyền suốt thời gian người dùng suy nghĩ.

## 7. Chưa làm

Lồng tiếng TTS · tự dò vùng chữ bằng OCR · giao diện desktop · nhúng phụ đề mềm ·
đăng nhập và phân quyền · hàng đợi ngoài · WebSocket · triển khai máy chủ · chạy nhiều
video song song.

Vùng mờ theo cảnh **đã làm**: vùng gán được cho từng câu thoại (§2). Cái chưa làm là
vùng tự bám theo chuyển động trong một câu — trong một câu, vùng vẫn đứng yên.

Đã có số đo mẫu trong [V8](docs/ketqua/V8.md), nhưng chưa có benchmark video dài
hay chi phí API đại diện cho một phim. Các số đo trên là lịch sử, không phải
kết quả kiểm chứng lại phiên bản hiện tại hoặc cam kết hiệu năng.
