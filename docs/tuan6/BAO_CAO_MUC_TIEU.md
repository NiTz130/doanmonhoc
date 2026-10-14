# Tuần 6 — Sprint 3: dữ liệu mẫu và kiểm thử tích hợp

Dành cho giảng viên và nhóm thực hiện. Tài liệu trình bày dữ liệu, kết quả kiểm thử và phiếu lỗi để nộp phần mục tiêu tuần 6.

Ngày kiểm chứng: **14/10/2026**. Dự án: dịch phụ đề video tiếng Anh sang tiếng Việt và kết xuất video có phụ đề.

## 1. Kết quả đối chiếu yêu cầu

Trong dự án này, một phiên giao dịch được hiểu là một lượt xử lý video: nhận video → nhận dạng lời thoại → dịch → xuất video → kiểm tra kết quả.

| Yêu cầu từ đề bài | Kết quả thực hiện | Bằng chứng |
|---|---|---|
| Tích hợp toàn bộ hệ thống | Đã kiểm HTTP, SQLite, ffmpeg và luồng xử lý; kiểm model thật ở bộ riêng | minh_chung/runtime-results.json; minh_chung/real.txt |
| Dữ liệu mẫu đầy đủ một phiên | Đã lưu PHIEN-01 gồm đầu vào, phụ đề gốc, phụ đề Việt, video kết quả và CSDL | phien_01/manifest.json |
| Hoàn thành test một công việc cụ thể | Xử lý 30 giây đầu video_2 bằng Whisper base, NLLB và ffmpeg thật; kiểm thử qua | minh_chung/phien.txt; phien_01/ra_vi.mp4 |
| Dữ liệu lỗi và phản hồi hợp lý | Đã kiểm trực tiếp 8 trường hợp sai và 2 đối chứng | minh_chung/mau_loi.json; PHIEU_LOI.md |
| Phiếu lỗi từ mẫu test sai | Có 8 phiếu ghi mẫu sai, cách kích hoạt, phản hồi và kết luận | PHIEU_LOI.md |
| Làm đẹp, thống nhất giao diện | Không thay đổi hoặc đánh giá lại giao diện trong đợt này | NOT RUN: ngoài phạm vi tổng hợp dữ liệu |
| Chức năng bổ sung, nếu có | Không bổ sung chức năng trong đợt này | Hạng mục tùy chọn của đề bài |

**Kết luận:** Đã có bộ dữ liệu và bằng chứng mới cho một phiên xử lý hoàn chỉnh. Chưa dùng kết quả này để xác nhận toàn bộ giao diện hoặc chất lượng dịch trên mọi video.

## 2. Dữ liệu của phiên PHIEN-01

Mục đích: kiểm công việc nhận dạng, dịch và xuất video tiếng Việt bằng các thành phần thật trên máy local.

| Thuộc tính | Giá trị |
|---|---|
| Nguồn | test/video_2.mp4; trích 30 giây đầu bằng bộ test hiện có |
| Đầu vào đóng gói | phien_01/clip.mp4 |
| Nhận dạng | Whisper base, GPU CUDA |
| Dịch | NLLB local; dùng model đã có trong cache |
| Làm mờ | Tắt; kiểm chọn vùng và tiếp tục xử lý ở bộ runtime riêng |
| Đầu ra | phien_01/ra_vi.mp4; 640 × 360; 30,071708 giây |
| Âm thanh | ffprobe xác nhận có luồng âm thanh |
| Phụ đề | 5 câu gốc và 5 câu dịch; giữ mốc bắt đầu và kết thúc |
| CSDL | phien_01/s.db; chỉ dữ liệu thử của phiên mới |
| Toàn vẹn dữ liệu | Kích thước và SHA-256 của các tệp trong manifest.json |

Các tệp sub_goc.srt, sub_vi.srt và sub_vi.ass được tạo trong chính phiên này. Đây không phải phụ đề mẫu độc lập của tuần 5. Không sử dụng artifact cũ trong work/ của dự án.

