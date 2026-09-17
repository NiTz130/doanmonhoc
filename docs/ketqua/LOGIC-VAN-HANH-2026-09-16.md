# Completion Report — logic-van-hanh-2026-09-16 v2

Plan ID / version: logic-van-hanh-2026-09-16 / v2

Base SHA / candidate snapshot / final commit:
d248c7bc89f436286aaa772c73dd1e9c5b1b3201 / branch vung-mo-nhieu-cue,
working tree chưa commit / không có

Actual executor: Anthropic Claude Opus 5, STEP-1…7 đã bàn giao.
Validator: GPT-5.6 Luna, effort Ultra.
Independent reviewer: GPT-5.6 Luna Max router, fresh read-only context; không có
runtime Luna Ultra trong registry.
Status: BLOCKED — G-8 trả NEEDS VALIDATION vì reviewer không hoàn tất; G-13 commit
chưa được yêu cầu.

## Outcome

Candidate hiện tại đã retest xanh toàn bộ các reproduction từng được ghi là đỏ:
7/7 PASS, full offline 34/34 PASS, V-10 media thật PASS, V-11 HTTP thật PASS.
Không có product source nào được Luna sửa; không nới hoặc xoá test hợp lệ.
Report trước có 7 finding P1 ở một snapshot trung gian; chúng không còn tái hiện
ở candidate hiện tại và được ghi là CLOSED/RETESTED bên dưới.

## Gate summary

| Gate | Status | Evidence / reason |
| --- | --- | --- |
| G-0 Preflight | PASS, có deviation | Candidate không có BEFORE thật; so sánh ở detached worktree base, không reset checkout. |
| G-1 Implement | PASS handoff | Claude bàn giao STEP-1…7; DEC-1 và DEC-2/LD-7 không bị mở lại. |
| G-2 Self Review | PASS | Harness dùng fake đúng seam; phép tính vùng, cache, race và stale đều có assertion thật. |
| G-3 Diff | PASS | 13 tracked files trong allowlist; một runtime harness và report là untracked candidate; user dirty giữ nguyên. |
| G-4 Syntax/tooling | PASS | compileall, node --check, git diff --check exit 0; lint/typecheck không cấu hình. |
| G-5 Test | PASS | 7/7 reproduction, full offline 34/34, browser 3/3; test hợp lệ được giữ nguyên. |
| G-6 Runtime | PASS | V-10 ffmpeg/media thật và V-11 uvicorn/HTTP thật; ASR/provider fake được ghi rõ. |
| G-7 Requirement matrix | PASS WITH DOC NOTE | AC/CS/IC/LD/MD matrix đủ; README còn số đếm offline cũ là P2 documentation drift. |
| G-8 Independent review | NEEDS VALIDATION | Luna Max fresh reviewer bị timeout/interrupt rồi shutdown, không có source review/verdict hoàn chỉnh; không gọi là APPROVE. |
| G-9 Fix | NOT NEEDED hiện tại | Không còn reproduction source-level đỏ ở candidate snapshot này. |
| G-10 Re-test | PASS | Đã chạy từng reproduction → full offline → runtime bị ảnh hưởng. |
| G-11 Final diff | BLOCKED | Diff đã khóa và kiểm tra lại; thiếu verdict độc lập hoàn chỉnh. |
| G-12 CI | NOT CONFIGURED | Không có .github/workflows; không tạo CI mới. |
| G-13 Commit | PENDING | Không commit/push trong lượt validation này. |
| G-14 Report | PASS | Bản này cập nhật evidence hiện tại và ghi rõ G-8 blocker. |

## G-0 / V-00: baseline và isolation

Baseline BEFORE trong candidate checkout không tồn tại: source đã được sửa trước
khi Luna nhận bàn giao. Không dựng baseline giả ở HEAD hiện tại và không reset
working tree. Tôi tạo worktree detached tại:

C:\Users\BINH\AppData\Local\Temp\logic-van-hanh-2026-09-16-base

Worktree này ở đúng base SHA và chạy:

