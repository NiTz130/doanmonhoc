# Phân công đồ án: Dịch phụ đề video Anh → Việt

**Nhóm:** 4 thành viên · **Thời gian:** 7 tuần · **Nhóm trưởng:** TV1 (bạn).

Thay TV1–TV4 bằng họ tên và MSSV sau khi nhóm chốt danh sách. Tuần 1 bắt đầu theo lịch môn học; chưa gán ngày cụ thể để tránh lệch hạn nộp.

## 1. Mục tiêu và phạm vi

Xây dựng CLI nhận video tiếng Anh, tận dụng phụ đề có sẵn hoặc nhận dạng bằng Whisper, dịch sang tiếng Việt bằng DeepSeek, làm mờ vùng phụ đề cứng do người dùng chọn và xuất video có phụ đề Việt. SQLite lưu nhóm, thuật ngữ và nhật ký. Có chế độ xử lý một video và batch tuần tự.

Không làm TTS, OCR tự dò vùng chữ, giao diện web, batch song song hoặc vùng blur di chuyển theo cảnh.

Tài liệu kỹ thuật dùng chung:

- [Thiết kế hệ thống](superpowers/specs/2026-09-09-video-dich-phu-de-design.md).
- [Kế hoạch triển khai và tiêu chí kiểm thử](superpowers/plans/2026-09-09-dich-phu-de-video.md).

File này phân công công việc tương lai, không xác nhận các chức năng đã được hoàn thành. Mọi ô kiểm ban đầu đều chưa hoàn tất.

## 2. Trách nhiệm chính của 4 thành viên

| Thành viên | Phần phụ trách | File/module chính | Phần báo cáo và bảo vệ |
|---|---|---|---|
| **TV1 — Nhóm trưởng** | Chốt yêu cầu, điều phối tiến độ, nền tảng SRT/cache, SQLite, CLI và tích hợp | `main.py`, `pipeline/srt.py`, `pipeline/db.py`, cấu hình dự án | Bài toán, kiến trúc, CSDL, luồng tổng thể, tổng hợp báo cáo |
| **TV2** | Đầu vào video, tìm phụ đề có sẵn, tách audio, ASR và fallback CPU | `pipeline/subs.py`, `pipeline/audio.py`, `pipeline/asr.py` | Tiền xử lý, nhận dạng giọng nói, đánh giá phụ đề nguồn |
| **TV3** | DeepSeek, chia lô, kiểm tra JSON, retry và thuật ngữ nhất quán | `pipeline/translate.py` | Phương pháp dịch, prompt, thuật ngữ, chất lượng và chi phí đo được |
| **TV4** | Chọn vùng blur, hình học phụ đề, ffmpeg render, điều phối kiểm thử tích hợp | `pipeline/markbox.py`, `pipeline/render.py` | Xử lý hình ảnh, kết xuất, kết quả kiểm thử và kịch bản demo |

Mỗi người tự viết kiểm thử cho phần mình và viết nội dung báo cáo tương ứng. TV4 tổng hợp kết quả kiểm thử, không chịu trách nhiệm viết toàn bộ test thay nhóm. TV1 duyệt thay đổi và tích hợp, không làm thay các phần còn lại.

## 3. Lịch làm việc chi tiết trong 7 tuần

