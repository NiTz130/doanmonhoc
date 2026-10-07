# Dữ liệu kiểm thử tuần 5

Dành cho giảng viên và thành viên kiểm thử. Các tệp này giúp thử dữ liệu đúng và dữ liệu sai theo TEST_CASE.md.

| Tệp | Cách dùng |
|---|---|
| phu_de_en.srt | Ba câu phụ đề hợp lệ; kiểm đọc, lưu và dịch |
| phu_de_loi.srt | Có câu ngược thời gian và câu rỗng; kiểm phát hiện câu lỗi |
| hop_hop_le.json | Vùng mờ nằm trong khung hình |
| hop_loi.json | Bốn vùng sai: vượt khung, rộng bằng 0, sai kiểu dữ liệu, thiếu thông tin; kiểm từng vùng |
| vung_theo_cau.json | Một vùng chung và một vùng riêng cho câu thứ hai |
| nhom.json | Nhóm DemoTuan5 để thử quản lý dữ liệu |
| thuat_ngu.json | Ironhold → Thành Sắt để thử thêm, sửa và dùng thuật ngữ |
| tep_rong.mp4 | Tệp rỗng để kiểm từ chối đầu vào |
| khong_phai_video.txt | Tệp văn bản để kiểm sai định dạng |
| co_so_du_lieu_hong.db | Tệp cố ý sai để kiểm từ chối khôi phục |

## Lưu ý khi dùng

Phụ đề mẫu không phải bản chép lời của video_3. Vùng mẫu dùng tỷ lệ từ 0 đến 1; cần vẽ lại theo vị trí chữ khi thử video thật. Thuật ngữ mẫu không chứng minh video có từ Ironhold.

Tệp lỗi chỉ dùng ở môi trường thử. Không khôi phục tệp hỏng vào dữ liệu đang sử dụng. Các test về 450 thuật ngữ, lỗi mạng hoặc thiết bị tự tạo dữ liệu giả.

## Video thật

Video nằm tại test/video_3.mp4. Chạy cai_dat.bat từ thư mục gốc để tải, hoặc dùng liên kết trong README của hồ sơ tuần 5. Hướng dẫn đối chiếu tệp ở test/README.md.
