# Hồ sơ nộp tuần 6

Dành cho giảng viên và nhóm thực hiện. Bộ hồ sơ chứng minh một phiên xử lý video và phản hồi với dữ liệu sai, kiểm ngày 14/10/2026.

## Mở tài liệu

- BAO_CAO_MUC_TIEU.docx: báo cáo kết quả, dữ liệu phiên và giới hạn kiểm chứng.
- PHIEU_LOI.docx: tám phiếu ghi nhận phản hồi từ mẫu sai.
- phien_01/: video đầu vào/đầu ra, phụ đề, CSDL thử, ảnh và manifest SHA-256.
- du_lieu_loi/: các tệp mẫu sai và một vùng mờ đúng để đối chứng.
- minh_chung/: kết quả kiểm thử và bản lệnh giữ dữ liệu/tái hiện mẫu lỗi.

Các bản Markdown là nguồn của tài liệu Word. Bộ mẫu không dùng dữ liệu cũ của work/. Video không được theo dõi trong Git; khi chuyển hồ sơ, dùng ZIP đầy đủ thay vì chỉ tải các tệp Git.

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
