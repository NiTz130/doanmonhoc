# Báo cáo phần việc tuần 6 — Đinh Hoàng Phú

Dành cho giảng viên và nhóm 14. Tài liệu trình bày phần bằng chứng tuần 6 về đầu vào, nhận dạng và phản hồi dữ liệu sai, phục vụ Sprint 3: tích hợp và hoàn thiện.

**Nhóm:** 14 — Tuần 6, Sprint 3: tích hợp và hoàn thiện.

**Đề tài:** Hệ thống web dịch và chèn phụ đề tiếng Việt cho video tiếng Anh.

**Thành viên:** Đinh Hoàng Phú — MSSV 23050002 — Thành viên.

**Phụ trách:** Đầu vào video, nhận dạng lời thoại, kiểm vùng mờ và tiến độ.

**Ngày tổng hợp:** 14/10/2026.

## 1. Phạm vi và nguồn

Nội dung lấy từ [báo cáo mục tiêu](BAO_CAO_MUC_TIEU.md), [phiếu lỗi](PHIEU_LOI.md) và tệp bằng chứng trong docs/tuan6. Các tuần trước chỉ là mẫu bố cục.

Đây là cách chia phần báo cáo theo tên thành viên đã có trong bộ hồ sơ. Chưa có nhật ký xác nhận người trực tiếp thực hiện từng công việc; kết quả dưới đây là bằng chứng chung của hệ thống.

## 2. Kết quả được ghi nhận

| Nội dung | Kết quả tuần 6 | Bằng chứng |
|---|---|---|
| Nhận dạng thật | Whisper base và large-v3: 2 chạy / 2 qua / 0 lỗi / 0 NOT RUN, nằm trong bộ 6 test thật. | [Tệp đối chiếu](minh_chung/real.txt) |
| Phụ đề đầu vào | PHIEN-01 có clip 30 giây và 5 câu nhận dạng được lưu. | [Tệp đối chiếu](phien_01/sub_goc.srt) |
| Tiến độ và chọn vùng | Runtime đã kiểm chờ chọn vùng rồi tiếp tục; không thay thế demo bằng thao tác web. | [Tệp đối chiếu](minh_chung/runtime-results.json) |
| Dữ liệu sai | PL-01–PL-04 và PL-07–PL-08 ghi vùng mờ và tệp tải lên sai được xử lý đúng. | [Tệp đối chiếu](PHIEU_LOI.md) |

Các số liệu lấy từ lượt kiểm ngày 14/10/2026. Không cộng phần trích của bộ kiểm vào tổng chung và không coi lần biên tập này là lượt chạy mới.

## 3. Vướng mắc và phần chưa hoàn thành

Cần nghe/đối chiếu lời thoại với phụ đề và demo tải lên trên máy trình bày. Mẫu 30 giây chưa chứng minh chất lượng nhận dạng trên mọi video.

## 4. Việc tiếp theo

1. Thực hiện phần quan sát liên quan trong [kịch bản demo](KICH_BAN_DEMO.md).
2. Ghi kết quả thật, dữ liệu sử dụng và bằng chứng sau khi thao tác.
3. Thành viên xác nhận công việc thực tế trước khi dùng báo cáo đánh giá đóng góp.

## 5. Liên hệ yêu cầu tuần 6

Phần báo cáo phục vụ yêu cầu có phiên tích hợp, mẫu dữ liệu và phản hồi lỗi. Kết luận chung theo bốn tiêu chí chấm nằm trong [báo cáo tổng](BAO_CAO_TUAN6_TONG.md).
