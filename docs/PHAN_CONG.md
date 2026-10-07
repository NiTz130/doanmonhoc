# Phân công đồ án: Dịch phụ đề video Anh → Việt

**Nhóm:** 3 thành viên · **Nhóm trưởng:** TV1.

Thay TV1–TV3 bằng họ tên và MSSV sau khi nhóm chốt danh sách.

Tài liệu này phân công **theo thứ tự phụ thuộc kỹ thuật, không theo lịch**. Việc nào chưa đủ đầu vào thì chưa bắt đầu được; việc nào đủ đầu vào thì bắt đầu ngay, không chờ mốc thời gian. Deadline nộp bài do môn học quy định, nhóm tự áp lên các cổng ở §3 và §7.

## 1. Mục tiêu và phạm vi

Xây dựng **web app** dịch phụ đề video: người dùng tải video tiếng Anh lên qua trình duyệt, hệ thống tận dụng phụ đề có sẵn hoặc nhận dạng bằng Whisper, dịch sang tiếng Việt tại máy bằng NLLB (không khoá API), làm mờ vùng phụ đề cứng do người dùng khoanh trên canvas, và trả về video có phụ đề Việt. SQLite lưu nhóm, thuật ngữ, nhật ký và trạng thái công việc.

Sản phẩm chia hai giai đoạn: **backend HTTP API + pipeline xử lý làm trước**, **frontend web làm sau**. CLI `main.py` vẫn giữ nhưng chỉ là công cụ nội bộ để chạy kiểm thử và gỡ lỗi, không phải sản phẩm.

Không làm TTS, OCR tự dò vùng chữ, giao diện desktop, đăng nhập/phân quyền, hàng đợi ngoài (Celery/Redis), WebSocket, triển khai máy chủ, batch song song hoặc vùng blur di chuyển theo cảnh.

Tài liệu kỹ thuật dùng chung:

- [Thiết kế hệ thống](superpowers/specs/2026-09-09-video-dich-phu-de-design.md).
- [Kế hoạch triển khai và tiêu chí kiểm thử](superpowers/plans/2026-09-09-dich-phu-de-video.md).

File này phân công công việc tương lai, không xác nhận các chức năng đã được hoàn thành. Mọi ô kiểm ban đầu đều chưa hoàn tất.

## 2. Trách nhiệm chính của 3 thành viên

Nguyên tắc chia: **mỗi người đi theo lĩnh vực của mình xuyên suốt cả ba tầng** — module xử lý, route API, và màn hình frontend tương ứng. Nhờ vậy không ai phải học lại phần người khác, và ranh giới file vẫn không chồng nhau.

| Thành viên | Lĩnh vực | Module xử lý | Tầng API | Màn frontend | File test |
|---|---|---|---|---|---|
| **TV1**<br>Nhóm trưởng | Nền tảng, CSDL, điều phối, tích hợp, tổng hợp kiểm thử | `pipeline/srt.py`, `db.py`, `dieu_phoi.py`, `main.py` | — (duyệt kiến trúc, giữ `api/` mỏng) | Khung chung, điều hướng, gộp và tích hợp | `test_pipeline.py`, `tests_db.py`, `tests_smoke.py` |
| **TV2** | Đầu vào (video, phụ đề sẵn, âm thanh, nhận dạng) và hình học vùng mờ | `pipeline/subs.py`, `audio.py`, `asr.py`, `markbox.py` | `api/app.py`, `api/viec.py` — tải lên, tạo công việc, chạy nền, tiến độ, **route khung ảnh và nhận hộp** | Trang tải lên, bảng tiến độ | `tests_media.py`, `tests_api.py` |
| **TV3** | Dịch, thuật ngữ và kết xuất | `pipeline/translate.py`, `render.py` | `api/nhom.py` — nhóm, thuật ngữ, khung mặc định | Trang quản lý nhóm và thuật ngữ, **canvas vẽ hộp trên các khung câu thoại, trang kết quả** | `tests_translate.py`, phần render trong `tests_media.py` |

