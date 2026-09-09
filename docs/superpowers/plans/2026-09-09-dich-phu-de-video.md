# Kế hoạch triển khai: Hệ thống dịch phụ đề video Anh → Việt

## Plan Metadata

- Plan ID: dich-phu-de-video-2026-09-09; Version: 3; Status: DRAFT.
- Tier: 2 — API ngoài, lưu trữ SQLite và bàn giao cho executor khác.
- Base: workspace chỉ có hai tài liệu, không có `.git` hay mã nguồn.
- SHA256 plan v1: `53a9799f0c75dddbb570db02f6b6d6042c35d42e957de9cf4ec6f92791c2a29b`.
- SHA256 spec trước sửa: `5ef8489e485215be1c5a0384a3285ed19b09c961bf5603d14574c3154e7b6a48`.
- Nguồn quyết định: người dùng yêu cầu `fix` sau review cache, batch, bản dịch, file dở, fallback và kiểm thử.
- Executor: triển khai theo contract dưới đây; không sao chép code mẫu v1.
- Lịch sử: v2 thay code mẫu v1 bằng contract và kiểm chứng. v2.1 tách file test theo module để bốn thành viên ghi song song. **v3 đổi sản phẩm từ CLI sang web app** theo yêu cầu người dùng: thêm tầng `api/` (FastAPI), tách `pipeline/dieu_phoi.py` dùng chung cho API và CLI, bỏ GUI tkinter khỏi `markbox.py`, thêm bảng `cong_viec`, thêm AC-9/CS-6/LD-9, STEP-8 (backend API) và STEP-9 (frontend), V-9 và V-10. Pipeline xử lý và LD-1–8 giữ nguyên.
- DRAFT vì preflight môi trường và kiểm tra tích hợp chưa chạy; không đồng nghĩa đã có implementation.

## Context & Scope

Spec: `../specs/2026-09-09-video-dich-phu-de-design.md`, bản sửa v2.
Phạm vi: sửa kế hoạch cho pipeline video Anh → Việt, chạy từng video hoặc batch tuần tự.
Ngoài phạm vi: TTS, OCR, giao diện desktop, xử lý song song, blur chuyển động, phụ đề mềm, đăng nhập/phân quyền, hàng đợi ngoài, triển khai máy chủ.
Lần sửa tài liệu này không triển khai code, cài gói, gọi API trả phí hay commit.

## Preconditions

- PC-1 — MUST-VERIFY: Python 3.12 và venv. `py -0p` hiện báo không có Python được cài; ghi nhận này thay thế tuyên bố đã xác minh trên máy khác trong spec. Khi triển khai, kiểm tra `uv --version`, tạo venv khi có quyền cài và chạy `.venv\Scripts\python.exe --version` (3.12.x). Dùng interpreter trong venv cho mọi lệnh, không dùng `py -3.12` sau khi cài dependency vào venv.
- PC-2 — MUST-VERIFY: `ffmpeg -version`, `ffprobe -version`, kiểm tra filters `subtitles`, `crop`, `gblur`, `overlay`; chạy encode 1 giây bằng `h264_nvenc`. Liệt kê encoder không chứng minh GPU chạy được. Trước render phải xác minh encoder hoạt động; nếu không, báo rõ, không tự đổi cấu hình chất lượng.
- PC-3 — MUST-VERIFY: dependency chính `faster-whisper`, `openai`, `python-dotenv`, `fastapi`, `uvicorn`, `python-multipart`; Demucs là extra tùy chọn. Kiểm `uvicorn api.app:app` khởi động được và `TestClient` gọi được một route rỗng trước khi ghép pipeline. Kiểm tra import trong venv. CUDA runtime là phụ thuộc môi trường; hướng dẫn theo tài liệu phiên bản cài, không coi chỉ cài pip là đủ. CPU fallback phải được test không cần GPU.
- PC-4 — MUST-VERIFY trước gọi mạng: khóa lấy từ `.env`/môi trường, không log khóa. Model `deepseek-v4-flash`, URL `https://api.deepseek.com`; tài liệu chính thức liệt kê JSON Output: https://api-docs.deepseek.com/quick_start/pricing/. Test API thật chỉ khi có ủy quyền; không tự chuyển sang Pro.
- PC-5 — VERIFIED: hiện chỉ có tài liệu, không có baseline test. Khi tiếp tục ở workspace khác, đọc lại AGENTS và kiểm tra file/user changes trước ghi; không ghi đè implementation đã có.

