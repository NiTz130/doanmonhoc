# BÁO CÁO TUẦN 4 — SPRINT 1

**Đề tài:** Xây dựng hệ thống web tự động dịch và chèn phụ đề tiếng Việt cho video tiếng Anh, có xử lý che phụ đề cứng.

**Nhóm:** 14 · **Ngày cập nhật:** 30/09/2026.

| Thành viên | MSSV | Vai trò theo phân công |
|---|---|---|
| Nguyễn Lê Đức Bình | 23050025 | Nhóm trưởng; nền tảng, CSDL, điều phối, tích hợp |
| Đinh Hoàng Phú | 23050002 | Đầu vào video, phụ đề, ASR, vùng mờ, API công việc |
| Phạm Tuấn Kiệt | 23050046 | Dịch, thuật ngữ, nhóm video, kết xuất và giao diện liên quan |

## 1. Mục tiêu và phạm vi tuần 4

Mục tiêu của Sprint 1 là trình diễn chức năng chính chạy xuyên suốt từ giao diện đến xử lý và lưu dữ liệu, đồng thời báo cáo việc đã làm, vướng mắc và kế hoạch tiếp theo. Báo cáo sử dụng cách trình bày Sprint 1 như bộ tài liệu tuần 4 đã có. Quy trình đã mô tả ở tuần 3 là lặp tăng dần theo các cổng G0–G5, chưa phải Scrum đầy đủ.

Hai nghiệp vụ được chọn:

1. Dịch phụ đề video Anh → Việt: tải video, lấy phụ đề hoặc nhận dạng lời thoại, chọn vùng làm mờ, dịch, kết xuất và tải video kết quả.
2. Quản lý nhóm video và thuật ngữ: tạo/đọc nhóm; đọc, thêm và cập nhật thuật ngữ để sử dụng nhất quán giữa các video cùng nhóm.

Chức năng xóa nhóm và xóa thuật ngữ chưa có trong tài liệu API hiện tại; vì vậy chưa tuyên bố hoàn thành CRUD đầy đủ. Đăng nhập/phân quyền nằm ngoài phạm vi ứng dụng cục bộ một người dùng theo đặc tả dự án. Đây là giới hạn phạm vi cần trình bày với giảng viên, không phải bằng chứng đã được miễn tiêu chí của môn học.

## 2. Đối chiếu yêu cầu và tiêu chí chấm

| Tiêu chí trong đề | Điểm tối đa | Nội dung và minh chứng | Giới hạn cần nêu |
|---|---|---|---|
| Chức năng chính chạy thật, không phải giao diện tĩnh | 4 | Luồng nghiệp vụ ở mục 3; biên bản V-8, ảnh V-10; demo 5 phút theo tài liệu kèm | V-8 là kết quả cũ; V-10 thay tầng dịch bằng dữ liệu giả; cần demo lại bản hiện tại |
| Bám thiết kế tuần 3, ghi nhận thay đổi nếu lệch | 2 | Ánh xạ kiến trúc ở mục 4; đối chiếu thay đổi ở mục 5 | Bản tuần 3 trong thư mục đã được cập nhật; cần phân biệt mốc thiết kế ban đầu và nội dung điều chỉnh |
| Báo cáo tuần thể hiện nhiều thành viên đóng góp | 2 | Phân công và bảng xác nhận đóng góp ở mục 7 | Cần ghi đủ việc đã làm, kết quả và sản phẩm của từng thành viên |
| Nhận diện đúng rủi ro/vướng mắc và hướng xử lý | 2 | Mục 8: phạm vi, dữ liệu, chi phí, demo và đóng góp nhóm | Các hướng xử lý là kế hoạch, không phải việc đã hoàn tất |

Bảng này dùng để truy vết yêu cầu, không tự chấm điểm hoặc thay thế đánh giá của giảng viên.

## 3. Chức năng chính và dữ liệu xử lý

