# Kế hoạch sửa logic vận hành — Claude Opus 5 thực thi, GPT‑5.6 Luna nghiệm thu

## Phần 1. Executor in codebase — Anthropic Claude Opus 5

### 1. Plan Metadata

- **Plan ID:** `logic-van-hanh-2026-09-16`; **Version:** 1.
- **Status:** `BLOCKED` riêng quyết định `ES-2` về nghĩa của vùng riêng. Các phần độc lập được chỉ rõ bên dưới; đây không phải lệnh bắt đầu triển khai.
- **Mode / Tier:** `DIRECT-PLAN`, Tier 2: contract HTTP, artifact đã lưu và bàn giao sang agent/session khác.
- **Planner:** Astra. **Executor mã sản phẩm:** Anthropic Claude Opus 5. **Validation lead:** GPT‑5.6 Luna, Ultra theo chỉ dẫn global.
- **Base revision:** `d248c7bc89f436286aaa772c73dd1e9c5b1b3201`; branch lúc lập plan: `vung-mo-nhieu-cue`.
- **Dirty state ban đầu:** `?? AGENTS.md`, `?? CLAUDE.md`; không có diff tracked. Không xóa, sửa, stage hoặc commit hai file này theo plan này.
- SHA256 `AGENTS.md`: `E83CD3AB1350FBF764F0E602A051FAC59BB34DAF20BB6932179840883A7F4DDE`.
- SHA256 `CLAUDE.md`: `D18F5218027E229C1744A5EA8C0A619568684B2533733D671E99AF99834594DE`.
- **Ranh giới phiên hiện tại:** chỉ lập plan. Chưa sửa source/test, chưa chạy CI, chưa commit/push, chưa gọi ASR hoặc dịch thật.
- **Target executor profile:** triển khai theo contract đã chốt; được chọn mechanics nhỏ trong MD, không tự thay product/API/schema/cache policy. Không đổi sang model khác mà không báo rõ.
- Các số dòng tham chiếu là ở base này; khi revision thay đổi, đối chiếu symbol, không sửa máy móc theo số dòng.

### 2. Context & Scope

#### 2.1. Bằng chứng đầu vào

Audit ở lượt trước trong cùng hội thoại đã có các kết quả sau. Đây là baseline đã quan sát, không phải kết quả sau sửa:

| ID | Lỗi / bằng chứng | Điểm mã nguồn |
| --- | --- | --- |
| F-1 | 40 request GET nhóm, 8 luồng: 35 `sqlite3.ProgrammingError` vì khác thread; tái hiện thêm trong subprocess cô lập, exit probe 0 | `pipeline/db.py:54`, `api/viec.py:25` |
| F-2 | Tại câu có vùng riêng phía trên, cả vùng chung phía dưới và vùng riêng cùng active. UI nói chỉ các câu chưa có vùng riêng dùng vùng chung | `web/app.js:225`, `web/app.js:442`, `pipeline/dieu_phoi.py:189` |
| F-3 | Hai upload cùng byte tạo hai work directory; upload lại không có callable dịch báo thiếu khóa dù lần trước đã dịch xong | `api/app.py:75`, `api/app.py:107`, `pipeline/srt.py:115` |
| F-4 | `force_asr=True`: trước chọn vùng ASR=1, gửi vùng xong ASR=2 | `api/viec.py:41`, `pipeline/dieu_phoi.py:128` |
| F-5 | Thay bộ cue A/B trên cùng video vẫn dùng vùng gắn index cũ; vùng dành cho A áp sang B | `pipeline/dieu_phoi.py:202`, chữ ký ở dòng 211 |
| F-6 | Giả lập mất `_HO_SO` nhưng DB còn: GET vẫn `cho_chon_khung`; POST vùng ném `KeyError` | `api/viec.py:43`, `api/app.py:123`, `api/app.py:153` |

Baseline kiểm tra: `test_pipeline.py` **17/17 PASS**; Playwright hiện có **PASS**, dùng API giả và screenshot ở thư mục tạm. Hai kết quả không phủ hết sáu lỗi. Đặc biệt `test_pipeline.py:test_vung_mo_gan_tung_cau_thoai` và `test/frontend.cjs` đang khẳng định hành vi cộng vùng.

#### 2.2. Quyết định đã có hiệu lực

**DEC-1 — người dùng chốt trong hội thoại ngày 2026-09-16:**

> Tự nhận diện theo nội dung video + nhóm; upload lại vẫn tạo công việc mới nhưng dùng lại cache phù hợp. Giữ nguyên dữ liệu cũ, không tự di chuyển/xóa.

Phạm vi: upload web mới sau bản sửa; nhận diện tài nguyên xử lý khác với ID công việc. Không suy ra quyền hợp nhất DB, đổi cache CLI, quét/di chuyển artifact cũ hoặc dùng chung bản dịch giữa các nhóm.

#### 2.3. In scope

- F-1 đến F-6, test hồi quy, kiểm tra runtime cô lập và README liên quan.
- Các race phát sinh trực tiếp khi nhiều CID dùng chung một work directory: admission, lock, snapshot lúc chờ vùng và output từng CID.
- Giữ endpoint/CLI hiện tại; chỉ mở rộng nội bộ khi cần để phân biệt lượt chạy mới với tiếp tục lượt đang chờ.
- Chuỗi nghiệm thu đầy đủ ở Phần 2, có checkpoint CI và Commit trung thực theo quyền/cấu hình thực tế.

#### 2.4. Out of scope

- OCR, TTS, UI redesign, queue ngoài, Redis/Celery, ORM, WebSocket, đăng nhập, nhiều backend worker.
- Tự resume tác vụ sau process crash; tự xóa lock sót; tự migration/hợp nhất dữ liệu cũ.
- Dùng chung cache giữa web và CLI hoặc giữa các nhóm; sửa mọi vấn đề kỹ thuật khác phát hiện trong quá trình làm.
- Đổi model dịch/ASR, prompt, batch size, timeout/retry provider, codec/chất lượng, ngưỡng ASR hoặc thuật toán nới/gộp khoảng blur.
- Thêm framework test, formatter/type checker hoặc CI provider để biến checkpoint chưa cấu hình thành PASS.
- Cài dependency, gọi dịch trả phí, download model, push/deploy/upload artifact ra ngoài khi chưa có quyền tương ứng.

### 3. Preconditions

| ID | Điều kiện, nguồn | Preflight trước mutation | Trạng thái lúc lập plan |
| --- | --- | --- | --- |
| PC-1 | Đúng checkout/base; source tham chiếu tồn tại | `git rev-parse HEAD`; `git status --short`; `git diff`; `git diff --cached`; đọc lại AGENTS | VERIFIED tại plan; MUST-VERIFY khi bàn giao |
| PC-2 | Python 3.12, venv repo; `pyproject.toml` | `.venv/Scripts/python.exe --version`; import FastAPI/TestClient/uvicorn trong venv | Python 3.12.10 VERIFIED; imports MUST-VERIFY |
| PC-3 | Node/Playwright hiện có; `package.json` | `node --version`; `node -e "require('playwright')"`; launch Chromium từ harness test | Node v24.18.0 VERIFIED; browser MUST-VERIFY |
| PC-4 | ffmpeg/ffprobe phục vụ runtime media | `ffmpeg -version`; `ffprobe -version`; kiểm filters và encode thực bằng fixture | command paths VERIFIED; khả năng media MUST-VERIFY |
| PC-5 | Một backend process như README; không multi-worker | Đọc command start thực, process do harness sở hữu; runtime dùng `--workers 1`, không reload | Contract VERIFIED; deployment thực MUST-VERIFY |
| PC-6 | Test không chạm dữ liệu người dùng | Tạo temp root; cwd process test nằm trong đó; audit harness chặn tạo client mạng thật | MUST-VERIFY |
| PC-7 | Baseline audit không thay baseline trước sửa | Luna chạy V-00, lưu log/hash trước khi Claude sửa | MUST-VERIFY |
| PC-8 | Danh tính model đúng và có runtime | Kiểm model executor/reviewer thật; không suy luận từ tên task | MUST-VERIFY; plan không xác nhận model đã chạy |
| PC-9 | CI/lint/typecheck không có config ở base | Kiểm `.github/workflows`, scripts, pyproject và config ẩn ở checkout mới | VERIFIED: chưa cấu hình ở base |
| PC-10 | Hook/nhánh/attribution không bị bỏ qua | `git branch --show-current`; đọc `.githooks/*`; đọc config `core.hooksPath`, `nhom.nhanh`; kiểm byline runtime | MUST-VERIFY trước Commit |