## Outcome

Một web app sinh MP4 có phụ đề Việt và vùng blur tùy chọn, giữ thuật ngữ theo nhóm.
Giai đoạn 1 giao backend HTTP API + pipeline chạy được qua `TestClient` và qua CLI;
giai đoạn 2 giao frontend web dùng chính API đó. Chạy lại dùng đúng artifact hợp lệ,
không dùng kết quả lỗi hoặc cấu hình cũ.

## Acceptance Criteria

- AC-1: timestamp và thứ tự cue giữ nguyên qua dịch; chuỗi Việt UTF-8 không BOM.
- AC-2: thay nguồn/cấu hình chỉ chạy lại bước bị ảnh hưởng và các bước phụ thuộc; `--force-asr`, `--blur off`, `--blur-box` có tác dụng trên lần chạy lại.
- AC-3: ngắt giữa lúc ghi không tạo artifact được coi là hoàn tất, không phá output tốt cũ.
- AC-4: batch có output riêng, không nhận output đã sinh làm input, có lỗi thì exit khác 0.
- AC-5: JSON dịch được kiểm cấu trúc/khóa/chuỗi; thiếu dòng được retry hữu hạn; glossary truyền giữa các lô và không ghi đè từ khóa.
- AC-6: lỗi CUDA trong khởi tạo, transcribe hoặc duyệt segments đều đi qua cùng fallback một lần; lỗi khác không bị che.
- AC-7: blur box hợp lệ trong hình; blur và burn-in một lần encode, giữ audio theo spec.
- AC-8: lỗi được báo rõ, có nhật ký; test offline bao phủ điều phối, smoke media kiểm render/audio; không tuyên bố end-to-end khi chưa chạy ASR và dịch thật.
- AC-9: API và CLI cho cùng kết quả trên cùng đầu vào vì dùng chung `dieu_phoi`; lỗi đầu vào trả mã HTTP đúng và không tạo công việc rác; công việc thiếu khung mờ dừng ở `cho_chon_khung` rồi chạy tiếp được sau khi nhận hộp.

## Contract Surface

- CS-1 (AC-1,5): mỗi cue nguồn tương ứng đúng một cue kết quả; giữ timestamp, không ghép/tách cue theo phản hồi model. Nguồn: spec §6 bước 3.
- CS-2 (AC-2,3): file hệ thống là nguồn sự thật của resume, DB không quyết định bước đã xong. Nguồn: spec §5 và §9 sửa v2.
- CS-3 (AC-4): batch tuần tự, không mất kết quả video trước và phản ánh thất bại qua exit code. Nguồn: spec §8–9 và review được user yêu cầu sửa.
- CS-4 (AC-5): thuật ngữ dùng chung theo nhóm; từ khóa giữ nguyên. Nguồn: spec §6–7.
- CS-5 (AC-6,7,8): fallback đúng phạm vi, lỗi rõ, kiểm hình học và output. Nguồn: spec §9–10.
- CS-6 (AC-9): `api/` không chứa logic xử lý — mọi việc đi qua `pipeline/dieu_phoi.py`; thêm đường vào không được sinh nhánh xử lý thứ hai. Bảng `cong_viec` chỉ báo tiến độ, không quyết định resume. Nguồn: spec §4, §7–8.

## Inherited Constraints