Ranh giới file không chồng nhau — đó là điều kiện để ba nhánh chạy song song mà không tranh chỗ. Route nhóm tách riêng thành `api/nhom.py` (FastAPI `APIRouter`) chính là để TV2 và TV3 không cùng sửa `app.py`. File dùng chung chỉ còn `pyproject.toml`, `pipeline/__init__.py`, `api/__init__.py` và `README.md`; sửa các file này phải báo trong nhóm trước khi merge. Ngoại lệ duy nhất là `tests_media.py`: TV2 ghi test audio/khung/hộp, TV3 ghi test render, mỗi người thêm hàm ở khối của mình để tránh đụng nhau.

**Việc của TV4 cũ được chia lại theo lĩnh vực kỹ thuật, không chia đều:**

- **Sang TV2:** `markbox.py` (trích khung theo từng câu thoại, validator hộp, đổi phần trăm ↔ pixel, gộp khoảng mờ) và route khung ảnh/nhận hộp — vì cùng dùng ffmpeg với `audio.py` và route nằm sẵn trong `api/app.py` của TV2.
- **Sang TV3:** `render.py` (một lần encode, chữ Việt, audio), canvas vẽ hộp và trang kết quả — vì TV3 đang nhẹ nhất và `api/nhom.py` đã xử lý hộp mặc định.
- **Sang TV1:** tổng hợp kiểm thử, `tests_smoke.py`, ảnh/video kết quả, demo. Chỉ nhận việc ở G5 vì TV1 đã nằm trên đường găng hai lần (G0, G2); không nhận thêm việc ở giữa.

**`markbox.py` không còn GUI.** Bản thiết kế cũ dùng cửa sổ tkinter; giờ việc vẽ hộp nằm ở frontend, module chỉ còn trích khung PNG (mỗi câu thoại một khung) và validate hộp. Phần canvas ở G4 do TV3 làm, gọi đúng route của TV2 — hai người phải thống nhất khuôn dạng JSON hộp trước G3 (hợp đồng route, xem §5).

Mỗi người tự viết kiểm thử cho phần mình và viết nội dung báo cáo tương ứng. TV1 tổng hợp kết quả kiểm thử, không chịu trách nhiệm viết toàn bộ test thay nhóm; đồng thời duyệt thay đổi và tích hợp, không làm thay các phần còn lại.

## 3. Thứ tự phụ thuộc và sáu cổng

Sáu giai đoạn nối tiếp; trong một giai đoạn thì ba người chạy song song. Không chuyển giai đoạn khi cổng ra chưa đạt.