Lỗi preflight chỉ chặn bước phụ thuộc. Không cài tool hoặc đổi cấu hình để che kết quả; báo `NOT AVAILABLE` / `NOT RUN` với bằng chứng. Tool semantic Serena đã không có language server ở lượt audit: có thể dùng `rg` và đọc symbol/caller trực tiếp, không nhận là đã có semantic verification.

### 4. Outcome

Upload lại đúng video và nhóm dùng lại artifact còn hợp lệ; mỗi công việc vẫn có trạng thái/output riêng. Chọn vùng rồi tiếp tục không chạy lại nhận dạng vô cớ, không gắn vùng lên bộ cue khác, và request đồng thời/restart không gây lỗi thread hay trạng thái sống giả.

### 5. Acceptance Criteria

| ID | Điều kiện nghiệm thu quan sát được | Verification |
| --- | --- | --- |
| AC-1 | 40 GET nhóm đồng thời/8 workers và bộ đọc-ghi xen kẽ không có lỗi thread/500; transaction, rollback, FK vẫn đúng | V-01, V-11 |
| AC-2 | Nghĩa vùng chung/riêng nhất quán giữa UI, HTTP, artifact và render, theo ES-2 đã chốt; không âm thầm diễn giải lại dữ liệu cũ | V-02, V-08, V-10 |
| AC-3 | Cùng byte + cùng nhóm tạo CID mới nhưng cùng tài nguyên cache; lượt 2 không gọi ASR/dịch nếu dependencies không đổi. Nhóm khác hoặc byte khác tách biệt | V-03, V-11 |
| AC-4 | Hai công việc không đồng thời ghi một work directory; trùng lúc đang xử lý bị 409 trước scheduling; không ghi source dở, không lock rò ở lỗi thông thường | V-04, V-11 |
| AC-5 | Cùng job `force_asr`/`force`, chuỗi upload → chờ vùng → gửi vùng chỉ xử lý upstream một lần; lượt chạy mới vẫn giữ nghĩa force của CLI/API | V-05, V-11 |
| AC-6 | Đổi nguồn SRT, thứ tự, timestamp, số cue hay version làm vùng theo cue mất hiệu lực; submission từ snapshot cũ bị 409, không áp nhầm index | V-06, V-11 |
| AC-7 | Sau restart, công việc không-terminal mất hồ sơ được phản ánh `loi`; POST vùng trả 409, ID không tồn tại trả 404; job hoàn tất còn tải output nếu file còn | V-07, V-11 |
| AC-8 | CLI/batch, dữ liệu/manifest cũ, manual SRT hợp lệ, glossary transaction, hình học, một lần encode và output tốt cũ không bị phá ngoài chính sách đã công bố | V-03, V-06, V-09, V-10 |
| AC-9 | Có log mỗi gate, test được collect thực, final diff đúng scope, independent review có verdict; không gọi mock là end-to-end thật | V-00, V-12, V-13, V-14 |

### 6. Contract Surface

Các ID trong plan này có namespace cục bộ; không dùng để thay nghĩa CS/LD của plan gốc.

| ID | Contract phải giữ | Evidence |
| --- | --- | --- |
| CS-1 | CID nhận diện job, cache nhận diện video theo nội dung + nhóm; output/job cũ không đổi khi job mới render | DEC-1; `api/app.py:tai_len`, `ket_qua` |
| CS-2 | Artifact/manifest quyết định cache hit; DB không thay filesystem làm nguồn sự thật | `CLAUDE.md:62`; plan gốc LD-1/2 |
| CS-3 | Cache dịch vẫn phụ thuộc sub gốc/model/prompt/glossary; manual SRT chỉ được giữ khi upstream hợp lệ | `pipeline/dieu_phoi.py:_buoc_dich`; README §4 |
| CS-4 | Vùng thiếu thì chờ trước dịch; resume không chạy lại upstream; full force mới vẫn force thật | README §2; plan gốc AC-2/9, LD-9; F-4 |
| CS-5 | Một writer/work; atomic replace; lock sót không tự xóa; pending job không được áp vùng lên cue khác | `pipeline/srt.py:khoa_work`, `file_tam`; F-3/5 |
| CS-6 | Nghĩa common/private và tương thích payload/JSON cũ phải được xác định trước đổi | UI `dat_pham_vi`; tests hiện tại mâu thuẫn; ES-2 |
| CS-7 | Quy tắc `hop_chinh` dùng đồng nhất cho style và mặc định nhóm; lưu nhóm chỉ khi được chọn; `blur off` không xóa mặc định nhóm | `markbox.hop_chinh`; `test_hop_nhom_khong_bi_ghi_de_am_tham`; `tests_media.py:test_kieu_chu_bam_hop_ap_cho_moi_cau` |
| CS-8 | FastAPI request có connection riêng; transaction/rollback/FK/marker glossary không bị chia sẻ sai | `api/viec.py:ket_noi`; `db.ap_dung_dich`; `tests_db.py:test_glossary_transaction_resume` |
| CS-9 | Restart không tự resume; không-terminal phải thành lỗi có thể hiểu được; terminal/download cũ giữ nguyên | README §6; `_work` đã dùng 409 khi thiếu hồ sơ |
| CS-10 | Không đổi schema, CLI flags/exit codes, cue/timestamp, model, codec, dependency hay kiến trúc ngoài scope | AGENTS; CLAUDE; plan gốc IC/LD; `main.py` |
| CS-11 | Chỉ thay file được phân công; không stage dirty đầu phiên; mọi tuyên bố PASS có evidence tại revision được review | Yêu cầu người dùng và Scope/Authority global |

### 7. Inherited Constraints

- **IC-1 — kiến trúc:** API gọi điều phối; module media không biết HTTP/DB; không thêm nhánh pipeline thứ hai. `CLAUDE.md:75`, plan gốc CS-6. Các truy cập DB đã có trong API không phải lý do mở refactor toàn bộ kiến trúc.
- **IC-2 — nền tảng:** Python 3.12, JS thuần, `assert`, `TestClient`, SQLite, Playwright hiện có. Không thêm pytest/ORM/framework/queue. AGENTS §Testing; `pyproject.toml`; `package.json`.
- **IC-3 — dữ liệu:** atomic artifact rồi manifest, giữ file tốt cũ khi lỗi; giữ nguyên cache CLI `work/<stem>-<hash-path>`. Plan gốc LD-1/2; `srt.py:115`.
- **IC-4 — nhóm:** không dùng chung state bản dịch/vùng/glossary giữa nhóm khác; không đổi cách viết tên nhóm, case hoặc Unicode normalization âm thầm. DEC-1; `db.lay_nhom` dùng tên chính xác.
- **IC-5 — vùng:** validator chung `kiem_hop`/`kiem_vung`, toạ độ 0–1, index cue zero-based; không bỏ qua index ngoài phạm vi. `markbox.py:38`; test vùng hiện tại.
- **IC-6 — media:** nới ±0.4s, merge gap và giới hạn khoảng hiện có; cùng `hop_chinh`; audio copy và một lần encode. `render.py`; README §2. Không sửa thuật toán này để che lỗi chọn cue.
- **IC-7 — force:** giữ `force_asr` chọn ASR thay sidecar/embedded; không chỉ set False rồi vô tình quay lại nguồn cũ. `_nguon_sub`, `_buoc_sub_goc`; `test_resume_dependencies_and_atomic_write`.
- **IC-8 — authority:** chỉ lập plan hiện tại. Không commit/push/API thật hoặc thay model vì một checklist có tên bước đó. Khi người dùng sau này cho thực thi cả plan bao gồm Commit, không hỏi lại cùng quyền.
- **IC-9 — role:** Claude sửa source; Luna viết/chạy verification và review. Independent reviewer là fresh context, không phải lời tự đánh giá của người vừa viết/fix. Yêu cầu chia hai phần của người dùng.

### 8. Locked Decisions

#### LD-1 — nhận diện upload mới, đã được người dùng chốt