- IC-1: Python 3.12; dependency chính `faster-whisper`, `openai`, `python-dotenv`, `fastapi`, `uvicorn`, `python-multipart`; Demucs tùy chọn; không thêm framework test, không thêm hàng đợi ngoài (Celery/Redis), không thêm ORM. Nguồn: spec §2,8,10.
- IC-2: module xử lý không gọi DB và không biết HTTP; chỉ `pipeline/dieu_phoi.py` điều phối SQLite, chỉ `api/` biết request/response. Phụ thuộc một chiều `api/` → `dieu_phoi` → module. Giữ schema nhóm/video/thuật ngữ/nhật ký/công việc, FK và khóa từ như spec §7–8.
- IC-3: tên nội bộ tiếng Việt không dấu; tên API/tham số bên ngoài giữ nguyên. SRT đọc `utf-8-sig`, ghi `utf-8`.
- IC-4: sản phẩm là web app; API là đường vào chính, CLI giữ làm công cụ nội bộ với cùng bộ tuỳ chọn và cùng validator. `--force` chạy lại mọi bước; render luôn chạy để nhận chỉnh SRT/cỡ chữ. Không dùng cache output để bỏ render.
- IC-5: không commit/push/cài đặt/gọi API ngoài nếu chưa được cấp quyền tương ứng; không kế thừa lệnh commit tự động từ v1.

## Locked Decisions

- LD-1 (AC-2,3; CS-2): `work/<stem>-<hash-path>/` giữ tên cũ, thêm `trang_thai.json` lưu chữ ký artifact từng bước. Băm SHA256 nội dung đầu vào và tham số có ảnh hưởng; băm theo khối, một lần mỗi file trong một lượt. Không chỉ xét đường dẫn hoặc `exists()`: thay nội dung tại cùng đường dẫn phải bị phát hiện.
- LD-2 (AC-3): ghi file tạm cùng thư mục, đóng file, kiểm tra rồi `os.replace`; ghi manifest sau artifact bằng cùng cách. Metadata gồm phiên bản bước, chữ ký dependency/cấu hình, SHA256 output. Crash giữa hai lần replace chỉ gây cache miss. Không đánh dấu bước lỗi là xong; không xóa output tốt cũ trước render mới. File tạm media giữ đúng đuôi hoặc truyền format rõ. Một tiến trình cho một work directory; dùng lock file tạo độc quyền, tiến trình thứ hai báo lỗi. Lock sót sau crash cần người dùng xác minh không còn tiến trình rồi xóa, không tự đoán lock đã chết.
- LD-3 (AC-4): batch từ chối `-o` với lỗi argparse trước mọi xử lý. Output mặc định từng video là `<stem>_vi.mp4`; hậu tố `_vi.mp4` dành cho output, loại khỏi quét batch. Chỉ lấy file thực; tính toàn bộ đích trước chạy, hai nguồn cùng stem gây trùng đích thì từ chối batch trước ghi. Output trùng input bị từ chối, kể cả alias cùng file. Không tự chọn hậu tố khác.
- LD-4 (AC-5): phản hồi là object; `lines` là object có đúng khóa `1..N`, mỗi giá trị là chuỗi không rỗng sau strip, không có dòng trống tạo block SRT mới. `thuat_ngu_moi` nếu có phải là dict chuỗi không rỗng → chuỗi không rỗng. Không ép số/list thành chuỗi. Khóa dư bị cảnh báo và bỏ; chỉ giữ dòng hợp lệ trong bộ khóa mong đợi.
- LD-5 (AC-5): thiếu/hỏng một phần thì giữ dòng tốt, gọi lại mỗi dòng lỗi đúng một lần, kèm ngữ cảnh và glossary. Cả lô rỗng/sai cấu trúc thì chia đôi tối đa hai tầng; ở lá retry lẻ mỗi dòng một lần, còn hỏng giữ nguồn và cảnh báo. Không retry auth/network bằng chia lô. Client có timeout 120 giây và tối đa 2 retry transport; hết lỗi thì dừng video, không ghi bản dịch hoàn tất. Không đổi model. Trả trạng thái suy giảm nếu có dòng giữ nguồn.
- LD-6 (AC-5; CS-4): glossary hiệu lực = glossary nhóm cộng từ mới đã chấp nhận; tên đã có giữ bản dịch trong suốt video. Truyền glossary cập nhật cho lô kế tiếp và nửa sau khi chia lô. Không cắt mù 400 mục; nếu request vượt giới hạn thì báo lỗi rõ. Lưu từ mới cùng artifact dịch để resume có thể hoàn tất ghi DB sau crash. Trong một transaction DB: upsert thuật ngữ và ghi dấu phiên bản artifact đã áp dụng trong nhật ký; cùng video + hash artifact chỉ áp dụng một lần. Không tăng `so_lan` lần nữa khi resume. Giữ từ khóa; thay bản dịch đã chốt phải qua lệnh người dùng.
- LD-7 (AC-6): bao phủ toàn bộ nhận dạng và duyệt generator; chỉ lỗi thiếu CUDA/cuDNN/DLL CUDA hoặc hết VRAM mới thử CPU một lần, giải phóng model CUDA trước. Lỗi model không tồn tại, audio hỏng hoặc input sai phải truyền ra. CPU vẫn lỗi thì dừng và giữ lỗi gốc làm context.
- LD-8 (AC-7,9): box gồm bốn số hữu hạn, `0<=x,y<1`, `w,h>0`, `x+w<=1`, `y+h<=1`. Pixel chẵn, ít nhất 2×2, nằm trong ảnh; từ chối nếu làm tròn không còn vùng hợp lệ. **Một validator duy nhất** dùng cho CLI, thân request API, JSON trên đĩa và DB — frontend kiểm thêm chỉ để báo sớm, không thay backend. `font-scale` hữu hạn và >0.
- LD-9 (AC-9; CS-6): `api/` chỉ nhận request, validate, gọi `dieu_phoi` và trả JSON. Việc chạy lâu chạy nền trong chính tiến trình backend qua `BackgroundTasks`, cập nhật `cong_viec` bằng callable `bao_tien_do`; frontend hỏi tiến độ theo chu kỳ. Một video một lúc: công việc thứ hai trên cùng work directory bị từ chối bằng đúng cơ chế lock của LD-2, không có hàng đợi thứ hai. Thiếu khung mờ là trạng thái `cho_chon_khung`, không phải lỗi. Không thêm WebSocket, Celery, Redis, đăng nhập hay ORM.

