# Hướng dẫn Git cho thành viên

Nhánh của bạn:

| Thành viên | Nhánh |
|---|---|
| TV1 | `feat/cli-db` |
| TV2 | `feat/asr` |
| TV3 | `feat/translate` |
| TV4 | `feat/render` |

Thay `feat/asr` bên dưới bằng nhánh của mình.

## Cài một lần

Tải Git tại https://git-scm.com/download/win, cài để mặc định. Mở **Git Bash**, khai báo tên:

```bash
git config --global user.name "Tên của bạn"
git config --global user.email "email-github@example.com"
```

## Lấy code về (một lần duy nhất)

```bash
cd ~/Desktop
git clone https://github.com/NiTz130/doanmonhoc.git
cd doanmonhoc
git switch feat/asr
git config core.hooksPath .githooks
git config nhom.nhanh feat/asr
```

Lần đầu `git` sẽ hỏi đăng nhập GitHub — chọn "Sign in with your browser".

Hai dòng `git config` cuối bật khoá an toàn: máy sẽ **từ chối** commit hoặc push nếu
bạn đang đứng nhầm ở `main` hay ở nhánh của người khác. Chạy thiếu hai dòng này là
tự tháo khoá — bắt buộc chạy đủ.

## Đã clone từ trước? Chạy một lần khối này

Nếu bạn clone repo trước khi có phần khoá an toàn, chạy đúng bốn dòng sau
(thay `feat/asr` bằng nhánh của mình):

```bash
cd ~/Desktop/doanmonhoc
git switch feat/asr
git pull origin main
git config core.hooksPath .githooks
git config nhom.nhanh feat/asr
```

Kiểm tra đã xong chưa — lệnh dưới phải in ra `feat/asr`:

```bash
git config nhom.nhanh
```

## Mỗi lần bắt đầu làm

```bash
cd ~/Desktop/doanmonhoc
git switch feat/asr
git pull
```

## Mỗi lần làm xong (lưu lên GitHub)

```bash
git add .
git commit -m "mô tả ngắn việc vừa làm"
git push
```

Lần push đầu tiên nếu báo lỗi `no upstream`, chạy:

```bash
git push -u origin feat/asr
```

## Lấy phần mới nhất của cả nhóm về nhánh mình

Làm việc này khi nhóm trưởng báo `main` có cập nhật:

```bash
git switch feat/asr
git pull origin main
git push
```

## Khi làm xong một phần, xin gộp vào main

Vào https://github.com/NiTz130/doanmonhoc → bấm **Pull requests** → **New pull request**
→ base = `main`, compare = nhánh của mình → **Create pull request** → ghi mô tả → báo người review.

## Ba lệnh cứu hộ

```bash
git status                  # đang ở nhánh nào, sửa file nào
git switch feat/asr         # về đúng nhánh của mình
git restore <tên-file>      # bỏ sửa đổi của một file, quay về như cũ
```

## Bốn điều tránh

- Không làm việc trực tiếp trên `main`, cũng không đụng nhánh của người khác. Máy đã chặn sẵn, nhưng vẫn `git status` xem mình đang ở đâu trước khi sửa.
- Nếu thấy dòng `DUNG LAI:` là bạn đang đứng nhầm nhánh — làm theo lệnh nó gợi ý, **đừng** thêm `--no-verify` để đi qua.
- Không commit `.env`, khóa API, thư mục `work/`, model hay video lớn.
- Không sửa file của người khác. Ranh giới file xem ở [PHAN_CONG.md](PHAN_CONG.md) §2.
- Kẹt thì báo nhóm ngay, chụp màn hình lệnh và lỗi — đừng tự chạy lệnh lạ tìm thấy trên mạng.