### 3.1 Nghiệp vụ 1 — dịch và chèn phụ đề

| Bước | Thao tác người dùng / hệ thống | Dữ liệu và kết quả mong đợi |
|---|---|---|
| 1 | Chọn video tiếng Anh, nhóm video và tùy chọn; gửi tải lên | API nhận tệp, kiểm đầu vào và trả mã công việc |
| 2 | Theo dõi tiến độ | Lấy phụ đề có sẵn hoặc tách âm thanh, chạy Whisper; trạng thái công việc lưu trong SQLite |
| 3 | Khi cần, chọn khung theo câu thoại và vẽ vùng mờ | Vùng được kiểm hợp lệ; trạng thái chờ người dùng không bị coi là lỗi |
| 4 | Hệ thống dịch phụ đề | Gửi nội dung phụ đề cùng ngữ cảnh và thuật ngữ nhóm đến dịch vụ dịch; giữ cấu trúc cue và thời gian |
| 5 | Hệ thống kết xuất | ffmpeg làm mờ và chèn phụ đề Việt; xuất video để phát/tải về |
| 6 | Người dùng xem kết quả | Phân biệt hoàn thành, suy giảm và lỗi; xem tiếng Việt đủ dấu, thời điểm xuất hiện và vùng che |

Luồng HTTP theo thiết kế tuần 3: `POST /api/video` → `GET /api/cong-viec/{cid}` → nếu cần, `GET .../khung`, `POST .../hop` → `GET .../ket-qua`.

Video và âm thanh xử lý tại máy; nội dung phụ đề/ngữ cảnh/thuật ngữ được gửi đến API dịch. Không mô tả toàn bộ dữ liệu là luôn ở máy người dùng.

### 3.2 Nghiệp vụ 2 — nhóm video và thuật ngữ

| Thao tác | Hành vi theo hồ sơ dự án | Minh chứng cần trình diễn |
|---|---|---|
| Tạo và xem nhóm | Lưu nhóm vào SQLite, đọc lại danh sách | Tạo nhóm demo có tên riêng, tải lại trang và mở nhóm |
| Thêm thuật ngữ | Ghi cặp từ gốc – bản dịch vào nhóm | Thêm `Ironhold` → `Thành Sắt`, mở lại nhóm để kiểm dữ liệu |
| Sửa thuật ngữ | Cập nhật bản dịch của từ đã tồn tại | Đổi bản dịch, tải lại và đọc giá trị mới |
| Dùng thuật ngữ khi dịch | Truyền bảng thuật ngữ vào yêu cầu dịch video trong nhóm | Biên bản V-8 phần 8 ghi phép thử hai tập; không suy ra mọi bản dịch luôn đúng |
| Xóa | Chưa có chức năng trong API được mô tả | Ghi là phần chưa hoàn thành, không trình diễn giả |

## 4. Kiến trúc và sự bám sát thiết kế

Hệ thống dùng kiến trúc phân lớp; bảng dưới đối chiếu với Model–View–Controller theo yêu cầu môn học. Agile là quy trình phát triển, còn phân lớp/MVC là cách tổ chức phần mềm.

| Lớp | Vị trí trong mã nguồn | Trách nhiệm | Đối chiếu MVC |
|---|---|---|---|
| Trình bày | `web/index.html`, `web/app.js`, `web/style.css` | Nhận thao tác, gọi HTTP, hiển thị tiến độ và kết quả | View |
| HTTP API | `api/app.py`, `api/viec.py`, `api/nhom.py` | Nhận/kiểm request, gọi nghiệp vụ, trả JSON hoặc tệp | Controller |
| Điều phối | `pipeline/dieu_phoi.py` | Sắp thứ tự xử lý, cache, điểm dừng, trạng thái | Lớp ứng dụng, nối Controller với Model |
| Xử lý và dữ liệu | `pipeline/asr.py`, `translate.py`, `render.py`, `markbox.py`, `srt.py`, `db.py` | Nhận dạng, dịch, hình học, kết xuất và lưu dữ liệu | Model/dịch vụ |

