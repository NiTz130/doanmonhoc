# Báo cáo phần việc tuần 6 — Phạm Tuấn Kiệt

Dành cho giảng viên và nhóm 14. Tài liệu trình bày phần bằng chứng tuần 6 về dịch, phụ đề và video đầu ra, phục vụ Sprint 3: tích hợp và hoàn thiện.

**Nhóm:** 14 — Tuần 6, Sprint 3: tích hợp và hoàn thiện.

**Đề tài:** Hệ thống web dịch và chèn phụ đề tiếng Việt cho video tiếng Anh.

**Thành viên:** Phạm Tuấn Kiệt — MSSV 23050046 — Thành viên.

**Phụ trách:** Dịch, thuật ngữ, làm mờ và xuất video.

**Ngày tổng hợp:** 14/10/2026.

## 1. Phạm vi và nguồn

Nội dung lấy từ [báo cáo mục tiêu](BAO_CAO_MUC_TIEU.md), [phiếu lỗi](PHIEU_LOI.md) và tệp bằng chứng trong docs/tuan6. Các tuần trước chỉ là mẫu bố cục.

Đây là cách chia phần báo cáo theo tên thành viên đã có trong bộ hồ sơ. Chưa có nhật ký xác nhận người trực tiếp thực hiện từng công việc; kết quả dưới đây là bằng chứng chung của hệ thống.

## 2. Kết quả được ghi nhận

| Nội dung | Kết quả tuần 6 | Bằng chứng |
|---|---|---|
| Dịch thật | Kiểm NLLB, giữ số câu khi gọi model và luồng đầu cuối: 3 chạy / 3 qua / 0 lỗi / 0 NOT RUN; thuộc bộ 6 test thật. | [Tệp đối chiếu](minh_chung/real.txt) |
| Thuật ngữ | Bộ test NLLB thật có bước ép thuật ngữ; một trong 3 test dịch ở dòng trên, không cộng thêm. | [Tệp đối chiếu](minh_chung/real.txt) |
| Phụ đề Việt | Có 5 câu dịch, giữ mốc thời gian của phụ đề gốc. | [Tệp đối chiếu](phien_01/sub_vi.srt) |
| Kết xuất | Video 640 × 360, khoảng 30,072 giây, có hình và âm thanh. | [Tệp đối chiếu](phien_01/manifest.json) |
| Hiển thị phụ đề | Khung đầu ra đã được xem và có chữ Việt; PHIEN-01 tắt làm mờ. | [Tệp đối chiếu](phien_01/khung_phu_de.png) |

Các số liệu lấy từ lượt kiểm ngày 14/10/2026. Không cộng phần trích của bộ kiểm vào tổng chung và không coi lần biên tập này là lượt chạy mới.

## 3. Vướng mắc và phần chưa hoàn thành

Cần nghe/xem toàn bộ để đánh giá nghĩa, xưng hô và đồng bộ. Kiểm vùng mờ và giao diện cần thực hiện riêng; không suy ra từ phiên tắt làm mờ.

## 4. Việc tiếp theo

1. Thực hiện phần quan sát liên quan trong [kịch bản demo](KICH_BAN_DEMO.md).
2. Ghi kết quả thật, dữ liệu sử dụng và bằng chứng sau khi thao tác.
3. Thành viên xác nhận công việc thực tế trước khi dùng báo cáo đánh giá đóng góp.

## 5. Liên hệ yêu cầu tuần 6

Phần báo cáo phục vụ yêu cầu có phiên tích hợp, mẫu dữ liệu và phản hồi lỗi. Kết luận chung theo bốn tiêu chí chấm nằm trong [báo cáo tổng](BAO_CAO_TUAN6_TONG.md).