| Tuần | TV1 — Nhóm trưởng | TV2 — Đầu vào/ASR | TV3 — Dịch | TV4 — Blur/render | Mốc bàn giao cuối tuần |
|---|---|---|---|---|---|
| **1: Chuẩn bị** | Chốt phạm vi và tiêu chí nghiệm thu; tạo repo, quy tắc nhánh; dựng Python 3.12/uv; thống nhất `Cue`, đường dẫn và API module | Kiểm ffmpeg/ffprobe, CUDA/CPU; chuẩn bị video ngắn có/không sidecar; ghi đặc điểm đầu vào | Đọc contract DeepSeek; chuẩn bị JSON mẫu và callable giả; thống nhất glossary với TV1; dự toán cách đo usage | Kiểm NVENC bằng encode thật; chuẩn bị video synthetic/SRT giả; chốt tọa độ phần trăm và công thức style | Cả nhóm chạy được kiểm tra môi trường; API module và bộ dữ liệu mẫu được thống nhất |
| **2: Thành phần nền tảng** | Làm SRT đọc/ghi/validate, atomic write, SQLite và test khóa từ/FK | Làm tìm sidecar/track chữ, bỏ bitmap; tách audio 16 kHz mono; test lựa chọn nguồn | Làm chia lô 400 cue, 5 cue ngữ cảnh, ánh xạ dòng; test bằng phản hồi giả | Làm validator box, đổi tọa độ pixel, gộp khoảng blur; test hình học | Các hàm nền tảng có kiểm thử offline chạy được; mỗi người có PR riêng |
| **3: Chức năng chính** | Làm manifest/cache/lock; CLI một video và ghép các module qua fake trước | Làm Whisper, nhận dạng và duyệt segments, fallback CUDA→CPU; thử clip ngắn; Demucs tùy chọn theo plan | Làm API adapter, timeout/retry hữu hạn, validation JSON; xử lý thiếu dòng; truyền glossary giữa lô | Làm cửa sổ Tk chọn vùng trên nhiều khung; render blur + phụ đề trong một lần encode | Có đường chạy từng module và bản tích hợp đầu tiên; lỗi/giới hạn được ghi rõ |
| **4: Tích hợp đầu-cuối** | Ghép luồng thật, nhật ký, lưu thuật ngữ và trạng thái; cùng TV3 kiểm transaction/resume | Kiểm video có sidecar bỏ ASR; không sidecar chạy ASR; không audio báo đúng; hỗ trợ sửa lỗi tích hợp | Kiểm dịch thật khi có khóa và ngân sách; giữ timestamp, từ khóa; phối hợp ghi glossary idempotent với TV1 | Kiểm chữ Việt và vùng mờ trên video đầu ra; thử 720p/1080p, ngang/dọc; xác nhận audio còn | Demo một video hoàn chỉnh; còn lỗi phải có người phụ trách và hạn xử lý |
| **5: Batch và độ tin cậy** | Làm batch tuần tự, chống trùng output, exit code và cache invalidation; kiểm ngắt giữa lúc ghi | Kiểm đổi video cùng path, `--force-asr`, resume dùng vocals; đo thời gian ASR | Kiểm JSON sai kiểu/rỗng/thiếu, mạng lỗi; kiểm tên riêng qua nhiều video; đo usage thực tế | Kiểm `--blur off`, đổi box/font không gọi lại ASR/API; tổ chức bộ kiểm thử tích hợp | V-1–V-6 đạt trên phạm vi đã triển khai; batch hai video không ghi đè nhau |
| **6: Nghiệm thu và báo cáo** | Chốt tính năng; tổng hợp báo cáo, README, hướng dẫn cài/chạy; rà lỗi mức cao | Hoàn thiện chương ASR và bảng kết quả; kiểm cài lại môi trường theo README | Hoàn thiện chương dịch, ví dụ trước/sau, bảng usage; kiểm lại glossary và cảnh báo suy giảm | Chạy smoke V-7, phối hợp V-8 có quyền; tổng hợp ma trận test, ảnh kết quả, video demo | Bản dự kiến nộp; đủ minh chứng kiểm thử và bản nháp báo cáo hoàn chỉnh |
| **7: Hoàn thiện và bảo vệ** | Kiểm checklist nộp bài; duyệt release; tổng hợp slide, phân vai thuyết trình; nộp bài | Sửa lỗi phần đầu vào/ASR; chuẩn bị giải thích thuật toán và demo dự phòng | Sửa lỗi phần dịch; chuẩn bị giải thích prompt, retry, hạn chế và chi phí | Sửa lỗi render; hoàn thiện demo, kiểm chạy trên máy thuyết trình và file dự phòng | Mã nguồn, báo cáo, slide và demo sẵn sàng; cả nhóm diễn tập bảo vệ |