Dòng dữ liệu: trình duyệt → API → điều phối → các module xử lý và kho dữ liệu → API → trình duyệt. `main.py` là đường vào CLI dùng chung điều phối. Khi giảng viên review trực tiếp, mở các vị trí trên và lần theo một yêu cầu tải video; không chỉ trình chiếu sơ đồ.

SQLite lưu nhóm, video, thuật ngữ, nhật ký và công việc. Tệp trung gian cùng manifest trong `work/` phục vụ tái sử dụng kết quả; bảng tiến độ không thay thế manifest. Tham chiếu: [Kiến trúc/API tuần 3](../tuan3/PHAN1_KIEN_TRUC_API.md), [CSDL tuần 3](../tuan3/PHAN2_CSDL.md).

## 5. Ghi nhận thay đổi so với tuần 3

Mốc đối chiếu là báo cáo thiết kế tuần 3 ngày 23/09/2026 và các ghi chú cập nhật 30/09/2026 trong tài liệu hiện có. Thay đổi được ghi nhận trong tài liệu không đồng nghĩa đã kiểm chứng trên bản hiện tại.

| Hạng mục | Mốc tuần 3 / trước cập nhật | Hồ sơ hiện tại | Lý do và ảnh hưởng |
|---|---|---|---|
| Nhân sự | Tài liệu tuần 3 ghi 4 thành viên | Phân công hiện tại còn 3 thành viên | Phân bổ lại trách nhiệm; cần xác nhận đóng góp thực tế của từng người |
| Cách áp dụng vùng mờ | Hồ sơ cũ có `che_do_vung`, cộng thêm/thay thế | Báo cáo tổng hợp ghi đã bỏ lựa chọn chế độ ngày 30/09, dùng nghĩa thay thế | Giảm lựa chọn và tránh hiểu sai vùng theo câu; cần kiểm tương thích payload/artifact cũ trên bản cuối |
| Cột dữ liệu chưa dùng | Có các cột cấu hình nhóm và thuộc tính thuật ngữ chưa tác động hành vi | Tuần 3 phần CSDL mục 1.6 ghi gỡ khỏi schema mới ngày 30/09; CSDL cũ giữ cột nhưng không đọc/ghi | Tinh giản lược đồ; cần kiểm CSDL mới và CSDL đã có dữ liệu |
| Kiến trúc, giao diện canvas, lô dịch và lấy khung | Bản tuần 3 đã có phân lớp, canvas web, lô 25 câu, khung theo câu và `suy_giam` | Tiếp tục sử dụng | Đây là phần bám thiết kế, không tính thành cải tiến mới của tuần 4 |

Các thay đổi 400 → 25 câu/lô, 8 khung → khung theo câu, desktop → web là lịch sử phát triển trước đó; không gán toàn bộ thành công việc tuần 4.

## 6. Minh chứng và trạng thái kiểm chứng

| Mã | Nguồn | Kết quả được nguồn ghi nhận | Phạm vi sử dụng |
|---|---|---|---|
| E-01 | [V8.md](../ketqua/V8.md), biên bản bắt đầu ngày 10/09/2026 | Video 12 giây: đủ 4 cue, giữ timestamp; lượt chạy lại ghi 0 token. Có ASR/dịch/kết xuất trên video dài hơn và thử thuật ngữ giữa hai tập | Bằng chứng lịch sử với dịch vụ thật; không phải chạy mới ngày 30/09 |
| E-02 | [Ảnh V-10](../ketqua/README.md) | Trình duyệt, ffmpeg/ffprobe thật; tầng dịch thay bằng bảng tra | Chứng minh luồng giao diện/kết xuất tại lượt ghi nhận, không chứng minh dịch vụ dịch thật qua web |
| E-03 | [B-frontend](../ketqua/B-frontend.md) | Kiểm giao diện Chromium với API giả lập | Bằng chứng giao diện trong biên bản; không thay thế E-01 hoặc demo hiện tại |
| E-04 | Bản nháp tuần 4 trước lần biên tập này | Ghi 41 PASS / 0 FAIL ngày 30/09/2026 | Chưa có log chạy kèm được xác minh trong lần biên tập; không dùng làm kết quả kiểm thử mới |

