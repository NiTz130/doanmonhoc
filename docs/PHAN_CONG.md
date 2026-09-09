# Phân công đồ án: Dịch phụ đề video Anh → Việt

**Nhóm:** 4 thành viên · **Nhóm trưởng:** TV1.

Thay TV1–TV4 bằng họ tên và MSSV sau khi nhóm chốt danh sách.

Tài liệu này phân công **theo thứ tự phụ thuộc kỹ thuật, không theo lịch**. Việc nào chưa đủ đầu vào thì chưa bắt đầu được; việc nào đủ đầu vào thì bắt đầu ngay, không chờ mốc thời gian. Deadline nộp bài do môn học quy định, nhóm tự áp lên các cổng ở §3 và §7.

## 1. Mục tiêu và phạm vi

Xây dựng CLI nhận video tiếng Anh, tận dụng phụ đề có sẵn hoặc nhận dạng bằng Whisper, dịch sang tiếng Việt bằng DeepSeek, làm mờ vùng phụ đề cứng do người dùng chọn và xuất video có phụ đề Việt. SQLite lưu nhóm, thuật ngữ và nhật ký. Có chế độ xử lý một video và batch tuần tự.

Không làm TTS, OCR tự dò vùng chữ, giao diện web, batch song song hoặc vùng blur di chuyển theo cảnh.

Tài liệu kỹ thuật dùng chung:

- [Thiết kế hệ thống](superpowers/specs/2026-09-09-video-dich-phu-de-design.md).
- [Kế hoạch triển khai và tiêu chí kiểm thử](superpowers/plans/2026-09-09-dich-phu-de-video.md).

File này phân công công việc tương lai, không xác nhận các chức năng đã được hoàn thành. Mọi ô kiểm ban đầu đều chưa hoàn tất.

## 2. Trách nhiệm chính của 4 thành viên

| Thành viên | Phần phụ trách | File/module sở hữu | File test sở hữu | Phần báo cáo và bảo vệ |
|---|---|---|---|---|
| **TV1 — Nhóm trưởng** | Chốt yêu cầu, điều phối tiến độ, nền tảng SRT/cache, SQLite, CLI và tích hợp | `main.py`, `pipeline/srt.py`, `pipeline/db.py`, cấu hình dự án | `test_srt.py`, `test_db.py`, `test_pipeline.py` | Bài toán, kiến trúc, CSDL, luồng tổng thể, tổng hợp báo cáo |
| **TV2** | Đầu vào video, tìm phụ đề có sẵn, tách audio, ASR và fallback CPU | `pipeline/subs.py`, `pipeline/audio.py`, `pipeline/asr.py` | `test_asr.py` | Tiền xử lý, nhận dạng giọng nói, đánh giá phụ đề nguồn |
| **TV3** | DeepSeek, chia lô, kiểm tra JSON, retry và thuật ngữ nhất quán | `pipeline/translate.py` | `test_translate.py` | Phương pháp dịch, prompt, thuật ngữ, chất lượng và chi phí đo được |
| **TV4** | Chọn vùng blur, hình học phụ đề, ffmpeg render, điều phối kiểm thử tích hợp | `pipeline/markbox.py`, `pipeline/render.py` | `test_render.py` | Xử lý hình ảnh, kết xuất, kết quả kiểm thử và kịch bản demo |

Ranh giới file không chồng nhau — đó là điều kiện để bốn nhánh chạy song song mà không tranh chỗ. File dùng chung chỉ còn `pyproject.toml`, `pipeline/__init__.py` và `README.md`; sửa các file này phải báo trong nhóm trước khi merge.

Mỗi người tự viết kiểm thử cho phần mình và viết nội dung báo cáo tương ứng. TV4 tổng hợp kết quả kiểm thử, không chịu trách nhiệm viết toàn bộ test thay nhóm. TV1 duyệt thay đổi và tích hợp, không làm thay các phần còn lại.

## 3. Thứ tự phụ thuộc và bốn cổng

Bốn giai đoạn nối tiếp; trong một giai đoạn thì bốn người chạy song song. Không chuyển giai đoạn khi cổng ra chưa đạt.