Các LD là biện pháp tối thiểu sửa các lỗi review đã được yêu cầu; không mở rộng sản phẩm. Phương án bị loại: cache theo tồn tại, overwrite chung trong batch, retry toàn lô khi chỉ thiếu một dòng, fallback mọi exception.

## Material Delegations

- MD-1: executor chọn cấu trúc hàm nhỏ và bố trí helper trong các module hiện có; được thêm helper chữ ký/atomic write trong `srt.py`, không tạo framework cache hay abstraction provider. Verify V-1–V-7.
- MD-2: executor chọn cách giả lập dependency qua tham số/callable để chạy test offline. Không thêm mock framework, không gọi mạng trong test mặc định. Verify V-2–V-6.

## Escalations

None trong phạm vi sửa lỗi đã được yêu cầu. Nếu môi trường thực không đáp ứng preflight, ghi NOT RUN/BLOCKED cho bước phụ thuộc; không tự đổi model, encoder, dependency hoặc scope để che lỗi.

## Implementation Plan

Các bước tuần tự; đọc lại spec trước bắt đầu. Mọi bước giữ CS/IC, chỉ tự chọn mechanics trong MD. Khi dữ liệu hoặc API thực mâu thuẫn contract, dừng phần phụ thuộc và báo bằng chứng.

### STEP-1 — nền móng (không dependency)

- Targets: `pyproject.toml`, `.env.example`, `.gitignore`, `pipeline/__init__.py`, `pipeline/srt.py`, `test_srt.py`, `test_pipeline.py`.
- Cấu hình Python/ba dependency như IC-1; chọn dự án uv không đóng gói (`package=false`), dùng `uv sync`, không `pip install -e .`. Không tự cài nếu chưa có quyền.
- `Cue(idx, bat_dau, ket_thuc, text)` tính giây. Parser kiểm số hữu hạn, `0<=bat_dau<ket_thuc`; không âm thầm bỏ block hỏng. File không cue báo rõ trước dịch, không âm thầm xuất video chưa dịch.
- Ghi SRT atomic và helper signature/manifest theo LD-1,2; định nghĩa trạng thái cache miss nếu metadata thiếu/hỏng/khác version/hash. File tạm không bao giờ là cache hit.
- Test tách theo module để bốn người ghi song song không đụng nhau: `test_srt.py`, `test_db.py`, `test_asr.py`, `test_translate.py`, `test_render.py`, `test_api.py`. `test_pipeline.py` giữ test điều phối (resume, batch, smoke), import các file kia và là nơi duy nhất có runner; runner đặt ở cuối file sau mọi import và định nghĩa test. Vẫn `assert` trần, không thêm framework — IC-1 giữ nguyên. Điểm vào duy nhất vẫn là `test_pipeline.py`. Verify V-1, V-2.

