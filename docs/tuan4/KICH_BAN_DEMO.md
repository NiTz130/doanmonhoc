# KỊCH BẢN DEMO TUẦN 4 — 5 PHÚT

**Nhóm 14** · Mục tiêu: chứng minh chức năng có xử lý và lưu dữ liệu, giải thích kiến trúc, nêu vướng mắc và kế hoạch.

## 1. Chuẩn bị

- Cài môi trường theo README; mở backend bằng `start_system.bat` hoặc `.venv/Scripts/python.exe -m uvicorn api.app:app`, truy cập `http://127.0.0.1:8000`.
- Chuẩn bị video tiếng Anh 12–30 giây, lời thoại rõ; nếu dùng phụ đề nhúng thì nói rõ không minh họa ASR trong lượt đó. Chạy thử trước trên đúng máy demo để biết thời gian.
- Chuẩn bị một video kết quả và ảnh dự phòng từ lượt đã biết điều kiện chạy. Không sửa/xóa artifact hay phụ đề đã chỉnh tay để ép hiện bước chọn vùng.
- Chọn dữ liệu đã tập trước để minh họa chọn vùng; nếu cache hoặc vùng nhóm làm bỏ qua bước này, giải thích hành vi thay vì khẳng định luôn dừng chờ.
- Dịch mới cần mạng và API key đã cấu hình. Chỉ thực hiện khi nhóm có cho phép dùng tài khoản/ngân sách; không mở `.env` trên màn chiếu.
- Chuẩn bị nhóm demo có tên riêng và cặp thuật ngữ mẫu. Mở sẵn mã nguồn các tầng và kết quả kiểm thử đã ghi rõ ngày/điều kiện.

## 2. Dòng thời gian

| Thời gian | Thao tác | Nội dung trình bày | Người dự kiến |
|---|---|---|---|
| 0:00–0:30 | Giới thiệu đề tài, mở sơ đồ hoặc cây thư mục | Hai nghiệp vụ chính; phân lớp `web` → `api` → điều phối → xử lý/dữ liệu | Bình |
| 0:30–1:10 | Chọn video, nhóm và tải lên | API nhận dữ liệu, tạo công việc; đây là xử lý thật trên backend | Phú |
| 1:10–2:00 | Xem tiến độ, khi xuất hiện bước chờ thì chọn câu và vẽ vùng mờ | Vùng phải hợp lệ; chờ chọn vùng không phải lỗi; gửi vùng để tiếp tục | Phú |
| 2:00–2:50 | Trong lúc video xử lý, tạo/mở nhóm demo; thêm rồi sửa thuật ngữ | Đọc lại sau tải trang để chứng minh dữ liệu lưu, không chỉ đổi giao diện | Kiệt |
| 2:50–3:40 | Quay lại công việc, phát/tải kết quả | Kiểm chữ Việt đủ dấu, thời điểm và vùng che; nêu rõ nếu dùng kết quả đã chuẩn bị | Kiệt |
| 3:40–4:20 | Mở `web/app.js`, `api/app.py`, `pipeline/dieu_phoi.py` và `pipeline/db.py` | Lần theo request đến xử lý/lưu dữ liệu; API không trực tiếp làm media | Bình |
| 4:20–5:00 | Hiện sprint review và bằng chứng kiểm thử có sẵn | Việc đã làm, phần thiếu, rủi ro, kế hoạch; phân biệt test giả với dịch thật | Bình và cả nhóm |

Nếu đến 2:50 tác vụ chưa xong, mở video đầu ra dự phòng để bảo đảm thời lượng; nói rõ tác vụ mới vẫn đang chạy. Không gọi kết quả dự phòng là kết quả vừa sinh.

## 3. Tiêu chí quan sát

| Mục | Dấu hiệu cần thấy |
|---|---|
| Chức năng thật | Có request, mã công việc và trạng thái backend; kết quả là tệp video phát/tải được |
| Dữ liệu đúng | Cặp thuật ngữ vẫn có sau khi tải lại; video có phụ đề tiếng Việt và thời điểm phù hợp |
| Kiến trúc | Chỉ ra lớp giao diện, API, điều phối và module dữ liệu/xử lý trong mã nguồn |
| Review ngắn | Nêu được việc đã làm, thiếu sót, cách xử lý và kế hoạch của nhóm |

## 4. Phương án dự phòng

| Sự cố | Cách trình bày và xử lý |
|---|---|
| Mạng/API lỗi | Mở kết quả đã chạy trước và biên bản V-8; ghi lượt demo mới chưa hoàn tất. Chỉ dùng cache sau khi đã kiểm đủ điều kiện, không bảo đảm 0 token cho mọi lượt |
| ASR/dịch lâu | Dùng video ngắn, chuyển sang phần quản lý nhóm trong lúc chờ; đến mốc thời gian thì dùng đầu ra dự phòng có chú thích |
| Backend lỗi hoặc restart | Ghi nhận lỗi; trình bày bằng chứng cũ đúng phạm vi. Không coi ảnh chụp là thay thế nghiệm thu trực tiếp |
| Video có cảnh báo suy giảm | Giải thích chưa đủ chất lượng, kiểm lại lời thoại/phụ đề; không báo là hoàn thành đầy đủ |

## 5. Câu hỏi dự kiến

| Câu hỏi | Câu trả lời |
|---|---|
| Đây có phải MVC? | Kiến trúc phân lớp, có thể ánh xạ View/Controller/Model. Giao diện gọi API JSON, có lớp điều phối riêng; trình bày theo thiết kế tuần 3 |
| Vì sao chưa đăng nhập? | Phạm vi hiện tại là ứng dụng cục bộ một người dùng. Nhóm trình bày giới hạn này để giảng viên đối chiếu yêu cầu môn học |
| CRUD đã đủ chưa? | Nhóm có tạo/đọc; thuật ngữ có thêm/đọc/sửa. Xóa chưa có, không tuyên bố đủ CRUD |
| Có gửi dữ liệu ra ngoài không? | Video/âm thanh xử lý tại máy; phụ đề, ngữ cảnh và thuật ngữ gửi dịch vụ dịch |
| Ai đóng góp phần nào? | Trình bày báo cáo tuần của từng thành viên: việc đã làm, kết quả, sản phẩm bàn giao và vướng mắc; nhóm trưởng tổng hợp |
| Test đã chạy mới chưa? | Trong lần biên tập báo cáo chưa chạy lại. Khi có log mới thì nêu đúng ngày, số test và điều kiện; không dùng số cũ để xác nhận bản mới |

## 6. Ghi nhận sau demo

- Ngày/giờ và người thực hiện: ........................................
- Phiên bản demo và ngày cập nhật: ........................................
- Video/cấu hình; API thật, giả lập hay cache: ........................................
- Kết quả quan sát, thời gian, lỗi: ........................................
- Ý kiến giảng viên và việc cần bổ sung: ........................................