| Giai đoạn | TV1 — Nhóm trưởng | TV2 — Đầu vào/ASR | TV3 — Dịch | TV4 — Blur/render | Cổng ra |
|---|---|---|---|---|---|
| **G0 — Hợp đồng dữ liệu**<br>(chặn mọi việc khác) | Chốt phạm vi và tiêu chí nghiệm thu; tạo repo và quy tắc nhánh; dựng Python 3.12/uv; **làm STEP-1 (`Cue`, `srt.py`, atomic write, manifest) và merge thẳng vào `main`** | Kiểm ffmpeg/ffprobe, CUDA/CPU (PC-2, PC-3); chuẩn bị video ngắn có và không có sidecar; ghi đặc điểm đầu vào | Đọc contract DeepSeek (PC-4); chuẩn bị JSON mẫu và callable giả; thống nhất glossary với TV1; dự toán cách đo usage | Kiểm NVENC bằng **encode thật** (PC-2); chuẩn bị video synthetic và SRT giả; chốt tọa độ phần trăm và công thức style | `srt.py` có trên `main`; chữ ký module §8 spec được chốt; PC-1–PC-3 có kết quả ghi lại; V-1 pass |
| **G1 — Nền tảng song song**<br>(sau G0) | STEP-2: schema SQLite, FK, khóa từ, transaction glossary | STEP-3: tìm sidecar/track chữ, bỏ bitmap; tách audio 16 kHz mono; Whisper, duyệt segments, fallback CUDA→CPU; Demucs tùy chọn | STEP-4: chia lô 400 cue, 5 cue ngữ cảnh, ánh xạ dòng, API adapter, validation JSON, retry hữu hạn | STEP-5: validator box, đổi tọa độ pixel, gộp khoảng blur, cửa sổ Tk 8 khung, render một lần encode | Mỗi module chạy được độc lập với dữ liệu giả; V-3, V-4, V-5 và phần box của V-6 pass |
| **G2 — Tích hợp và độ tin cậy**<br>(sau G1) | STEP-6: ghép luồng thật, manifest/cache/lock, batch tuần tự, exit code, nhật ký | Kiểm sidecar bỏ ASR, không sidecar chạy ASR, không audio báo đúng, `--force-asr`, resume dùng vocals; đo thời gian ASR | Kiểm JSON sai kiểu/rỗng/thiếu và mạng lỗi; glossary giữa lô và giữa video; phối hợp transaction resume với TV1; đo usage thực tế | Kiểm chữ Việt và vùng mờ trên video ra; 720p/1080p, ngang/dọc; `--blur off` và đổi box/font không gọi lại ASR/API; tổ chức bộ test tích hợp | Demo một video hoàn chỉnh; V-2 và V-6 pass; batch hai video không ghi đè nhau; mọi lỗi còn lại có người phụ trách |
| **G3 — Nghiệm thu và bảo vệ**<br>(sau G2) | STEP-7: README, hướng dẫn cài/chạy; chốt tính năng; tổng hợp báo cáo và slide; duyệt release; nộp bài | Hoàn thiện chương ASR và bảng kết quả; kiểm cài lại môi trường theo README; demo dự phòng phần đầu vào | Hoàn thiện chương dịch, ví dụ trước/sau, bảng usage; kiểm lại glossary và cảnh báo suy giảm | Chạy V-7 smoke, phối hợp V-8 khi có quyền; tổng hợp ma trận test, ảnh kết quả, video demo; kiểm chạy trên máy thuyết trình | V-1–V-7 có kết quả; V-8 ghi PASS hoặc NOT RUN kèm lý do; mã nguồn, báo cáo, slide và demo sẵn sàng; nhóm diễn tập bảo vệ |

**Hai điểm chặn thật sự, cần canh:**

1. **G0 chặn tất cả.** Cả TV2, TV3 và TV4 đều đọc/ghi SRT, nên `srt.py` và kiểu `Cue` phải lên `main` trước. TV1 làm phần này trước mọi việc khác của mình và merge thẳng, không xếp hàng chờ review — ba người còn lại làm việc chuẩn bị của G0 song song trong lúc đó.
2. **TV1 nằm trên đường găng hai lần** (STEP-1 ở G0, STEP-6 ở G2). Nếu TV1 chậm, cả nhóm dừng. Khi G0 xong thì TV1 chỉ còn `db.py` ở G1 — đó là chỗ TV1 nên chuẩn bị sẵn STEP-6 chứ không nhận thêm việc.

