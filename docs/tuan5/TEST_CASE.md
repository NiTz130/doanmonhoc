# Bộ ca kiểm thử tuần 5

Dành cho giảng viên và thành viên kiểm thử. Mỗi ca nêu dữ liệu, cách kiểm và kết quả cần đạt.

## Cách đọc kết quả

- **Đạt kiểm tự động:** kết quả đã ghi nhận ngày 07/10/2026. Các ca lỗi dùng dữ liệu tạm hoặc giả lập.
- **Đạt kiểm giao diện:** kết quả đã ghi nhận trên trình duyệt, với phần xử lý máy chủ giả lập.
- **Chưa quan sát thực tế:** cần phát video và kiểm lời thoại, chữ Việt, âm thanh, vùng mờ khi demo.

24 ca đại diện này liên kết với bộ kiểm thử hiện có. Tổng của bộ kiểm thử là 102, không cộng thành 126. Tên hàm để tra cứu nằm trong TEST_CASE.csv.

## Bình phụ trách TC01 đến TC08

### TC01 Xử lý thống nhất trên web và công cụ nội bộ

**Dữ liệu:** Video và bộ xử lý giả trong test.
**Cách kiểm:** Chạy cùng dữ liệu qua hai đường vào rồi đối chiếu kết quả.
**Mong đợi:** Hai đường xử lý cho cùng phụ đề và kết quả.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC02 Đọc và lưu phụ đề đúng nội dung

**Dữ liệu:** phu_de_en.srt, gồm ba câu.
**Cách kiểm:** Đọc phụ đề, lưu thành tệp mới rồi đọc lại.
**Mong đợi:** Nội dung, thứ tự và thời gian không thay đổi.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC03 Giữ tệp kết quả khi xảy ra lỗi ghi

**Dữ liệu:** Tệp kết quả có sẵn; giả lập lỗi ghi.
**Cách kiểm:** Ghi kết quả trong điều kiện lỗi và kiểm tra tệp cũ.
**Mong đợi:** Không lưu tệp dở thành kết quả; giữ tệp cũ hợp lệ.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC04 Ngăn hai lượt cùng xử lý một công việc

**Dữ liệu:** Hai yêu cầu trùng; khóa công việc trong thư mục tạm.
**Cách kiểm:** Gửi hai yêu cầu trùng và kiểm thông báo khóa công việc.
**Mong đợi:** Chỉ một lượt được xử lý; lượt còn lại nhận thông báo rõ.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC05 Lưu lịch sử tạo sửa xóa dữ liệu

**Dữ liệu:** Nhóm DemoTuan5; Ironhold → Thành Sắt.
**Cách kiểm:** Tạo, sửa, xóa nhóm và thuật ngữ trong CSDL tạm.
**Mong đợi:** Lịch sử lưu đủ thao tác và giá trị thay đổi.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC06 Từ chối bản sao lưu bị hỏng

**Dữ liệu:** CSDL tạm; co_so_du_lieu_hong.db.
**Cách kiểm:** Sao lưu, khôi phục bản tốt rồi thử bản hỏng trong CSDL tạm.
**Mong đợi:** Bản tốt khôi phục được; bản hỏng bị từ chối, dữ liệu được giữ.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC07 Dọn tệp cũ và bảo vệ dữ liệu đang dùng

**Dữ liệu:** Tệp cũ, tệp mới và tệp của công việc đang chạy.
**Cách kiểm:** Chạy chức năng dọn dẹp trên cây thư mục tạm.
**Mong đợi:** Chỉ xóa tệp đủ điều kiện; giữ tệp đang dùng và ngoài phạm vi.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC08 Tải video mẫu và giữ tệp đã có

**Dữ liệu:** Mẫu thiếu, mẫu đúng, mẫu sai và lỗi mạng giả.
**Cách kiểm:** Tải mẫu, chạy lại, rồi thử mẫu sai và lỗi mạng giả.
**Mong đợi:** Mẫu đúng được lưu; lần hai không tải lại; lỗi không ghi đè tệp.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

## Phú phụ trách TC09 đến TC16

### TC09 Tải video và tiếp tục sau chọn vùng mờ

**Dữ liệu:** Video thử; bật làm mờ; chưa chọn vùng.
**Cách kiểm:** Tải video, xem khung, gửi vùng hợp lệ và theo dõi tiếp.
**Mong đợi:** Chờ người dùng chọn vùng rồi tiếp tục xử lý.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC10 Từ chối tệp và tùy chọn không hợp lệ

**Dữ liệu:** tep_rong.mp4; khong_phai_video.txt; tùy chọn sai.
**Cách kiểm:** Gửi từng tệp lỗi và tùy chọn sai.
**Mong đợi:** Báo lỗi đầu vào và không để lại tệp rác.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC11 Kiểm giới hạn dung lượng tải lên

**Dữ liệu:** Yêu cầu giả vượt 4 GiB và thông tin dung lượng sai.
**Cách kiểm:** Gửi các yêu cầu giả về dung lượng; không cần tạo tệp lớn.
**Mong đợi:** Từ chối dung lượng quá lớn; thông tin sai không làm sập hệ thống.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC12 Chọn phụ đề hợp lệ và bỏ câu lỗi

**Dữ liệu:** Phụ đề ngoài video hợp lệ, rỗng; phu_de_loi.srt.
**Cách kiểm:** Cho hệ thống chọn nguồn phụ đề rồi đọc tệp có câu lỗi.
**Mong đợi:** Ưu tiên nguồn hợp lệ; bỏ câu rỗng hoặc thời gian sai theo chế độ đọc.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC13 Xử lý lỗi nhận dạng và thời gian phụ đề