| Giai đoạn | TV1 | TV2 | TV3 | Cổng ra |
|---|---|---|---|---|
| **G0 — Hợp đồng dữ liệu**<br>(chặn mọi việc khác) | Chốt phạm vi và tiêu chí; tạo repo và quy tắc nhánh; dựng Python 3.12/uv; **làm STEP-1 (`Cue`, `srt.py`, ghi file an toàn, manifest) và merge thẳng vào `main`** | Kiểm ffmpeg/ffprobe, CUDA/CPU (PC-2, PC-3); kiểm NVENC bằng **encode thật** (PC-2); kiểm `uvicorn` khởi động và `TestClient` gọi được route rỗng; chuẩn bị video mẫu có/không sidecar, video synthetic, SRT giả; chốt tọa độ phần trăm | Chuẩn bị JSON mẫu và callable dịch giả; thống nhất glossary với TV1; chốt công thức style phụ đề | `srt.py` có trên `main`; chữ ký module §8 spec và bảng route được chốt; PC-1–PC-3 có kết quả ghi lại; V-1 pass |
| **G1 — Các module song song**<br>(sau G0) | STEP-2: schema SQLite gồm bảng `cong_viec`, FK, transaction glossary | STEP-3: tìm sidecar/track chữ, tách audio 16 kHz, Whisper, fallback CUDA→CPU. STEP-5a: trích khung theo từng câu thoại, validator hộp, gộp khoảng mờ | STEP-4: chia lô 25 cue, ánh xạ dòng, kiểm đầu ra, phục hồi hữu hạn. STEP-5b: render một lần encode | Mỗi module chạy độc lập với dữ liệu giả; V-3, V-4, V-5 và phần hộp của V-6 pass |
| **G2 — Điều phối**<br>(sau G1) | STEP-6: `dieu_phoi.chay()`, cache/chạy lại, lock, batch, `bao_tien_do`; CLI gọi vào đó | Kiểm sidecar bỏ ASR, không sidecar chạy ASR, không audio, `--force-asr`, resume; `--blur off` không gọi lại ASR/API | Kiểm JSON sai/rỗng và lỗi mạng; glossary giữa lô và giữa video; transaction resume; kiểm chữ Việt và vùng mờ ở 720p/1080p, ngang/dọc | Chạy trọn một video qua CLI; V-2 và V-6 pass; batch hai video không ghi đè nhau |
| **G3 — Backend API**<br>(sau G2) | Duyệt kiến trúc: giữ `api/` mỏng, không để logic rơi vào route (CS-6) | STEP-8: `app.py` + `viec.py` — tải lên, tạo công việc, chạy nền, tiến độ, mã lỗi; route trả khung PNG và nhận hộp; trạng thái `cho_chon_khung` chạy tiếp đúng | `api/nhom.py`: route nhóm, thuật ngữ, khung mặc định; chốt khuôn dạng JSON hộp với TV2 | V-9 pass; chạy trọn một video qua `TestClient`, cho cùng kết quả với CLI |
| **G4 — Frontend web**<br>(sau G3) | Khung trang, điều hướng, gộp bốn màn, xử lý lỗi chung | Trang tải lên và bảng tiến độ hỏi theo chu kỳ | Trang quản lý nhóm và thuật ngữ; canvas vẽ hộp trên các khung câu thoại (hộp giữ nguyên khi chuyển khung); trang kết quả | V-10: tải lên → vẽ hộp → tải kết quả chạy được trên trình duyệt, có ảnh chụp màn hình |
| **G5 — Nghiệm thu**<br>(sau G4) | STEP-7: README, hướng dẫn cài/chạy; chốt tính năng; V-7 smoke media; tổng hợp ma trận test, ảnh kết quả, video demo; tổng hợp báo cáo và slide; nộp bài | Chương ASR và vùng mờ, bảng kết quả; kiểm cài lại môi trường theo README | Chương dịch và kết xuất, ví dụ trước/sau, bảng thời gian đo được | V-1–V-7, V-9, V-10 có kết quả; V-8 PASS hoặc NOT RUN kèm lý do; mã nguồn, báo cáo, slide, demo sẵn sàng |

**Ba điểm cần canh:**

1. **G0 chặn tất cả.** Cả TV2 và TV3 đều đọc/ghi SRT, nên `srt.py` và kiểu `Cue` phải lên `main` trước. TV1 làm phần này trước mọi việc khác của mình và merge thẳng, không xếp hàng chờ review — hai người còn lại làm việc chuẩn bị của G0 song song trong lúc đó.
2. **TV1 nằm trên đường găng hai lần** (STEP-1 ở G0, STEP-6 ở G2). Vì vậy TV1 **không nhận route API nào** — `api/` giao cho TV2 và TV3, TV1 chỉ duyệt để nó không phình ra thành nơi chứa logic.
3. **G3 và G4 là phần mới so với bản CLI.** Nếu hết thời gian, cắt G4 trước: backend chạy được qua `TestClient` vẫn là sản phẩm bảo vệ được, còn frontend không có backend thì không. Ghi rõ trong báo cáo phần nào chưa làm, không ghi PASS cho màn chưa dựng.

**Không phải chờ đủ mới bắt đầu:** TV3 dùng dict glossary giả, không chờ `db.py` (module dịch không được gọi DB — IC-2), và dùng SRT viết tay khi làm `render.py`, không chờ ASR của TV2. TV3 chỉ cần `srt.py` từ G0. Ở G4, cả ba người có thể dựng màn của mình trên dữ liệu JSON giả trước khi backend hoàn chỉnh.

