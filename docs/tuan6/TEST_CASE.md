# Bộ ca kiểm thử và dữ liệu tuần 6

Dành cho giảng viên và nhóm kiểm thử. Tài liệu trình bày các kiểm đã có bằng chứng trong docs/tuan6, theo yêu cầu dữ liệu đúng, dữ liệu sai và hoàn thành một công việc cụ thể.

## 1. Nguồn và cách đọc

Nguồn gồm [báo cáo mục tiêu](BAO_CAO_MUC_TIEU.md), [manifest phiên](phien_01/manifest.json), [kết quả mẫu lỗi](minh_chung/mau_loi.json) và log trong minh_chung/. Mã T6 dưới đây dùng phân nhóm bằng chứng tuần 6, không phải tên hàm test mới.

PASS nghĩa là phép kiểm tương ứng đã qua trong lượt ghi nhận ngày 14/10. NOT RUN nghĩa là chưa có kết quả thực hiện. Dữ liệu sai bị từ chối đúng là test PASS.

## 2. Dữ liệu đúng và kiểm tích hợp

| Mã | Dữ liệu, thao tác | Mong đợi | Kết quả và bằng chứng |
|---|---|---|---|
| T6-01 | PHIEN-01: clip.mp4 → Whisper base → NLLB → ffmpeg, blur off | Hoàn thành và lưu được bộ đầu vào/đầu ra | [phien.txt](minh_chung/phien.txt): PASS một phiên |
| T6-02 | Đối chiếu sub_goc.srt với sub_vi.srt trong phiên | Cùng 5 câu, giữ mốc thời gian | [manifest](phien_01/manifest.json): PASS |
| T6-03 | Kiểm ra_vi.mp4 và dấu hiệu vẽ phụ đề | Có hình, âm thanh, thời lượng gần 30 giây | [báo cáo mục tiêu](BAO_CAO_MUC_TIEU.md): PASS; chưa nghe/xem toàn bộ |
| T6-04 | Video tổng hợp trong runtime; gửi vùng rồi tiếp tục | Tải được kết quả; xử lý đúng xung đột/restart | [runtime-results.json](minh_chung/runtime-results.json): PASS; ASR/dịch giả lập |
| T6-05 | GPU, Whisper base/large-v3 và NLLB trong cache | Model thật hoạt động; giữ cấu trúc câu và xuất được video | [real.txt](minh_chung/real.txt): 6/6 PASS |
| T6-06 | Dữ liệu do bộ offline tạo khi chạy | Các chức năng và nhánh lỗi theo phép kiểm hoạt động đúng | [offline.txt](minh_chung/offline.txt): 102/102 PASS |

T6-02 và T6-03 là các điều kiện trong phiên T6-01. Phiên T6-01 chạy lại một test đầu cuối của bộ thật để giữ dữ liệu. Không cộng những nhóm này thành số test độc lập.

## 3. Mẫu sai và đối chứng đã kiểm trực tiếp

| Mã | Mẫu trong du_lieu_loi/ | Mong đợi / phản hồi thực tế | Cấp kiểm | Kết quả |
|---|---|---|---|---|
| PL-01 | hop_loi.json[0] | Hop vuot ra ngoai khung hinh | validator | PASS |
| PL-02 | hop_loi.json[1] | w va h phai duong | validator | PASS |
| PL-03 | hop_loi.json[2] | Toa do hop phai la so huu han, nhan duoc True | validator | PASS |
| PL-04 | hop_loi.json[3] | Hop thieu khoa: ['h'] | validator | PASS |
| PL-05 | phu_de_loi.srt | Khoi SRT hong hoac rong | validator | PASS |
| PL-06 | co_so_du_lieu_hong.db | Không phải file CSDL hợp lệ: file is not a database | validator | PASS |
| PL-07 | tep_rong.mp4 | HTTP 400; File rong | FastAPI TestClient, test fixture | PASS |
| PL-08 | khong_phai_video.txt | HTTP 400; Chi nhan .avi, .mkv, .mov, .mp4, .ts, .webm | FastAPI TestClient, test fixture | PASS |
| DC-01 | phu_de_loi.srt | 1 valid cue | parser | PASS |
| DC-02 | hop_hop_le.json | accepted | validator | PASS |

Tổng: **10 chạy / 10 qua / 0 lỗi / 0 NOT RUN**, gồm tám mẫu sai và hai đối chứng. Bước tái hiện và cách xử lý từng mẫu nằm trong [PHIEU_LOI.md](PHIEU_LOI.md). Bản lệnh đã dùng: [kiem_mau.py.txt](minh_chung/kiem_mau.py.txt).

PL-01–PL-06 kiểm ở hàm xử lý dữ liệu; PL-07–PL-08 kiểm qua FastAPI TestClient. Chưa có quan sát giao diện tương ứng. DC-01 giữ một câu hợp lệ khi cho phép bỏ câu lỗi; DC-02 chấp nhận hộp đúng.

## 4. Điều kiện kích hoạt và trigger

Runtime ghi nhận kiểm xung đột khi gửi trùng, tiếp tục từ phụ đề cũ và khóa còn sau sự cố. Các nhánh đó được kiểm HTTP 409. Không tự xóa khóa để né lỗi.

Trigger SQLite là cơ chế ghi lịch sử khi dữ liệu đổi. Log offline có test_trigger_lich_su_moi_duong_ghi PASS. Đây là kiểm riêng, không đồng nghĩa với điều kiện kích hoạt một lỗi đầu vào.

## 5. Giới hạn bao phủ yêu cầu

Có bộ dữ liệu lưu của một phiên và các mẫu lỗi cụ thể. Một số dữ liệu của bộ offline/runtime được tạo tạm trong lúc chạy, không nằm thành bộ mẫu dùng thử độc lập trong thư mục này.

Vì vậy, chưa khẳng định có đủ phiên thao tác thủ công cho mọi chức năng. Các kiểm sau còn NOT RUN: demo web, kiểm giao diện desktop/mobile, nghe/xem toàn bộ video. Đối chiếu đầy đủ mọi chức năng với đặc tả ban đầu cũng chưa có trong hồ sơ tuần 6.

Độ phủ offline ghi nhận 97,0% trong [coverage.txt](minh_chung/coverage.txt). Độ phủ không chứng minh chất lượng bản dịch hoặc toàn bộ trải nghiệm người dùng.

## 6. Chạy lại và ghi kết quả

Dùng lệnh trong [README](README.md). Khi chạy lại, ghi ngày, điều kiện máy, số chạy/qua/lỗi/NOT RUN và lý do chưa chạy. Kịch bản thủ công nằm trong [KICH_BAN_DEMO.md](KICH_BAN_DEMO.md). Không khôi phục CSDL hỏng hoặc thử crash trên dữ liệu đang sử dụng.
