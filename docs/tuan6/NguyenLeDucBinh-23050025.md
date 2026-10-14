# Báo cáo phần việc tuần 6 — Nguyễn Lê Đức Bình

Dành cho giảng viên và nhóm 14. Tài liệu trình bày phần bằng chứng tuần 6 về tích hợp, lưu trữ và tổng hợp kiểm thử, phục vụ Sprint 3: tích hợp và hoàn thiện.

**Nhóm:** 14 — Tuần 6, Sprint 3: tích hợp và hoàn thiện.

**Đề tài:** Hệ thống web dịch và chèn phụ đề tiếng Việt cho video tiếng Anh.

**Thành viên:** Nguyễn Lê Đức Bình — MSSV 23050025 — Nhóm trưởng.

**Phụ trách:** Nền tảng, cơ sở dữ liệu, điều phối và tích hợp.

**Ngày tổng hợp:** 14/10/2026.

## 1. Phạm vi và nguồn

Nội dung lấy từ [báo cáo mục tiêu](BAO_CAO_MUC_TIEU.md), [phiếu lỗi](PHIEU_LOI.md) và tệp bằng chứng trong docs/tuan6. Các tuần trước chỉ là mẫu bố cục.

Đây là cách chia phần báo cáo theo tên thành viên đã có trong bộ hồ sơ. Chưa có nhật ký xác nhận người trực tiếp thực hiện từng công việc; kết quả dưới đây là bằng chứng chung của hệ thống.

## 2. Kết quả được ghi nhận

| Nội dung | Kết quả tuần 6 | Bằng chứng |
|---|---|---|
| Kiểm luồng tích hợp | Runtime HTTP, SQLite và ffmpeg: 1 chạy / 1 qua / 0 lỗi / 0 NOT RUN. ASR/dịch được giả lập trong bộ này. | [Tệp đối chiếu](minh_chung/runtime-results.json) |
| Dữ liệu phiên | PHIEN-01 có CSDL riêng và manifest ghi mã băm của tệp. | [Tệp đối chiếu](phien_01/manifest.json) |
| Bảo vệ dữ liệu | Log offline ghi PASS kiểm trigger lịch sử, sao lưu, khôi phục và xử lý xung đột. | [Tệp đối chiếu](minh_chung/offline.txt) |
| Mẫu lỗi phụ đề | PL-05: chế độ chặt từ chối SRT có câu lỗi; chế độ bỏ câu lỗi giữ một câu hợp lệ. | [Tệp đối chiếu](PHIEU_LOI.md) |
| Mẫu lỗi CSDL | PL-06: bản sao không phải SQLite bị từ chối đúng. | [Tệp đối chiếu](PHIEU_LOI.md) |

Các số liệu lấy từ lượt kiểm ngày 14/10/2026. Không cộng phần trích của bộ kiểm vào tổng chung và không coi lần biên tập này là lượt chạy mới.

## 3. Vướng mắc và phần chưa hoàn thành

Cần demo toàn luồng, xác nhận dữ liệu của từng chức năng và đối chiếu đầy đủ đặc tả. Khi xử lý khóa còn sót, phải xác minh không còn tiến trình chạy.

## 4. Việc tiếp theo

1. Thực hiện phần quan sát liên quan trong [kịch bản demo](KICH_BAN_DEMO.md).
2. Ghi kết quả thật, dữ liệu sử dụng và bằng chứng sau khi thao tác.
3. Thành viên xác nhận công việc thực tế trước khi dùng báo cáo đánh giá đóng góp.

## 5. Liên hệ yêu cầu tuần 6

Phần báo cáo phục vụ yêu cầu có phiên tích hợp, mẫu dữ liệu và phản hồi lỗi. Kết luận chung theo bốn tiêu chí chấm nằm trong [báo cáo tổng](BAO_CAO_TUAN6_TONG.md).
