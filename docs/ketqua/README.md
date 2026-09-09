# Ảnh kết quả V-10 — chạy thật trên trình duyệt

Chụp tự động bằng Playwright + Chromium trên `http://127.0.0.1:8765`, ffmpeg và
ffprobe thật. **Không có lỗi hay cảnh báo JavaScript nào** trong suốt lượt chạy.

Chỉ tầng dịch được thay bằng bảng tra sẵn, vì nhóm chưa có `DEEPSEEK_API_KEY` —
đó cũng chính là lý do V-8 ghi NOT RUN.

| Ảnh | Chứng minh |
|---|---|
| `01_tai_len.png` | Màn tải lên với đủ tuỳ chọn |
| `02_tien_do.png` | Bảng tiến độ hỏi theo chu kỳ, dừng ở "Chờ bạn khoanh vùng phụ đề cứng" — trạng thái chờ, không phải lỗi |
| `04_da_ve_hop.png` | Kéo chuột thật trên canvas ở khung 2/4; hộp ra `x=0.300 y=0.780 w=0.400 h=0.140` theo phần trăm |
| `05_hop_giu_nguyen.png` | Chuyển sang khung 3/4, **hộp vẫn còn nguyên** — đó là toàn bộ lý do có thanh trượt |
| `06_xong.png` | Công việc về trạng thái Xong, hiện link tải kết quả |
| `08_thuat_ngu.png` | Thuật ngữ `Ironhold` máy tự học trong lượt dịch, `Shadow Realm` người dùng thêm và khoá |
| `ket_qua_khung.png` | Khung cắt từ video **trình duyệt tải về**: chữ Việt đủ dấu nằm đúng trên vệt mờ |

Video tải về: h264 1280×720, còn nguyên audio AAC, 12.04 s — đúng độ dài và độ phân
giải của bản gốc, chỉ qua một lần nén.

Ảnh smoke media V-7 (`smoke_*.png`) sinh bằng `test_pipeline.py --smoke`, không lưu
trong repo vì tái tạo được bất cứ lúc nào.
