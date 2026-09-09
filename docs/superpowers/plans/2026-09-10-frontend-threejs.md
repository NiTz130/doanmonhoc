# Kế hoạch thiết kế frontend Three.js

Ngày: 2026-09-10. Trạng thái: **Đã chọn hướng B — thiết kế chưa hoàn thiện, chưa triển khai**.

## 1. Mục tiêu và cơ sở

Nâng cấp giao diện web dịch phụ đề video Anh → Việt thành một không gian làm việc rõ ràng, có điểm nhấn 3D liên quan đến video và phụ đề. Người dùng vẫn hoàn thành được luồng tải video → theo dõi → chọn vùng mờ nếu cần → tải kết quả.

Cơ sở: [README](../../../README.md), mục 2 và 6; [thiết kế hiện có](../specs/2026-09-09-video-dich-phu-de-design.md), mục 8–11. Thư mục `web/` hiện có `index.html`, `style.css`, `app.js`. Plan dựa trên tài liệu và cấu trúc thư mục; cần đối chiếu handler, selector và test thực tế trước khi sửa mã.

Phạm vi gồm bốn màn hiện có: Tải lên, Tiến độ, Vùng làm mờ, Nhóm & thuật ngữ. Kết quả là trạng thái của công việc, không mở thêm một sản phẩm hoặc dashboard thống kê.

## 2. Ba hướng thiết kế để khám phá

Các hướng dưới đây là đề xuất bằng văn bản, chưa phải mockup đã duyệt.

| Hướng | Bố cục và cảm giác | Vai trò Three.js | Đánh đổi |
|---|---|---|---|
| A — Phòng dựng phim | Nền than ấm, chữ sáng, điểm nhấn hổ phách; vùng làm việc rộng, điều hướng gọn | Các khung phim xếp lớp, một dải phụ đề nổi nhẹ bên cạnh form tải lên | Hợp chủ đề video; cần kiểm soát tương phản màn tối |
| B — Bàn biên tập | Nền giấy sáng, chữ đậm, nhấn xanh lá trầm; ưu tiên form và bảng thuật ngữ | Mô hình các lớp video/phụ đề nhỏ trong phần giới thiệu | Dễ đọc khi làm việc lâu; hiệu ứng 3D ít nổi bật hơn |
| C — Luồng chuyển ngữ | Nền xám trung tính, nhấn xanh lam; bố cục theo các bước xử lý | Dải khung hình chuyển thành các lớp phụ đề, chuyển động ngắn khi đổi bước | Minh họa quy trình tốt; phải tránh làm người dùng hiểu chuyển động là tiến độ thật |

**Đề xuất A** vì phù hợp tác vụ video và buổi trình bày đồ án. Đây chưa phải lựa chọn thay người dùng.

Bước thiết kế đầu tiên: tạo ba bản mẫu màn Tải lên với cùng nội dung, cùng kích thước desktop/mobile, kèm ảnh chụp để so sánh. Áp dụng `huashu-design` cho phần tạo mẫu; người dùng chọn hướng trước khi hoàn thiện toàn bộ giao diện. Yêu cầu hiện tại chỉ là soạn plan nên chưa tạo các mẫu này.

## 3. Bố cục và hành vi từng màn

