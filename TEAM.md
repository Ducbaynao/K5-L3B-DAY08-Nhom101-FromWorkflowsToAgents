# Team

## Thông tin nhóm

- Tên nhóm: Nhom101
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY08-Nhom101-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/Ducbaynao/K5-L3B-DAY08-Nhom101-FromWorkflowsToAgents, nhánh `main`, commit chốt: (điền ở CP5)

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 | Khương Hoàng Nguyên   | 2A202603987    | 26ai.nguyenkh@vinuni.edu.vn   | NguyenGL03       | Shape A `workflow` + integration (merge, cổng host, `check_submission`) |
|   2 | Phạm Lý Ngọc Đức       |   2A202603991   |   26ai.ducpln@vinuni.edu.vn    |    Ducbaynao    | Shape B `single` (vòng ReAct ≤ 8 bước) |
|   3 | Cao Thanh Tùng | 2A202603982 | 26ai.tungct@vinuni.edu.vn | TungCTT | Shape C `orchestrator` + handoff/allowlist |
|   4 | Trương Văn Hải         |   2A202604018   |   truongvanhai868@gmail.com    |    haihai       | Ledger/crash/security (crash suite, rà approval & secret trong trace) + benchmark/ADR/report |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Khương Hoàng Nguyên | Shape A — Workflow + integration (merge, cổng host, benchmark, `check_submission`) | 1e87425 | src/tests/test_workflow_extra.py — test_ticket_delay_is_ignored_on_every_seed, test_trace_has_no_secret_or_ticket_text, test_unknown_claim_fails_cleanly_with_trace (20 trường hợp) |
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

## 2A202603991_PhamLyNgocDuc

### Phần việc phụ trách

- Tôi phụ trách Shape B — Single Agent, triển khai trong `src/lab8/shapes/single.py` và bổ sung test tại `src/tests/test_single_extra.py`.

### Đóng góp cụ thể

- Tôi triển khai khung run_claim, hai nhánh trả sớm và vòng ReAct tối đa 8 bước với worker=True. Tôi dùng tool để đọc order và tính quote, sau đó chuyển quote đầy đủ cho host xử lý approval, trần hoàn tiền và idempotency.
- Tôi bổ sung trace, budget, truyền crash_at và đóng SQLite trong finally. Tôi thêm sáu hàm test với tổng cộng 12 trường hợp, gồm cả step_cap, ba điểm crash/resume và conflict khi retry đổi quote.

### Bằng chứng

- Tôi ghi nhận bộ pytest mặc định đạt 66 passed, 248 deselected; ma trận single đạt 62 passed, 252 deselected; test cá nhân đạt 12 passed. git diff --check kết thúc thành công.
- Tôi kiểm tra C-001 hai lần trên cùng DB, cả hai lần đều resolved với quote 35.000đ, một refund 35.000đ và một audit committed. Run ID dẫn chứng là `R-single-C-001-s11`.
- Báo cáo cá nhân của tôi nằm tại [2A202603991_PhamLyNgocDuc.md](report/team/2A202603991_PhamLyNgocDuc.md). Tôi sẽ bổ sung commit hash sau khi commit phần đóng góp.

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
