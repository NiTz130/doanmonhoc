# Lời cảm ơn · Lời mở đầu · Kết luận

> **Đây là bản nháp.** Mọi chỗ trong `[ngoặc vuông]` cần nhóm điền. Văn phong nên được sửa lại cho giống
> giọng của nhóm — một bài báo cáo đọc lên phải ra tiếng người viết nó, không phải tiếng của công cụ.
> Số liệu trong bản nháp này đều lấy từ [BAO_CAO_TONG_HOP.md](BAO_CAO_TONG_HOP.md); nếu sửa số ở đây thì
> phải đối chiếu lại bên đó.

---

## LỜI CẢM ƠN

Nhóm chúng em xin gửi lời cảm ơn chân thành đến thầy/cô **[Tên giảng viên hướng dẫn]**, giảng viên học phần
**[Tên học phần]**, đã hướng dẫn và góp ý cho nhóm trong suốt quá trình thực hiện đồ án. Những nhận xét của
thầy/cô ở các buổi báo cáo tiến độ đã giúp nhóm nhìn ra nhiều vấn đề mà bản thân nhóm không tự thấy được.

Chúng em cũng xin cảm ơn quý thầy cô **[Khoa/Bộ môn]**, **[Tên trường]** đã trang bị cho chúng em nền tảng
kiến thức để có thể bắt tay vào một đồ án có cả phần xử lý đa phương tiện, phần dịch máy lẫn phần ứng dụng
web.

Cảm ơn các bạn trong lớp đã dành thời gian dùng thử sản phẩm và góp ý về giao diện — những góp ý đó dẫn tới
không ít thay đổi trong bản cuối.

Đồ án được thực hiện trong thời gian và điều kiện có hạn của sinh viên, nên chắc chắn còn nhiều thiếu sót.
Nhóm đã cố gắng ghi lại trung thực cả những phần chưa hoàn thành lẫn những lỗi từng mắc phải, và rất mong
nhận được góp ý của quý thầy cô để hoàn thiện hơn.

Chúng em xin chân thành cảm ơn.

**[Địa điểm], ngày [__] tháng [__] năm [____]**

Nhóm sinh viên thực hiện

**[Họ tên TV1]** — [MSSV] · **[Họ tên TV2]** — [MSSV] · **[Họ tên TV3]** — [MSSV] · **[Họ tên TV4]** — [MSSV]

---

## LỜI MỞ ĐẦU

### 1. Lý do chọn đề tài

Phần lớn nội dung học thuật, kỹ thuật và giải trí có giá trị trên Internet hiện nay là tiếng Anh. Với người
xem Việt Nam, rào cản không nằm ở chỗ tìm nội dung mà ở chỗ hiểu được nội dung ấy. Phụ đề tiếng Việt vì thế
là nhu cầu thường trực, và việc tạo phụ đề bằng tay cho một tập phim dài hai tiếng là công việc tốn nhiều giờ
đồng hồ.

Nhóm nhận thấy một tình huống cụ thể hơn và khó hơn: **video đã có sẵn phụ đề tiếng Anh cháy cứng vào hình**.
Đây là trường hợp rất phổ biến với phim, video bài giảng và nội dung tải về từ các nền tảng chia sẻ. Khi chữ
đã trở thành một phần của khung hình, việc thêm phụ đề tiếng Việt sẽ tạo ra hai dòng chữ chồng lên nhau, còn
việc gỡ chữ cũ ra thì không có lời giải hoàn hảo — pixel bị chữ che đi thì không còn để phục hồi.

Từ quan sát đó, nhóm chọn đề tài **xây dựng một ứng dụng web dịch phụ đề video từ tiếng Anh sang tiếng Việt,
đồng thời xử lý được phần phụ đề cứng có sẵn trong hình**.

### 2. Khảo sát các hệ thống tương tự

Trước khi bắt tay vào thiết kế, nhóm khảo sát **bốn hệ thống đang hoạt động trên thị trường**, chia làm hai
nhóm: công cụ tạo và dịch phụ đề (Subtitle Edit, VEED.IO, Kapwing) và công cụ xoá phụ đề cứng
(GhostCut/Media.io). Dữ liệu lấy từ trang chủ và trang giá chính thức, truy cập ngày **16/09/2026**, có ảnh
chụp màn hình làm bằng chứng lưu tại `docs/khaosat/`.