**Thứ tự phụ thuộc:** hợp đồng dữ liệu tuần 1 → nền tảng tuần 2 → module tuần 3 → tích hợp tuần 4 → kiểm độ tin cậy tuần 5 → nghiệm thu tuần 6 → nộp/bảo vệ tuần 7. Các thành viên dùng dữ liệu giả khi module phụ thuộc chưa xong, không chờ nhau mới bắt đầu.

## 4. Danh sách công việc theo thành viên

### TV1 — Nhóm trưởng

- [ ] Chốt phạm vi, deadline và tiêu chí nghiệm thu với cả nhóm.
- [ ] Chuẩn bị repository, cấu hình môi trường và hợp đồng dữ liệu/API.
- [ ] Hoàn thành SRT, cache, atomic write và lock.
- [ ] Hoàn thành SQLite, nhật ký và ghi thuật ngữ an toàn khi resume.
- [ ] Hoàn thành CLI, batch, tích hợp và xử lý lỗi chung.
- [ ] Theo dõi tiến độ mỗi tuần; duyệt PR sau review và test.
- [ ] Tổng hợp báo cáo, slide và hồ sơ nộp bài.

### TV2 — Đầu vào và ASR

- [ ] Chuẩn bị bộ video mẫu phù hợp, có quyền sử dụng.
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

- [ ] Validate box, đổi pixel và tính khoảng blur.
- [ ] Làm GUI đánh dấu, lưu lựa chọn và xử lý đóng cửa sổ.
- [ ] Làm render một lần encode, kiểm audio và output.
- [ ] Kiểm chữ Việt, vùng mờ, video ngang/dọc và nhiều độ phân giải.
- [ ] Tổng hợp test tích hợp, ghi PASS/FAIL/NOT RUN có bằng chứng.
- [ ] Chuẩn bị ảnh/video kết quả, chương kiểm thử và demo bảo vệ.

## 5. Cách phối hợp và làm việc trên GitHub

- Đầu mỗi tuần: họp 20–30 phút, chốt việc và người review. Cuối tuần: demo phần đã làm, cập nhật checklist và việc còn lỗi.
- Mỗi việc có một người chịu trách nhiệm chính, kết quả bàn giao, hạn và người review. Báo sớm khi bị chặn; không đợi đến cuối tuần.
- Nhánh theo phần việc: `feat/cli-db`, `feat/asr`, `feat/translate`, `feat/render`; việc lớn tách nhánh nhỏ theo nhiệm vụ.
- Mỗi PR mô tả thay đổi, cách chạy test, kết quả và hạn chế. Không commit `.env`, token, venv, model hoặc video lớn.
- Review chéo: TV2 review TV1; TV3 review TV2; TV4 review TV3; TV1 review TV4. Thay đổi API chung phải được các bên gọi hàm thống nhất trước khi merge.
- Nhóm trưởng tích hợp sau khi có review; không tự duyệt phần mình mà bỏ review chéo. Mỗi thành viên dùng tài khoản của mình để ghi nhận đóng góp thật.
- Tuần 6 chốt tính năng, tuần 7 ưu tiên sửa lỗi và bảo vệ, không thêm tính năng ngoài phạm vi.

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

## 7. Bảng theo dõi cuối tuần

| Tuần | Kết quả/PR đã bàn giao | Lỗi hoặc việc bị chặn | Người xử lý + hạn | Nhóm trưởng xác nhận |
|---|---|---|---|---|
| 1 | Chưa cập nhật | — | — | [ ] |
| 2 | Chưa cập nhật | — | — | [ ] |
| 3 | Chưa cập nhật | — | — | [ ] |
| 4 | Chưa cập nhật | — | — | [ ] |
| 5 | Chưa cập nhật | — | — | [ ] |
| 6 | Chưa cập nhật | — | — | [ ] |
| 7 | Chưa cập nhật | — | — | [ ] |

Nếu công việc trễ, nhóm trưởng điều chỉnh người hỗ trợ và ghi lại trong bảng; không giảm kiểm tra bảo vệ dữ liệu hoặc che lỗi để kịp hạn. Dành tuần 7 làm khoảng dự phòng sửa lỗi, đồng thời giữ demo đã kiểm chứng để dùng khi mạng/API không hoạt động.
