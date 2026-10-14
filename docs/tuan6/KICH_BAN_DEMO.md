# Kịch bản demo tuần 6 — phiên tích hợp và phản hồi lỗi

Dành cho nhóm 14 khi trình bày trước giảng viên. Kịch bản bám dữ liệu trong docs/tuan6 và yêu cầu demo tốt, đủ mẫu dùng thử, có phản hồi lỗi.

**Trạng thái:** chuẩn bị nội dung trình bày; chưa có biên bản demo trực tiếp. Cách chia người trình bày là dự kiến, không phải xác nhận đã thực hiện.

## 1. Dữ liệu và tài liệu cần mở

- [clip.mp4](phien_01/clip.mp4): đầu vào 30 giây.
- [ra_vi.mp4](phien_01/ra_vi.mp4): đầu ra của lượt PHIEN-01 đã ghi nhận ngày 14/10.
- [sub_goc.srt](phien_01/sub_goc.srt) và [sub_vi.srt](phien_01/sub_vi.srt): năm câu cùng mốc thời gian.
- [manifest](phien_01/manifest.json): cấu hình và thông số phiên.
- [tệp sai định dạng](du_lieu_loi/khong_phai_video.txt) và [phiếu lỗi](PHIEU_LOI.md).
- [báo cáo tổng](BAO_CAO_TUAN6_TONG.md) và [bộ kiểm thử](TEST_CASE.md).

Dùng máy đã cài môi trường, ffmpeg và cache model theo hướng dẫn vận hành. Từ thư mục gốc dự án, chạy start_system.bat và mở http://127.0.0.1:8000. Cấu hình phiên mẫu là Whisper base, NLLB local, tắt làm mờ.

## 2. Trình tự demo

| Bước | Người trình bày dự kiến | Thao tác | Điều cần chứng minh |
|---|---|---|---|
| 1 | Bình | Mở báo cáo và manifest | Xác định đúng đầu vào, cấu hình, công việc và đầu ra |
| 2 | Phú | Tải clip, chọn cấu hình tương ứng và bắt đầu | Có mã công việc mới và tiến độ |
| 3 | Phú | Theo dõi tới trạng thái kết thúc | Phân biệt hoàn thành, suy giảm và lỗi |
| 4 | Kiệt | Mở video kết quả mới, nghe/xem toàn bộ | Có hình, âm thanh, chữ Việt; kiểm lời dịch và đồng bộ |
| 5 | Kiệt | Đối chiếu hai tệp phụ đề của lượt vừa chạy | Kiểm số câu và thời gian thực tế |
| 6 | Phú | Chọn tệp .txt | Ghi phản hồi giao diện; nếu bị chặn trước khi gửi thì không ghi đã nhận HTTP 400 |
| 7 | Bình | Mở PL-08 và bằng chứng kiểm lỗi | So sánh mong đợi, thực tế và kết luận |

Nếu dùng ra_vi.mp4 đã chuẩn bị, nói rõ đó là kết quả PHIEN-01 ngày 14/10. Việc mở tệp cũ không được ghi thành lượt xử lý mới. Thời gian xử lý phụ thuộc máy; cần tập trước trên máy trình bày.

## 3. Kiểm bổ sung theo tiêu chí giao diện và dữ liệu

- Quan sát màn tải lên, tiến độ, vùng mờ và kết quả tại các khổ màn hình cần dùng; ghi chữ bị cắt, nút khó thao tác hoặc phản hồi không rõ nếu có.
- Để kiểm làm mờ, tạo lượt riêng, bật làm mờ và chọn vùng khi hệ thống yêu cầu. PHIEN-01 tắt làm mờ nên không chứng minh nhánh này.
- Nếu vùng đã lưu khiến bước chọn vùng được bỏ qua, giải thích trạng thái đó; không xóa phụ đề hoặc dữ liệu đang dùng để ép màn hình xuất hiện.
- Các chức năng chưa có mẫu thao tác riêng cần chuẩn bị thêm và ghi kết quả. Không coi một clip đã chạy là đủ bằng chứng cho mọi chức năng.

Không thử khôi phục CSDL hỏng hoặc dừng tiến trình đang xử lý dữ liệu thật trong buổi demo. Những nhánh này đã có bằng chứng kiểm thử riêng.

## 4. Biên bản cần hoàn thành sau demo

| Nội dung | Trạng thái hiện có |
|---|---|
| Ngày, máy và người thao tác | Chưa ghi nhận |
| Tệp đầu vào, cấu hình và mã công việc mới | Chưa ghi nhận |
| Tải lên, theo dõi và tải kết quả trên web | NOT RUN |
| Nghe/xem toàn bộ và nhận xét bản dịch | NOT RUN |
| Phản hồi giao diện với tệp sai | NOT RUN |
| Vùng mờ trên lượt riêng | NOT RUN |
| Giao diện desktop/mobile | NOT RUN |

Sau khi thực hiện, ghi kết quả quan sát và tệp minh chứng; giữ NOT RUN cho phần chưa làm. Ảnh chụp hỗ trợ biên bản, không thay thế thao tác trực tiếp.

## 5. Nguồn

[Báo cáo mục tiêu tuần 6](BAO_CAO_MUC_TIEU.md), [phiếu lỗi](PHIEU_LOI.md), [manifest phiên](phien_01/manifest.json) và ảnh yêu cầu tuần 6 do người dùng cung cấp.