Bốn nhận xét rút ra:

**Một là, không công cụ nào làm cả hai việc trong một lượt.** Nhóm công cụ dịch phụ đề không xử lý phụ đề
cứng; nhóm công cụ xoá phụ đề cứng thì không dịch. Người dùng cần cả hai buộc phải chạy qua hai phần mềm,
nghĩa là **video bị nén lại hai lần** và mất chất lượng hai lần.

**Hai là, không công cụ nào giữ thuật ngữ nhất quán giữa các tập.** Với một bộ phim nhiều tập, tên riêng được
dịch ở tập đầu không được nhớ sang tập sau; người dùng phải tự dò và sửa tay.

**Ba là, các công cụ web đều yêu cầu tải video lên máy chủ của họ.** Với video chưa phát hành hoặc có bản
quyền, đây là rào cản thật. Chi phí cũng đáng kể: chức năng dịch của VEED chỉ có từ gói Pro 21 USD mỗi người
mỗi tháng, còn gói miễn phí của Kapwing giới hạn 10 phút phụ đề, video tối đa 4 phút, chất lượng 720p và có
dấu chìm.

**Bốn là, xoá phụ đề cứng không có lời giải hoàn hảo.** Các công cụ dùng AI để dựng lại nền thường để lại vệt
nhoè. Nhóm chọn cách trung thực hơn: **làm mờ vùng đó rồi đặt phụ đề tiếng Việt đè lên**, che gần hết vệt cũ
mà không giả vờ phục hồi được thứ không còn.

### 3. Mục tiêu của đề tài

Từ khoảng trống tìm được, nhóm đặt mục tiêu xây dựng một ứng dụng web **chạy cục bộ trên máy người dùng**,
làm được ba việc mà không công cụ khảo sát nào làm đủ:

1. **Dịch phụ đề Anh → Việt** có tận dụng phụ đề sẵn có, chỉ nhận dạng bằng Whisper khi không có phụ đề.
2. **Làm mờ vùng phụ đề cứng và cháy phụ đề tiếng Việt vào hình trong một lần nén duy nhất**, giữ nguyên âm
   thanh gốc.
3. **Giữ thuật ngữ nhất quán giữa các tập** của cùng một bộ phim bằng một bảng thuật ngữ theo nhóm.

Vì ứng dụng chạy cục bộ nên video **không rời khỏi máy người dùng**; chỉ phần văn bản phụ đề được gửi đi
dịch, và người dùng chỉ trả tiền cho lượng API thật sự dùng.

### 4. Phạm vi

**Trong phạm vi:** ứng dụng web bốn màn (tải lên, theo dõi tiến độ, khoanh vùng làm mờ, quản lý nhóm và thuật
ngữ); API HTTP; pipeline xử lý dùng chung cho cả web lẫn công cụ dòng lệnh nội bộ; cơ sở dữ liệu SQLite lưu
nhóm, thuật ngữ, nhật ký và trạng thái công việc; cơ chế chạy lại an toàn khi bị ngắt giữa chừng.

**Ngoài phạm vi, có chủ ý:** lồng tiếng bằng giọng nói tổng hợp; tự động dò vùng chữ bằng OCR (người dùng tự
khoanh); giao diện desktop; vùng mờ tự bám theo cảnh; đăng nhập và phân quyền; hàng đợi tác vụ ngoài; triển
khai lên máy chủ; xử lý nhiều video song song.

### 5. Phương pháp thực hiện

Nhóm chia sản phẩm làm hai giai đoạn: **backend và pipeline xử lý làm trước, giao diện web làm sau**. Bốn
thành viên mỗi người phụ trách một lĩnh vực xuyên suốt cả ba tầng — module xử lý, route API và màn hình
tương ứng — để ranh giới file không chồng lên nhau mà cũng không ai phải học lại phần của người khác.