## 4. Danh sách công việc theo thành viên

### TV1 — Nhóm trưởng

- [ ] Chốt phạm vi và tiêu chí nghiệm thu với cả nhóm.
- [ ] Chuẩn bị repository, cấu hình môi trường, hợp đồng dữ liệu và bảng route API.
- [ ] **G0:** hoàn thành `Cue`, `srt.py`, ghi file an toàn, manifest và merge vào `main`.
- [ ] **G1:** hoàn thành SQLite (kèm bảng `cong_viec`), nhật ký, ghi thuật ngữ an toàn khi resume.
- [ ] **G2:** hoàn thành `dieu_phoi.chay()`, cache/lock, batch, CLI và xử lý lỗi chung.
- [ ] **G3:** duyệt để `api/` không chứa logic xử lý; giữ một luồng duy nhất cho cả API và CLI.
- [ ] **G4:** khung trang, điều hướng, gộp bốn màn.
- [ ] **G5:** README, tổng hợp báo cáo, slide và hồ sơ nộp bài.
- [ ] **G5 (nhận từ TV4 cũ):** tổng hợp test tích hợp, ghi PASS/FAIL/NOT RUN có bằng chứng; chạy V-7 smoke media (`tests_smoke.py`); chuẩn bị ảnh/video kết quả, chương kiểm thử và demo bảo vệ.

### TV2 — Đầu vào, nhận dạng, vùng mờ và tầng công việc

- [ ] Chuẩn bị bộ video mẫu phù hợp, có quyền sử dụng; video synthetic và SRT giả.
- [ ] Kiểm ffmpeg/ffprobe, đường CUDA/CPU và khởi động `uvicorn`; ghi kết quả PC-2, PC-3.
- [ ] Kiểm NVENC bằng encode thật, không chỉ liệt kê encoder. *(nhận từ TV4 cũ)*
- [ ] Tìm sidecar/track chữ và kiểm tra phụ đề nguồn.
- [ ] Tách audio và đường Demucs tùy chọn.
- [ ] Nhận dạng Whisper, CPU fallback và lưu SRT.
- [ ] `markbox.py`: trích khung mẫu cho từng câu thoại (seek tại đầu câu + 0,3 s); validator hộp dùng chung cho mọi nguồn; đổi phần trăm ↔ pixel, tính và gộp khoảng blur. *(nhận từ TV4 cũ)*
- [ ] Route tải lên, tạo công việc, chạy nền và trả tiến độ; mã lỗi 400/404/409 đúng.
- [ ] Route trả khung PNG và nhận hộp; trạng thái `cho_chon_khung` chạy tiếp đúng. *(nhận từ TV4 cũ)*
- [ ] Trang tải lên và bảng tiến độ ở frontend.
- [ ] Đo kết quả, viết chương ASR và vùng mờ, chuẩn bị phần bảo vệ.

### TV3 — Dịch, thuật ngữ, quản lý nhóm và kết xuất

- [ ] Thống nhất prompt, dữ liệu phản hồi và glossary.
- [ ] Làm chia lô, giữ thứ tự và timestamp qua ánh xạ cue.
- [ ] Làm API adapter và kiểm tra JSON tại biên.
- [ ] Làm retry hữu hạn, cảnh báo dòng giữ nguyên nguồn.
- [ ] Duy trì glossary giữa lô/video, phối hợp transaction với TV1.
- [ ] `render.py`: render một lần encode, kiểm audio và output. *(nhận từ TV4 cũ)*
- [ ] Kiểm chữ Việt, vùng mờ, video ngang/dọc và nhiều độ phân giải. *(nhận từ TV4 cũ)*
- [ ] Route nhóm, thuật ngữ và khung mặc định (`api/nhom.py`).
- [ ] Trang quản lý nhóm và thuật ngữ ở frontend.
- [ ] Canvas vẽ hộp ở frontend: hộp giữ nguyên khi chuyển khung, đổi toạ độ chuột về khung gốc; trang kết quả. *(nhận từ TV4 cũ)*
- [ ] Đánh giá chất lượng, ghi usage và viết chương dịch và kết xuất.

