# Đề cương đồ án: Web app dịch phụ đề video Anh → Việt

**Nhóm:** 4 thành viên (TV1 nhóm trưởng). Tên và MSSV bổ sung sau khi chốt danh sách.

## 1. Nội dung đề tài cần thực hiện

Xây dựng một **ứng dụng web** bằng Python: người dùng mở trình duyệt, tải lên một video có thoại tiếng Anh, theo dõi tiến độ xử lý, khoanh vùng phụ đề cứng bằng chuột trên khung hình mẫu, rồi tải về chính video đó với **phụ đề tiếng Việt cháy vào hình** và **vệt phụ đề cứng tiếng Anh đã bị làm mờ**.

Sản phẩm xây theo hai giai đoạn: **backend HTTP API + pipeline xử lý làm trước**, **frontend web làm sau**. Dòng lệnh `main.py` vẫn giữ nhưng chỉ là công cụ nội bộ để chạy kiểm thử và gỡ lỗi từng bước.

Năm vấn đề kỹ thuật chính phải giải:

1. **Lấy phụ đề gốc.** Nếu video đã kèm phụ đề tiếng Anh dạng chữ (file `.srt` cạnh video hoặc track nhúng) thì rút thẳng ra — nhanh và chính xác hơn. Không có mới tách âm thanh và nhận dạng bằng `faster-whisper` (model `large-v3`), có đường lui về CPU khi GPU lỗi.
2. **Dịch giữ đúng cấu trúc phụ đề.** Gọi API DeepSeek theo lô 400 câu, đánh số từng dòng và kiểm đếm khi nhận về, để model không gộp hai câu hay tách thành ba làm lệch toàn bộ timestamp phía sau. Timestamp của cue nguồn được giữ nguyên, không phụ thuộc phản hồi model.
3. **Giữ thuật ngữ nhất quán qua nhiều video.** SQLite lưu bảng thuật ngữ theo **nhóm** (một bộ phim, một kênh). Tên riêng dịch ở tập 1 được dùng lại nguyên vẹn ở tập 24; người dùng khóa được bản dịch để máy không sửa.
4. **Làm mờ và ghép trong một lần encode.** Người dùng tự kéo chuột khoanh vùng phụ đề cứng trên canvas trong trình duyệt (không dùng OCR). Vùng này lưu dạng phần trăm nên dùng chung được cho 1080p lẫn 720p, và cả nhóm chỉ khoanh một lần. `ffmpeg` chạy `crop → gblur → overlay → subtitles` trong cùng một `filter_complex`, chỉ nén lại đúng một lần, giữ nguyên audio.
5. **Việc chạy lâu trong môi trường web.** Nhận dạng và kết xuất mất vài phút, không thể trả về trong một request HTTP. Backend tạo một **công việc** chạy nền, ghi tiến độ vào bảng `cong_viec`, frontend hỏi tiến độ theo chu kỳ. Khi chưa có khung mờ, công việc **dừng ở trạng thái chờ** thay vì báo lỗi; người dùng vẽ hộp xong thì nó chạy tiếp từ bước kết xuất.

Hệ thống còn phải **chạy lại được an toàn**: mỗi bước ghi ra một file trung gian kèm chữ ký nội dung, đổi cấu hình thì chỉ tính lại bước bị ảnh hưởng, ngắt giữa chừng không tạo file dở bị hiểu nhầm là hoàn tất.

**Ngoài phạm vi:** lồng tiếng TTS, tự dò vùng chữ bằng OCR, giao diện desktop, vùng mờ di chuyển theo cảnh, đăng nhập và phân quyền, hàng đợi ngoài (Celery/Redis), WebSocket, triển khai lên máy chủ, xử lý nhiều video song song.

Chi tiết kỹ thuật: [thiết kế hệ thống](superpowers/specs/2026-09-09-video-dich-phu-de-design.md) · [kế hoạch và kiểm thử](superpowers/plans/2026-09-09-dich-phu-de-video.md).

## 2. Dự kiến đầu vào

