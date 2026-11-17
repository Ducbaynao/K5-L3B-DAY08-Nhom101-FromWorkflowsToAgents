# Team

## Thông tin nhóm

- Tên nhóm: Nhom101
- Lớp: L3B
- Repo nhóm: `K5-L3B-DAY08-Nhom101-FromWorkflowsToAgents` (xem [SUBMISSION.md](SUBMISSION.md))
- URL repo, nhánh nộp, commit chốt: https://github.com/Ducbaynao/K5-L3B-DAY08-Nhom101-FromWorkflowsToAgents, nhánh `main`, commit chốt: (điền ở CP5)

## Thành viên

| STT | Họ tên | MSSV | Email | GitHub | Vai trò |
| --: | ------ | ---- | ----- | ------ | ------- |
|   1 |        |      |       |        | Shape A `workflow` + integration (merge, cổng host, `check_submission`) |
|   2 | Phạm Lý Ngọc Đức       |   2A202603991   |   26ai.ducpln@vinuni.edu.vn    |    Ducbaynao    | Shape B `single` (vòng ReAct ≤ 8 bước) |
|   3 |        |      |       |        | Shape C `orchestrator` + handoff/allowlist |
|   4 |        |      |       |        | Ledger/crash/security (crash suite, rà approval & secret trong trace) + benchmark/ADR/report |

Gợi ý chia vai:

- Nhóm 6 người: integration; workflow; single agent; orchestrator; ledger/policy/crash; eval/report.
- Nhóm 4 người: workflow + integration; single; orchestrator + handoff; ledger + evaluation.

## Bảng đóng góp

`python -m lab8.check_submission` đọc bảng này bằng máy: giữ nguyên tiêu đề `## Bảng đóng góp` và các cột. Mỗi người một dòng: commit có nội dung và ít nhất một test đã thêm hoặc sửa.

| Người | Vai | Commit | Test đã thêm hoặc sửa |
| --- | --- | --- | --- |
| Phạm Lý Ngọc Đức | Shape B — Single Agent; triển khai run_claim, ReAct, tích hợp host và test cá nhân | [3943c48](https://github.com/Ducbaynao/K5-L3B-DAY08-Nhom101-FromWorkflowsToAgents/commit/3943c481d17515f73d9b92f41f6c9f43e535c3da), đã merge qua PR #2 tại fe41178 | src/tests/test_single_extra.py — test_single_early_exit; test_single_react_reads_order_and_counts_calls; test_single_react_escalates_invisible_order; test_single_step_cap_returns_failed_without_refund; test_single_crash_resumes_with_one_refund; test_single_retry_changed_quote_preserves_committed_refund (12 trường hợp) |

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
- Tôi chạy hidden self-check CP5 cho workflow, single và orchestrator trên 40 claim không nhãn với 5 seed, rồi tổng hợp các tiêu chí error/leak_suspect để chuẩn bị bàn giao Người 4.

### Bằng chứng

- Trước merge, tôi ghi nhận bộ pytest mặc định đạt 66 passed, 248 deselected; ma trận single đạt 62 passed, 252 deselected; test cá nhân đạt 12 passed. git diff --check kết thúc thành công.
- Sau khi merge và pull main tại fe41178 ngày 17/11/2026, tôi ghi nhận bộ mặc định đạt 90 passed, 248 deselected và bộ student bốn shape đạt 248 passed, 90 deselected.
- Tôi kiểm tra C-001 hai lần trên cùng DB, cả hai lần đều resolved với quote 35.000đ, một refund 35.000đ và một audit committed. Run ID dẫn chứng là `R-single-C-001-s11`.
- Kết quả hidden self-check có 600 trial, mỗi shape 200 trial, tổng cộng 0 error và 0 leak_suspect. Cả 600 trial có reason=unlabeled; pass rate hidden chính thức chờ grader giảng viên. [Hidden self-check](src/reports/hidden_selfcheck.json)
- Phần đóng góp của tôi thuộc commit 3943c48 và đã tích hợp vào main qua PR #2, merge commit fe41178. [PR #2](https://github.com/Ducbaynao/K5-L3B-DAY08-Nhom101-FromWorkflowsToAgents/pull/2)
- Báo cáo cá nhân của tôi nằm tại [2A202603991_PhamLyNgocDuc.md](report/team/2A202603991_PhamLyNgocDuc.md).