- Giá trị: SHA256 toàn bộ byte video + namespace nhóm chính xác; `None` là namespace riêng, không phải chuỗi `"None"`. CID luôn UUID mới.
- Không lấy tên file, mtime, độ dài file, prefix hash hoặc CID làm content identity. Tên khác nhưng byte/nhóm giống nhau phải tái dùng cache.
- Giữ upload nguồn ổn định và work chung; output cuối đặt ở thư mục từng CID với tên tải xuống gắn filename gốc đã sanitize.
- Layout nội bộ dự kiến: `work/tai_len/nguon/<sha256-scope>/<sha256-video>/nguon.media`; output `work/tai_len/<cid>/<stem>_vi.mp4`. Work vẫn qua `thu_muc_lam_viec(canonical_source)` như contract cũ. Đuôi nội bộ cố định để đổi extension/tên upload không đổi identity; validation vẫn dựa filename upload và ffprobe nội dung.
- Bản ghi `video` phải bám canonical source, tránh hai source path khác nhau cùng `thu_muc_work` UNIQUE. Không sửa schema để lách xung đột.
- Dữ liệu upload/cache trước bản sửa để nguyên. Không hứa tự phát hiện/tái sử dụng cache cũ thuộc UUID khác; lần đầu vào layout mới có thể phải xử lý lại. Cache mới hợp lệ dùng lại được sau restart bình thường.
- Protects: AC-3/4/8, CS-1/2/3/5, IC-3/4.
- Evidence: DEC-1; `srt.py:115`; UNIQUE path/work trong `db.py`; F-3.
- Loại: đổi CID thành content hash; dùng hash tên file; dùng chung mọi nhóm; tự migration hoặc đổi đường cache CLI.

#### LD-2 — connection request riêng, có thể chuyển thread

- Mở rộng `db.mo` bằng tham số keyword-only tương đương `check_same_thread`, mặc định giữ True cho callers cũ; `api.viec.ket_noi` truyền False.
- Connection vẫn chỉ thuộc một request; không tạo singleton/global connection, không chia sẻ connection request cho background task, không tắt foreign keys hoặc autocommit để che lỗi.
- Background job tiếp tục tự mở/đóng connection trong chính job. Context manager vẫn commit/rollback như trước.
- Protects: AC-1/8, CS-8, IC-2. Evidence: F-1; `ket_noi`, `chay_nen`, `db.mo`.
- Loại: bắt `ProgrammingError` rồi retry; global lock cho cả API; một connection chung; chuyển stack DB.

#### LD-3 — resume là tiếp tục một lượt, không phải yêu cầu force mới

- Giữ lại nguồn sub đã chọn, option fingerprint và hash artifact tại `cho_chon_khung` trong checkpoint nội bộ của job. Checkpoint không do HTTP client tự khai là hợp lệ.
- Gửi vùng hợp lệ tiếp tục từ vùng/dịch/render trên snapshot đó; không chạy lại audio/ASR chỉ vì request thứ hai còn cờ force.
- Phân biệt lựa chọn nguồn ASR với hành động buộc chạy lại. Không reset mù `force_asr=False`: video có embedded/sidecar sẽ chọn nhầm nguồn.
- `force`/`force_asr` vẫn làm mới bản dịch khi đó là ý định của lượt mới, kể cả ASR tạo byte SRT giống trước; không bỏ force dịch trước khi bước dịch của lượt đó hoàn thành.
- Khi retry sau lỗi, artifact và checkpoint quyết định bước nào đã hoàn tất; không coi một attempt thất bại là đã tiêu thụ force thành công.
- Protects: AC-5/6, CS-3/4/5, IC-7. Evidence: plan gốc AC-2/9; `_nguon_sub`; F-4.
- Loại: gọi lại `chay` y nguyên; bỏ toàn bộ force sau POST vùng; bắt ASR result cũ theo `exists()`.

#### LD-4 — bind vùng theo cue vào nguồn sub và snapshot

- Chữ ký vùng theo cue bao gồm SHA256 SRT gốc hợp lệ/đã normalize, bên cạnh hash video, W/H, version và mode vùng nếu ES-2 tạo mode mới.
- Bump `VER['vung_blur']` đúng một lần cho thay đổi contract cuối; không tăng version audio/sub/dịch hoặc PROMPT_VER khi chúng không đổi thuật toán.
- Cache vùng không chứng minh được source cue thì không tự áp lại index. Single box cho mọi câu chỉ được dùng lại khi chứng minh không phụ thuộc index và hình học/video còn đúng.
- Với JSON cũ thiếu metadata: không xóa/sửa chỉ vì startup; khi xử lý lại, trường hợp không chứng minh được an toàn phải chọn lại vùng, không tự chuyển sang group box để che mất vùng riêng cũ.
- Submission đã stale trả 409 trước dịch/render/ghi vùng/ghi nhóm; không tự chạy lại ASR rồi gán vùng cũ lên bộ cue mới.
- Protects: AC-6/8, CS-2/5/6/7; evidence F-5, `kiem_vung(so_cue)`, README quy tắc ưu tiên vùng riêng.
- Loại: chỉ so số cue; chỉ so video; cắt bỏ index vượt range; dùng manifest version mới để diễn giải lại payload cũ mà không có compatibility rule.

#### LD-5 — stale jobs sau restart

- Trong mô hình một backend process, startup phản ánh các job cũ `cho`, `dang_chay`, `cho_chon_khung` không còn hồ sơ thành `loi`, dùng trường `loi` sẵn có để hướng dẫn tải lại.
- Không thêm enum DB, không resume tự động, không sửa job terminal `xong`, `suy_giam`, `loi`, không xóa `duong_dan_ra` tốt cũ.
- POST vùng: job không tồn tại → 404; job tồn tại nhưng thiếu hồ sơ/checkpoint hợp lệ → 409; không `KeyError`/500. GET status cũ phải đủ để UI dừng polling và mở lại thao tác upload.
- File lock còn sau crash giữ nguyên; hướng dẫn operator xác minh tiến trình trước xử lý lock. Upload lại không được tự xóa lock để thực hiện lời hứa resume.
- Protects: AC-7/8; CS-9; evidence README §6, `_work` dùng 409, plan gốc yêu cầu không treo `dang_chay`.
- Loại: đổi mọi job thành lỗi theo từng request mà không biết chủ sở hữu; phát sinh queue khôi phục; xóa output hoặc lock hàng loạt.

#### LD-6 — admission và output isolation

- Kiểm tra `.lock.exists()` đơn thuần không phải admission nguyên tử. Claim đúng work trước publication source/scheduling; chuyển quyền giữ claim cho background job một lần, release trong mọi exit thông thường.
- Dùng cùng file-lock contract tại shared boundary. Internal ownership/capability phải được kiểm path; không thêm cờ HTTP cho phép bỏ lock.
- Claim kết thúc khi lượt xử lý trả `cho_chon_khung`; không giữ khóa độc quyền vô thời hạn trong lúc chờ người. Khi nhận vùng phải claim lại và kiểm checkpoint dưới claim.
- Mỗi CID giữ snapshot cần cho màn chọn vùng. Không phục vụ âm thầm frame/cue của job khác sau khi shared cache đã đổi; frame snapshot cần bất biến hoặc việc đọc được bảo vệ tương đương, theo MD-1.
- Trùng lúc active: trả 409 trước tạo task thứ hai, không làm trạng thái job đang chạy thành lỗi. Job cũ đã hoàn tất tiếp tục trỏ đúng output của chính nó khi job mới dùng option khác.
- Protects: AC-3/4/6/8; CS-1/5; evidence DEC-1, plan gốc LD-2/9, `FileResponse` theo `duong_dan_ra`.
- Loại: thêm queue; chỉ khóa trong UI; dùng global mutex cho mọi video; ghi output chung rồi đổi link nhiều CID cùng trỏ file đó.

### 9. Material Delegations

- **MD-1 — mechanics tài nguyên nội bộ.** Claude được chọn helper nhỏ trong `api/viec.py`, `pipeline/dieu_phoi.py`, `pipeline/srt.py` cho ownership claim/checkpoint/canonical publication. Allowed: stdlib context manager/ExitStack, dataclass nhỏ nếu cần lưu checkpoint, snapshot frame trong thư mục CID. Forbidden: đổi contract LD-1/3/6, làm mới schema, custom queue/cache framework, cờ bỏ validation. Verify V-03/04/05/06/11. Tên helper và field nội bộ có thể khác plan; behavior không được khác.
- **MD-2 — cơ chế kiểm chứng.** Luna được dùng `unittest.mock`, callable fake, subprocess, `threading.Event`/barrier, temp directory và Playwright đang có. Forbidden: test phụ thuộc sleep đoán thời gian, real credentials, production DB, mock chính tính toán cần chứng minh, framework mới. Verify V-00/01/11/12.
- **MD-3 — bố trí test.** Luna giữ test chức năng trong các file `tests_*.py`/`test_pipeline.py` hiện có; được thêm một `test/runtime_logic.py` cho subprocess/runtime và một `test/runtime_frontend.cjs` nếu thật sự cần browser chạm backend thật. Không tạo test framework/fixture hierarchy. Verify V-09/11/12.

Các MD chỉ cho mechanics bảo toàn contract, không ủy quyền tự chọn product/API/compatibility policy chưa chốt.

### 10. Escalations

#### ES-1 — RESOLVED: cache theo nội dung + nhóm

