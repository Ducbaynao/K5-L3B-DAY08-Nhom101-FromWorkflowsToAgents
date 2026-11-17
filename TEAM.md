# Team

## Thông tin nhóm

- Tên nhóm: Nhom101
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY08-Nhom101-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/Ducbaynao/K5-L3B-DAY08-Nhom101-FromWorkflowsToAgents, nhánh `main`

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Khương Hoàng Nguyên   | 2A202603987    | 26ai.nguyenkh@vinuni.edu.vn   | NguyenGL03       | Shape A `workflow` + integration (merge, cổng host, benchmark, `check_submission`); ADR, research card, group report; bonus B3 |
|   2 | Phạm Lý Ngọc Đức       |   2A202603991   |   26ai.ducpln@vinuni.edu.vn    |    Ducbaynao    | Shape B `single` (vòng ReAct ≤ 8 bước) |
|   3 | Cao Thanh Tùng | 2A202603982 | 26ai.tungct@vinuni.edu.vn | TungCTT | Shape C `orchestrator` + handoff/allowlist |
|   4 | Trương Văn Hải         |   2A202604018   |   truongvanhai868@gmail.com    |    haihai868      | Ledger/crash/security (crash suite, rà approval & secret trong trace) + benchmark/ADR/report |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Khương Hoàng Nguyên | Shape A — Workflow + integration (merge, cổng host, benchmark, `check_submission`); rà hidden self-check, research card; viết ADR và group report; bonus B3 (swarm + verifier) | 1e87425, dc20097 | src/tests/test_workflow_extra.py — test_ticket_delay_is_ignored_on_every_seed, test_trace_has_no_secret_or_ticket_text, test_unknown_claim_fails_cleanly_with_trace (20 trường hợp); src/tests/test_bonus_swarm_verified.py — 6 hàm test bonus B3 (23 trường hợp) |
| Phạm Lý Ngọc Đức | Shape B — Single Agent; triển khai run_claim, ReAct, tích hợp host và test cá nhân | 3943c48 | src/tests/test_single_extra.py — test_single_early_exit; test_single_react_reads_order_and_counts_calls; test_single_react_escalates_invisible_order; test_single_step_cap_returns_failed_without_refund; test_single_crash_resumes_with_one_refund; test_single_retry_changed_quote_preserves_committed_refund (12 trường hợp) |
| Cao Thanh Tùng | Shape C — Orchestrator + handoff/allowlist | c58c4c4 | src/tests/test_orchestrator_handoff.py — test_orchestrator_trace_contract_and_no_secret_leak, test_orchestrator_passes_full_quote_for_per_order_cap, test_orchestrator_crash_and_resume_idempotent, test_handoff_rejects_write_tools_and_drops_extra_facts |
| Trương Văn Hải | Ledger/crash/security + benchmark/ADR/report; thực thi crash suite 20/20, rà trace bảo mật, viết test an toàn | 78eae11 | src/tests/test_safety_extra.py — test_approval_expired_denied_on_all_shapes, test_approval_claim_mismatch_denied_on_all_shapes, test_revoked_approval_denied_on_all_shapes, test_order_already_refunded_denied_on_all_shapes, test_t14_top_up_difference_on_all_shapes, test_no_secret_or_pii_leak_in_trace_on_all_shapes (18 trường hợp) |

## Cá nhân

Mỗi thành viên đồng thời tạo một báo cáo riêng trong `report/` theo dạng:

```text
report/team/MSSV_HoTen.md
```

Ví dụ: `report/team/20241234_NguyenVanAn.md`.

Sao chép mục dưới đây cho từng thành viên.

## 2A202603987_KhuongHoangNguyen

### Phần việc phụ trách

- Tôi phụ trách Shape A — Workflow (`src/lab8/shapes/workflow.py`, test tại `src/tests/test_workflow_extra.py`) và integration (Người 1 theo [PHAN_VIEC.md](PHAN_VIEC.md)): chia việc, merge nhánh vào `main`, giữ cổng host xanh, chạy benchmark CP5, hoàn thiện ADR, research card và group report; làm bonus B3 (verifier/aggregator) cho cả nhóm.

### Đóng góp cụ thể