| Loại | Nội dung |
|---|---|
| **Bắt buộc** | Một file video (`.mp4`, `.mkv`) có thoại tiếng Anh, tải lên qua trình duyệt; hoặc một thư mục video khi chạy bằng công cụ dòng lệnh nội bộ |
| **Tùy chọn — nguồn phụ đề** | File `.srt` tiếng Anh đặt cạnh video, hoặc track phụ đề **dạng chữ** nhúng sẵn (`subrip`, `ass`, `mov_text`…). Có thì bỏ qua toàn bộ khâu nhận dạng. Track dạng ảnh (`hdmv_pgs_subtitle`, `dvd_subtitle`) coi như không có |
| **Tùy chọn — người dùng nhập trên web** | Tên nhóm, vùng làm mờ vẽ bằng chuột trên canvas (hoặc nhập trực tiếp bốn số phần trăm), cỡ chữ, ngôn ngữ nguồn, model nhận dạng, bật/tắt tách giọng hát |
| **Môi trường** | Python 3.12 + `uv`; `ffmpeg`/`ffprobe` có `libass`, `gblur`, `overlay`; GPU NVIDIA (tùy chọn, thiếu thì chạy CPU); `DEEPSEEK_API_KEY` đặt trong `.env`; một trình duyệt hiện đại |
| **Dữ liệu tích lũy** | `work/subtitles.db` — thuật ngữ, khung làm mờ và kiểu chữ của các nhóm đã tạo từ những lần chạy trước |

Bộ dữ liệu thử nghiệm dự kiến: video ngắn có sidecar, video ngắn không có sidecar, video dọc (mạng xã hội), video 720p và 1080p, và video synthetic sinh bằng `ffmpeg lavfi` để chạy kiểm thử không cần dữ liệu thật.

## 3. Dự kiến đầu ra

**Sản phẩm chính** — video `<tên>_vi.mp4` tải về từ trình duyệt:

- Phụ đề tiếng Việt cháy vào hình, đặt đúng lên vị trí vệt mờ để che gần hết nó.
- Vùng phụ đề cứng tiếng Anh đã bị làm mờ, chỉ bật trong các khoảng có thoại (nới ±0.4 s).
- Âm thanh gốc giữ nguyên (`-c:a copy`), thời lượng và độ phân giải không đổi.
- Chỉ qua một lần nén, không mất chất lượng hai lần.

**Ứng dụng web** gồm hai phần:

- **Backend** — HTTP API bằng FastAPI: tải video lên và tạo công việc, hỏi trạng thái/bước/tiến độ, lấy 8 khung hình mẫu, gửi hộp đã vẽ, tải video kết quả, quản lý nhóm và thuật ngữ.
- **Frontend** — bốn màn: trang tải lên và chọn tùy chọn; bảng tiến độ; canvas vẽ hộp làm mờ trượt qua 8 khung; trang quản lý nhóm và thuật ngữ.

**File trung gian** trong `work/<tên>-<8 ký tự băm>/`: `audio.wav`, `sub_goc.srt` (phụ đề Anh), `sub_vi.srt` (phụ đề Việt, UTF-8 không BOM — dùng riêng được), `vung_blur.json`, `trang_thai.json`, `khung_*.png`.

**Cơ sở dữ liệu** `work/subtitles.db` — 5 bảng `nhom`, `video`, `thuat_ngu`, `nhat_ky`, `cong_viec`: bảng thuật ngữ dùng lại cho video sau, nhật ký thời gian/token của từng bước, và trạng thái các công việc đang chạy.

**Mã nguồn:** `api/` (3 file) + `pipeline/` (8 module) + `web/` (frontend) + `main.py` (công cụ nội bộ) + 7 file kiểm thử chạy bằng `assert`, không cần mạng, GPU, cổng mạng hay màn hình.

**Tài liệu:** README hướng dẫn cài đặt và sử dụng, tài liệu thiết kế, và ma trận kết quả kiểm thử ghi rõ PASS/FAIL/NOT RUN kèm bằng chứng.

## 4. Lộ trình công việc dự kiến

Lộ trình sắp theo **thứ tự phụ thuộc kỹ thuật**: mỗi giai đoạn là một cổng, chỉ mở khi việc trước đủ đầu vào. Trong một giai đoạn thì bốn thành viên chạy song song trên bốn nhánh Git riêng.

| Giai đoạn | Nội dung | Điều kiện đóng cổng |
|---|---|---|
| **G0 — Hợp đồng dữ liệu** | Chốt phạm vi, tạo repo, dựng môi trường, kiểm `ffmpeg`/GPU/web server. TV1 làm trước lớp đọc-ghi SRT vì cả ba người còn lại đều cần | Lớp SRT có trên `main`; chữ ký module và bảng route API được chốt; môi trường kiểm xong |
| **G1 — Bốn module song song** | Mỗi người làm phần xử lý của mình với dữ liệu giả, không chờ nhau | Bốn module chạy độc lập, có kiểm thử offline pass |
| **G2 — Điều phối** | TV1 ghép luồng thật, làm cache/chạy lại, khóa tiến trình, xử lý hàng loạt. Ba người còn lại kiểm phần mình trên dữ liệu thật | Chạy trọn một video qua dòng lệnh; không ghi đè kết quả nhau |
| **G3 — Backend API** | Bọc HTTP quanh luồng đã có: tải lên, công việc chạy nền, tiến độ, khung ảnh, nhận hộp, quản lý nhóm | Chạy trọn một video qua API và cho **cùng kết quả** với dòng lệnh |
| **G4 — Frontend web** | Bốn màn giao diện, mỗi người dựng màn thuộc lĩnh vực của mình | Tải lên → vẽ hộp → tải kết quả chạy được trên trình duyệt |
| **G5 — Nghiệm thu** | README, kiểm thử media, tổng hợp báo cáo và slide, diễn tập bảo vệ | Đủ kết quả kiểm thử; mã nguồn, báo cáo, demo sẵn sàng |

