# Hồ sơ nộp tuần 6

Dành cho giảng viên và nhóm thực hiện. Bộ hồ sơ chứng minh một phiên xử lý video và phản hồi với dữ liệu sai, kiểm ngày 14/10/2026.

## Bộ báo cáo Markdown tuần 6

Nội dung báo cáo lấy từ BAO_CAO_MUC_TIEU.md, PHIEU_LOI.md, phien_01/, du_lieu_loi/ và minh_chung/ trong thư mục này. Báo cáo bám ảnh yêu cầu tuần 6: mục tiêu, hoạt động kiểm thử, sản phẩm nộp và bốn tiêu chí chấm. Tài liệu tuần 3–5 chỉ dùng tham khảo bố cục; không dùng làm bằng chứng hoàn thành tuần 6.

| Tài liệu | Nội dung |
|---|---|
| [Báo cáo tổng tuần 6](BAO_CAO_TUAN6_TONG.md) | Mục tiêu, dữ liệu phiên, tích hợp, kiểm thử, phiếu lỗi và tiêu chí nộp |
| [Nguyễn Lê Đức Bình](NguyenLeDucBinh-23050025.md) | Nền tảng, CSDL, điều phối và tích hợp |
| [Đinh Hoàng Phú](DinhHoangPhu-23050002.md) | Đầu vào, nhận dạng, vùng mờ và tiến độ |
| [Phạm Tuấn Kiệt](PhamTuanKiet-23050046.md) | Dịch, thuật ngữ, làm mờ và xuất video |
| [Bộ ca kiểm thử tuần 6](TEST_CASE.md) | Dữ liệu đúng, mẫu sai, điều kiện kiểm và kết quả từ bằng chứng tuần 6 |
| [Kịch bản demo](KICH_BAN_DEMO.md) | Chuẩn bị, phân vai dự kiến, thao tác và biên bản cần ghi |
| [Báo cáo mục tiêu chi tiết](BAO_CAO_MUC_TIEU.md) | Dữ liệu PHIEN-01 và kết quả chạy kiểm đã có |
| [Phiếu lỗi](PHIEU_LOI.md) | Tám mẫu sai, cách kích hoạt và phản hồi thực tế |

Các báo cáo theo thành viên chia phần trình bày bằng chứng tuần 6; chưa xác nhận ai trực tiếp thực hiện từng việc. Không dùng kết quả kiểm thử chung để tự tính mức đóng góp cá nhân.

## Mở tài liệu

- BAO_CAO_MUC_TIEU.docx: báo cáo kết quả, dữ liệu phiên và giới hạn kiểm chứng.
- PHIEU_LOI.docx: tám phiếu ghi nhận phản hồi từ mẫu sai.
- phien_01/: video đầu vào/đầu ra, phụ đề, CSDL thử, ảnh và manifest SHA-256.
- du_lieu_loi/: các tệp mẫu sai và một vùng mờ đúng để đối chứng.
- minh_chung/: kết quả kiểm thử và bản lệnh giữ dữ liệu/tái hiện mẫu lỗi.

Hai bản DOCX được tạo từ BAO_CAO_MUC_TIEU.md và PHIEU_LOI.md tại lần đóng gói trước. Các báo cáo MD mới chưa có bản Word tương ứng. Bộ mẫu không dùng dữ liệu cũ của work/. Video không được theo dõi trong Git; khi chuyển dữ liệu phiên, cần kèm tệp media thay vì chỉ tải các tệp Git.

## Chạy lại kiểm chứng

Chạy tại thư mục gốc dự án đã cài môi trường, ffmpeg và cache model:

```powershell
$env:PYTHONUTF8='1'
$env:HF_HUB_OFFLINE='1'
$env:TRANSFORMERS_OFFLINE='1'
.venv\Scripts\python.exe test_pipeline.py
$env:LOGIC_RUNTIME_EVIDENCE="$PWD\.cache\tuan6-chay-lai\runtime"
.venv\Scripts\python.exe test\runtime_logic.py
.venv\Scripts\python.exe test_pipeline.py --real
.venv\Scripts\python.exe tools_coverage.py --min 90
```

Lệnh --real cần test/video_2.mp4 và model đã có. Thiếu điều kiện phải ghi NOT RUN. Test runtime dùng video tổng hợp và ASR/dịch giả; bộ thật dùng model thật.

Muốn giữ dữ liệu phiên mới, dùng bản lệnh minh_chung/luu_phien.py.txt từ thư mục gốc. Đổi đích .cache/tuan6-20261014/phien-01 thành thư mục mới chưa tồn tại trước khi chạy. Lệnh cố ý không ghi đè phiên cũ.

Bản lệnh minh_chung/kiem_mau.py.txt ghi lại đúng thao tác kiểm 10 mẫu của đợt này. Lệnh dùng helper kiểm thử đã có và đường dẫn của repo. Đây không phải công cụ chạy độc lập khi thiếu mã nguồn.

## Giới hạn

Chưa nghe và xem toàn bộ video, chưa demo web hoặc kiểm lại giao diện. Tám mẫu sai đều bị chặn đúng; không có tám lỗi phần mềm mới. CSDL và tệp lỗi chỉ dùng trong môi trường thử.