- Authority/source: câu trả lời trực tiếp của người dùng được chép ở DEC-1.
- Áp dụng LD-1; mở STEP-3 và verification liên quan. Không hỏi lại cùng quyết định.

#### ES-2 — OPEN: thay thế hay cộng thêm vùng

- Evidence mâu thuẫn: UI `web/app.js:229` nói chỉ câu chưa có vùng riêng dùng vùng chung; `_cue_cua` và test hiện tại cho chung áp mọi câu.
- **A, đề nghị không binding:** vùng riêng thay vùng chung theo mô tả UI. Khi chọn A, cần biểu diễn mới có nghĩa tường minh hoặc danh sách cue đã resolve; payload/artifact cũ không âm thầm đổi nghĩa. Tách chọn hộp đại diện cho style khỏi việc trừ cue nếu cần.
- **B:** vùng riêng cộng thêm. Giữ backend/test contract cộng vùng; sửa UI mô tả và preview cho thấy cả hai vùng. Khi đó F-2 được giải quyết bằng tính nhất quán sản phẩm, không báo đã sửa thành override.
- Compatibility proposal cho A: giữ input legacy `cue:null` là literal mọi câu; thêm mode tường minh ở boundary mới hoặc resolve ở frontend mà bảo toàn `hop_chinh`. Bất kỳ field/mode mới phải ghi exact schema, default và behavior unknown value trong phiên bản plan tiếp theo trước implementation.
- **Blocks:** STEP-4; phần mode/schema của STEP-5; AC-2; V-02/08/10 tương ứng. Không block STEP-1/2/3/6 khi chúng không diễn giải lại JSON vùng.
- Sau câu trả lời: Astra cập nhật decision record, CS-6, contract truyền/lưu vùng, primary box, test expectations và status ở v2. Không giao Claude tự chốt phần còn thiếu.

### 11. Implementation Plan — chỉ nhiệm vụ mã sản phẩm của Claude

**Thứ tự:** STEP-1 → STEP-2 → STEP-3 → STEP-6; STEP-4 sau ES-2; STEP-5 sau STEP-3/4/6; STEP-7 sau các bước mã. Luna chuẩn bị/chạy các V ở Phần 2, không chèn test/review checklist vào phần executor.

#### STEP-1 — connection SQLite phù hợp FastAPI

- Depends on: PC-1/2, baseline V-00 đã được Luna ghi.
- Targets: `pipeline/db.py:mo`, `api/viec.py:ket_noi`; đọc callers `chay_nen`, CLI, tests DB trước sửa.
- Required change: LD-2; keyword-only option giữ default cho callers cũ, opt-in tại dependency request. Giữ close khi route raise và khi response hoàn thành.
- Preserved: AC-1/8, CS-8/10, IC-2.
- Freedom: tên tham số nội bộ và cách truyền keyword; không thay transaction ownership.
- Stop: cần shared connection/global serialization, schema/PRAGMA tuning hoặc dependency mới.
- Handoff verification: V-01/09/11. Expected: request thread hopping không còn lỗi; transaction vẫn nguyên.

#### STEP-2 — báo rõ công việc stale và chặn resume không có hồ sơ

- Depends on: STEP-1, PC-5.
- Targets: `api/app.py` startup/lifespan, `_cong_viec`, `trang_thai`, `nhan_hop`; `api/viec.py:lay`, `dat_hop`, `chay_nen`; helper DB nhỏ trong `pipeline/db.py` nếu cần update status tập trung.
- Required change: LD-5; guard lookup trước unpack; startup reconciliation chỉ các trạng thái không-terminal mất owner. Không dùng lỗi thiếu hồ sơ để xóa dữ liệu.
- Giữ status response keys hiện có; thông báo lỗi tiếng Việt có hành động tiếp theo; không lộ secret/traceback/đường dẫn máy trong response.
- Preserved: AC-7/8, CS-9/10, IC-1/3.
- Freedom: helper query/transaction cục bộ, không database migration.
- Stop: phát hiện đang chạy nhiều backend processes hoặc có owner task khác cần được giữ.
- Handoff verification: V-07/08/11. Expected: ID stale đọc ra lỗi rõ, POST 409, ID lạ 404, terminal download còn nguyên.

#### STEP-3 — canonical upload, admission và output từng job

- Depends on: STEP-1/2, DEC-1, PC-6; phối hợp interface checkpoint STEP-6 trước sửa `_HO_SO`.
- Targets: `api/app.py:_nhan_file`, `tai_len`, `_work`, `ket_qua`; `api/viec.py:dat`, `lay`, `chay_nen`; `pipeline/srt.py` hash/atomic/lock helpers; `pipeline/dieu_phoi.py:chay` và lookup `db.ghi_video`.
- Required change tuần tự:
  1. Validate filename/size/video như hiện tại; tính SHA256 theo chunk khi nhận, không đọc 4 GiB thành một buffer.
  2. Validate namespace nhóm trước publication; encode null và tên nhóm không nhập nhằng. Không tự lower/strip khác contract hiện có.
  3. Resolve canonical source/work theo LD-1; claim nguyên tử theo LD-6. Nếu bận, cleanup đúng temp file của request, trả 409; không tạo job/task rác.
  4. Publish nguồn atomically chỉ sau validate. Nếu canonical đã có, chứng minh đúng content; nếu hỏng hoặc không khớp identity, fail rõ và giữ dữ liệu, không ghi đè mù.
  5. Tạo CID/job mới, `tc.ra` riêng và record metadata/checkpoint nội bộ cần thiết. DB video dùng canonical source để không vi phạm UNIQUE(work).
  6. Background nhận ownership claim; failures trước/sau đăng ký job phải có đường cleanup xác định. Không thả claim rồi để khoảng trống trước khi job claim lại.
  7. Khi dừng chờ, release claim nhưng giữ snapshot CID; resume claim lại và kiểm snapshot. Không giữ lock qua thời gian người dùng suy nghĩ.
  8. Cache dependencies stage vẫn quyết định hit/miss; group glossary thay đổi phải invalidate dịch như cũ. Đổi tên upload không làm cache miss; output download vẫn theo tên lượt đó.
- Preserved: AC-3/4/8; CS-1/2/3/5/10; IC-3/4. Không thay `thu_muc_lam_viec()` cho CLI.
- Freedom: MD-1, không được biến tồn tại file thành bằng chứng cache hợp lệ.
- Stop: cần migration dữ liệu cũ, đổi schema, chọn giữ/xóa output cũ, hoặc đổi policy liên nhóm.
- Handoff verification: V-03/04/09/11. Expected: một tài nguyên cho cùng byte+nhóm, CID/output độc lập, writer tối đa 1/work, lỗi không phá artifact cũ.

#### STEP-4 — thống nhất vùng chung/riêng

- Depends on: ES-2 đã resolved và contract cụ thể đã có ở v2; không triển khai bản đề nghị khi còn OPEN.
- Targets: `web/app.js:dat_pham_vi`, `ve_khung`, `xay_vung`, `gui_hop`; `api/app.py:nhan_hop`; `pipeline/markbox.py:kiem_vung`, `hop_chinh`; `pipeline/dieu_phoi.py:_cue_cua`, `_buoc_hop`, `_hop_chung`; `pipeline/render.py:ket_xuat` nếu phải giữ hộp đại diện độc lập.
- Nhánh A phải thỏa:
  - Cue riêng không được vô tình còn trong tập cue nguồn của vùng chung.
  - Giữ ý nghĩa legacy theo compatibility contract, không reinterpret toàn bộ `cue:null`.
  - Có rule tường minh cho common rỗng sau trừ, không có common, tất cả cue riêng, trùng index, nhiều common và unknown mode.
  - Style/default nhóm dùng cùng hộp đại diện, không đổi khi chỉ resolve index cho render.
  - Việc ±0.4s/merge gap có thể làm blur lấn khoảng lân cận là contract riêng; không hứa không overlap tuyệt đối ở cue kề nhau.
- Nhánh B phải thỏa: preview/text hiện đúng các vùng đồng thời; không đổi thuật toán/test cộng vùng.
- Preserved: AC-2/8; CS-6/7/10; IC-5/6.
- Freedom: mechanics DOM/helper sau khi schema/semantics đã chốt; không redesign UI.
- Stop: phải chọn wire/schema/default/precedence chưa ghi trong v2.
- Handoff verification: V-02/08/10; expected theo nhánh ES-2 đã chốt, không dùng test của nhánh khác.

#### STEP-5 — invalidate vùng theo cue và chống snapshot cũ

