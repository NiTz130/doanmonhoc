# Phiếu ghi nhận lỗi từ mẫu test sai — Tuần 6

Dành cho giảng viên và nhóm kiểm thử. Tài liệu ghi dữ liệu sai, phản hồi thực tế và kết luận sau kiểm ngày 14/10/2026.

## Kết luận chung

Đã chạy 8 trường hợp sai: 8 phản hồi đúng, 0 sai lệch so với mong đợi. Đây là phiếu lỗi đầu vào được hệ thống phát hiện, không phải danh sách 8 lỗi phần mềm. Không tạo phiếu bug giả khi chưa có hành vi sai.

Nguồn: du_lieu_loi/ và minh_chung/mau_loi.json. Tái hiện bằng bản lệnh minh_chung/kiem_mau.py.txt tại thư mục gốc dự án. Người thực hiện: kiểm thử tự động trong phiên hỗ trợ; nhóm chưa ký nghiệm thu thủ công.

Mức phân loại: **LỖI đầu vào** phải từ chối hoặc xử lý theo chế độ đọc. **cảnh báo** bỏ câu hỏng ở chế độ cho phép không phải lỗi test; không sửa mã để loại bỏ cảnh báo.

## PL-01 — Vùng mờ vượt khung

- **Mẫu:** du_lieu_loi/hop_loi.json[0].

- **Điều kiện kích hoạt:** x=0,8; w=0,4 nên x+w>1.

- **Tái hiện:** Kiểm phần tử 0 của hop_loi.json bằng kiem_hop.

- **Mong đợi:** ValueError.

- **Thực tế:** Hop vuot ra ngoai khung hinh.

- **Cấp kiểm:** validator. Không gán kết quả validator thành kết quả giao diện.

- **Ảnh hưởng:** thao tác với đầu vào sai bị chặn; chưa phát hiện sai lệch của phần mềm trong ca này.

- **Cách xử lý dữ liệu:** Người dùng cần giảm x hoặc chiều rộng để vùng nằm trong khung.

- **Trạng thái:** PASS — hệ thống phản hồi đúng. Không cần sửa mã từ kết quả này.

## PL-02 — Chiều rộng bằng không

- **Mẫu:** du_lieu_loi/hop_loi.json[1].

- **Điều kiện kích hoạt:** w=0.

- **Tái hiện:** Kiểm phần tử 1 của hop_loi.json bằng kiem_hop.

- **Mong đợi:** ValueError.

- **Thực tế:** w va h phai duong.

- **Cấp kiểm:** validator. Không gán kết quả validator thành kết quả giao diện.

- **Ảnh hưởng:** thao tác với đầu vào sai bị chặn; chưa phát hiện sai lệch của phần mềm trong ca này.

- **Cách xử lý dữ liệu:** Nhập chiều rộng lớn hơn 0.

- **Trạng thái:** PASS — hệ thống phản hồi đúng. Không cần sửa mã từ kết quả này.

## PL-03 — Tọa độ sai kiểu

- **Mẫu:** du_lieu_loi/hop_loi.json[2].

- **Điều kiện kích hoạt:** x=true.

- **Tái hiện:** Kiểm phần tử 2 của hop_loi.json bằng kiem_hop.

- **Mong đợi:** ValueError.

- **Thực tế:** Toa do hop phai la so huu han, nhan duoc True.

- **Cấp kiểm:** validator. Không gán kết quả validator thành kết quả giao diện.

- **Ảnh hưởng:** thao tác với đầu vào sai bị chặn; chưa phát hiện sai lệch của phần mềm trong ca này.

- **Cách xử lý dữ liệu:** Dùng tọa độ số hữu hạn; không dùng boolean.

- **Trạng thái:** PASS — hệ thống phản hồi đúng. Không cần sửa mã từ kết quả này.

## PL-04 — Thiếu chiều cao

- **Mẫu:** du_lieu_loi/hop_loi.json[3].

- **Điều kiện kích hoạt:** Không có khóa h.

- **Tái hiện:** Kiểm phần tử 3 của hop_loi.json bằng kiem_hop.

- **Mong đợi:** ValueError.

- **Thực tế:** Hop thieu khoa: ['h'].

- **Cấp kiểm:** validator. Không gán kết quả validator thành kết quả giao diện.

- **Ảnh hưởng:** thao tác với đầu vào sai bị chặn; chưa phát hiện sai lệch của phần mềm trong ca này.

- **Cách xử lý dữ liệu:** Bổ sung đủ x, y, w, h.

- **Trạng thái:** PASS — hệ thống phản hồi đúng. Không cần sửa mã từ kết quả này.

## PL-05 — Phụ đề không hợp lệ

- **Mẫu:** du_lieu_loi/phu_de_loi.srt.

- **Điều kiện kích hoạt:** Tệp có câu ngược thời gian và câu rỗng.

- **Tái hiện:** Đọc phu_de_loi.srt bằng doc_srt ở chế độ chặt.

- **Mong đợi:** ValueError.

