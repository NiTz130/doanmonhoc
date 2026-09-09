# Hướng dẫn cho TV3 — Dịch, thuật ngữ và quản lý nhóm

Nhánh của bạn: **`feat/translate`**. Đọc [GIT.md](GIT.md) trước để cài Git và lấy code về.

## 1. Phần việc của bạn

| Tầng | File bạn sở hữu |
|---|---|
| Xử lý | `pipeline/translate.py` |
| API | `api/nhom.py` |
| Frontend | Trang quản lý nhóm và thuật ngữ |
| Kiểm thử | `tests_translate.py` |

Chỉ sửa bốn chỗ này. File của người khác có lỗi thì báo trong nhóm, đừng tự vá — hai người sửa cùng một file là lúc merge sinh xung đột.

## 2. Lấy code về

```bash
cd ~/Desktop
git clone https://github.com/NiTz130/doanmonhoc.git
cd doanmonhoc
git switch feat/translate
git config core.hooksPath .githooks
git config nhom.nhanh feat/translate
```

Hai dòng `git config` cuối bật khoá an toàn — máy sẽ từ chối commit khi bạn đứng nhầm nhánh. Chạy thiếu là tự tháo khoá.

Môi trường:

```bash
uv sync
cp .env.example .env      # rồi mở .env, điền DEEPSEEK_API_KEY
```

Chạy thử bộ kiểm thử — không cần mạng, không cần GPU:

```bash
.venv/Scripts/python.exe test_pipeline.py
```

Hiện phải ra **8 PASS, 1 FAIL**. FAIL duy nhất là `test_box_intervals_and_style` vì `pipeline/markbox.py` của TV4 chưa có. Đó không phải lỗi của bạn.

## 3. Phần của bạn đã xong tới đâu

**`pipeline/translate.py` đã viết xong ở G1.** Đừng viết lại từ đầu. Nó đã có:

- `dich(lines, glossary, goi, lo=400)` — chia lô 400 cue, kèm 5 dòng ngữ cảnh trước mỗi lô.
- Kiểm JSON tại biên: `lines` phải là object có đúng khoá `1..N`, giá trị chuỗi không rỗng, không có dòng trống phá SRT.
- Thiếu dòng thì gọi lại đúng dòng đó một lần; cả lô hỏng thì chia đôi tối đa hai tầng; vẫn hỏng thì giữ nguyên bản gốc và báo index.
- `tao_goi(key, model)` — dựng client DeepSeek, timeout 120 giây, tối đa 2 lần thử lại ở tầng vận chuyển, `max_tokens=16000`, JSON mode.
- `tests_translate.py` đã có `test_translation_validation_and_context`, đang PASS.

Việc còn lại của bạn nằm ở G2 trở đi.

## 4. Việc còn lại theo cổng

### G2 — kiểm phần dịch trên dữ liệu thật

Chưa cần viết code mới, cần bằng chứng:

- [ ] Phản hồi sai kiểu, phản hồi rỗng, `finish_reason` không phải `stop` — xác nhận không cue nào bị mất.
- [ ] Lỗi mạng và lỗi auth — xác nhận dừng hẳn video, **không** ghi bản dịch nửa vời rồi đánh dấu hoàn tất.
- [ ] Thuật ngữ truyền được giữa các lô, và giữa video này sang video sau trong cùng nhóm.
- [ ] Từ có `khoa = 1` không bị lượt dịch sau ghi đè.
- [ ] Đo chi phí thật trên một video ngắn. Chỉ chạy khi cả nhóm đã thống nhất tài khoản và ngân sách.

### G3 — `api/nhom.py`

Ba nhóm route, theo bảng ở [thiết kế §8](superpowers/specs/2026-09-09-video-dich-phu-de-design.md):

```
GET/POST  /api/nhom
GET/POST  /api/nhom/{ten}/thuat-ngu
GET/POST  /api/nhom/{ten}/hop
```

Dùng `APIRouter` riêng, không sửa `api/app.py` — file đó là của TV2, tách ra chính là để hai người không đụng nhau.

**Không gọi `pipeline/db.py` trực tiếp.** Bốn hàm sau đã có sẵn trong `pipeline/dieu_phoi.py`, route chỉ việc gọi:

```python
dieu_phoi.nhom_danh_sach(con)                          -> list[dict]
dieu_phoi.nhom_thuat_ngu(con, ten)                     -> dict[str, str]
dieu_phoi.nhom_dat_thuat_ngu(con, ten, goc, dich, khoa=False)
dieu_phoi.nhom_dat_hop(con, ten, hop, W, H)            -> dict   # tự validate hộp
```

`main.py` cũng gọi đúng bốn hàm này. Giữ như vậy thì CLI và web không bao giờ cho ra kết quả khác nhau.

### G4 — trang quản lý nhóm và thuật ngữ

Một màn: liệt kê nhóm, xem và sửa bảng thuật ngữ, khoá một bản dịch. Dựng được trên JSON giả trước khi backend xong.

### G5 — báo cáo

Chương dịch: cách chia lô, cách chặn lệch cue, ví dụ trước/sau, và bảng chi phí **đo được**. Không ghi số ước lượng thành kết quả.

## 5. Bốn ràng buộc không được phá

1. **`translate.py` không được biết gì về CSDL và về HTTP.** Glossary đi vào là một `dict`, từ mới đi ra là một `dict`. Ai ghi xuống SQLite là việc của `dieu_phoi.py`. Đây là lý do bạn test được mà không cần dựng DB.

2. **Không đổi chữ ký `dich(lines, glossary, goi, lo=400)`.** `pipeline/dieu_phoi.py` đang gọi nó và đọc `kq.ban`, `kq.thuat_ngu_moi`, `kq.giu_nguon`, `kq.token_vao`, `kq.token_ra`. Cần đổi thì báo nhóm trước khi merge — đây là hợp đồng, đổi một mình là làm gãy phần người khác.

3. **Mốc thời gian của cue không phụ thuộc phản hồi model.** Model chỉ trả nội dung từng dòng; timestamp lấy nguyên từ `sub_goc.srt`. Nối phụ đề thành một khối rồi tách lại theo dòng là nguồn lỗi phổ biến nhất của bài toán này.

4. **Không thêm thư viện.** Dependency đã chốt ở `pyproject.toml`. Không thêm framework test — cứ `assert` trần như file hiện có.

## 6. Đo chi phí ở đâu

Sau mỗi lượt dịch thật, số token được ghi vào bảng `nhat_ky`:

```sql
SELECT video_id, giay, token_vao, token_ra
FROM nhat_ky WHERE buoc = 'dich' AND ket_qua != 'loi';
```

Lượt chạy lại dùng cache thì `token_vao`/`token_ra` bằng 0 — vì thật sự không tốn gì. Lấy đúng những dòng khác 0 để lập bảng chi phí.

## 7. Khi nào phải hỏi nhóm

- Muốn đổi chữ ký hàm, tên route, hoặc hình dạng JSON trả về.
- Muốn sửa file không thuộc bốn chỗ ở §1.
- Muốn thêm dependency.
- Chạy dịch thật tốn tiền.

Kẹt thì báo ngay, chụp màn hình lệnh và lỗi. Đừng chạy lệnh lạ tìm trên mạng.