**Ba điểm cần canh:** G0 chặn tất cả nên lớp SRT phải xong sớm nhất; TV1 nằm trên đường găng hai lần (G0 và G2) nên không nhận route API nào; và nếu hết thời gian thì **cắt G4 trước** — backend chạy được vẫn là sản phẩm bảo vệ được, còn frontend không có backend thì không.

## 5. Phân công cho từng thành viên

Nguyên tắc chia: mỗi người đi theo **lĩnh vực của mình xuyên suốt cả ba tầng** — module xử lý, route API, và màn hình frontend tương ứng. Nhờ vậy không ai phải học lại phần người khác, và ranh giới file vẫn không chồng nhau.

| Thành viên | Lĩnh vực | Module xử lý | Tầng API | Màn frontend |
|---|---|---|---|---|
| **TV1**<br>Nhóm trưởng | Nền tảng, CSDL, điều phối, tích hợp | `pipeline/srt.py`, `db.py`, `dieu_phoi.py`, `main.py` | Duyệt kiến trúc, giữ `api/` mỏng | Khung trang, điều hướng, gộp bốn màn |
| **TV2** | Đầu vào: nhận video, phụ đề sẵn, âm thanh, nhận dạng | `pipeline/subs.py`, `audio.py`, `asr.py` | `api/app.py`, `api/viec.py` — tải lên, tạo công việc, chạy nền, tiến độ | Trang tải lên, bảng tiến độ |
| **TV3** | Dịch và thuật ngữ | `pipeline/translate.py` | `api/nhom.py` — nhóm, thuật ngữ, khung mặc định | Trang quản lý nhóm và thuật ngữ |
| **TV4** | Hình học, vùng mờ, kết xuất, tổng hợp kiểm thử | `pipeline/markbox.py`, `render.py` | Route khung ảnh và nhận hộp | Canvas vẽ hộp trên 8 khung, trang kết quả |

**Việc theo giai đoạn:**

| | G0–G1 | G2–G3 | G4–G5 |
|---|---|---|---|
| **TV1** | Chốt phạm vi và hợp đồng; lớp SRT, ghi file an toàn; SQLite 5 bảng, khóa từ, transaction thuật ngữ | Ghép luồng, cache/chạy lại, khóa tiến trình, xử lý hàng loạt; duyệt để `api/` không chứa logic | Khung trang và điều hướng; README, tổng hợp báo cáo và slide |
| **TV2** | Kiểm `ffmpeg`/GPU/web server, chuẩn bị video mẫu; tìm sidecar và track chữ, tách audio, chạy Whisper, lui về CPU khi lỗi CUDA | Kiểm video có/không phụ đề sẵn, không audio, đo thời gian; route tải lên, công việc chạy nền, tiến độ, mã lỗi | Trang tải lên và bảng tiến độ; chương nhận dạng, kiểm cài lại theo README |
| **TV3** | Đọc tài liệu API, chuẩn bị dữ liệu phản hồi giả; chia lô, ánh xạ dòng, kiểm JSON trả về, thử lại có giới hạn | Kiểm phản hồi sai/rỗng và lỗi mạng, thuật ngữ qua nhiều video, đo chi phí thật; route nhóm và thuật ngữ | Trang quản lý nhóm và thuật ngữ; chương dịch, ví dụ trước/sau, bảng chi phí |
| **TV4** | Kiểm NVENC bằng encode thật, chuẩn bị video synthetic; trích 8 khung, kiểm tra hộp, gộp khoảng mờ, lệnh `ffmpeg` một lần encode | Kiểm chữ Việt và vùng mờ ở 720p/1080p, ngang/dọc; route khung ảnh và nhận hộp | Canvas vẽ hộp và trang kết quả; kiểm thử media, ma trận kết quả, video demo |

Mỗi người tự viết kiểm thử cho phần mình (`test_srt.py`, `test_db.py`, `test_asr.py`, `test_translate.py`, `test_render.py`, `test_api.py`); TV4 tổng hợp kết quả chung. Review chéo vòng tròn: TV2 → TV1 → TV4 → TV3 → TV2.

Phân công đầy đủ kèm checklist và bảng theo dõi: [PHAN_CONG.md](PHAN_CONG.md).