Lần biên tập này đối chiếu tài liệu và liên kết; không chạy lại offline, browser, media smoke hoặc API trả phí. Trạng thái kiểm chứng bản hiện tại: **NOT RUN**. Kết quả lịch sử cần giữ nguyên phạm vi, ngày và điều kiện chạy.

Lưu ý nguồn cũ: phần đầu `docs/ketqua/README.md` còn ghi V-8 chưa chạy, trong khi `V8.md` đã có kết quả; dùng biên bản V-8 chi tiết cho kết quả lịch sử. V-8 phần 7 đã ghi thử Demucs, vì vậy không tiếp tục dùng nhận định “Demucs chưa chạy lần nào”.

![Khung kết quả đã ghi nhận](../ketqua/ket_qua_khung.png)

*Hình 1. Khung kết quả trong hồ sơ V-10: minh họa chữ Việt và vùng mờ; tầng dịch của lượt này là bảng tra, không phải ảnh nghiệm thu bản hiện tại.*

## 7. Đóng góp của thành viên

Nhóm sử dụng báo cáo tuần để trình bày đóng góp của từng thành viên theo phương án được đề bài cho phép. Mỗi thành viên ghi công việc thực tế, kết quả đạt được, sản phẩm bàn giao và vướng mắc. Phân công dự kiến được tách khỏi kết quả đã hoàn thành; nội dung chưa được cung cấp vẫn chờ thành viên xác nhận.

| Thành viên | Phạm vi theo phân công | Việc thực tế tuần 4 | Bằng chứng / trạng thái xác nhận |
|---|---|---|---|
| Nguyễn Lê Đức Bình | Nền tảng, CSDL, điều phối, tích hợp, tổng hợp | Chờ thành viên xác nhận việc cụ thể và thời điểm | Bổ sung kết quả, tệp sản phẩm hoặc biên bản làm việc |
| Đinh Hoàng Phú | Đầu vào, ASR, vùng mờ, API công việc | Chờ thành viên xác nhận | Bổ sung kết quả, tệp sản phẩm, ảnh demo hoặc biên bản làm việc |
| Phạm Tuấn Kiệt | Dịch, thuật ngữ, nhóm, kết xuất và giao diện | Chờ thành viên xác nhận | Bổ sung kết quả, tệp sản phẩm, ảnh demo hoặc biên bản làm việc |

Mẫu bổ sung cho mỗi người: **ngày — việc đã làm — kết quả — đường dẫn bằng chứng — vướng mắc**. Báo cáo tuần là minh chứng đóng góp được nhóm lựa chọn. Chỉ ghi công việc thực tế; có thể đính kèm tệp sản phẩm, ảnh kết quả hoặc biên bản làm việc.

## 8. Rủi ro, vướng mắc và hướng xử lý

