# Kịch bản demo tuần 5

Dành cho ba thành viên khi trình bày với giảng viên. Mục tiêu là cho thấy luồng dịch video, quản lý thuật ngữ và cách xử lý lỗi.

## Chuẩn bị trước buổi trình bày

1. Từ thư mục gốc, chạy cai_dat.bat để cài môi trường và tải video mẫu.
2. Chạy start_system.bat, mở http://127.0.0.1:8000.
3. Dùng nhóm riêng DemoTuan5 và video test/video_3.mp4.
4. Chuẩn bị sẵn bộ nhận dạng và bộ dịch; tập trước để biết thời gian xử lý.
5. Chuẩn bị một video kết quả dự phòng, ghi rõ là kết quả của lượt chạy trước.

Phụ đề và vùng mẫu trong du_lieu_demo dùng kiểm riêng. Không ghép phụ đề mẫu vào video_3 vì chúng không khớp lời thoại.

## Những điều cần chứng minh

- Video tải lên được; có tiến độ và kết quả để xem hoặc tải.
- Hệ thống chờ chọn vùng rồi tiếp tục sau khi người dùng xác nhận.
- Thuật ngữ vẫn còn sau khi tải lại trang.
- Video kết quả còn âm thanh, có chữ Việt đủ dấu và vùng làm mờ đúng vị trí.
- Dữ liệu sai được báo lỗi. Dùng TC10 để minh họa tệp sai, TC14 để minh họa vùng sai.