Toàn bộ mã được kiểm bằng **bốn tầng kiểm thử**: kiểm đơn vị và tích hợp chạy ngoại tuyến, kiểm media với
ffmpeg thật, kiểm giao diện bằng trình duyệt thật, và kiểm ranh giới runtime với máy chủ thật. Kết quả và
bằng chứng được ghi lại đầy đủ để có thể kiểm chứng lại.

### 6. Bố cục báo cáo

- **Chương 1** — Tổng quan: bối cảnh, khảo sát hệ thống tương tự, mục tiêu và phạm vi.
- **Chương 2** — Phân tích yêu cầu: yêu cầu chức năng, phi chức năng, sơ đồ use case.
- **Chương 3** — Thiết kế hệ thống: kiến trúc, module, cơ sở dữ liệu, luồng xử lý dữ liệu.
- **Chương 4** — Cài đặt: các thuật toán và xử lý quan trọng, đặc tả API.
- **Chương 5** — Kiểm thử và đánh giá: kịch bản kiểm thử, kết quả đo, các lỗi đã phát hiện.
- **Chương 6** — Kết luận và hướng phát triển.

---

## KẾT LUẬN

### 1. Kết quả đạt được

Nhóm đã hoàn thành một ứng dụng web chạy được đầy đủ luồng đã đặt ra: người dùng tải video lên trình duyệt,
theo dõi tiến độ, khoanh vùng phụ đề cứng trên khung hình thật, và tải về chính video đó với phụ đề tiếng
Việt cháy vào hình cùng vùng phụ đề cũ đã được làm mờ — **qua đúng một lần nén**, âm thanh giữ nguyên.

Về khối lượng, sản phẩm gồm khoảng **3 100 dòng mã** chia cho tầng xử lý, tầng API và giao diện, cùng khoảng
**2 300 dòng mã kiểm thử**. Hệ thống cung cấp **12 thao tác API** trên 9 đường dẫn và **5 bảng** cơ sở dữ
liệu. Mười bảy chức năng đặt ra ban đầu đều đã hiện thực xong.

Về kiểm chứng, bốn tầng kiểm thử đều đạt: **34/34** kiểm thử ngoại tuyến chạy trong **7,8 giây**; kiểm media
với ffmpeg thật, kiểm giao diện với trình duyệt thật và kiểm ranh giới runtime với máy chủ thật đều đạt.

Một số kết quả đo đáng chú ý:

- **Nhận dạng** chạy khoảng **0,4 lần** thời lượng video trên GPU và khoảng **2,2 lần** trên CPU.
- **Kết xuất** chỉ tốn khoảng **0,03 lần** thời lượng video.
- **Cơ chế chạy lại** rút bước nhận dạng từ hàng chục giây xuống dưới 0,2 giây — nhanh hơn khoảng **150 đến
  270 lần** — và bước dịch xuống **0 giây, 0 token**, tức không tốn thêm tiền API.

### 2. Những đóng góp chính

**Một là, xử lý cả dịch lẫn che phụ đề cứng trong một lần nén.** Đây là khoảng trống rõ nhất tìm được khi
khảo sát. Việc ghép `crop → gblur → overlay → subtitles` vào cùng một chuỗi lọc của ffmpeg cho phép làm hai
việc mà chỉ mã hoá lại một lần.

**Hai là, đặt bước khoanh vùng trước bước dịch** dù xét về dữ liệu thì nó không cần đứng trước. Đây là bước
duy nhất cần con người, nên đặt sớm khiến thời gian chờ của máy và của người chồng lên nhau, và người bỏ dở ở
màn khoanh vùng **không tốn một đồng tiền API nào**.

**Ba là, cơ chế chạy lại dựa trên chữ ký nội dung.** Mỗi bước ghi ra một tệp trung gian kèm chữ ký gồm phiên
bản bước, mã băm nội dung của thứ nó phụ thuộc, và các tham số ảnh hưởng tới kết quả. Đổi một tuỳ chọn thì
chỉ bước bị ảnh hưởng chạy lại. Bản kê chữ ký luôn được ghi **sau** tệp sản phẩm, nên một lần ngắt giữa chừng
chỉ khiến hệ thống tính lại, chứ không bao giờ báo xong nhầm.