## 5. Cách phối hợp và làm việc trên GitHub

- Nhánh theo phần việc, cắt từ `main`: `feat/nen-tang`, `feat/asr-api-box`, `feat/translate-render`; việc lớn tách nhánh nhỏ theo nhiệm vụ. Phần frontend dùng nhánh riêng `feat/web-*` theo màn.
- Mỗi việc có một người chịu trách nhiệm chính, kết quả bàn giao và người review. Báo ngay khi bị chặn, không đợi buổi đồng bộ.
- Đồng bộ 20–30 phút mỗi khi một cổng sắp đóng hoặc có người bị chặn: chốt việc còn lại, người review, và ai đang chờ ai.
- Mỗi PR mô tả thay đổi, cách chạy test, kết quả và hạn chế. Không commit `.env`, token, venv, model, video lớn hoặc thư mục `work/`.
- Review chéo: TV2 review TV1; TV3 review TV2; TV1 review TV3. **Ngoại lệ duy nhất:** STEP-1 ở G0 merge thẳng vào `main` để mở khóa cả nhóm, review bù ngay sau đó.
- **Thay đổi hợp đồng phải được thống nhất trước khi merge.** Có hai hợp đồng: chữ ký module ở §8 spec (`translate.dich`, `markbox.kiem_hop`, `dieu_phoi.chay`…) và **bảng route HTTP**. Đổi một trong hai giữa G3/G4 làm gãy phần của người khác.
- **`api/` phải mỏng.** Route chỉ validate, gọi `dieu_phoi` rồi trả JSON. Bắt gặp ffmpeg, model hay filtergraph trong `api/` là lý do từ chối PR — nếu không, sẽ có hai nhánh xử lý và CLI với web cho ra kết quả khác nhau.
- Sau G4 chốt tính năng; G5 chỉ sửa lỗi và chuẩn bị bảo vệ, không thêm tính năng ngoài phạm vi.

**Kiểm thử tách theo người, không dùng chung một file.** Spec §10 và plan STEP-1 ban đầu mô tả một `test_pipeline.py` duy nhất với runner ở cuối; với nhiều người cùng ghi thì lần nào cũng đụng đúng vị trí cuối file. Nhóm tách thành `tests_db.py`, `tests_media.py`, `tests_translate.py`, `tests_api.py` và `tests_smoke.py` theo bảng §2; `test_pipeline.py` giữ test SRT và điều phối, import các file kia rồi chạy runner. Vẫn `assert` trần, vẫn không thêm framework test, không phạm IC-1. Test API dùng `TestClient` của FastAPI, không mở cổng mạng thật.

## 6. Tiêu chí hoàn thành và minh chứng

| Hạng mục | Điều kiện hoàn thành | Người tổng hợp |
|---|---|---|
| Cài đặt | Thành viên khác làm theo README, khởi động được server và chạy được test offline | TV1 + TV2 |
| Phụ đề/ASR | Có sidecar dùng đúng; không sidecar nhận dạng được; lỗi input/fallback có test | TV2 |
| Dịch | Đủ cue, giữ timestamp, có glossary; phản hồi lỗi được xử lý hữu hạn | TV3 |
| Vùng mờ | Khung 8 điểm, hộp validate đúng, khoảng blur gộp đúng | TV2 |
| Render | Output phát được, audio còn, chữ Việt rõ và đúng vùng; blur on/off đúng | TV3 |
| Resume/batch | Không dùng file dở/cấu hình cũ, không trùng đích, có lỗi trả exit code khác 0 | TV1 |
| Backend API | Tải lên → tiến độ → nhận hộp → tải kết quả chạy trọn qua `TestClient`; API và CLI cho cùng artifact; 400/404/409 đúng chỗ | TV2 |
| Frontend | Bốn màn dùng được trên trình duyệt; hộp vẽ ra gửi đúng phần trăm; có ảnh chụp màn hình | TV3 + TV1 |
| Kiểm thử | Có kết quả V-1–V-7, V-9, V-10; V-8 ghi đúng đã chạy hoặc NOT RUN cùng lý do | TV1, từng người cung cấp test phần mình |
| Báo cáo/bảo vệ | Đủ kiến trúc, phương pháp, kết quả, hạn chế; mỗi người giải thích được phần mình | Cả nhóm, TV1 tổng hợp |