- Depends on: STEP-3/4/6; phần không đụng mode chỉ chuẩn bị khi ES-2 còn mở.
- Targets: `pipeline/dieu_phoi.py:VER`, `_buoc_hop`, `chay`; `api/app.py:khung`, `mot_khung`, `nhan_hop`; checkpoint `api/viec.py`.
- Required change: LD-4/6; source fingerprint có đầy đủ hash sub gốc và option/source choice. Kiểm dưới claim trước nhận vùng, trước ghi group default và trước render.
- Không dùng `len(cues)` làm source identity; reorder cùng số lượng vẫn invalidate. Metadata không có/không khớp là unproven, không đoán.
- Cùng CID đang chờ có snapshot immutable cho UI; CID khác đổi shared cache không được làm ảnh/nhãn của CID cũ đổi lặng lẽ. Stale submit báo 409 và đường phục hồi tải lại, không tiếp tục trên snapshot khác.
- Không tự sửa JSON legacy trên startup. Khi cần chọn lại vùng, giữ dữ liệu cũ cho tới khi có lựa chọn thay thế hợp lệ; publish nguyên tử.
- Preserved: AC-6/8; CS-2/5/6/7; IC-3/5.
- Freedom: MD-1; exact mode compatibility theo v2.
- Stop: không xác định được nguồn cue của snapshot hoặc phải xóa/migrate hàng loạt.
- Handoff verification: V-06/09/11. Expected: không một vùng index cũ nào được áp im lặng lên source cue mới.

#### STEP-6 — checkpoint tiếp tục sau chọn vùng

- Depends on: STEP-1/2; interface shared with STEP-3, không sửa cạnh tranh cùng file.
- Targets: `api/viec.py:dat_hop`, `chay_nen`; `pipeline/dieu_phoi.py:TuyChon`, `KetQua`, `_nguon_sub`, `_buoc_sub_goc`, `_buoc_dich`, `chay`, `_chay`.
- Required change: LD-3; lưu/check nguồn và artifact đã hoàn tất khi trả trạng thái chờ. Entry resume vẫn vào điều phối chung, không gọi trực tiếp translate/render từ API.
- Giữ đúng ASR source khi video có embedded subtitle; giữ `separate`/VAD/model đã dùng; dịch forced một lần theo ý định lượt mới, kể cả upstream byte trùng.
- Phân biệt job mới, resume cùng job, retry sau lỗi trước/sau dịch; checkpoint server-side không được chế từ payload client.
- Checkpoint không còn khớp: fail rõ trước side effects; không tự sửa cue hoặc lặp ASR rồi tiếp nhận vùng cũ.
- Preserved: AC-5/6/8; CS-3/4/5; IC-7. CLI explicit force mỗi invocation vẫn như trước.
- Freedom: MD-1 cho cấu trúc checkpoint; không thêm public CLI flag hay HTTP option bỏ force/validation.
- Stop: phải đổi nghĩa force toàn hệ thống hoặc cần checkpoint persisted qua crash; việc đó ngoài scope.
- Handoff verification: V-05/06/09/11. Expected: ASR counter không tăng khi chỉ gửi vùng; full rerun vẫn tăng như contract.

#### STEP-7 — README và bàn giao implementation

- Depends on: STEP-1…6 hoàn thành hoặc ghi rõ phần blocked; chỉ cập nhật hành vi thực sự đã làm.
- Targets: `README.md` §2/4/5/6; không sửa AGENTS/CLAUDE dirty đầu phiên, không viết lại spec/plan lịch sử.
- Mô tả rõ identity mới, phạm vi cache mới, không migration cũ, output riêng, vùng theo ES-2, restart/stale lock, phân biệt force mới/resume.
- Bàn giao cho Luna: file/symbol thay đổi theo STEP, quyết định dùng, điểm còn hạn chế, diff snapshot, cảnh báo schema/API nếu có. Không tự ghi PASS cho V chưa được Luna chạy.
- Preserved: AC-9, CS-11, IC-8/9. Freedom: văn phong ngắn gọn, giữ tiếng Việt.
- Stop: README phải hứa behavior chưa có evidence hoặc plan còn ES chưa resolved.
- Handoff verification: V-12/13/14; expected tài liệu đúng implementation cuối và không lẫn bằng chứng lịch sử với lượt mới.

## Phần 2. GPT‑5.6 Luna — Implement → Self Review → Diff → Lint/Typecheck → Test → Runtime Test → Requirement Check → Independent Review → Fix → Re-test → Final Diff → CI → Commit → Completion Report

### 12. Phân vai và quy tắc chạy chuỗi

- **Luna validation lead, Ultra:** sở hữu phần này, test code, test harness, evidence và báo cáo.
- **Implement:** gate nhận implementation của Claude ở Phần 1; không phải chỉ thị để Luna viết lại source sản phẩm.
- **Fix:** Luna mô tả lỗi và red reproduction, Claude sửa source đúng scope; Luna sửa test của mình nếu test trái requirement đã chốt, không nới assertion để xanh.
- **Independent Review:** một Luna fresh context khác, read-only, không tham gia viết source/test ở lượt được xét. Gửi repo/base/plan/current diff/evidence, không chỉ gửi kết luận mong muốn.
- Không dùng một agent tự gọi việc review của mình là độc lập. Nếu chưa có đúng model/effort/runtime, báo `NOT AVAILABLE`; không giả tên Luna Ultra hoặc tự đổi sang model đắt hơn.
- Trong lượt lập plan này không spawn executor/reviewer. Khi được yêu cầu thực thi plan, phần này là yêu cầu phân công rõ ràng cho các vai trên.
- Không hai agent cùng sửa một file. Test owner và source owner bàn giao tuần tự với diff snapshot; đều phải giữ user changes.
- Baseline + red reproduction là preflight trước production mutation dù tên chuỗi bắt đầu bằng Implement. Các gate sau vẫn giữ đúng thứ tự người dùng yêu cầu.

### 13. Verification — danh mục dùng chung

#### V-00 — baseline và isolation (`BEFORE`)

**Covers:** PC-1…10, AC-9, CS-10/11, IC-2/8/9, MD-2/3.

```powershell
git rev-parse HEAD
git status --short
git diff --name-status
git diff --cached --name-status
.venv/Scripts/python.exe --version
node --version
.venv/Scripts/python.exe test_pipeline.py
```

- Chạy browser baseline theo G-5 bên dưới, output ở temp. Ghi exit code, tên/count test thực tế; baseline lịch sử 17 không phải số test cố định sau sửa.
- Ghi manifest dirty + hashes trước sửa. Không `git reset`, `git clean`, `git add .` hoặc thay user config.
- Test tạo DB/source/artifact trong `TemporaryDirectory`; subprocess có cwd temp và `PYTHONPATH` trỏ repo. Child exit trước khi parent cleanup để Windows giải phóng SQLite handles.
- Chặn tại provider seam trước `load_dotenv`/`tao_goi`; đừng dựa vào việc xóa env key vì `.env` có thể được tự nạp. Không in env/secrets.
- **PASS:** checkout xác định, dirty giữ nguyên, test baseline được ghi trung thực, sandbox test được chứng minh nằm ngoài work thật. Baseline fail không được gán cho patch mới.

#### V-01 — SQLite concurrency và transaction (`BOTH`)

**Owner/targets:** Luna; `tests_api.py`, `tests_db.py`; đăng ký qua runner hiện có.

**Tên dự kiến:** `test_api_sqlite_concurrent_requests`, `test_api_sqlite_connection_lifecycle`.

```powershell
.venv/Scripts/python.exe -c "import tests_api as t; t.test_api_sqlite_concurrent_requests(); t.test_api_sqlite_connection_lifecycle()"
```

- Trong một child process riêng, một TestClient app, `ThreadPoolExecutor(max_workers=8)` và 40 GET `/api/nhom`; thu mọi exception/status, assert 40/40=200 sau sửa.
- Đường này dùng dependency `ket_noi` và `db.mo` thật; không mock SQLite/threadpool để né lỗi.
- Thêm đọc-ghi xen kẽ với tên nhóm tách biệt; kiểm đủ rows, foreign keys ON, rollback request hỏng không lưu dữ liệu nửa chừng.
- Kiểm connection close khi route raise; subprocess exit và temp root cleanup không bị `WinError 32`.
- Giữ test `test_glossary_transaction_resume`; không tăng/nhân đôi marker do concurrency.
- **Red:** base có ProgrammingError ở concurrency; nếu lịch chạy tình cờ không tái hiện, dùng barrier kiểm connection được dùng tuần tự qua thread khác, không thêm sleep hoặc tuyên bố lỗi đã biến mất.
- **Green:** không ProgrammingError/500/DB corruption, lifecycle và transaction assertions pass.
- **Covers:** AC-1/8, CS-8/10, IC-2, LD-2, MD-2.

#### V-02 — semantics và compatibility vùng (`BOTH`, chờ ES-2)

