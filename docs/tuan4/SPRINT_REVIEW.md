# BÁO CÁO TỔNG TUẦN 4 — SPRINT REVIEW

**Nhóm 14** · Tổng hợp ba phần công việc.

## Phần 1. Nền tảng, cơ sở dữ liệu và điều phối

**Thành viên phụ trách:** Nguyễn Lê Đức Bình — 23050025.

### 1.1. Việc đã làm

- Hệ thống đã có lớp dữ liệu phụ đề và cơ sở dữ liệu SQLite phục vụ lưu nhóm video, thuật ngữ, nhật ký và trạng thái công việc.
- Luồng điều phối kết nối các bước lấy phụ đề, chọn vùng mờ, dịch và kết xuất; API và công cụ dòng lệnh dùng chung phần điều phối.
- Đã tổng hợp mô tả kiến trúc phân lớp và đối chiếu thiết kế tuần 3; báo cáo tuần được chia theo ba phần công việc để tổng hợp kết quả của nhóm.

### 1.2. Vướng mắc

- Tác vụ nền nằm trong tiến trình máy chủ nên có thể bị gián đoạn khi khởi động lại; cần phân biệt trạng thái công việc với dữ liệu trung gian đã lưu.
- Thay đổi lược đồ dữ liệu và cơ chế vùng mờ cần được kiểm chứng trên bản cuối, bao gồm dữ liệu cũ. Chưa có kết quả chạy lại trong lần biên tập báo cáo này.

### 1.3. Kế hoạch

- Phối hợp kiểm tra luồng tích hợp, lưu trữ và khả năng sử dụng lại dữ liệu trung gian; ghi nhận kết quả thực tế.
- Tổng hợp kết quả từ hai phần còn lại, cập nhật báo cáo chung và chuẩn bị phần trình bày kiến trúc.
- Thống nhất phạm vi chức năng còn thiếu với giảng viên và phối hợp tổ chức demo 5 phút.

## Phần 2. Đầu vào, nhận dạng và API công việc

**Thành viên phụ trách:** Đinh Hoàng Phú — 23050002.

### 2.1. Việc đã làm

- Hệ thống đã có luồng tiếp nhận video, tìm phụ đề sẵn; khi cần thì tách âm thanh và nhận dạng lời thoại bằng Whisper.
- Đã có API tải lên, tạo công việc, trả tiến độ, lấy khung hình và tiếp nhận vùng mờ. Module hình học kiểm tra vùng trước khi đưa vào xử lý.
- Hồ sơ V-8 đã ghi nhận nhận dạng trên video thật, ảnh hưởng của VAD với video có nhạc và đường lui từ GPU về CPU. Đây là bằng chứng của lượt chạy trước.

### 2.2. Vướng mắc

- Video có nhạc có thể bị bỏ sót lời thoại; cấu hình VAD ảnh hưởng chất lượng nhận dạng.
- Nhận dạng trên CPU có thể kéo dài thời gian demo; luồng chọn vùng và các trường hợp đầu vào không hợp lệ cần được kiểm chứng lại trên bản hiện tại.

### 2.3. Kế hoạch

- Chuẩn bị video tiếng Anh ngắn, lời thoại rõ; phân biệt mẫu dùng phụ đề sẵn với mẫu cần chạy nhận dạng.
- Kiểm tra tải lên, tiến độ, lấy khung và tiếp nhận vùng mờ; ghi lại kết quả và lỗi để phối hợp xử lý.
- Chuẩn bị phần demo đầu vào và tiến độ, bàn giao dữ liệu phụ đề cùng vùng mờ hợp lệ cho phần dịch và kết xuất.

## Phần 3. Dịch, thuật ngữ, kết xuất và giao diện liên quan

**Thành viên phụ trách:** Phạm Tuấn Kiệt — 23050046.

### 3.1. Việc đã làm

- Hệ thống đã có dịch phụ đề sang tiếng Việt, sử dụng ngữ cảnh và thuật ngữ theo nhóm video; có tạo, xem nhóm và thêm, xem, cập nhật thuật ngữ.
- Đã có kết xuất video với vùng làm mờ và phụ đề Việt; giao diện có quản lý nhóm, canvas chọn vùng và trang xem/tải kết quả.
- Hồ sơ V-8 ghi nhận dịch với API thật và sử dụng thuật ngữ giữa hai tập; V-10 ghi nhận luồng trình duyệt với tầng dịch giả lập. Đây là bằng chứng của các lượt chạy trước.

### 3.2. Vướng mắc

- Thời gian, lượng token và chi phí dịch có thể dao động; mạng/API ảnh hưởng tiến độ demo.
- Chưa có thao tác xóa nhóm và xóa thuật ngữ. Cần kiểm tra lại chữ Việt, thời điểm phụ đề, vùng mờ và lưu thuật ngữ trên bản hiện tại.

### 3.3. Kế hoạch

- Chuẩn bị nhóm và thuật ngữ mẫu; kiểm tra thêm, sửa và đọc lại dữ liệu sau khi tải trang.
- Kiểm tra kết xuất, canvas và trang kết quả; chuẩn bị video đầu ra dự phòng có ghi rõ điều kiện chạy.
- Làm rõ yêu cầu xóa và cách bảo toàn dữ liệu; chuẩn bị phần demo dịch và kết quả. Gọi API dịch mới chỉ trong phạm vi tài khoản/ngân sách được cho phép.