**Dữ liệu:** Giả lỗi GPU; một mảnh câu có thời gian bằng nhau.
**Cách kiểm:** Chạy kiểm thử lỗi GPU và lỗi tách câu nhận dạng.
**Mong đợi:** Thử xử lý bằng CPU khi phù hợp; không làm hỏng cả đoạn thoại.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC14 Từ chối vùng mờ không hợp lệ

**Dữ liệu:** hop_hop_le.json; hop_loi.json; chỉ số câu sai.
**Cách kiểm:** Kiểm riêng từng hộp và gửi chỉ số câu không tồn tại.
**Mong đợi:** Chặn vùng vượt khung, rộng bằng 0, thiếu dữ liệu hoặc chỉ số câu sai.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC15 Giữ kết quả đã xong sau khi khởi động lại

**Dữ liệu:** Công việc chưa xong và công việc đã xong.
**Cách kiểm:** Khởi động lại máy chủ trong môi trường kiểm thử.
**Mong đợi:** Đánh dấu lỗi công việc bị gián đoạn; giữ video đã hoàn thành.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC16 Cảnh báo khi phụ đề thiếu lời thoại

**Dữ liệu:** Phụ đề chỉ phủ 6 giây trong video 100 giây.
**Cách kiểm:** Kiểm trạng thái trả về khi số lời nhận dạng quá ít.
**Mong đợi:** Hiển thị cảnh báo phụ đề thiếu thay vì báo hoàn thành đầy đủ.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

## Kiệt phụ trách TC17 đến TC24

### TC17 Dịch giữ thứ tự và thời gian câu

**Dữ liệu:** Ba câu phụ đề và bộ dịch giả.
**Cách kiểm:** Dịch dữ liệu thử rồi đối chiếu số câu và mốc thời gian.
**Mong đợi:** Giữ số câu, thứ tự và thời gian; phát hiện phản hồi sai.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC18 Áp dụng thuật ngữ đã lưu

**Dữ liệu:** thuat_ngu.json; hai lượt dịch.
**Cách kiểm:** Lưu thuật ngữ, dùng khi dịch rồi chạy lại công việc.
**Mong đợi:** Dùng bản dịch đã nhập; chạy lại không nhân đôi dữ liệu.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC19 Xử lý lỗi bộ dịch

**Dữ liệu:** Giả lỗi GPU và lỗi đánh dấu thuật ngữ.
**Cách kiểm:** Chạy bộ dịch trong điều kiện lỗi được giả lập.
**Mong đợi:** Có đường xử lý thay thế; lỗi thuật ngữ được phát hiện và xử lý.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC20 Thêm sửa đọc và xóa nhóm thuật ngữ

**Dữ liệu:** nhom.json; thuat_ngu.json; nhóm đang được xử lý.
**Cách kiểm:** Tạo, sửa, đọc, xóa dữ liệu và thử xóa nhóm đang bận.
**Mong đợi:** Dữ liệu lưu được; nhóm không có hoặc đang bận được báo đúng lỗi.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC21 Đọc đủ danh sách 450 thuật ngữ

**Dữ liệu:** 450 thuật ngữ do test tạo.
**Cách kiểm:** Mở danh sách, đọc hết các trang và thử lỗi lưu.
**Mong đợi:** Hiển thị đủ 450 mục; lỗi lưu vẫn giữ nội dung đang nhập.
**Kết quả đã ghi nhận:** Đạt kiểm thử giao diện đã ghi nhận, với dữ liệu giả.

### TC22 Áp dụng vùng mờ riêng cho từng câu

**Dữ liệu:** vung_theo_cau.json, gồm vùng chung và vùng riêng.
**Cách kiểm:** Áp dụng vùng chung rồi vùng riêng cho câu thứ hai.
**Mong đợi:** Vùng riêng thay vùng chung tại câu được gán.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC23 Từ chối video kết xuất bị hỏng

**Dữ liệu:** Giả lỗi xuất video; tệp kết quả cũ.
**Cách kiểm:** Xuất video trong điều kiện lỗi và kiểm tệp đầu ra.
**Mong đợi:** Không công bố video hỏng; không phá kết quả cũ.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động ngày 07/10/2026.

### TC24 Kiểm vùng mờ và chữ tiếng Việt trên giao diện

**Dữ liệu:** Khung ngang, dọc và chữ Việt đủ dấu.
**Cách kiểm:** Vẽ, di chuyển, đổi kích thước vùng; kiểm cách hiển thị phụ đề.
**Mong đợi:** Vùng đúng khi đổi kích thước; cách tạo chữ Việt được kiểm.
**Kết quả đã ghi nhận:** Đạt kiểm thử tự động đã ghi nhận; quan sát video thực tế chưa thực hiện.

## Chạy lại kiểm thử

Từ thư mục gốc của dự án:

```powershell
.venv/Scripts/python.exe test_pipeline.py
.venv/Scripts/python.exe tools_coverage.py --min 90
```

Các lệnh trên kiểm chức năng và độ phủ, không xác nhận chất lượng lời dịch. Giao diện chạy riêng bằng npm run test:frontend sau khi chuẩn bị môi trường theo README chính.

Không thử xóa, khôi phục hoặc ngắt công việc trên dữ liệu đang sử dụng. Test tự động tạo dữ liệu tạm để kiểm các trường hợp này.