C:\codev2\doanmonhoc\.venv\Scripts\python.exe test_pipeline.py

Kết quả base: 17/17 PASS, exit 0. Browser base cũng chạy 3/3 PASS với API mock.
Chi tiết V-00 nằm ở:

C:\Users\BINH\AppData\Local\Temp\logic-van-hanh-2026-09-16-luna-ultra\v00-g0-baseline.md

Đây là evidence so sánh base/isolation, không phải nhãn BEFORE của candidate.
Các test candidate dùng temporary root; V-11 xác nhận cleanup sau process.

Hash dirty được kiểm tra trước/sau:

- AGENTS.md = E83CD3AB1350FBF764F0E602A051FAC59BB34DAF20BB6932179840883A7F4DDE
- CLAUDE.md = D18F5218027E229C1744A5EA8C0A619568684B2533733D671E99AF99834594DE

AGENTS.md, CLAUDE.md, docs/plans/ và untracked docs của người dùng không bị
sửa, stage, commit hay xoá.

## Reproduction → full offline → runtime

### Reproduction từng finding

Các lệnh được chạy tuần tự trong current checkout. Mỗi log dưới đây có
REPRO_PASS và PROCESS_EXIT=0. Một lượt sentinel trước đó dùng quoting sai và
ra SyntaxError; lượt đó đã bị loại khỏi evidence, không dùng làm kết luận.

| Finding | Reproduction | Result | Evidence |
| --- | --- | --- | --- |
| F-LUNA-1 | test_vung_cue_source_invalidation_before_side_effect | PASS | ...\reproductions\F-LUNA-1-stale-cue.log |
| F-LUNA-2 | test_cached_region_mode_is_authoritative | PASS | ...\reproductions\F-LUNA-2-cache-mode.log |
| F-LUNA-3 | test_legacy_region_without_mode_is_not_valid_cache | PASS | ...\reproductions\F-LUNA-3-legacy-mode.log |
| F-LUNA-4 | test_api_mode_validation_before_mutation | PASS | ...\reproductions\F-LUNA-4-null-mode.log |
| F-LUNA-5 | test_api_scheduler_failure_cleans_admission | PASS | ...\reproductions\F-LUNA-5-scheduler.log |
| F-LUNA-6 | test_api_resume_claim_is_single_winner | PASS | ...\reproductions\F-LUNA-6-resume-race.log |
| F-LUNA-7 | test_api_cue_index_out_of_range_is_rejected | PASS | ...\reproductions\F-LUNA-7-cue-range.log |

Các assertion hợp lệ không bị xoá/đổi để né lỗi. Bảy finding P1 của report cũ:
stale cue ordering, cache mode authority, missing mode, explicit null, scheduler
cleanup, resume race và out-of-range cue đều CLOSED/RETESTED ở snapshot này.

### Full offline

Command:

C:\codev2\doanmonhoc\.venv\Scripts\python.exe test_pipeline.py

Kết quả sau chuỗi reproduction: 34 collected, 34 PASS, exit 0.
Log:

C:\Users\BINH\AppData\Local\Temp\logic-van-hanh-2026-09-16-luna-ultra\v09-after-repros-final.log

Browser check trước đó trên đúng candidate, static server loopback, API mock:
3/3 PASS; screenshot output dùng thư mục temp:

C:\Users\BINH\AppData\Local\Temp\logic-van-hanh-2026-09-16-luna-ultra\frontend-final

### Runtime bị ảnh hưởng

V-10 chạy test_pipeline.py --smoke trong temp cwd, dùng ffmpeg/ffprobe thật,
fixture 1280x720 và 1920x1080, một lần encode, audio, replacement mask và
inclusive boundary frames. Kết quả PASS; log:

C:\Users\BINH\AppData\Local\Temp\logic-van-hanh-2026-09-16-luna-ultra\v10-smoke-after-repros-final.log

Frame evidence:

C:\Users\BINH\AppData\Local\Temp\logic-van-hanh-2026-09-16-luna-ultra\smoke-after-repros-2