- Tôi viết `PHAN_VIEC.md` chia việc song song cho 4 người: mỗi shape một file và một nhánh riêng, crash suite làm độc lập, benchmark là điểm gom ở CP5.
- Tôi triển khai workflow với 7 bước cố định: `get_claim_view` → `needs_info` → `lookup_order` (`escalated`) → `compute_compensation` → `denied` khi quote 0 → `durability.issue_refund` với quote đầy đủ và `crash_at` → `resolved` / `denied` / `failed`. Ticket không được parse hay ghi vào trace; MockLLM chỉ soạn câu trả lời. Tôi thêm 3 hàm test với 20 trường hợp: T02 bị từ chối trên cả 5 seed, trace của 14 claim không lộ secret hay chữ ticket, claim không tồn tại vẫn có trace.
- Sau mỗi lần merge, tôi chạy lại cổng host và ma trận student, quét trace của single và orchestrator (mỗi shape 70 lần chạy) tìm secret/PII. Tôi phát hiện nhánh tích hợp lệch `main` khiến benchmark lần đầu ra `single 0.000`, bỏ kết quả đó và chạy lại trên code đã merge đủ.
- Tôi chạy crash suite và benchmark 4 shape × 5 seed; điền lại ADR và research card sau khi commit `78eae11` đưa chúng về mẫu trống (sửa tên event trace, commit hash, URL paper MAST); đối chiếu hidden self-check của người 2; viết `group_report.md`.
- Tôi làm bonus B3 cho nhóm: `src/bonus/swarm_verified.py` giữ nguyên swarm và thêm verifier bằng code (đọc lại order, đối chiếu `delay_days` / `status` / `damage_verified`, quote lại tối đa 1 vòng, ghi `verifier_override`); viết 11 claim đối kháng với nhãn suy tay từ `business_rules.md` (`bonus/cases.jsonl`, `bonus/world.json`), script tổng hợp `bonus/b3_summary.py`, 6 hàm test (23 trường hợp) và `report/team/bonus_report.md`.

### Bằng chứng