| Màn | Thiết kế dự kiến | Trạng thái bắt buộc |
|---|---|---|
| Tải lên | Tiêu đề ngắn; vùng chọn/kéo thả video; tên file; nhóm; tùy chọn hiện có; nút Bắt đầu. Khối 3D cạnh form trên desktop, thu gọn trên mobile | Chưa chọn file, đã chọn, đang gửi, lỗi xác thực, lỗi mạng; chống gửi trùng khi đang gửi |
| Tiến độ | Tên video, trạng thái chữ, bước hiện tại, thanh tiến độ, thông báo cần thao tác. Kết quả và nút tải xuống nằm cùng màn | `cho`, `dang_chay`, `cho_chon_khung`, `xong`, `suy_giam`, `loi`; giữ thông tin công việc khi lỗi polling |
| Vùng làm mờ | Khung ảnh lớn, dải 8 ảnh mẫu, vùng chọn dễ nhìn, hướng dẫn ngắn, gửi vùng và Bỏ qua. Có nhập tọa độ để dùng bằng bàn phím | Đang tải ảnh, chưa vẽ, vùng hợp lệ/không hợp lệ, đang gửi, lỗi; giữ hộp khi đổi ảnh |
| Nhóm & thuật ngữ | Chọn/tạo nhóm; bảng từ gốc, bản dịch và khóa; vùng thiết lập hộp mặc định. Mobile cho bảng cuộn trong vùng riêng | Nhóm rỗng, đang tải, đang lưu, lưu thành công/thất bại; lỗi lưu không làm mất nội dung đang sửa |

Điều hướng desktop đặt bên trái; mobile chuyển thành hàng điều hướng gọn có nhãn. Không thêm lịch sử công việc, sửa timeline phụ đề, đăng nhập hoặc nút hủy/retry khi backend chưa có hợp đồng tương ứng.

Các tùy chọn nâng cao phải có nhãn dễ hiểu và giữ giá trị/default hiện tại. Không dùng phần trăm giả hoặc ETA suy đoán. Trạng thái `suy_giam` cần thông báo còn dòng giữ nguyên ngôn ngữ nguồn, không trình bày như thành công hoàn toàn.

## 4. Phạm vi Three.js và kỹ thuật đề xuất

- Giữ HTML/CSS/JavaScript thuần cùng cơ chế phục vụ frontend hiện tại. Three.js là phần bổ sung cho cảnh minh họa; form, bảng, thông báo và vùng chọn vẫn dùng DOM/canvas 2D.
- Một canvas 3D ở màn Tải lên, dùng hình học đơn giản để tạo khung phim và lớp phụ đề. Chuyển động chậm, biên độ nhỏ, không chiếm con trỏ hoặc che nút bấm. Chữ quan trọng luôn ở DOM.
- Đề xuất module riêng `web/scene.js`, khởi tạo sau khi UI chính đã dùng được. Lỗi tải module hoặc khởi tạo WebGL chỉ chuyển cảnh sang hình tĩnh, không làm ngừng `app.js`.
- Đề xuất phân phối module Three.js tại `web/vendor/three/`, khóa phiên bản cụ thể và giữ license. Khi triển khai phải kiểm tra các module phụ thuộc của bản chọn. Không tải thư viện lúc chạy từ CDN để ứng dụng local ít phụ thuộc mạng. Không mặc định thêm React, bundler, GSAP, model 3D hoặc texture ngoài.
- Khi ẩn màn, đổi tab hoặc backend xử lý video: dừng chuyển động 3D để giảm cạnh tranh tài nguyên. Khi `prefers-reduced-motion` bật: dùng hình tĩnh; có điều khiển dừng hiệu ứng chuyển động.
- Khi mất WebGL context hoặc thiết bị không hỗ trợ: hiển thị fallback 2D cùng kích thước, không để trống hoặc nhảy bố cục.
- Khi resize: đồng bộ camera và drawing buffer với kích thước canvas; giới hạn pixel ratio đề xuất ở 1.5. Đây là cấu hình cần đo trên máy demo.
- Khi tháo cảnh: ngừng animation, gỡ listener/observer, giải phóng geometry/material/texture và renderer. Không tạo thêm renderer mỗi lần đổi màn.