**Không phải chờ đủ mới bắt đầu:** TV3 dùng dict glossary giả, không chờ `db.py` (module dịch không được gọi DB — IC-2). TV4 dùng SRT viết tay, không chờ ASR của TV2. Cả hai chỉ cần `srt.py` từ G0.

## 4. Danh sách công việc theo thành viên

### TV1 — Nhóm trưởng

- [ ] Chốt phạm vi và tiêu chí nghiệm thu với cả nhóm.
- [ ] Chuẩn bị repository, cấu hình môi trường và hợp đồng dữ liệu/API.
- [ ] **G0:** hoàn thành `Cue`, `srt.py`, atomic write, manifest và merge vào `main`.
- [ ] **G1:** hoàn thành SQLite, nhật ký và ghi thuật ngữ an toàn khi resume.
- [ ] **G2:** hoàn thành cache/lock, CLI, batch, tích hợp và xử lý lỗi chung.
- [ ] Theo dõi tiến độ theo cổng; duyệt PR sau review và test.
- [ ] **G3:** tổng hợp README, báo cáo, slide và hồ sơ nộp bài.

### TV2 — Đầu vào và ASR

- [ ] Chuẩn bị bộ video mẫu phù hợp, có quyền sử dụng.
- [ ] Kiểm ffmpeg/ffprobe và đường CUDA/CPU, ghi lại kết quả PC-2, PC-3.
- [ ] Tìm sidecar/track chữ và kiểm tra phụ đề nguồn.
- [ ] Tách audio và đường Demucs tùy chọn.
- [ ] Nhận dạng Whisper, CPU fallback và lưu SRT.
- [ ] Kiểm lỗi đầu vào, không audio, đổi nguồn và resume.
- [ ] Đo kết quả, viết chương ASR và chuẩn bị phần bảo vệ.

### TV3 — Dịch và thuật ngữ

- [ ] Thống nhất prompt, dữ liệu phản hồi và glossary.
- [ ] Làm chia lô, giữ thứ tự và timestamp qua ánh xạ cue.
- [ ] Làm API adapter và kiểm tra JSON tại biên.
- [ ] Làm retry hữu hạn, cảnh báo dòng giữ nguyên nguồn.
- [ ] Duy trì glossary giữa lô/video, phối hợp transaction với TV1.
- [ ] Đánh giá chất lượng, ghi usage và viết chương dịch.

### TV4 — Vùng mờ, kết xuất và tổng hợp test

- [ ] Kiểm NVENC bằng encode thật, không chỉ liệt kê encoder.
- [ ] Validate box, đổi pixel và tính khoảng blur.
- [ ] Làm GUI đánh dấu, lưu lựa chọn và xử lý đóng cửa sổ.
- [ ] Làm render một lần encode, kiểm audio và output.
- [ ] Kiểm chữ Việt, vùng mờ, video ngang/dọc và nhiều độ phân giải.
- [ ] Tổng hợp test tích hợp, ghi PASS/FAIL/NOT RUN có bằng chứng.
- [ ] Chuẩn bị ảnh/video kết quả, chương kiểm thử và demo bảo vệ.

## 5. Cách phối hợp và làm việc trên GitHub

- Nhánh theo phần việc, cắt từ `main`: `feat/cli-db`, `feat/asr`, `feat/translate`, `feat/render`; việc lớn tách nhánh nhỏ theo nhiệm vụ.
- Mỗi việc có một người chịu trách nhiệm chính, kết quả bàn giao và người review. Báo ngay khi bị chặn, không đợi buổi đồng bộ.
- Đồng bộ 20–30 phút mỗi khi một cổng sắp đóng hoặc có người bị chặn: chốt việc còn lại, người review, và ai đang chờ ai.
- Mỗi PR mô tả thay đổi, cách chạy test, kết quả và hạn chế. Không commit `.env`, token, venv, model hoặc video lớn.
- Review chéo: TV2 review TV1; TV3 review TV2; TV4 review TV3; TV1 review TV4. **Ngoại lệ duy nhất:** STEP-1 ở G0 merge thẳng vào `main` để mở khóa cả nhóm, review bù ngay sau đó.
- **Thay đổi API chung phải được thống nhất trước khi merge.** Chữ ký ở §8 spec (`subs.tim_phu_de`, `translate.dich`, `markbox.chon_khung`, `render.ket_xuat`) và kiểu `Cue` là hợp đồng — đổi giữa G1 làm gãy cả ba nhánh đang chạy.
- Nhóm trưởng tích hợp sau khi có review; không tự duyệt phần mình mà bỏ review chéo. Mỗi thành viên dùng tài khoản của mình để ghi nhận đóng góp thật.
- Sau G2 chốt tính năng; G3 chỉ sửa lỗi và chuẩn bị bảo vệ, không thêm tính năng ngoài phạm vi.