**Owner/targets:** Luna; `test_pipeline.py`, `tests_media.py`, `tests_api.py`.

**Tên dự kiến:** `test_vung_chung_rieng_contract`, `test_vung_legacy_compatibility`.

```powershell
.venv/Scripts/python.exe -c "import test_pipeline as t; t.test_vung_chung_rieng_contract(); t.test_vung_legacy_compatibility()"
```

- Fixture hai cue `[0,1]` và `[10,11]`, duration 12; common dưới, private trên cho index 1. Khoảng cách lớn tránh nhầm với ±0.4s/merge gap.
- Nhánh A: tại 10.5s, dưới không active, trên active; tại 0.5s chỉ dưới active. Nhánh B: 10.5s cả hai active và UI phải nói/hiện đúng như vậy.
- Kiểm thêm không private, không common, mọi cue private, private trùng index, common sau resolve không còn cue, index ngoài range, bool/NaN/infinity trong box. Expected của duplicate/common/mode theo contract v2, không tự chọn trong test.
- Kiểm primary style/default nhóm bằng box có kích thước khác rõ ràng; chúng phải cùng dùng hộp đại diện theo CS-7.
- Golden JSON/payload cũ giữ expected behavior hoặc yêu cầu chọn lại đúng theo v2; không viết lại fixture để khớp code mới.
- **Covers:** AC-2/8, CS-6/7, IC-5/6, ES-2, phần liên quan LD-4.

#### V-03 — nhận diện lại video, cache và output (`BOTH`)

**Owner/targets:** Luna; `tests_api.py`, helpers fake sẵn có, DB/manifest thật.

**Tên dự kiến:** `test_api_reupload_cache_identity`, `test_api_reupload_output_isolation`.

```powershell
.venv/Scripts/python.exe -c "import tests_api as t; t.test_api_reupload_cache_identity(); t.test_api_reupload_output_isolation()"
```

| Case | Expected riêng biệt |
| --- | --- |
| Cùng bytes/nhóm, filename giống | CID khác, canonical source/work giống; audio/ASR/dịch không tăng ở lượt 2; render tăng vì luôn render |
| Đổi tên hoặc extension nhưng byte giống | Cache identity không đổi; tên download theo lượt mới |
| Lượt 2 provider seam `None` | Dùng dịch cache hợp lệ và hoàn tất, không gọi mạng/không báo thiếu khóa |
| Nhóm A/B có glossary giống hoặc khác | Work/source tách, không dùng bản dịch/vùng/default của nhau |
| Không nhóm so với tên nhóm literal tương tự null | Namespace không đụng nhau |
| Cùng tên file nhưng byte khác | Cache miss; không overwrite input/output job cũ |
| Đổi VAD/model/source/glossary | Chỉ đúng stages phụ thuộc bị invalidate theo contract cũ |
| Job B dùng style khác sau job A xong | SHA256 output tải qua CID A không đổi, B có output riêng |
| Dữ liệu layout cũ | Hash/sự tồn tại không đổi; không auto-scan/migration; không hứa cache hit từ layout cũ |
| Canonical source bị hỏng | Fail rõ, không đọc như cache hợp lệ hoặc overwrite mù |

- Đếm calls ở module seams; không patch `thu_muc_lam_viec` thành đường cố định như test lock cũ, vì sẽ che F-3.
- Kiểm DB `video` không lỗi UNIQUE(work), không đổi `nhom_id` qua namespace khác, `cong_viec` có CID riêng.
- **Covers:** AC-3/8, CS-1/2/3/10, IC-3/4, LD-1, MD-1/2.

#### V-04 — admission, races và partial failure (`BOTH`)

**Tên dự kiến:** `tests_api.test_api_shared_work_admission`.

```powershell
.venv/Scripts/python.exe -c "import tests_api as t; t.test_api_shared_work_admission()"
```

- Dùng Event/barrier giữ job A đang active, upload B cùng identity; assert một accepted, một 409, counter writer tối đa 1/work. Không serialize test thành hai request xong lần lượt.
- Hai POST vùng cạnh tranh cùng CID/cùng work: một continuation, request còn lại 409; không đổi successful job thành `loi` vì background thứ hai tranh lock.
- Inject failure sau temp write, validate, claim, DB insert và trước scheduling: không temp-file/owned-lock rò; không job báo queued khi chẳng có task; không xóa lock của job khác.
- Fake process crash giữ lock để chứng minh không auto-remove. Operator cleanup chỉ trên fixture test thuộc harness.
- Một job trả chờ phải release active claim; job khác có thể tiến hành, nhưng job chờ cũ chịu snapshot validation của V-06.
- **Covers:** AC-4/6/8, CS-1/5, IC-3, LD-6, MD-1/2.

#### V-05 — force/resume bằng counters (`BOTH`)

**Tên dự kiến:** `test_pipeline.test_resume_force_checkpoint`.

```powershell
.venv/Scripts/python.exe -c "import test_pipeline as t; t.test_resume_force_checkpoint()"
```

- `force_asr=True`: upload → `cho_chon_khung` có ASR=1, dịch=0; gửi vùng → ASR vẫn 1, dịch=1, render=1.
- Có embedded/sidecar khác nội dung ASR: resume vẫn dùng ASR đã chọn, không quay sang embedded/sidecar.
- `force=True` với audio/sub/dịch cache trước đó: lượt mới thực sự invalidates theo cờ; gửi vùng trong lượt đó không xử lý audio/sub lần nữa; dịch không được reuse bản cũ do reset force sớm.
- ASR mới tạo SRT byte giống trước: dịch của full forced run vẫn được ép lại một lần.
- `separate=True`/VAD: checkpoint dùng đúng output vocals/source option; không chuyển audio.wav âm thầm.
- Box invalid/409 không tiêu thụ checkpoint/force, không gọi ASR/dịch. Retry sau dịch lỗi không xem bản dịch cũ là kết quả forced run mới.
- CLI hai invocation `force_asr=True` vẫn có hai ASR calls; khác với hai HTTP requests tiếp tục cùng job.
- **Covers:** AC-5/8, CS-3/4, IC-7, LD-3, MD-1/2.

#### V-06 — source cue changed/stale (`BOTH`)

**Tên dự kiến:** `test_pipeline.test_vung_cue_source_invalidation`, `tests_api.test_api_stale_box_snapshot`.

```powershell
.venv/Scripts/python.exe -c "import test_pipeline as p, tests_api as a; p.test_vung_cue_source_invalidation(); a.test_api_stale_box_snapshot()"
```

- Test từng thay đổi riêng: text, timestamp, reorder cùng count, số cue tăng/giảm, source sidecar→ASR, version. Vùng theo index cũ không được reuse im lặng.
- Single box không phụ thuộc index và JSON legacy thiếu fingerprint theo LD-4/v2; fixture bao gồm group default để không che mất yêu cầu chọn lại vùng riêng.
- Job A chờ; job B cùng identity cập nhật source khác dưới claim; ảnh/cue A không đổi lặng lẽ, POST vùng A=409. Assert group box, translation file, output cũ chưa bị ghi.
- File sub/manifest bị sửa giữa bước chờ và POST: 409, không model call tự động để hợp thức hóa vùng cũ.
- **Covers:** AC-6/8, CS-2/5/6/7, IC-3/5, LD-4/6.

#### V-07 — restart/state machine (`BOTH`)

**Tên dự kiến:** `tests_api.test_api_restart_orphans`.

```powershell
.venv/Scripts/python.exe -c "import tests_api as t; t.test_api_restart_orphans()"
```

- Temp DB có một job cho mỗi enum hiện tại; clear RAM/start app mới bằng lifespan, không sửa DB thành expected trước gọi app.
- `cho`/`dang_chay`/`cho_chon_khung` → `loi` có hướng dẫn; terminal giữ nguyên; file output còn thì GET `/ket-qua`=200.
- POST vùng orphan=409, ID lạ=404; không traceback. Existing stale lock giữ nguyên.
- Kiểm errors giữa DB/state/RAM lookup bằng seam hẹp; không bắt mọi exception và trả giả 200.
- **Covers:** AC-7/8, CS-9/10, LD-5.

#### V-08 — frontend regression và trạng thái (`BOTH`)

**Owner/targets:** Luna; `test/frontend.cjs`. Cho phép thêm option env output screenshots, default giữ `docs/ketqua` để không phá cách chạy cũ.

```powershell
# Server tĩnh do harness sở hữu, chỉ bind loopback; UI_URL trỏ đúng server đó.
$env:UI_URL = 'http://127.0.0.1:8765'
$env:SCREENSHOT_DIR = '<thu-muc-evidence-cua-luot-chay>'
npm run test:frontend
```