- **Thực tế:** Khoi SRT hong hoac rong.

- **Cấp kiểm:** validator. Không gán kết quả validator thành kết quả giao diện.

- **Ảnh hưởng:** thao tác với đầu vào sai bị chặn; chưa phát hiện sai lệch của phần mềm trong ca này.

- **Cách xử lý dữ liệu:** Sửa thời gian và nội dung câu. Chế độ bo_cue_hong=True đã kiểm riêng, giữ lại 1 câu hợp lệ.

- **Trạng thái:** PASS — hệ thống phản hồi đúng. Không cần sửa mã từ kết quả này.

## PL-06 — Bản sao CSDL hỏng

- **Mẫu:** du_lieu_loi/co_so_du_lieu_hong.db.

- **Điều kiện kích hoạt:** Tệp không phải cơ sở dữ liệu SQLite.

- **Tái hiện:** Kiểm co_so_du_lieu_hong.db bằng db._kiem_file_db; không khôi phục vào CSDL đang dùng.

- **Mong đợi:** ValueError.

- **Thực tế:** Không phải file CSDL hợp lệ: file is not a database.

- **Cấp kiểm:** validator. Không gán kết quả validator thành kết quả giao diện.

- **Ảnh hưởng:** thao tác với đầu vào sai bị chặn; chưa phát hiện sai lệch của phần mềm trong ca này.

- **Cách xử lý dữ liệu:** Chọn bản sao lưu SQLite hợp lệ. Test hồi quy khôi phục và giữ dữ liệu cũ cũng đã qua.

- **Trạng thái:** PASS — hệ thống phản hồi đúng. Không cần sửa mã từ kết quả này.

## PL-07 — Video rỗng

- **Mẫu:** du_lieu_loi/tep_rong.mp4.

- **Điều kiện kích hoạt:** Tệp 0 byte.

- **Tái hiện:** Gửi tep_rong.mp4 tới POST /api/video bằng FastAPI TestClient trong môi trường thử.

- **Mong đợi:** HTTP 400, no upload artifacts.

- **Thực tế:** HTTP 400; File rong.

- **Cấp kiểm:** FastAPI TestClient, test fixture. Không gán kết quả validator thành kết quả giao diện.

- **Ảnh hưởng:** thao tác với đầu vào sai bị chặn; chưa phát hiện sai lệch của phần mềm trong ca này.

- **Cách xử lý dữ liệu:** Chọn video có dữ liệu. Kiểm không có tệp tải lên còn sót.

- **Trạng thái:** PASS — hệ thống phản hồi đúng. Không cần sửa mã từ kết quả này.

## PL-08 — Tệp không phải video

- **Mẫu:** du_lieu_loi/khong_phai_video.txt.

- **Điều kiện kích hoạt:** Đuôi .txt.

- **Tái hiện:** Gửi khong_phai_video.txt tới POST /api/video bằng FastAPI TestClient trong môi trường thử.

- **Mong đợi:** HTTP 400, no upload artifacts.

- **Thực tế:** HTTP 400; Chi nhan .avi, .mkv, .mov, .mp4, .ts, .webm.

- **Cấp kiểm:** FastAPI TestClient, test fixture. Không gán kết quả validator thành kết quả giao diện.

- **Ảnh hưởng:** thao tác với đầu vào sai bị chặn; chưa phát hiện sai lệch của phần mềm trong ca này.

- **Cách xử lý dữ liệu:** Chọn tệp video hợp lệ. Kiểm không có tệp tải lên còn sót.

- **Trạng thái:** PASS — hệ thống phản hồi đúng. Không cần sửa mã từ kết quả này.

## Hai đối chứng đã chạy

- DC-01: đọc cùng SRT với bo_cue_hong=True; bỏ hai câu lỗi và giữ một câu hợp lệ. PASS.

- DC-02: hop_hop_le.json được validator chấp nhận. PASS.

## Bằng chứng lỗi vận hành bổ sung

Runtime mới đã kiểm gửi trùng, phụ đề nguồn thay đổi, khởi động lại và khóa còn sót. Các nhánh xung đột trả HTTP 409 theo assertion của test. Xem minh_chung/runtime-results.json và test/runtime_logic.py.

Sau sự cố giữ khóa, hệ thống yêu cầu chỉ xóa khóa thủ công khi chắc chắn không còn tiến trình chạy. Bộ kiểm không tự xóa khóa còn sót để né lỗi.

Trigger SQLite ghi lịch sử tạo/sửa/xóa đã được kiểm bởi test_trigger_lich_su_moi_duong_ghi trong 102 test offline. Điều kiện kích hoạt lỗi đầu vào không đồng nghĩa với trigger CSDL.

## Khi phát hiện lỗi phần mềm trong buổi demo

Ghi mã mới, đầu vào, bước tái hiện, mong đợi, thực tế, mức ảnh hưởng và tệp bằng chứng. Chỉ đóng phiếu sau khi chạy lại đạt. Không sửa kết quả trong tám phiếu trên để ghi một lần chạy khác.