Test dùng thư mục riêng và CSDL riêng. Chỉ thay cơ chế dọn thư mục tạm của hàm test để giữ bằng chứng; không thay assertion, model hoặc mã sản phẩm. Bản lệnh đã dùng nằm tại minh_chung/luu_phien.py.txt.

### Trình tự và điều kiện đạt

1. Cắt đoạn đầu vào từ video_2.mp4 và tách WAV 16 kHz mono.
2. Chạy bộ điều phối với Whisper base, NLLB và chế độ không làm mờ.
3. Kiểm trạng thái cuối là xong; CSDL có ít nhất ba bản ghi nhật ký xử lý.
4. Kiểm số câu gốc và dịch bằng nhau; giữ nguyên thời gian; đầu ra có dấu tiếng Việt.
5. Kiểm video có hình, có âm thanh và thời lượng sai lệch dưới 1,5 giây so với 30 giây.
6. So sánh khung hình: sai khác ở vùng dưới phải lớn hơn vùng trên để xác nhận đã vẽ phụ đề.

Kết quả: **1 phiên chạy / 1 qua / 0 lỗi / 0 NOT RUN**. Sai khác trung bình vùng dưới/trên là 17,0/0,4 theo phép kiểm trong tests_real.py.

### Ảnh từ video kết quả

![Khung hình trích tại 2,17 giây, có phụ đề tiếng Việt](phien_01/khung_phu_de.png)

Ảnh được trích từ video đầu ra mới và đã xem trực tiếp. Ảnh xác nhận chữ Việt hiển thị tại một thời điểm; không thay thế việc nghe và xem toàn bộ video.

## 3. Kết quả kiểm thử mới

| Bộ kiểm | Chạy | Qua | Lỗi | NOT RUN | Phạm vi |
|---|---|---|---|---|---|
| test_pipeline.py | 102 | 102 | 0 | 0 | Hồi quy offline; có các thành phần giả lập |
| test/runtime_logic.py | 1 | 1 | 0 | 0 | Một kịch bản tổng hợp HTTP, SQLite, ffmpeg thật; ASR và dịch giả lập |
| test_pipeline.py --real | 6 | 6 | 0 | 0 | GPU, Whisper base/large-v3, NLLB và luồng đầu cuối thật |
| Phiên PHIEN-01 giữ dữ liệu | 1 | 1 | 0 | 0 | Chạy lại test đầu cuối thật để lưu bộ mẫu |
| Kiểm trực tiếp bộ mẫu lỗi | 10 | 10 | 0 | 0 | 8 đầu vào sai và 2 đối chứng |
| Độ phủ offline, ngưỡng 90% | 1 | 1 | 0 | 0 | 97,0%; 2.109 dòng, 64 dòng chưa phủ |
| Xem một khung hình đầu ra | 1 | 1 | 0 | 0 | Có chữ Việt hiển thị |
| Nghe và xem toàn bộ video | 0 | 0 | 0 | 1 | Chưa đánh giá thủ công lời dịch, đồng bộ và âm thanh |
| Demo thao tác trên trình duyệt | 0 | 0 | 0 | 1 | Chưa thực hiện; kiểm HTTP không thay thế demo web |
| Kiểm giao diện desktop/mobile | 0 | 0 | 0 | 1 | Không thuộc phạm vi đợt tổng hợp này |

Không cộng các dòng thành số test độc lập: PHIEN-01 chạy lại một test trong bộ thật; lệnh đo độ phủ cũng chạy lại offline. Bộ runtime có nhiều assertion nhưng được tính là một kịch bản.

Máy kiểm thử có NVIDIA GeForce RTX 4050 Laptop GPU, 6.141 MiB VRAM. Các lệnh chạy với UTF-8. Bộ thật bật HF_HUB_OFFLINE=1 và TRANSFORMERS_OFFLINE=1, không tải model hoặc gọi dịch vụ trả phí.

Các tệp bằng chứng trong minh_chung/ được tạo từ lần chạy này. offline.txt chỉ giữ tên các test qua; coverage.txt giữ tổng độ phủ. Log đầy đủ còn tại .cache/tuan6-20261014/ trên máy thực hiện.

## 4. Mẫu lỗi và điều kiện kích hoạt