- Harness tạo screenshot dir trước, restore env sau; không overwrite ảnh lịch sử B-frontend. Tạo server bằng subprocess ẩn hoặc server trong process test, dừng đúng PID đã tạo.
- Giữ test validation/upload failure/poll retry/resize/mobile 360–768–1440/glossary/keyboard-reduced-motion/WebGL fallback.
- Thêm case vùng riêng theo ES-2, mode/payload compatibility, stale 409 hiện thông báo, restart `loi` dừng polling và mở upload lại.
- API giả chỉ chứng minh UI; không dùng kết quả này để nghiệm thu concurrency/cache/backend.
- **Covers:** AC-2/7/9, CS-6/7/9/11; IC-2/9.

#### V-09 — full offline và CLI contracts (`BOTH`)

```powershell
.venv/Scripts/python.exe test_pipeline.py
```

- Tất cả test mới phải được runner gọi; report liệt kê tên và count, không chỉ exit 0.
- Giữ coverage cũ: SRT roundtrip, atomic write/lock, batch collision/exit, subtitle priority, CUDA fallback, translation validation, glossary transaction, manual SRT, group default, geometry/style.
- Nếu sửa assertion F-2 theo quyết định người dùng, ghi old→new và ID AC-2; không xóa case. Test valid khác không được nới.
- **Covers:** AC-8/9, CS-2/3/7/8/10, IC-1…7.

#### V-10 — ffmpeg media thật và hình ảnh (`AFTER`)

```powershell
.venv/Scripts/python.exe test_pipeline.py --smoke
```

- Chạy script bằng interpreter/path tuyệt đối với cwd là evidence temp để các `smoke_*.png` không làm bẩn root; harness set import path đúng repo.
- Lệnh `--smoke` hiện chỉ chạy media suite rồi exit, không bao gồm suite offline: luôn chạy V-09 riêng.
- Giữ 720p/1080p, có audio, duration lệch ≤0.1s, không blur/có blur/hai vùng; thêm fixture common/private theo quyết định ES-2 chạy qua điều phối thật đến render thật, không chỉ truyền hai vùng đã lọc sẵn.
- Dùng cue cách xa để phân biệt lỗi override với padding/gap. Trích frame tại giữa cue thường, giữa cue riêng và khoảng ngoài cue; xem ảnh thật bằng image tool, ghi đường dẫn và kết luận từng vùng.
- Kiểm primary font/margin và một pipeline encode; không lấy file tồn tại hoặc ffprobe thành công làm bằng chứng vùng đúng.
- Thiếu ffmpeg/libass/encoder chạy được → `NOT RUN`, ghi gate bị chặn. Không thêm codec/auto-transcode ngoài scope.
- **Covers:** AC-2/8, CS-6/7/10, IC-5/6; không chứng minh ASR/dịch thật.

#### V-11 — Runtime Test qua HTTP thật, cô lập (`AFTER`)

**Artifact được Luna tạo:** `test/runtime_logic.py`, và `test/runtime_frontend.cjs` nếu browser cần module riêng. Đây là test harness, không production entrypoint hay debug backdoor.

```powershell
.venv/Scripts/python.exe test/runtime_logic.py
```

Yêu cầu harness:

1. Tạo temp root, DB, fixture media ngắn bằng ffmpeg, evidence dir; không dùng video/.env/work thật. Chặn provider adapter bằng callable fake trước app startup; fail nếu code cố tạo client thật.
2. Launch uvicorn app thật từ child process, loopback + cổng riêng, một worker, không reload; health-check request có deadline. Không dùng sleep cố định để đoán ready.
3. Chỉ fake ASR và provider để output/counters xác định; dùng API routing, multipart, SQLite, admission/lock, filesystem, điều phối và ffmpeg thật. Fake chỉ ở test entrypoint/import seam, không cấy switch test vào source sản phẩm.
4. Browser hoặc HTTP client gửi video → poll `cho_chon_khung` → lấy frames → gửi vùng → poll terminal → tải MP4. Không chặn/mock các HTTP API responses trong case này.
5. Reupload cùng byte/nhóm: CID mới, cache shared, counters audio/ASR/dịch không tăng khi hợp lệ, output CID trước giữ nguyên. Nhóm khác không hit cache của nhóm trước.
6. Giữ stage bằng Event qua test adapter; upload/POST cạnh tranh thật chứng minh một writer và response409, không chỉ unit helper.
7. Restart child **bình thường** khi đang chờ và chưa có lock active: status orphan phải đúng, upload lại cache mới vẫn dùng được. Child crash trong khi giữ lock là case riêng: lock còn và bị từ chối, không gắn nhãn lỗi cache reuse.
8. Force/source/checkpoint và snapshot stale kiểm cùng expected V-05/06. Ghi counters, response codes, state transitions, SHA256 artifacts/output, browser errors và process exit.
9. `finally`: dừng đúng child PID, đóng browser/server/SQLite, cleanup temp có xác minh đường dẫn; giữ evidence text/images cần bàn giao trong thư mục riêng đã chọn. Không dùng kill-all hoặc recursive delete dựa cwd.

**PASS:** toàn bộ assertions HTTP/state/artifact/counters pass; media output probe được; không 500/uncaught JS; restart/409 phục hồi đúng. **Tên bằng chứng:** runtime integration với ASR/provider fake, không full end-to-end AI.

ASR thật/DeepSeek thật là lane riêng **NOT RUN — ngoài scope hiện tại**. Chỉ chạy nếu có quyền model/network/cost rõ ràng; không coi thiếu lane đó là reason để gọi mạng tự động.

**Covers:** AC-1…9 tương ứng branch ES-2, CS-1…11, LD-1…6, MD-1/2/3.

#### V-12 — diff, syntax và requirement matrix (`BOTH/AFTER`)

```powershell
git diff --check
git diff --stat
git diff --name-status
git diff --cached --name-status
.venv/Scripts/python.exe -m compileall -q api pipeline main.py test_pipeline.py tests_api.py tests_db.py tests_media.py tests_translate.py tests_smoke.py
node --check web/app.js
node --check test/frontend.cjs
```

- Thêm path test mới đã tạo vào check; `node --check web/scene.js` nếu file đó bị đụng (bình thường ngoài scope).
- `compileall`/`node --check` là **syntax checks**, không phải lint/typecheck. `Lint = NOT CONFIGURED`, `Typecheck = NOT CONFIGURED` ở base. Nếu checkout mới có cấu hình thật thì dùng command project đó và ghi kết quả riêng.
- Diff allowlist source: `api/app.py`, `api/viec.py`, `pipeline/db.py`, `pipeline/dieu_phoi.py`, `pipeline/srt.py`, `pipeline/markbox.py`, `pipeline/render.py`, `web/app.js`, `README.md`. Không cần sửa tất cả; sửa ngoài list phải có mapping AC và reason trước mutation.
- Test allowlist: files test hiện có liên quan, `test/runtime_logic.py`, `test/runtime_frontend.cjs`. Không đổi dependency/lockfile/schema bằng tiện tay.
- So hashes AGENTS/CLAUDE ban đầu; kiểm diff source không có secrets/test-mode switch/destructive migration/global connection/auto-clear lock.
- Trace matrix cuối phải có hàng cho mọi AC, CS, IC, LD, MD và DEC; mỗi hàng dẫn V + exact evidence + PASS/FAIL/BLOCKED/NOT RUN. Không lấy một dòng “suite xanh” thay chứng cứ riêng.
- **Covers:** AC-8/9, CS-10/11, IC-1…9, MD-3.

#### V-13 — independent review (`AFTER`)

- Reviewer: Luna Ultra fresh context, read-only, không từng viết/fix candidate này. Runtime chỉ có Luna effort khác không được ghi thành Ultra; báo thiếu capability để điều phối.
- Input packet: plan version/decisions, base SHA, full tracked + untracked candidate diff, test source, result logs, snapshot hash và dirty exclusions.
- Reviewer tự trace HTTP→job→checkpoint→cache→render, DB thread lifecycle và legacy compatibility; tự chạy tối thiểu một boundary test không chỉ đọc report.
- Điểm bắt buộc: force-ASR không bị reset về embedded; duplicate admission không TOCTOU; job output độc lập; group key null/name không đụng; pending cue/frame snapshot không đổi; old JSON không đổi nghĩa; orphan guard không biến terminal thành lỗi.
- Output: finding ID, severity, file/symbol/line, requirement ID, `Why:`, reproduction, expected/actual, fix boundary, verdict. Không có finding nhưng evidence thiếu → `NEEDS VALIDATION`, không `APPROVE`.
- P0/P1/blocker phải sửa và re-test; finding nhỏ chưa sửa chỉ có thể để lại khi không vi phạm AC và report rõ, không tự hạ severity để vượt gate.
- **Covers:** AC-9, CS-11, IC-9; kiểm độc lập AC-1…8.