| Mã | Vướng mắc / ảnh hưởng | Hướng xử lý | Người phụ trách theo phân công |
|---|---|---|---|
| R-1 | Thiếu bằng chứng nhiều thành viên đóng góp; ảnh hưởng tiêu chí 2 điểm | Mỗi người bổ sung việc đã làm, kết quả, sản phẩm bàn giao và vướng mắc vào báo cáo tuần; nhóm trưởng tổng hợp | Cả nhóm |
| R-2 | Chưa có xóa nhóm/thuật ngữ, chưa có xác thực | Trình bày phạm vi với giảng viên; chỉ cam kết bổ sung sau khi chốt yêu cầu và cách bảo toàn dữ liệu | TV1 tổng hợp, TV3 phụ trách nghiệp vụ nhóm |
| R-3 | Chi phí và thời gian dịch biến động; có thể vượt 5 phút | Dùng video ngắn, tập trước, có kết quả dự phòng; theo dõi token, chỉ gọi dịch vụ thật trong ngân sách đã được cho phép | TV3 |
| R-4 | API/mạng/GPU có thể lỗi lúc demo | Chuẩn bị đầu ra đã có; nếu dùng lại cache phải giữ đúng dữ liệu/cấu hình và kiểm trước; không cam kết mọi lần tải lại đều 0 token | TV2, TV3 |
| R-5 | Khởi động lại làm dừng tác vụ nền | Giải thích trạng thái lỗi sau restart; chạy lại có kiểm tra artifact hợp lệ, không hứa tiếp tục chính xác công việc cũ | TV1 |
| R-6 | ASR trên nhạc có thể bỏ sót lời; đầu ra có thể suy giảm | Chọn thoại rõ cho demo; khi thử nhạc, đối chiếu VAD và kiểm thủ công phụ đề | TV2 |
| R-7 | Tài liệu/test lịch sử lệch bản đang sửa | Kiểm bản cuối, ghi lệnh và log mới, chụp giao diện mới; không dùng số test hoặc ảnh cũ để chứng nhận mã mới | TV1 tổng hợp |

## 9. Kế hoạch tuần tiếp theo

| Thành viên | Nhiệm vụ dự kiến | Sản phẩm cần bàn giao |
|---|---|---|
| Nguyễn Lê Đức Bình | Tổng hợp xác nhận đóng góp, thống nhất phạm vi với giảng viên, phối hợp tích hợp và cập nhật hồ sơ | Báo cáo đầy đủ minh chứng; danh sách việc cần hoàn thiện theo phản hồi |
| Đinh Hoàng Phú | Chuẩn bị video thoại rõ, trình bày đầu vào/ASR/tiến độ/vùng mờ; ghi nhận vấn đề của luồng đầu vào | Dữ liệu demo và phần thuyết trình nghiệp vụ đầu vào |
| Phạm Tuấn Kiệt | Chuẩn bị nhóm/thuật ngữ mẫu, trình bày dịch và kết quả; làm rõ yêu cầu xóa trước khi bổ sung | Minh họa lưu/sửa thuật ngữ và video có phụ đề; yêu cầu nghiệp vụ còn thiếu |
| Cả nhóm | Tập demo 5 phút, kiểm chứng bản cuối và ghi nhận phản hồi | Log kiểm thử mới, ảnh/kết quả demo, vướng mắc và hướng xử lý |

Ưu tiên là hoàn thiện bằng chứng của hai nghiệp vụ đã chọn. Chưa mở rộng sang TTS, OCR, triển khai nhiều người dùng hoặc hàng đợi ngoài. Việc xóa dữ liệu cần thống nhất hành vi và cách bảo toàn dữ liệu trước khi triển khai. Các nhiệm vụ trong bảng là dự kiến, chưa ghi nhận hoàn thành.

## 10. Hồ sơ nộp và điều kiện còn lại

Bộ hồ sơ gồm báo cáo này, [Sprint review ngắn](SPRINT_REVIEW.md), [Kịch bản demo 5 phút](KICH_BAN_DEMO.md) và bản Word tổng hợp `BAO_CAO_TUAN4.docx`.

Trước khi nộp, nhóm cần xác nhận đóng góp ở mục 7, tập demo bản hiện tại, bổ sung log/ảnh của lượt kiểm mới và ghi ý kiến giảng viên về phạm vi xác thực/CRUD nếu có. Chưa xác nhận demo tại lớp hoặc đủ toàn bộ tiêu chí nghiệm thu.