Test offline không cần mạng, không cần GPU, không mở cổng mạng. Dịch thật cần tải model NLLB (khoảng 600 MB) lần đầu; ghi thời gian thực đo, không ghi số ước lượng thành kết quả. Không ghi PASS cho bước chưa chạy.

## 7. Bảng theo dõi theo cổng

| Cổng | Điều kiện đóng cổng | Kết quả/PR đã bàn giao | Việc bị chặn | Người xử lý | Nhóm trưởng xác nhận |
|---|---|---|---|---|---|
| **G0** | `srt.py` trên `main`, chữ ký module và bảng route chốt, PC-1–PC-3 có kết quả, V-1 pass | `pipeline/srt.py`; V-1 PASS | — | — | [ ] |
| **G1** | Các module chạy độc lập với dữ liệu giả; V-3, V-4, V-5 pass | `db.py`, `subs/audio/asr.py`, `translate.py`, `markbox.py`, `render.py`; V-3/V-4/V-5 và phần hộp V-6 PASS | — | — | [ ] |
| **G2** | Chạy trọn một video qua CLI; V-2, V-6 pass; batch hai video không ghi đè | `dieu_phoi.py`, `main.py`; V-2, V-6 PASS | — | — | [ ] |
| **G3** | V-9 pass; chạy trọn một video qua `TestClient`, cùng kết quả với CLI | `api/app.py`, `api/viec.py`, `api/nhom.py`; V-9 PASS (4 test, gồm `test_api_va_cli_cung_ket_qua`) | — | — | [ ] |
| **G4** | V-10: tải lên → vẽ hộp → tải kết quả chạy được trên trình duyệt | `web/index.html`, `app.js`, `style.css`; **V-10 PASS** — chạy thật trên Chromium, không lỗi JS, ảnh ở [docs/ketqua](ketqua/) | — | — | [x] |
| **G5** | V-7 có kết quả nhìn được; V-8 PASS hoặc NOT RUN có lý do; báo cáo/slide/demo xong | `README.md`; V-7 PASS có ảnh khung 720p/1080p, blur bật/tắt đúng khoảng. **V-8 PASS** trên video thật 2 phút (xem [V8.md](ketqua/V8.md)): ASR + dịch + kết xuất chạy trọn, đường lui CUDA→CPU kích hoạt thật, có bảng thời gian đo được. Nhờ lượt này tìm ra lỗi `vad_filter` nuốt 90% phụ đề. `batch` hai video và video thoại nói đều PASS. Thuật ngữ truyền được từ tập 1 sang tập 2 và bản khóa đè được lên bản máy học — chứng minh bằng phép thử nhân quả, không phải trùng khớp | Báo cáo, slide, demo; V-8 | Cả nhóm | [ ] |

Trạng thái V-1–V-10 chi tiết nằm ở §Verification của plan; bảng này chỉ ghi cổng đã đóng hay chưa.

Nếu một người bị chặn, nhóm trưởng điều chỉnh người hỗ trợ và ghi lại trong bảng; không giảm kiểm tra bảo vệ dữ liệu hoặc che lỗi để đóng cổng sớm. Nếu phải cắt phạm vi thì cắt G4 trước, không cắt kiểm thử. Giữ một demo đã kiểm chứng để dùng khi mạng hoặc API không hoạt động lúc bảo vệ.