#### V-14 — CI/Commit/report consistency (`AFTER`)

- CI không có workflow ở base: status `NOT CONFIGURED`; local checks không đổi tên thành “CI PASS”. Không tự thêm workflow/provider hoặc push để có đèn xanh.
- Nếu đã có CI được cấu hình ở revision sau, lấy evidence gắn đúng commit/candidate; CI revision cũ không cover diff mới. Không trigger remote action chưa được cho phép.
- Commit chỉ sau không còn blocker, V required đã đạt và có quyền thực thi Commit trong scope. Planning-only hiện tại không thực hiện commit.
- Stage file/hunk tường minh; loại AGENTS/CLAUDE dirty ban đầu và artifacts không thuộc patch; không `git add .`, `--no-verify`, amend/reset/rebase user history.
- Đọc staged diff/check lần cuối; commit message mô tả outcome, không dùng checklist làm message. Byline `Co-Authored-By` lấy từ active runtime authoritative; không đoán email/tên. Không có byline và repo không có fallback thì báo phần attribution chưa giải quyết.
- Sau commit kiểm `git show --stat --oneline HEAD`, `git status --short`; expected chỉ còn user dirty ban đầu và phần explicitly excluded. Không push.
- Report phân biệt implementation validated / commit pending / committed; không tuyên bố toàn chuỗi complete nếu gate bắt buộc còn fail.
- **Covers:** AC-9, CS-11, IC-8/9.

### 14. Chuỗi gate chi tiết của Luna

| Gate | Owner/action | Điều kiện ra gate | Khi không đạt |
| --- | --- | --- | --- |
| G-0 Preflight | Luna chạy V-00 và red cases, Claude chưa sửa source | Có baseline, dirty snapshot, quyết định đủ cho slice | Chặn slice phụ thuộc; không che baseline fail |
| G-1 Implement | Nhận bàn giao STEP-1…7 của Claude theo từng slice | Source diff map được STEP/AC; không ES mở trong slice | Trả Claude yêu cầu thiếu; không tự implement sản phẩm |
| G-2 Self Review | Luna rà logic test/harness, các invariant và evidence của candidate | Test kiểm behavior, fake đúng seam, không dữ liệu thật | Sửa test của Luna hoặc mở finding cho Claude |
| G-3 Diff | V-12: full diff gồm untracked candidate, staged/unstaged | Scope đúng, user dirty nguyên, không contract drift | Dừng gate, yêu cầu sửa đúng owner |
| G-4 Lint/Typecheck | Syntax + công cụ cấu hình thật nếu có | Syntax PASS; lint/typecheck báo đúng trạng thái | Không cài tool mới/nói syntax là typecheck |
| G-5 Test | V-01…09 theo nhánh đã chốt, full offline + browser | Red→green có lý do, mọi test mới thực sự chạy | Finding+reproduction; chưa qua Runtime acceptance |
| G-6 Runtime Test | V-10/11, HTTP thật/media thật có boundary fake rõ | Log state/counters/output + frame evidence đạt | Không thay bằng TestClient hoặc browser API mock |
| G-7 Requirement Check | Matrix V-12 đối AC/CS/IC/LD/MD | Không missing required ID, ES resolved | Giữ BLOCKED/NEEDS VALIDATION ở ID thiếu |
| G-8 Independent Review | V-13 fresh reviewer | Verdict APPROVE tại đúng snapshot; không P0/P1 | G-9 với finding packet |
| G-9 Fix | Claude sửa source; Luna quản lý finding/test | Root cause sửa trong boundary; không nới valid tests | Escalate nếu cần đổi policy/API/schema |
| G-10 Re-test | Luna chạy red case trước, impacted V, rồi full required suite cuối | Finding closed bằng evidence mới; snapshot mới được reviewer xác nhận nếu material | Lặp G-9; không coi pass trước fix còn hiệu lực |
| G-11 Final Diff | Luna và reviewer đối candidate cuối với base | Không code đổi sau lần verification cuối; staged scope đúng | Mọi source change quay lại impacted verification |
| G-12 CI | V-14, actual config/run revision | PASS thật hoặc NOT CONFIGURED được report rõ | CI có cấu hình mà fail/pending thì không commit complete |
| G-13 Commit | V-14, quyền thực thi và attribution/hook đạt | Commit đúng allowlist, không push | Báo commit pending; không bypass |
| G-14 Completion Report | Luna tổng hợp mẫu §16 | Tuyên bố đúng evidence/revision/known limits | Không gọi complete nếu required gate chưa đạt |

G-8 không có finding thì G-9=`NOT NEEDED`, G-10 không lặp test vô ích. Nếu chỉ đổi report sau G-11, ghi rõ documentation-only; source/test đổi phải có verification tương ứng mới.

### 15. Coverage và thứ tự ưu tiên

| Finding / phase | Executor | Validation owner | Evidence tối thiểu trước acceptance |
| --- | --- | --- | --- |
| F-1 SQLite | STEP-1 Claude | Luna | V-01 concurrency + transaction; runtime concurrent HTTP V-11 |
| F-6 Restart | STEP-2 Claude | Luna | V-07 state matrix + restart process thật V-11 |
| F-3 Cache/lock | STEP-3 Claude | Luna | V-03 identity/output; V-04 race; V-11 upload lại |
| F-4 Force | STEP-6 Claude | Luna | V-05 counters/source choice; V-11 resume |
| F-2 Vùng | STEP-4 Claude, sau ES-2 | Luna | V-02 compatibility; V-08 UI; V-10 ảnh render |
| F-5 Cue binding | STEP-5 Claude | Luna | V-06 đổi cue/stale submit; V-11 hai CID |
| Toàn patch | STEP-7 Claude | Luna + reviewer độc lập | V-09/12/13/14; không còn ES mở |

**Slices độc lập nếu ES-2 chưa chốt:** F-1 và F-6 đầy đủ; F-3/F-4 chỉ phần không diễn giải vùng cũ. Chưa được ghi “sáu lỗi đã sửa” hoặc commit cả gói với AC-2 chưa xác định.

### 16. Completion Report — mẫu Luna phải điền

```text
Plan ID / version:
Base SHA / candidate snapshot / final commit (nếu có):
Actual executor model / reviewer model + effort:
Status: VALIDATED | BLOCKED | VALIDATED_COMMIT_PENDING | COMMITTED

Đã thay đổi: F-1…F-6 -> STEP -> files -> outcome.
Quyết định đã dùng: DEC-1, ES-2 resolution; deviations nếu có.
Baseline: command, exit, test names/count, log.
Verification: V-ID | expected | actual | status | evidence path.
Runtime: HTTP/media thật; phần ASR/provider fake ghi rõ.
Independent review: reviewer, snapshot, verdict, findings và closure.
Lint / Typecheck / CI: công cụ/run thật hoặc NOT CONFIGURED/NOT RUN.
Final diff: files, scope, hashes, user dirty được giữ.
Commit: hash hoặc lý do pending; hook/attribution; push NOT RUN.
Known limitations: dữ liệu legacy không auto-migrate; stale lock vẫn cần operator;
ASR/dịch thật NOT RUN; các giới hạn khác thực sự còn.
Remaining actions / blockers (nếu có): issue, evidence, impact, options, status.
```

Artifact báo cáo theo convention có sẵn: `docs/ketqua/LOGIC-VAN-HANH-2026-09-16.md`; evidence nặng ở thư mục chạy riêng, không tự commit video/DB/model/screenshots lịch sử. Kết quả cần review được nhưng không chứa credential/nội dung video người dùng.

### 17. Implementation Freedom và handoff cuối

- Claude đọc Phần 1 cùng requirements/verification được tham chiếu ở Phần 2; Luna đọc toàn plan. Phân vai không có nghĩa executor được bỏ qua acceptance criteria.
- Chỉ tự chọn mechanics thỏa local, reversible, không đổi contract và sai có thể phát hiện bằng V đã nêu. Plan im lặng không cấp quyền thêm schema/API/policy.
- Đụng ambiguity consequential mới: nêu Issue, Evidence, Impact, Options, Status; chỉ dừng slice phụ thuộc. Không tự rollback user edits.
- Handoff phải mang plan version đang có hiệu lực, DEC/ES resolutions, exact base/diff snapshot và gate còn thiếu; không chỉ nói “làm theo chat trước”.
- Khi ES-2 resolved, planner viết v2 có exact region contract rồi mới đổi status READY. READY là đủ quyết định để triển khai, không phải bằng chứng code/test đã hoàn tất.
