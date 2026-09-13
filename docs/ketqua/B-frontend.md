# Kiểm tra giao diện B — 2026-09-10

Đã triển khai bốn màn theo hướng B bằng HTML/CSS/JavaScript hiện có. Three.js 0.180.0 và font Be Vietnam Pro/Lora được phục vụ cục bộ, kèm giấy phép. Không dùng Figma MCP để tiếp tục triển khai.

## Đã kiểm tra trong lượt 2026-09-10

- `node test/frontend.cjs`: Playwright/Chromium với API giả lập; viewport 360/768/1440, chống gửi lặp, validation tùy chọn nâng cao, upload thất bại, polling đơn sau 20 lần chuyển màn và thử lại sau mất mạng.
- Tám khung mẫu của bộ dữ liệu kiểm tra lúc đó; tọa độ trên ảnh ngang/dọc 720p/1080p, kéo ngược, resize, nhập tọa độ và từ chối vùng vượt ảnh; xử lý ảnh lỗi.
- Trạng thái suy_giam, đường dẫn tải kết quả, thao tác tải bằng dữ liệu mẫu; giữ thuật ngữ khi lưu lỗi và payload khóa bản dịch.
- Dừng cảnh, reduced motion, mất WebGL context, module 3D không tải; không có lỗi JavaScript không bắt được.
- `.venv/Scripts/python.exe test_pipeline.py`: 13 kiểm tra offline đạt.
- `node --check web/app.js`, `git diff --check`; review độc lập đã xử lý hai phát hiện về race upload/poll và validation trong details đóng.

## Thay đổi sau lượt kiểm tra

Mã hiện tại dùng canvas với một khung cho mỗi cue, hỗ trợ vùng riêng từng câu và áp vùng cho dải câu. Pipeline chờ chọn vùng sau khi có phụ đề gốc, trước bước dịch. Các kết quả kiểm tra lịch sử ở trên không xác nhận các thay đổi này; ảnh trong thư mục có thể đã được cập nhật sau lượt báo cáo.

## Giới hạn kiểm chứng

API trong lượt kiểm tra trình duyệt này là giả lập; tải thử dùng data URL sau khi xác nhận đường dẫn endpoint. Lượt này không chạy dịch/video thật hoặc gọi dịch vụ trả phí; các lượt ASR/DeepSeek thật riêng được ghi ở [V8.md](V8.md). Chưa đo FPS/bộ nhớ trên máy demo, kiểm tra trình đọc màn hình, tương phản tự động hoặc thao tác cảm ứng trên thiết bị thật. Đây là các mục chưa xác minh, không phải kết quả đạt.

## Chạy lại

Chạy `.venv/Scripts/python.exe -m http.server 8765 --bind 127.0.0.1 --directory web`, rồi đặt NODE_PATH tới thư mục chứa Playwright và chạy `node test/frontend.cjs`.

Ứng dụng thật: `.venv/Scripts/python.exe -m uvicorn api.app:app --host 127.0.0.1 --port 8000`.

Ảnh `B-upload-360.png`, `B-upload-768.png`, `B-upload-1440.png`, `B-progress.png`, `B-region.png`, `B-result.png`, `B-glossary.png` cùng thư mục. Các khung video là dữ liệu mẫu.
