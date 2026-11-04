# Hướng dẫn Git

Nhánh tích hợp là **`main`**. Kiểm tra nhánh hiện có bằng `git branch -a`; danh sách thay đổi theo máy và thời điểm.

Ghi chú lịch sử của nhóm: bốn nhánh `feat/*` cũ đã được gộp và xóa. Ghi chú này không thay thế việc kiểm tra lịch sử trước khi xóa một nhánh mới.

Có hai cách làm việc. Chọn một, cả nhóm làm giống nhau.

## Cài một lần

Tải Git tại https://git-scm.com/download/win, cài để mặc định. Mở **Git Bash**:

```bash
git config --global user.name "Tên của bạn"
git config --global user.email "email-github@example.com"
```

## Lấy code về

```bash
cd ~/Desktop
git clone https://github.com/NiTz130/doanmonhoc.git
cd doanmonhoc
git config core.hooksPath .githooks
```

Lần đầu `git` sẽ hỏi đăng nhập GitHub — chọn "Sign in with your browser".

Môi trường: xem [README §1](../README.md).

---

## Cách A — làm thẳng trên `main` (mặc định hiện tại)

Dùng khi chỉ một người viết code, hoặc nhóm chia việc theo thời gian chứ không song song.

```bash
git pull                       # truoc khi bat dau
# ... sua code ...
git add .
git commit -m "mô tả ngắn việc vừa làm"
git push
```

Ai cũng `git pull` trước khi sửa. Hai người sửa cùng lúc thì người sau `git pull --rebase`
rồi giải quyết xung đột.

## Cách B — mỗi người một nhánh (khi các thành viên làm song song)

Chỉ dùng khi thật sự có nhiều người viết code cùng lúc. Ranh giới file xem
[PHAN_CONG.md §2](PHAN_CONG.md).

Người nào cần thì tự tạo nhánh của mình từ `main`:

```bash
git switch main
git pull
git switch -c feat/asr             # đổi tên theo phần việc của bạn
git push -u origin feat/asr
git config nhom.nhanh feat/asr     # BẬT KHOÁ AN TOÀN
```

Dòng `git config nhom.nhanh` cuối là thứ bật khoá: sau đó máy **từ chối** commit hoặc
push sai nhánh: `pre-commit` kiểm tra nhánh hiện tại; `pre-push` kiểm tra nhánh đích trên remote, chặn `main` và nhánh khác nhánh đã khai báo. Không khai báo thì hook không
cản gì — đó cũng là lý do Cách A chạy được.

Tên nhánh gợi ý: `feat/nen-tang` (TV1), `feat/asr-api-box` (TV2), `feat/translate-render` (TV3). Phần frontend dùng `feat/web-*` theo màn.

Làm xong một phần thì mở Pull Request: vào https://github.com/NiTz130/doanmonhoc →
**Pull requests** → **New pull request** → base = `main`, compare = nhánh của mình →
ghi mô tả hành vi, kết quả kiểm thử, hạn chế và ảnh nếu đổi giao diện → báo người review. Vòng review xem [PHAN_CONG.md](PHAN_CONG.md).

Lấy phần mới của nhóm về nhánh mình:

```bash
git switch feat/asr
git pull origin main
```

Chỉ khi nhóm chuyển hẳn về làm tuần tự mới bỏ cấu hình `nhom.nhanh`; không tắt cấu hình hoặc hook để vượt lỗi nhầm nhánh. Cách A không phải ngoại lệ để push thẳng `main` khi đang dùng Cách B.

---

## Ba lệnh cứu hộ

```bash
git status                  # dang o nhanh nao, sua file nao
git switch main             # ve main
git restore <tên-file>      # bo sua doi cua mot file, quay ve nhu cu
```

## Bốn điều tránh

- Thấy dòng `DUNG LAI:` là bạn đang đứng nhầm nhánh — làm theo lệnh nó gợi ý,
  **đừng** thêm `--no-verify` để đi qua.
- Không commit file bí mật (như `.env`), thư mục `work/`, model hay video lớn. `.gitignore` đã
  chặn sẵn nhưng vẫn nên `git status` xem trước khi commit.
- Ở Cách B: không sửa file của người khác. Đụng cùng file là lúc merge sinh xung đột.
- Kẹt thì báo nhóm ngay, chụp màn hình lệnh và lỗi — đừng tự chạy lệnh lạ tìm trên mạng.