### STEP-2 — SQLite (sau STEP-1)

- Targets: `pipeline/db.py`, `test_db.py`.
- Giữ schema spec; bật foreign_keys; nhóm tùy chọn, xóa nhóm không xóa video.
- API: `mo`, `lay_nhom`, `doc_thuat_ngu`, `ghi_thuat_ngu`, `doc_hop`, `ghi_hop`, `ghi_video`, `ghi_nhat_ky`.
- Cập nhật metadata video mỗi lần probe; clear `xong_luc` khi bắt đầu lượt mới. Giao dịch thuật ngữ + dấu áp dụng như LD-6 phải commit cùng nhau, không commit giữa chừng trong helper.
- Nhật ký có `xong`, `bo_qua`, `loi`, `suy_giam`; render xong không che mất cảnh báo dịch. DB không thay manifest. Verify V-3.

### STEP-3 — phụ đề, audio và ASR (sau STEP-1)

- Targets: `pipeline/subs.py`, `pipeline/audio.py`, `pipeline/asr.py`, tests.
- Tìm sidecar theo thứ tự `.en.srt`, `.eng.srt`, `.srt`; với lang khác dùng alias đúng, không luôn chèn `.eng.srt`. Rồi tìm track chữ khớp ngôn ngữ, fallback track chữ đầu theo spec. Index map phụ đề tương đối, bỏ codec bitmap. Normalize SRT qua parser/writer.
- Không tìm thấy phụ đề mới tách audio mono 16 kHz. Nếu không có audio: lỗi rõ khi cần ASR; video im lặng có sidecar vẫn render được.
- Demucs khi `--separate`: kiểm extra trước chạy; ghi nhận `vocals.wav` là output audio thực. Thiếu vocals sau lệnh thành công vẫn là lỗi, không âm thầm dùng audio chưa tách. Resume ASR phải dùng đúng vocals.
- ASR theo LD-7, ghi atomic sau nhận dạng hoàn chỉnh. Verify V-4 và V-7.

### STEP-4 — dịch (sau STEP-1,2)

- Targets: `pipeline/translate.py`, tests.
- API `dich(lines, glossary, goi, lo=400)` trả bản dịch, từ mới, các index giữ nguồn và usage nếu provider có; callable `goi` để test offline. Mốc thời gian do caller giữ.
- Lô 400 cue, ngữ cảnh 5 cue; prompt tách rõ nội dung cần dịch với chỉ dẫn. Giữ JSON mode, max_tokens 16000; xem finish_reason để phát hiện truncation. LD-4–6 quyết định validation/retry, không coi JSON parse được là đủ.
- `main.py` ghi artifact SRT + metadata/từ mới rồi mới áp dụng DB; nếu thiếu một phần cặp artifact/metadata thì cache miss. Verify V-5.

### STEP-5 — vùng mờ và render (sau STEP-1,3)