**Kiểm thử tách theo người, không dùng chung một file.** Spec §10 và plan STEP-1 mô tả một `test_pipeline.py` duy nhất với runner đặt ở cuối; với bốn người cùng ghi thì lần nào cũng đụng đúng vị trí cuối file. Nhóm tách thành `test_srt.py`, `test_db.py`, `test_asr.py`, `test_translate.py`, `test_render.py` theo bảng §2, và `test_pipeline.py` import hết rồi chạy runner. Vẫn `assert` trần, vẫn không thêm framework test, không phạm IC-1. Ai đổi ranh giới này phải cập nhật lại spec §10 và plan STEP-1 cho khớp.

## 6. Tiêu chí hoàn thành và minh chứng

| Hạng mục | Điều kiện hoàn thành | Người tổng hợp |
|---|---|---|
| Cài đặt | Thành viên khác làm theo README và chạy được CLI/test offline | TV1 + TV2 |
| Phụ đề/ASR | Có sidecar dùng đúng; không sidecar nhận dạng được; lỗi input/fallback có test | TV2 |
| Dịch | Đủ cue, giữ timestamp, có glossary; phản hồi lỗi được xử lý hữu hạn | TV3 |
| Render | Output phát được, audio còn, chữ Việt rõ và đúng vùng; blur on/off đúng | TV4 |
| Resume/batch | Không dùng file dở/cấu hình cũ, không trùng đích, có lỗi trả exit code khác 0 | TV1 |
| Kiểm thử | Có kết quả V-1–V-7; V-8 ghi đúng đã chạy hoặc NOT RUN cùng lý do | TV4, từng người cung cấp test phần mình |
| Báo cáo/bảo vệ | Đủ kiến trúc, phương pháp, kết quả, hạn chế; mỗi người giải thích được phần mình | Cả nhóm, TV1 tổng hợp |

Test offline không cần khóa API. Chỉ thử dịch thật khi nhóm đã thống nhất tài khoản và ngân sách; ghi chi phí thực đo, không ghi số ước lượng thành kết quả. Không ghi PASS cho bước chưa chạy.

## 7. Bảng theo dõi theo cổng

| Cổng | Điều kiện đóng cổng | Kết quả/PR đã bàn giao | Việc bị chặn | Người xử lý | Nhóm trưởng xác nhận |
|---|---|---|---|---|---|
| **G0** | `srt.py` trên `main`, chữ ký module chốt, PC-1–PC-3 có kết quả, V-1 pass | Chưa cập nhật | — | — | [ ] |
| **G1** | Bốn module chạy độc lập với dữ liệu giả; V-3, V-4, V-5 pass | Chưa cập nhật | — | — | [ ] |
| **G2** | Demo một video hoàn chỉnh; V-2, V-6 pass; batch hai video không ghi đè | Chưa cập nhật | — | — | [ ] |
| **G3** | V-7 có kết quả nhìn được; V-8 PASS hoặc NOT RUN có lý do; báo cáo/slide/demo xong | Chưa cập nhật | — | — | [ ] |

Trạng thái V-1–V-8 chi tiết nằm ở §Verification của plan; bảng này chỉ ghi cổng đã đóng hay chưa.

Nếu một người bị chặn, nhóm trưởng điều chỉnh người hỗ trợ và ghi lại trong bảng; không giảm kiểm tra bảo vệ dữ liệu hoặc che lỗi để đóng cổng sớm. Giữ một demo đã kiểm chứng để dùng khi mạng hoặc API không hoạt động lúc bảo vệ.