V-11 chạy process uvicorn thật một worker, HTTP bằng urllib, multipart/JSON,
SQLite/filesystem/lock thật và ffmpeg/output thật. Upload race, resume race,
stale snapshot, restart/orphan, crash giữ lock, cache reuse và output retention
đều PASS. Counters: audio=7, asr=7, dich=5, render=6; temp_root_cleaned=true;
output SHA256 =
3c009856541e4bbeeb7594402e954b43fbdb657e26c4e1aa2a94b2ae016d2fd8.

Log:

C:\Users\BINH\AppData\Local\Temp\logic-van-hanh-2026-09-16-luna-ultra\v11-runtime-after-repros-final.log

Results:

C:\Users\BINH\AppData\Local\Temp\logic-van-hanh-2026-09-16-luna-ultra\runtime\runtime-results.json

ASR thật, DeepSeek thật, credential, paid translation và model download:
NOT RUN — ngoài scope và không được phép tự gọi. ASR và translation/provider fake
chỉ được dùng ở seam đã cho phép; không mock phép tính vùng, renderer, HTTP hay
admission cần chứng minh.

## V-01…V-09 / G-4 evidence

| V | Expected | Actual | Status |
| --- | --- | --- | --- |
| V-01 | concurrent request, lifecycle, rollback/FK | 40 GET, close và rollback đều đúng | PASS |
| V-02 | additive/replacement, legacy, mode/null/range/cache boundaries | offline + reproduction + media assertions đều đúng | PASS |
| V-03 | content+group identity, cache, CID/output isolation | canonical/no-overwrite/namespace/output riêng đúng | PASS |
| V-04 | atomic upload/resume admission, scheduler cleanup | upload và resume race đều single-winner; cleanup đúng | PASS |
| V-05 | force/resume counters và source pin | ASR/audio/dịch counters đúng; embedded source không bị chọn nhầm | PASS |
| V-06 | cue content signature và stale snapshot | text/time/order đổi làm miss; CID cũ POST 409; coordinator stale side effect bị chặn | PASS |
| V-07 | restart orphan/terminal/lock behavior | orphan thành loi; terminal/download giữ; lock sót giữ | PASS |
| V-08 | frontend behavior and fallback | browser 3/3, 360/768/1440, stale retry, mode payload | PASS |
| V-09 | full offline/CLI | 34/34 PASS, exit 0 | PASS |

G-4:

- Python compileall trên api, pipeline, main.py và test files: exit 0.
- node --check web/app.js và test/frontend.cjs: exit 0.
- git diff --check: exit 0, chỉ cảnh báo CRLF conversion.
- Lint/typecheck: NOT CONFIGURED; không cài công cụ mới.

## Requirement matrix G-7