- Targets: `pipeline/markbox.py`, `pipeline/render.py`, `test_render.py`.
- `markbox.py` **không còn GUI**: chỉ trích 8 khung PNG tại `bat_dau + 0.3s` của các câu rải đều, và validate hộp theo LD-8. Việc vẽ hộp nằm ở frontend (STEP-9). Không import tkinter.
- Quyết định box mỗi lượt: off hoặc auto+dọc → tắt; tiếp theo box truyền vào (CLI hoặc API) → box nhóm → lựa chọn đã lưu hợp lệ → **không có gì thì trả trạng thái `cho_chon_khung` kèm danh sách khung đã trích**, để caller quyết định (API chờ frontend, CLI báo lỗi gợi ý `--blur-box`/`--blur off`). Validate mọi nguồn theo LD-8. Box được lưu cho nhóm như spec, không lưu trạng thái off đè box nhóm.
- Video/geometry thay đổi phải bỏ box đã lưu. Đổi flags/box nhóm không được bị JSON cũ che. Muốn vẽ lại hộp dùng `--force` hoặc xóa artifact box.
- Nới cue ±0.4 s, clamp trong thời lượng, gộp gap <=1 giây. Tăng ngưỡng đến <=50; nếu vẫn quá khi gap vượt thời lượng thì blur toàn thời lượng. Không vòng lặp vô hạn khi tham số gap=0: từ chối tham số không hợp lệ.
- Render crop→gblur→overlay→subtitles trong một lần encode; dùng SRT tên an toàn tương đối trong work. Định nghĩa đơn vị style nhất quán: đặt PlayResX/Y bằng kích thước video để FontSize/MarginV theo pixel; verify vị trí thực ở 720p/1080p, không chỉ assert công thức.
- `h264_nvenc`, p5, cq23, audio copy theo spec; audio không tương thích MP4 báo lỗi rõ, không tự transcode. Output tạm→probe đủ video/duration→replace; không dùng filesize đơn thuần làm bằng chứng thành công. Verify V-6,V-7.

### STEP-6 — điều phối và CLI (sau STEP-2–5)

- Targets: `pipeline/dieu_phoi.py`, `main.py`, `test_pipeline.py`. Toàn bộ luồng 6 bước nằm trong `dieu_phoi.chay(video, tuy_chon, bao_tien_do)`; `main.py` chỉ phân tích tham số rồi gọi nó. Giữ các lệnh video/batch/nhom, default lang=en/model=large-v3/model-dich=deepseek-v4-flash/blur=auto/font-scale=0.42.
- `bao_tien_do(buoc, ti_le)` là callable do caller truyền: CLI in ra màn hình, API ghi vào `cong_viec`, test đếm. `dieu_phoi` không tự biết mình đang chạy dưới đường nào.
- Cache audio ký theo video + separate + phiên bản xử lý; cache sub gốc ký theo video, sidecar thực đã chọn hoặc audio output, lang/model/source mode. `--force-asr` bỏ sidecar và bỏ cache sub gốc mỗi lần được truyền, dùng audio hợp lệ; invalidates dịch kể cả ASR tạo nội dung trùng. `--force` bỏ mọi cache.
- Dịch ký theo sub gốc, model dịch, prompt version và glossary nhóm lúc bắt đầu. Sau upsert từ mới thành công, cập nhật baseline glossary trong metadata về trạng thái nhóm sau áp dụng để lần resume không tự invalidates bởi chính từ mới đó. Crash trước cập nhật metadata có thể dịch lại, không được dùng sai artifact. Sửa thuật ngữ bằng lệnh nhóm invalidates dịch.
- Chạy lại ASR hoặc sửa sub gốc invalidates dịch. Thay nguồn tại cùng path invalidates audio/sub/dịch/box GUI. Đổi box/blur/font chỉ render lại, không gọi ASR/API. Render luôn chạy, nên sửa tay sub_vi hợp lệ được giữ khi upstream không đổi: validate SRT và khớp cue/timestamp, cập nhật hash như override thủ công; không tự học glossary từ bản sửa tay. File output sai cấu trúc là cache miss.
- Giữ lock toàn bộ lượt video trong try/finally; release sau khi đóng DB/file. Batch theo LD-3, tiếp tục video tiếp sau lỗi cục bộ; lỗi cấu hình chung (khóa thiếu, tool thiếu) preflight trước vòng lặp. Tổng kết số thành công/suy giảm/lỗi; exit 1 nếu có lỗi hoặc suy giảm, ngược lại 0.
- Các lỗi ffmpeg in stderr nguyên văn; single và batch dùng cùng xử lý lỗi; helper không sys.exit. KeyboardInterrupt dừng batch và trả 130, không ghi trạng thái xong. Verify V-2–V-6.

### STEP-8 — backend HTTP API (sau STEP-6)