Trong tài liệu này, điều kiện kích hoạt lỗi là dữ liệu hoặc thao tác gây nhánh xử lý lỗi. Nó khác trigger SQLite, tức cơ chế tự động ghi lịch sử khi dữ liệu thay đổi.

| Nhóm | Điều kiện kích hoạt | Phản hồi đã kiểm |
|---|---|---|
| Vùng mờ | Vượt khung, rộng bằng 0, tọa độ boolean, thiếu chiều cao | Validator từ chối bằng ValueError |
| Phụ đề | Tệp có câu ngược thời gian và câu rỗng | Chế độ chặt từ chối; chế độ bỏ câu lỗi giữ 1 câu hợp lệ |
| CSDL | Đưa tệp không phải SQLite vào bộ kiểm bản sao lưu | Từ chối bằng ValueError |
| Tải lên | Tệp rỗng hoặc đuôi .txt | HTTP 400; không để lại tệp tải lên |
| Gửi trùng | Hai yêu cầu cùng xử lý nguồn/nhóm hoặc cùng tiếp tục | Runtime kiểm HTTP 409; chỉ một lượt được tiếp nhận |
| Phụ đề đã thay đổi | Tiếp tục từ ảnh chụp phụ đề cũ | Runtime kiểm HTTP 409 và giữ ảnh chụp cũ |
| Sự cố tiến trình | Máy chủ thử bị dừng khi đang giữ khóa | Sau khởi động lại, báo lỗi và HTTP 409; hướng dẫn xử lý khóa thủ công |
| Trigger SQLite | Thêm/sửa/xóa nhóm và thuật ngữ | test_trigger_lich_su_moi_duong_ghi qua trong bộ offline |

Các tình huống dừng tiến trình và CSDL hỏng chỉ chạy trong môi trường thử riêng. Không thao tác trên công việc hoặc CSDL người dùng đang sử dụng.

## 5. Đối chiếu thang chấm từ ảnh yêu cầu

| Tiêu chí | Điểm tối đa | Bằng chứng và giới hạn |
|---|---|---|
| Hệ thống tích hợp hoàn chỉnh, demo tốt | 3 | Runtime qua; có video đầu ra thật. Demo thao tác web còn cần trình bày trực tiếp |
| Hoàn thiện chức năng so với đặc tả ban đầu | 3 | 102 kiểm offline và 6 kiểm thật qua. Chưa đánh giá lại toàn bộ đặc tả để tự chấm điểm |
| Giao diện nhất quán, có đủ dữ liệu mẫu | 2 | Đã có bộ mẫu một phiên và mẫu lỗi. Chưa kiểm lại giao diện |
| Chất lượng kiểm thử lỗi và phản hồi | 2 | Có phiếu lỗi, dữ liệu tái hiện và kết quả phản hồi mới |

Không tự chấm điểm thay giảng viên. Hồ sơ này bổ sung phần dữ liệu và kiểm chứng mà nhóm còn thiếu.

## 6. Cách sử dụng khi nộp và demo

1. Nộp BAO_CAO_MUC_TIEU.docx, PHIEU_LOI.docx và bộ dữ liệu đi kèm trong ZIP.
2. Mở phien_01/clip.mp4 để giới thiệu đầu vào; mở ra_vi.mp4 để xem đầu ra của cùng phiên.
3. Mở sub_goc.srt và sub_vi.srt để đối chiếu 5 câu và mốc thời gian.
4. Mở PHIEU_LOI.docx, chọn một mẫu sai và đối chiếu minh_chung/mau_loi.json.
5. Khi demo ứng dụng, khởi động bằng start_system.bat rồi tải clip.mp4 lên; chọn Whisper base và tắt làm mờ để bám cấu hình mẫu.
6. Nghe và xem hết video; ghi kết quả đánh giá chất lượng dịch và thao tác web sau khi thực hiện.

Bước 5–6 là việc demo còn cần thực hiện; không được ghi là đã chạy chỉ vì hồ sơ có video đầu ra. Thời gian chạy lại phụ thuộc máy và cache model. Không khôi phục s.db vào CSDL đang sử dụng.