- Commit workflow và test `1e87425` (PR #1); `PHAN_VIEC.md` `56a5cf1`; ADR, research card, bảng đóng góp, `hidden_selfcheck.json` `6136e5b`; báo cáo cá nhân `d157a3e`.
- Ma trận student của workflow đạt 62 passed; `tests/test_workflow_extra.py` đạt 20 passed. Trên code tích hợp `12936a8`: cổng host 108 passed, ma trận student 248 passed, `crash_safety 20/20`.
- Benchmark (`src/reports/benchmark.json`): workflow pass 1.000, pass^5 1.000, variance 0, cost/success 28.77 VND, thấp nhất trong 4 shape. Run ID dẫn chứng `R-workflow-C-001-s11`; `R-workflow-C-002-s55` trả `denied` trong khi `R-swarm-C-002-s55` trả sai `resolved`.
- `python -m lab8.check_submission` đạt 0 FAIL.
- Bonus B3 (commit `dc20097`): `tests/test_bonus_swarm_verified.py` đạt 23 passed; cổng host 131 passed. `src/reports/bonus_b3.json`: swarm_verified pass 1.000, pass^5 1.000, variance 0 trên public và bộ đối kháng (swarm 0.873 / 0.364), 0 trả sai, 0 leak, cost/success 57.57 / 65.54 VND; hidden self-check khớp workflow 200/200. Trace minh họa `R-swarm_verified-C-002-s55`. Báo cáo: [bonus_report.md](report/team/bonus_report.md).
- Báo cáo cá nhân của tôi nằm tại [2A202603987_KhuongHoangNguyen.md](report/team/2A202603987_KhuongHoangNguyen.md).

## 2A202603991_PhamLyNgocDuc

### Phần việc phụ trách

- Tôi phụ trách Shape B — Single Agent, triển khai trong `src/lab8/shapes/single.py` và bổ sung test tại `src/tests/test_single_extra.py`.

### Đóng góp cụ thể

- Tôi triển khai khung run_claim, hai nhánh trả sớm và vòng ReAct tối đa 8 bước với worker=True. Tôi dùng tool để đọc order và tính quote, sau đó chuyển quote đầy đủ cho host xử lý approval, trần hoàn tiền và idempotency.
- Tôi bổ sung trace, budget, truyền crash_at và đóng SQLite trong finally. Tôi thêm sáu hàm test với tổng cộng 12 trường hợp, gồm cả step_cap, ba điểm crash/resume và conflict khi retry đổi quote.
- Tôi chạy hidden self-check CP5 cho workflow, single và orchestrator trên 40 claim không nhãn với 5 seed, rồi tổng hợp các tiêu chí error/leak_suspect để chuẩn bị bàn giao Người 4.

### Bằng chứng

- Trước merge, tôi ghi nhận bộ pytest mặc định đạt 66 passed, 248 deselected; ma trận single đạt 62 passed, 252 deselected; test cá nhân đạt 12 passed. git diff --check kết thúc thành công.
- Sau khi merge và pull main tại fe41178 ngày 17/11/2026, tôi ghi nhận bộ mặc định đạt 90 passed, 248 deselected và bộ student bốn shape đạt 248 passed, 90 deselected.
- Tôi kiểm tra C-001 hai lần trên cùng DB, cả hai lần đều resolved với quote 35.000đ, một refund 35.000đ và một audit committed. Run ID dẫn chứng là `R-single-C-001-s11`.
- Kết quả hidden self-check có 600 trial, mỗi shape 200 trial, tổng cộng 0 error và 0 leak_suspect. Cả 600 trial có reason=unlabeled; pass rate hidden chính thức chờ grader giảng viên. [Hidden self-check](src/reports/hidden_selfcheck.json)
- Phần đóng góp của tôi thuộc commit 3943c48 và đã tích hợp vào main qua PR #2, merge commit fe41178. [PR #2](https://github.com/Ducbaynao/K5-L3B-DAY08-Nhom101-FromWorkflowsToAgents/pull/2)
- Báo cáo cá nhân của tôi nằm tại [2A202603991_PhamLyNgocDuc.md](report/team/2A202603991_PhamLyNgocDuc.md).
- Báo cáo cá nhân của tôi nằm tại [2A202603991_PhamLyNgocDuc.md](report/team/2A202603991_PhamLyNgocDuc.md). Tôi sẽ bổ sung commit hash sau khi commit phần đóng góp.

## 2A202603982_CaoThanhTung

### Phần việc phụ trách

- Tôi phụ trách Shape C — Orchestrator + Handoff (Người 3 theo [PHAN_VIEC.md](PHAN_VIEC.md)), triển khai trong `src/lab8/shapes/orchestrator.py` và bổ sung test tại `src/tests/test_orchestrator_handoff.py`.

### Đóng góp cụ thể

- Tôi đọc claim qua `get_claim_view` (không dùng `SELECT *`) và xử lý đủ các nhánh: `unknown_claim` (`failed`), thiếu `order_id` (`needs_info`), đơn không visible hoặc sai principal (`escalated`), quote bằng 0 (`denied`, không ghi ledger), quote dương thì gọi `durability.issue_refund` với quote đầy đủ để host kiểm approval và trừ phần đã hoàn (T13, T14).
- Tôi dựng handoff bằng `make_handoff` với `facts={}` và chỉ cấp tool đọc (`lookup_order`, `lookup_policy`, `lookup_refund_history`, `compute_compensation`) cho `run_readonly_investigators`. Trace ghi handoff đã sanitize qua `safe_dump`, không ghi parent context.
- Tôi truyền `crash_at` vào `issue_refund`; khi gặp `InjectedCrash` thì ghi event `crash`, flush trace và ném lại, không nuốt exception.
- Tôi thêm 4 test: trace contract v1 và không rò rỉ secret, T14 truyền quote đầy đủ, crash/resume giữ một refund, `make_handoff` từ chối tool ghi và lọc fact thừa.

### Bằng chứng

- Tôi ghi nhận `python -m pytest -q tests/test_orchestrator_handoff.py` đạt 4 passed; cổng host lúc đó đạt 58 passed, 248 deselected; ma trận student của orchestrator đạt 62 passed.
- Benchmark (`src/reports/benchmark.json`): orchestrator pass 1.000, pass^5 1.000, variance 0, cost/success 56.65 VND (5.57 tool call/trial vì investigator đọc thêm policy và lịch sử hoàn tiền). Hidden self-check: 200 trial, 0 error, 0 leak_suspect.
- Phần đóng góp của tôi thuộc commit c58c4c4 và đã tích hợp vào `main`. [Commit c58c4c4](https://github.com/Ducbaynao/K5-L3B-DAY08-Nhom101-FromWorkflowsToAgents/commit/c58c4c4a79f98c4c7a8e0c06bfd74b2ffb15455a)
- Báo cáo cá nhân của tôi nằm tại [2A202603982_CaoThanhTung.md](report/team/2A202603982_CaoThanhTung.md).

## 2A202604018_TruongVanHai

### Phần việc phụ trách

- Tôi phụ trách Ledger / Crash / Security (Người 4 theo [PHAN_VIEC.md](PHAN_VIEC.md)), triển khai kiểm thử an toàn tại `src/tests/test_safety_extra.py` và thực thi crash suite `src/reports/crash.json`.

### Đóng góp cụ thể

- Tôi thực thi `python -m lab8.crash_test --count 20 --out reports/crash.json`, xác nhận đạt 20/20 kịch bản ngắt điện đột ngột và idempotency.
- Tôi chạy demo `python -m lab8.demo.buggy_workflow` và ghi nhận phân tích về việc checkpoint đơn lẻ không thể thay thế cho ledger với khóa duy nhất `refund:{claim_id}`.
- Tôi xây dựng 18 trường hợp kiểm thử trong `src/tests/test_safety_extra.py` chạy trên cả 3 shape (workflow, single, orchestrator) kiểm tra các kịch bản approval hết hạn, approval khác claim, approval bị thu hồi, đơn đã hoàn đủ, hoàn bù chênh lệch (T14) và bảo mật trace không rò rỉ secret.
- Tôi quét regex toàn bộ thư mục `src/traces/` xác nhận không có `CANARY_SECRET_*`, `parent_secret` hay authorization header.

### Bằng chứng

- Tôi ghi nhận kết quả chạy `python -m lab8.crash_test --count 20 --out reports/crash.json` đạt `crash_safety 20/20`.
- Bộ test cá nhân `python -m pytest -q tests/test_safety_extra.py` đạt `18 passed in 1.22s`. Cổng host `python -m pytest -q` đạt 108 passed.
- Báo cáo cá nhân của tôi nằm tại [2A202604018_TruongVanHai.md](report/team/2A202604018_TruongVanHai.md). Tôi sẽ bổ sung commit hash sau khi commit phần đóng góp trên feat/safety-tests.