- Targets: `api/__init__.py`, `api/app.py`, `api/viec.py`, `test_api.py`.
- Các route theo bảng spec §8. `api/` chỉ validate và gọi `dieu_phoi`; không gọi ffmpeg, không nạp model, không tự ghép filtergraph (CS-6). Thân request dùng chung validator với CLI, không viết kiểm tra thứ hai.
- Tải lên: giới hạn phần mở rộng và kích thước, ghi vào thư mục tạm rồi mới tạo `cong_viec`; file không phải video trả 400 và không để lại rác trong `work/`.
- Chạy nền bằng `BackgroundTasks`; `bao_tien_do` cập nhật `trang_thai`, `buoc`, `tien_do`. Ngoại lệ trong tác vụ nền phải chuyển công việc sang `loi` kèm thông báo, không để công việc treo ở `dang_chay` mãi.
- Thiếu khung mờ → `cho_chon_khung` (không phải lỗi); `POST .../hop` validate rồi chạy tiếp từ bước 5. Id không tồn tại → 404, không lộ đường dẫn hệ thống.
- Lock của LD-2 giữ nguyên vai trò: công việc thứ hai trên cùng work directory bị từ chối, API dịch thành 409. Verify V-9.

### STEP-9 — frontend web (sau STEP-8)

- Targets: `web/`. Giai đoạn sau; chỉ bắt đầu khi V-9 đạt.
- Bốn màn: tải lên và tuỳ chọn; bảng tiến độ hỏi theo chu kỳ; canvas vẽ hộp trên 8 khung (hộp giữ nguyên khi chuyển khung — đó là lý do có thanh trượt); quản lý nhóm và thuật ngữ.
- Đổi toạ độ chuột về khung gốc bằng `naturalWidth / clientWidth`; gửi hộp dạng phần trăm. Kiểm hợp lệ ở frontend chỉ để báo sớm, backend vẫn là nơi quyết định.
- Không thêm bundler hay framework nếu HTML + CSS + JS thuần đủ dùng; quyết định stack ghi lại kèm lý do trước khi viết. Verify V-10.

### STEP-7 — README và nghiệm thu (sau STEP-6, STEP-8)

- Targets: `README.md`, `test_pipeline.py`.
- Hướng dẫn venv, dependencies, extra Demucs, CUDA, cache và sửa SRT, batch từ chối -o, hậu tố output, lỗi/exit code, xử lý lock sót. Không tuyên bố hiệu năng/chi phí chưa đo.
- Verify V-1–V-7 và V-9; V-8 và V-10 khi có quyền và dữ liệu. Không commit tự động.

## Verification

Lệnh offline sau khi môi trường được phép cài: `.venv\Scripts\python.exe test_pipeline.py`.
Test API dùng `TestClient` trong cùng lệnh đó — không khởi động uvicorn, không mở cổng.
`test_pipeline.py` import sáu file test module (STEP-1, STEP-8) rồi chạy runner, nên lệnh chạy không đổi dù test nằm ở nhiều file.
Không model/mạng/GUI trong suite mặc định; callable giả, tempfile và SQLite memory, assert trần. Mỗi nhóm dưới đây có ít nhất một hàm `test_*` và assertion nêu rõ; tên hàm giữ nguyên, chỉ đổi file chứa nó.

