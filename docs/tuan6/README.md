# Hồ sơ nộp tuần 6

Dành cho giảng viên và nhóm thực hiện. Bộ hồ sơ chứng minh một phiên xử lý video và phản hồi với dữ liệu sai, kiểm ngày 14/10/2026.

## Tài liệu trong thư mục

Báo cáo bám ảnh yêu cầu tuần 6: mục tiêu, hoạt động kiểm thử, sản phẩm nộp và bốn tiêu chí chấm. Tài liệu tuần 3–5 chỉ dùng tham khảo bố cục.

| Tài liệu | Nội dung |
|---|---|
| [NguyenLeDucBinh-23050025.docx](NguyenLeDucBinh-23050025.docx) | Báo cáo tuần 6 của nhóm: dữ liệu phiên, kết quả kiểm thử, phiếu lỗi, cách chạy chương trình và bộ dữ liệu test mẫu |
| [a.docx](a.docx) | Báo cáo phần việc của Nguyễn Lê Đức Bình: nền tảng, CSDL, điều phối và tích hợp |
| [DinhHoangPhu-23050002.docx](DinhHoangPhu-23050002.docx) | Báo cáo phần việc của Đinh Hoàng Phú: đầu vào, nhận dạng, vùng mờ và tiến độ |
| [PhamTuanKiet-23050046.docx](PhamTuanKiet-23050046.docx) | Báo cáo phần việc của Phạm Tuấn Kiệt: dịch, thuật ngữ, làm mờ và xuất video |
| [PHIEU_LOI.docx](PHIEU_LOI.docx) | Tám phiếu ghi nhận phản hồi từ mẫu sai |
| [TEST_CASE.md](TEST_CASE.md) | Dữ liệu đúng, mẫu sai, điều kiện kiểm và kết quả |
| [KICH_BAN_DEMO.md](KICH_BAN_DEMO.md) | Chuẩn bị, phân vai dự kiến, thao tác và biên bản cần ghi |

Các báo cáo theo thành viên chia phần trình bày bằng chứng tuần 6; chưa xác nhận ai trực tiếp thực hiện từng việc. Không dùng kết quả kiểm thử chung để tự tính mức đóng góp cá nhân.

## Dữ liệu và bằng chứng

- phien_01/: video đầu vào/đầu ra, phụ đề, CSDL thử, ảnh và manifest SHA-256.
- du_lieu_loi/: các tệp mẫu sai và một vùng mờ đúng để đối chứng.
- minh_chung/: kết quả kiểm thử và bản lệnh giữ dữ liệu/tái hiện mẫu lỗi.

Bộ mẫu không dùng dữ liệu cũ của work/. Video không được theo dõi trong Git; khi chuyển dữ liệu phiên, cần kèm tệp media thay vì chỉ tải các tệp Git.

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

Chưa nghe và xem toàn bộ video. Demo web bằng API và màn vẽ hộp trên trình duyệt đã chạy ngày 14/10/2026 nhưng chưa có tệp bằng chứng trong thư mục này. Tám mẫu sai đều bị chặn đúng; không có tám lỗi phần mềm mới. CSDL và tệp lỗi chỉ dùng trong môi trường thử.