Three.js hỗ trợ cách tích hợp ES module; các import cần đồng nhất phiên bản theo [hướng dẫn cài đặt](https://threejs.org/manual/en/installation.html). Việc đồng bộ canvas/camera tham khảo [responsive design](https://threejs.org/manual/en/responsive.html); tài nguyên GPU cần giải phóng rõ ràng theo [cleanup](https://threejs.org/manual/en/cleanup.html).

## 5. Các hợp đồng phải giữ

1. Giữ endpoint, payload, default và validation của backend; không sửa API/schema/pipeline để phục vụ hiệu ứng.
2. Giữ polling 1.5 giây theo tài liệu hiện có; đảm bảo không tạo nhiều vòng polling khi đổi màn. Lỗi mạng hiển thị trạng thái kết nối, không tự tạo công việc mới.
3. Hộp làm mờ dùng tọa độ chuẩn hóa 0–1. Khi ảnh có khoảng đệm do giữ tỷ lệ, tính vùng theo phần ảnh thực, không theo toàn container. Resize không đổi vùng đã chọn.
4. Chuyển qua các khung mẫu vẫn giữ hộp. Bỏ qua vùng làm mờ không xóa hộp mặc định của nhóm.
5. Thuật ngữ khóa vẫn giữ nguyên ý nghĩa; lỗi lưu không được báo thành công.
6. Một video nặng mỗi lúc; không bổ sung xử lý song song, WebSocket hoặc tính năng cần API mới.
7. Không đưa nội dung video hay dữ liệu thuật ngữ lên dịch vụ hình ảnh/analytics. Dùng dữ liệu mẫu được ghi nhãn khi thiết kế.

## 6. Các bước thực hiện sau khi triển khai được yêu cầu

| Bước | Đầu ra và vị trí dự kiến | Phụ thuộc | Kiểm tra đạt |
|---|---|---|---|
| 1. Đối chiếu hiện trạng | Đọc toàn bộ `web/`, handler API liên quan và `tests_api.py`; ghi selector, payload, default, trạng thái cần giữ trong plan này | Không | Mỗi thao tác ở mục 3 được nối với handler thật; khác biệt giữa code và tài liệu được làm rõ |
| 2. Khám phá ba hướng | Ba mẫu Tải lên và ảnh desktop/mobile trong thư mục tài liệu thiết kế | Bước 1 | Cùng nội dung, khác biệt rõ về bố cục/hình ảnh; người dùng chọn một hướng |
| 3. Chốt bộ quy tắc giao diện | Màu, chữ hỗ trợ tiếng Việt, spacing, focus, nút/form/bảng và bố cục bốn màn theo hướng đã chọn | Bước 2 | Kiểm tra đủ trạng thái thường, trống, tải và lỗi; đọc rõ chữ Việt |
| 4. Xây giao diện 2D | `web/index.html`, `web/style.css`; chỉ sửa nối sự kiện cần thiết trong `web/app.js` | Bước 3 | Bốn luồng hoạt động bằng chuột, bàn phím và cảm ứng khi chưa có Three.js |
| 5. Tích hợp cảnh 3D | `web/scene.js`, thư viện có phiên bản/license, điểm khởi tạo trong frontend | Bước 4 | Cảnh đúng mẫu; fallback dùng được; không có renderer hoặc animation loop trùng |
| 6. Kiểm tra và bàn giao | Kiểm tra hồi quy phù hợp; ảnh và kết quả theo convention `docs/ketqua/` | Bước 5 | Đạt checklist mục 7, ghi rõ những kiểm tra chưa chạy |

Không đổi framework hoặc thêm dependency ngoài Three.js nếu chưa có nhu cầu được chứng minh. Phương án phân phối thư viện và hướng hình ảnh còn là đề xuất; chốt trước bước triển khai phụ thuộc.

## 7. Tiêu chí nghiệm thu

- **Luồng chính:** chọn video, gửi một lần, xem các trạng thái, chọn/bỏ qua hộp và tải kết quả. Dùng backend giả lập cho nhánh trạng thái; không gọi dịch vụ dịch trả phí chỉ để thử UI.
- **Vùng chọn:** kiểm tra ảnh ngang/dọc ở 720p/1080p, kéo mọi hướng, kéo ra ngoài ảnh, đổi ảnh và resize; tọa độ gửi khớp vùng nhìn thấy. Nếu sửa logic tọa độ, để lại một kiểm tra hồi quy chạy được.
- **Lỗi:** thử upload bị từ chối, polling mất mạng, ảnh mẫu tải lỗi, lưu thuật ngữ thất bại, `suy_giam`, lỗi WebGL và module 3D không tải được; thông báo rõ và giữ dữ liệu nhập liên quan.
- **Responsive:** kiểm tra viewport 360, 768 và 1440 px; không có cuộn ngang toàn trang, nút chính không bị che, bảng thuật ngữ cuộn trong vùng của nó.
- **Accessibility:** nhãn input đầy đủ, focus nhìn thấy, điều hướng bàn phím, thông báo trạng thái không chỉ dựa vào màu; tương phản chữ thường tối thiểu 4.5:1; vùng chạm đề xuất ít nhất 44×44 px.
- **Chuyển động:** reduced motion và nút dừng hoạt động; tab ẩn/màn không chứa cảnh không chạy animation. Tắt WebGL vẫn hoàn thành các tác vụ 2D.
- **Hiệu năng:** mục tiêu cảnh đạt ít nhất 30 FPS trên máy demo được ghi cấu hình; không dùng số này như kết quả đã đo. Đổi màn 20 lần không tăng số canvas/loop; kiểm tra tài nguyên không tăng tích lũy sau các lần tháo/tạo cảnh.
- **Hồi quy:** chạy `.venv/Scripts/python.exe test_pipeline.py` khi triển khai. Test này bảo vệ backend, không thay thế kiểm tra trình duyệt. Chỉ chạy media smoke khi cần xác minh đường xuất video và môi trường có ffmpeg.

## 8. Hoàn tất kế hoạch

Đã xác định phạm vi, ba hướng khám phá, bố cục bốn màn, ranh giới Three.js, trình tự công việc và nghiệm thu. Người dùng đã chọn hướng B theo quyết định ở mục 9. Chưa khóa phiên bản/phân phối Three.js, chưa hoàn thiện mockup, chưa sửa frontend và chưa chạy test. Không có commit, push hoặc triển khai.

## 9. Quyết định hướng thiết kế

- Người dùng xác nhận trong hội thoại: **“Tôi chọn B”**. Quyết định này thay thế đề xuất A và trạng thái chưa chọn hướng ở các mục trước.
- Hướng được chọn: **B — Bàn biên tập**. Nền giấy sáng, chữ đậm, điểm nhấn xanh lá trầm; ưu tiên form, bảng thuật ngữ và khả năng đọc lâu. Cảnh minh họa các lớp video/phụ đề nhỏ, hỗ trợ phần giới thiệu.
- File thiết kế: https://www.figma.com/design/xzkdWQlyYeosz1WWBatKIO. Khung B desktop: `2:4`; mobile: `2:5`.
- Tại thời điểm chọn, Figma mới có sáu khung A/B/C với điều hướng và tiêu đề. Chưa hoàn thiện form, cảnh minh họa hoặc chụp ảnh kiểm tra vì công cụ báo hết hạn mức MCP Starter. Không coi lựa chọn hướng là nghiệm thu các mockup hoàn chỉnh.
- Tiếp tục hoàn thiện bốn màn theo B khi công cụ Figma khả dụng; không cần hỏi lại lựa chọn hướng trong cùng phạm vi.

## 10. Triển khai trực tiếp được chấp thuận

Người dùng đồng ý tiếp tục phương án miễn phí bằng câu ‘được’. Đã triển khai hướng B trong web/, dùng Three.js 0.180.0 cục bộ kèm MIT và font cục bộ kèm OFL. Mục này thay thế trạng thái chưa triển khai ở mục 8 và việc chờ Figma ở mục 9. Kết quả và giới hạn kiểm chứng: [B-frontend](../../ketqua/B-frontend.md). Không commit, push hoặc triển khai công khai.