| ID | Status | Evidence |
| --- | --- | --- |
| AC-1 | PASS | V-01, V-11 |
| AC-2 | PASS | V-02, V-08, V-10 |
| AC-3 | PASS | V-03, V-11 |
| AC-4 | PASS | V-04, V-11 |
| AC-5 | PASS | V-05, V-11 |
| AC-6 | PASS | V-06, V-11 |
| AC-7 | PASS | V-07, V-11 |
| AC-8 | PASS | V-03, V-06, V-09, V-10 |
| AC-9 | PENDING | G-8/G-11 chưa hoàn tất |
| CS-1 | PASS | V-03, V-11 |
| CS-2 | PASS | V-02, artifact/manifest cache checks |
| CS-3 | PASS | V-05, translation/manual/cache regression |
| CS-4 | PASS | V-02, V-05 |
| CS-5 | PASS | V-04, V-06, V-07 |
| CS-6 | PASS | V-02, V-08, V-10 |
| CS-7 | PASS | V-02, V-10, group/default tests |
| CS-8 | PASS | V-01, V-11 |
| CS-9 | PASS | V-07, V-11 |
| CS-10 | PASS | diff/syntax/scope inspection |
| CS-11 | PENDING | G-8/G-11 |
| IC-1 | PASS | API delegates to coordinator; no new framework |
| IC-2 | PASS | existing Python/JS/SQLite/Playwright stack |
| IC-3 | PASS | atomic filesystem/media and scheduler cleanup |
| IC-4 | PASS | V-03 group/namespace identity |
| IC-5 | PASS | V-02 cue range validation |
| IC-6 | PASS | V-10 ffmpeg and geometry |
| IC-7 | PASS | V-05 force/source pin |
| IC-8 | PASS | no paid API, credential, push or deploy |
| IC-9 | PENDING | independent verdict chưa có |
| LD-1 | PASS | canonical SHA256 + exact group + no overwrite |
| LD-2 | PASS | connection option and request lifecycle |
| LD-3 | PASS | checkpoint/source/force fields |
| LD-4 | PASS | cue hash, snapshot and pre-side-effect guard |
| LD-5 | PASS | startup orphan reconciliation |
| LD-6 | PASS | atomic claim, upload/resume/scheduler cleanup |
| LD-7 | PASS | mode validation, additive legacy, replacement mask/cache |
| MD-1 | PASS | no extra queue/schema abstraction |
| MD-2 | PASS | fakes only at provider/ASR seams; media/calculation real |
| MD-3 | PASS | existing tests plus only test/runtime_logic.py |
| DEC-1 | PASS | content + exact group identity |
| DEC-2 | PASS | replacement new, additive legacy |

P2 documentation note: README.md còn hai dòng mô tả 17 test offline trong khi
runner hiện tại collect 34. Không ảnh hưởng product behavior/AC; nên cập nhật
ở lượt tài liệu kế tiếp, không đổi trong validation này để giữ ranh giới owner.

## G-8 / G-11 / G-12 / G-13

Reviewer độc lập được gọi với agent type
codex_auto_model_router_luna_max, agent id
01a0aabd-6b36-75e1-b054-44a135b409eb, fork_context=false, read-only; nhận full
tracked + untracked candidate diff, plan v2, base SHA, evidence và dirty
exclusions. Yêu cầu là trace HTTP → job → checkpoint → cache → render, SQLite,
legacy semantics, race/stale/restart và chạy boundary test.

Sau hai lượt chờ 120 giây, một interrupt yêu cầu trả verdict ngắn, rồi thêm lượt
chờ 60 giây, agent vẫn không trả completed result và bị đóng ở trạng thái
shutdown. Không có source review, finding list hay APPROVE để trích dẫn.
G-8 = NEEDS VALIDATION, không phải PASS; đây là giới hạn capability/runtime của
reviewer hiện có, không phải bằng chứng product fail.

Final tracked diff sau khi reviewer shutdown và sau lần kiểm tra local cuối:

13 files, 1249 insertions, 119 deletions:
README.md, api/app.py, api/viec.py, pipeline/db.py, pipeline/dieu_phoi.py,
pipeline/markbox.py, pipeline/render.py, pipeline/srt.py, test/frontend.cjs,
test_pipeline.py, tests_api.py, tests_smoke.py, web/app.js.

Allowed untracked candidate: test/runtime_logic.py và report này. Six B screenshots
do frontend test ghi đè đã được restore đúng base blob; không đưa vào diff.
git diff --cached --name-status rỗng. Không có dependency, schema, CI workflow,
model, video, DB, credential hay screenshot test được thêm vào candidate.

CI: NOT CONFIGURED; không trigger remote CI.
Commit: NOT RUN; không stage/commit/push. Attribution chưa áp dụng vì chưa commit.

## Remaining actions

1. Cần một independent reviewer đúng capability hoàn tất review tại cùng snapshot
   để đóng G-8/G-11 và AC-9/CS-11/IC-9.
2. Không có source finding cần trả Claude ở lượt này: 7 reproduction và full
   offline đã xanh; nếu reviewer mới tìm lỗi, gửi finding kèm reproduction cho
   Claude, không nới test.
3. README test-count note là việc tài liệu P2; không tự đổi product policy.
