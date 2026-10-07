# Video mẫu để kiểm thử

**Người đọc:** người cài hệ thống trên máy mới và thành viên kiểm thử.
**Mục đích:** tải đúng video mẫu, thử luồng trên web và hiểu giới hạn của kết quả.

## Tải mẫu khi cài đặt

Từ thư mục gốc của dự án, chạy:

```powershell
uv run --locked python tools_tai_video.py
```

Trên Windows, `.\cai_dat.bat` chạy cùng lệnh.
`uv` tạo hoặc đồng bộ môi trường Python trước khi tải.
Nếu đã có môi trường, có thể chỉ chạy `.venv/Scripts/python.exe tools_tai_video.py`.
Muốn lưu mẫu vào nơi khác, thêm `--dich "duong_dan/video_3.mp4"`.

Nguồn: [video_3.mp4 trên Google Drive](https://drive.google.com/file/d/16sh5oYQUdVYngAkxV-8d_rh4v5B-4ngV/view?usp=drivesdk).
Người có liên kết được xem và tải, không cần đăng nhập.

| Thuộc tính | Giá trị |
|---|---|
| Đích mặc định | `test/video_3.mp4` |
| Dung lượng | 5 732 135 byte (khoảng 5,5 MiB) |
| Thời lượng | 100,937 giây |
| Kích thước khung hình | 640×360 |
| SHA-256 | `48b89db16a49a6c8cf2c52dfe88d6b90d16320c9d296715518e42f3832d4d4fb` |

Công cụ tải theo từng khối; kiểm số byte và SHA-256 trước khi công bố tệp.
SHA-256 là mã băm dùng để đối chiếu nội dung với bản gốc.
Mẫu đúng đã có thì không gọi mạng.
Mẫu khác nội dung được giữ nguyên và báo lỗi; chuyển tệp đó đi trước khi chạy lại.
Lỗi mạng, tệp thiếu/thừa hoặc ngắt tải đều dọn tệp tạm.
Nếu hai lượt tải cùng đích, một lượt có thể báo lỗi do đích đã tồn tại; chạy lại để kiểm mẫu.
Hệ thống file cần hỗ trợ liên kết cứng (hard link), như NTFS; không hỗ trợ thì báo lỗi và giữ dữ liệu.

Mã thoát: `0` mẫu sẵn sàng; `1` tải hoặc kiểm mẫu lỗi; `130` người dùng ngắt tải.
Chủ sở hữu Drive cần giữ quyền xem/tải bằng liên kết để máy mới tải được.

## Thử luồng trên web

1. Khởi động backend bằng `start_system.bat` hoặc lệnh uvicorn trong README chính.
2. Mở `http://127.0.0.1:8000` và tải `test/video_3.mp4` lên.
3. Chọn làm mờ `on` nếu muốn kiểm màn khoanh vùng; vẽ vùng khi hệ thống yêu cầu.
4. Theo dõi tiến độ và tải video kết quả.
5. Kiểm bằng mắt và tai: video phát được, âm thanh còn, phụ đề có dấu và vùng mờ đúng chỗ.

Whisper/NLLB có thể cần tải model lần đầu; mẫu video không kèm model.
Mẫu dùng để thử vận hành, không chứng minh chất lượng nhận dạng/dịch hoặc hiệu năng trên phim dài.

## Phân biệt các bộ kiểm thử

| Lệnh hoặc tệp | Dữ liệu dùng | Cần mạng để lấy mẫu? |
|---|---|---|
| `test_pipeline.py` | Dữ liệu và callable giả; gồm test tải mẫu với mạng giả | Không |
| `test_pipeline.py --smoke` | Video tổng hợp bằng ffmpeg | Không |
| `test/runtime_logic.py` | Video tổng hợp, uvicorn và ffmpeg thật | Không |
| `test_pipeline.py --real` | 30 giây đầu `test/video_2.mp4`, GPU và model thật | Không tự tải mẫu hoặc model |
| Thử bằng tay trên web | `test/video_3.mp4` | Một lần khi cài đặt nếu chưa có mẫu |

`video_2.mp4` và `video.mp4` có thể có trên máy phát triển; lệnh cài đặt chỉ tải `video_3.mp4`.
Thiếu mẫu hoặc model của bộ `--real` thì test tương ứng báo `NOT RUN`, không phải `PASS`.
Video, model và kết quả dưới `work/` không được đưa vào Git.