- V-1 (AC-1; CS-1; IC-1,3): `test_srt_roundtrip_validation` kiểm BOM, multiline hợp lệ, timestamp roundtrip, từ chối thời gian âm/NaN/đảo chiều/block lỗi/nguồn rỗng. AFTER STEP-1.
- V-2 (AC-2,3; CS-2; LD-1,2; IC-4; MD-1): `test_resume_dependencies_and_atomic_write` giả lập pipeline, đếm calls. Lượt y nguyên chỉ render; blur off/font đổi không gọi dịch; force-asr gọi ASR và dịch; nguồn thay cùng path làm mới downstream; separate resume dùng vocals. Ngắt trước replace giữ output cũ; ngắt giữa artifact/manifest không cache hit; lock thứ hai bị từ chối; SRT sửa tay hợp lệ giữ khi upstream không đổi. AFTER STEP-1,6.
- V-3 (AC-5,8; CS-4; IC-2; LD-6): `test_glossary_transaction_resume` kiểm từ khóa không đổi, rollback không để glossary cập nhật một nửa, replay cùng artifact không tăng số lần, resume không tự invalidates glossary vừa học; xóa nhóm giữ video. AFTER STEP-2,6.
- V-4 (AC-6; CS-5; LD-7; MD-2): `test_asr_fallback_all_phases` fake model lỗi CUDA ở constructor/transcribe/generator: CPU đúng một lần, không SRT dở. Lỗi audio/model khác không fallback; CPU lỗi truyền ra. Kiểm phụ đề bitmap/text và đường audio/vocals. AFTER STEP-3.
- V-5 (AC-1,5; CS-1,4; LD-4,5,6): `test_translation_validation_and_context` kiểm 450 cue đúng thứ tự; root list, lines list, chuỗi rỗng, số, khóa dư/thiếu, glossary sai kiểu, truncation và network error. Một dòng lỗi chỉ retry dòng đó; lỗi vĩnh viễn kết thúc hữu hạn và báo index giữ nguồn. Glossary mới có mặt trong lô/nửa sau; không đổi glossary đã có. AFTER STEP-4.
- V-6 (AC-4,7,8; CS-3,5; LD-3,8): `test_batch_and_box_validation` kiểm batch -o bị từ chối trước side effect, trùng stem bị từ chối, output _vi không vào input, hai input→hai output, lỗi một video tiếp tục video sau và exit1. Box âm/NaN/Inf/vượt biên/0 pixel bị từ chối; cache không chặn blur off; single ffmpeg stderr hiện đầy đủ. AFTER STEP-5,6.
- V-7 (AC-7,8; CS-5; MD-1): `.venv\Scripts\python.exe test_pipeline.py --smoke` tạo video synthetic có audio, chạy audio.tach và render có/không blur, 720p/1080p. ffprobe xác nhận kích thước/thời lượng sai số <=0.1s, audio còn; kiểm WAV mono 16kHz. Xem frame trong/ngoài cue: chữ Việt đọc được, đúng vùng dự kiến và blur chỉ bật trong khoảng. Ghi rõ kết quả phần nhìn; không suy từ kích thước file. BEFORE nghiệm thu, AFTER STEP-7.
- V-9 (AC-9; CS-6; LD-9): `test_api.py` dùng `TestClient`, không mở cổng mạng thật, không gọi model. Tải file không phải video → 400 và `work/` không đổi; id lạ → 404; hộp sai gửi lên bị từ chối bằng đúng validator LD-8; công việc thiếu khung dừng ở `cho_chon_khung` rồi `POST .../hop` chạy tiếp và về `xong`; ngoại lệ trong tác vụ nền chuyển công việc sang `loi` chứ không treo `dang_chay`; công việc thứ hai cùng work directory trả 409. API và CLI trên cùng đầu vào cho cùng artifact. AFTER STEP-8.
- V-10 (AC-9): frontend — tải lên chạy được, tiến độ cập nhật, hộp vẽ trên canvas gửi đúng phần trăm và video kết quả tải về mở được. Kiểm thủ công trên trình duyệt, ghi lại ảnh chụp màn hình; không tự động hoá. AFTER STEP-9.
- V-8 (AC-1–9; IC-5): nghiệm thu thật CHỈ khi có ủy quyền API/model download và video mẫu: một video có sidecar, một cần ASR, chạy lại đổi blur, batch hai video cùng nhóm. Đầu ra phát được, timestamp giữ, tên riêng nhất quán, lỗi mạng không để file dịch được đánh dấu hoàn tất. NOT RUN nếu chưa có quyền/dữ liệu; không gọi V-7 là end-to-end.

Baseline: chưa có code/tests; mọi V implementation hiện NOT RUN. Review tài liệu không thay việc chạy verification khi triển khai.

## Implementation Freedom

Chỉ chọn cách tổ chức cục bộ trong MD-1/2, không thêm dependency, đổi model, schema hay chính sách output/retry. Nếu phát hiện contract không thực hiện được, báo evidence và bước bị ảnh hưởng trước khi thay đổi.