**Bốn là, bảng thuật ngữ theo nhóm.** Tên riêng được dịch ở tập đầu sẽ được dùng lại nguyên vẹn ở các tập
sau, và người dùng có thể khoá một bản dịch để máy không tự đổi.

### 3. Hạn chế

Nhóm cho rằng việc nêu rõ hạn chế cũng quan trọng như nêu kết quả.

**Chất lượng nhận dạng phụ thuộc vào loại video.** Với video thoại nói bình thường, phụ đề nhận được phủ gần
như trọn thời lượng. Nhưng với video có nhạc nền, Whisper nghe nhầm tên riêng và cắt vụn lời hát. Cờ tách
giọng hát đã được cài đặt nhưng **chưa chạy được lần nào** vì thư viện phụ trợ chưa cài.

**Chi phí dịch chưa đo được trên phim dài.** Mọi số liệu hiện có đều từ video dưới ba phút. Mô hình dịch sinh
ra lượng token đầu ra gấp 12 đến 25 lần token đầu vào và dao động mạnh giữa các lượt chạy giống hệt nhau, nên
không thể ước lượng chi phí cho phim hai tiếng bằng phép nhân đơn giản.

**Một số thao tác quản lý còn thiếu.** Hiện chưa có đường nào để xoá một thuật ngữ gõ nhầm, xoá một nhóm, xem
lại lịch sử công việc hay huỷ một công việc đang chạy.

**Việc làm mờ không phục hồi được hình.** Đây là giới hạn của bài toán chứ không phải của cách làm: phần hình
bị chữ che đi thì không còn để lấy lại.

### 4. Hướng phát triển

Nhóm xếp các việc tiếp theo theo tỉ lệ giá trị trên chi phí:

**Trước mắt:** bổ sung tích hợp liên tục để bộ kiểm thử 7,8 giây được chạy tự động; thêm đường tải riêng tệp
phụ đề, vì tệp đã có sẵn mà chưa có cách lấy; dọn thư mục tạm khi công việc kết thúc.

**Tiếp theo:** cho phép **sửa bản dịch ngay trên web** — đây là việc có giá trị cao nhất, vì phần lõi đã hỗ
trợ sẵn việc giữ bản sửa tay, chỉ còn thiếu màn soạn thảo; thêm trang lịch sử công việc; bổ sung thao tác xoá.

**Cần đo trước khi quyết:** chạy thử tách giọng hát để biết nó có thật sự cứu được nhận dạng trên nhạc không;
đo trên một bộ phim dài thật để có bảng chi phí đáng tin.

Nhóm chủ trương **không** mở rộng theo hướng thêm hàng đợi phân tán, WebSocket hay hệ quản trị đối tượng.
Với một ứng dụng chạy cục bộ, mỗi lần một video, những thứ đó chỉ thêm một tầng phải vận hành và một tầng
phải kiểm mà không giải quyết vấn đề nào đang có thật.

### 5. Bài học rút ra

**Con số trong thiết kế phải được đo lại khi chạm vào mã.** Kích thước lô dịch và số khung hình mẫu đều hợp
lý trên giấy và đều sai khi gặp thực tế; cả hai được sửa vì đo được, không phải vì cảm tính.

**Sai thầm lặng đắt hơn sai ồn ào.** Lỗi khiến nhóm mất nhiều công nhất là lỗi không ném ngoại lệ, không làm
kiểm thử đỏ, và chỉ lộ ra khi có người mở video ra xem: bộ lọc khoảng lặng nuốt mất chín phần mười nội dung
mà hệ thống vẫn báo hoàn thành. Từ đó nhóm rút ra rằng với bước nào có thể hỏng âm thầm thì phải tự nghĩ ra
một đại lượng để đo tính hợp lý của kết quả.

**Một phép kiểm chỉ có giá trị khi nó đi đúng con đường người dùng đi.** Có lần nhóm kết luận một nút bấm
hoạt động bình thường sau khi tự can thiệp để nó hiện ra rồi chụp ảnh — việc đó chỉ chứng minh nút vẽ được,
không chứng minh người dùng có bao giờ gặp nó. Lượt soát sau cho thấy nút ấy chưa bao giờ hiển thị.
