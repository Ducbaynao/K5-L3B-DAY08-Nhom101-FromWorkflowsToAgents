# Báo cáo cá nhân — 2A202603987_KhuongHoangNguyen

## 1. Thông tin thành viên

- Họ tên: Khương Hoàng Nguyên
- MSSV: 2A202603987
- Email: 26ai.nguyenkh@vinuni.edu.vn
- GitHub: NguyenGL03

## 2. Phần việc phụ trách

Người 1 trong phân việc của nhóm (`PHAN_VIEC.md`):

- **Shape A — `workflow`** (`src/lab8/shapes/workflow.py`): các bước Python cố định, tiền do code tính, host là nơi duy nhất ghi ledger.
- **Integration:** chia việc cho 4 người, merge nhánh vào `main`, giữ cổng host xanh sau mỗi lần merge.
- **CP5:** chạy crash suite, benchmark 4 shape × 5 seed, tự kiểm trên `student_drop/`, đưa `check_submission` về `0 FAIL, 0 WARN` (điền ADR, research card, bảng đóng góp).
- **Rà soát và báo cáo nhóm:** đối chiếu kết quả hidden self-check của người 2, rà và sửa `research_card.md`, viết `group_report.md`.

## 3. Đóng góp cụ thể

**CP1 — cài đặt và chia việc**

- Cài môi trường trên Windows (Python 3.13), xác nhận smoke pass, cổng host xanh, ma trận student `186 failed, 62 passed` đúng như CHECKPOINTS.
- Điền thông tin nhóm trong `TEAM.md`; viết `PHAN_VIEC.md` (commit `56a5cf1`): nhánh, file, test và mốc giờ cho từng người. Cơ sở để chạy song song: mỗi shape là một file riêng, test tách theo shape, crash suite chỉ gọi host nên người 4 làm được ngay từ đầu.

**CP2 + CP3 — shape workflow** (commit `1e87425`, PR #1)

- `run_claim` mở kết nối và luôn đóng trong `finally` (trên Windows, kết nối còn mở sẽ khóa file SQLite tạm của benchmark).
- 7 bước cố định: `get_claim_view` → thiếu `order_id` thì `needs_info` → `lookup_order` (không thấy đơn / sai principal thì `escalated`) → `compute_compensation` từ cột `delay_days` → quote 0 thì `denied` và không gọi host → quote > 0 thì `durability.issue_refund` với **quote đầy đủ** → `resolved` / `denied` / `failed` theo kết quả host.
- Mọi nhánh return đi qua một hàm `done()` gọi `finish()`, nên nhánh nào cũng có trace đúng contract v1.
- CP3: truyền `crash_at` vào `issue_refund`; khi `InjectedCrash` thì ghi event `crash`, flush trace rồi ném lại, không nuốt.
- Quyết định kỹ thuật:
  - Ticket **không bao giờ được parse hay ghi vào trace**. Shape không đọc số ngày trễ khách tự khai, nên lỗi kiểu swarm ở T02 seed 55 không thể xảy ra.
  - Không tự trừ phần đã hoàn trước: host đã trừ, shape trừ thêm thì T14 sai.
  - MockLLM chỉ gọi 1 lần để soạn câu trả lời, không ảnh hưởng tiền.

**Test thêm:** `src/tests/test_workflow_extra.py` (20 trường hợp, chạy trong cổng host)

- `test_ticket_delay_is_ignored_on_every_seed`: T02 phải `denied`, không có dòng ledger, trên cả 5 seed.
- `test_trace_has_no_secret_or_ticket_text`: trace của 14 claim public không chứa `CANARY_`, `Bearer`, chữ trong ticket.
- `test_unknown_claim_fails_cleanly_with_trace`: claim không tồn tại thì `failed`, vẫn có trace.

**Integration và CP4**

- Sau mỗi lần merge (orchestrator, single, safety-tests) chạy lại cổng host và ma trận student; quét trace của orchestrator và single (mỗi shape 14 claim × 5 seed = 70 lần chạy) tìm `CANARY_`, `Bearer`, `parent_secret`, `raw_headers`, `phone`, `address`, `internal_note`: không có.
- Phát hiện nhánh `feat/workflow` ở máy chưa có code `single` (benchmark lần đầu ra `single = 0.000`); bỏ kết quả sai, merge `main` vào nhánh, chạy lại.

**CP5 — benchmark và tài liệu** (commit `6136e5b`)

- Chạy lại crash suite và benchmark trên code cuối; kết quả trùng với file người 4 đã commit.
- Phát hiện commit `78eae11` đã đưa ADR, research card và group report về mẫu trống. Điền lại ADR và research card, sửa các chỗ sai của bản cũ: tên event trong trace không khớp code, commit hash không trỏ đúng code được chấm, URL paper MAST sai (`2503.11234` → `2503.13657`), câu khẳng định quét trace không có bằng chứng.
- Bổ sung bảng đóng góp đủ 4 người.

**Rà soát cuối và báo cáo nhóm**

- **Đối chiếu hidden self-check của người 2** (báo cáo của Phạm Lý Ngọc Đức): đọc lại `src/reports/hidden_selfcheck.json` và xác nhận số liệu khớp với báo cáo của Đức.
  - 600 trial, 40 claim `C-H01`…`C-H40`, 5 seed; mỗi shape 0 `error`, 0 `leak_suspect`, 90 resolved / 95 denied / 10 escalated / 5 needs_info.
  - Run id `R-single-C-H01-s11` có trong file.
  - Kiểm thêm: ba shape cho cùng status ở cả 600 cặp (claim, seed), và không claim nào đổi status giữa các seed.
  - Ghi chú: Đức chạy với đường dẫn `../instructor/student_drop/`, nhóm để `student_drop/` ở gốc repo. Hai lần chạy ra cùng con số.
- **Rà `research_card.md`:** giữ R2 (MAST).
  - Thêm confounder vào METHOD: "shape" gói chung topology, số model call và `REFERENCE_WEAKNESS` chỉ bật ở seed chia hết cho 5.
  - Gán lỗi của swarm vào failure mode cụ thể của MAST: "No or incomplete verification", và nêu cách xếp khác là "Disobey task specification".
  - Thêm nhận xét: lỗi chỉ lộ ở 1/5 seed, nên cần đo pass^5 và variance.
- **Viết `group_report.md`:**
  - Cách chia việc song song và thứ tự merge.
  - Bảng so sánh 3 shape (ai chọn bước, ai tính tiền, ai ghi tiền), trace event từng shape.
  - Bảng benchmark đủ cột (gồm p95 steps), crash 20/20, hidden self-check.
  - 5 khó khăn kèm bằng chứng.
  - Hạn chế: `decide` của single là luật Python cố định nên benchmark đo chi phí vòng ReAct chứ chưa đo rủi ro; 3 shape cùng dùng `compute_compensation` nên khớp 600/600 không phải kiểm chứng độc lập.

## 4. Bằng chứng

- Commit:
  - `1e87425`: workflow và test
  - `56a5cf1`: `PHAN_VIEC.md`
  - `6136e5b`: ADR, research card, bảng đóng góp, `hidden_selfcheck.json`
  - Commit sau `6136e5b`: rà research card, `group_report.md`, cập nhật báo cáo này và `TEAM.md`
- File: `src/lab8/shapes/workflow.py`, `src/tests/test_workflow_extra.py`, `report/team/decision_adr.md`, `report/team/research_card.md`, `report/team/group_report.md`.
- Kết quả chạy trong `src/` trên code cuối (`12936a8`):

  | Lệnh | Kết quả |
  | --- | --- |
  | `python -m pytest -q` | `108 passed, 248 deselected` |
  | `python -m pytest -q -m student -o addopts=` | `248 passed` (workflow 62/62) |
  | `python -m lab8.crash_test --count 20 --out reports/crash.json` | `crash_safety 20/20` |
  | `python -m lab8.benchmark ... --out reports/benchmark.json` | workflow pass 1.000, pass^5 1.000, variance 0, cost/success 28.77 VND |
  | Self-check `student_drop/` (3 shape × 40 claim × 5 seed) | 600 trial, 0 `error`, 0 `leak_suspect` |
  | `python -m lab8.check_submission` | `0 FAIL, 0 WARN` |

- Run id dẫn chứng:
  - `R-workflow-C-001-s11`: trace `claim → lookup_order → quote → issue_refund → decision`.
  - `R-workflow-C-014-s11`: `resolved`, `proposal_amount` 150.000, ledger 120.000 (host trừ 30.000 đã hoàn).
  - `R-workflow-C-002-s55`: `denied`, trong khi `R-swarm-C-002-s55` trả sai `resolved`.

## 5. Công cụ AI đã dùng

- **Công cụ:** Claude Code (Claude Opus 5.5) trong VS Code.
- **Dùng vào việc gì:** đọc đề và contract, đề xuất cách chia việc, viết `workflow.py` và `test_workflow_extra.py`, chạy test, benchmark và các lệnh git, quét trace, soạn ADR, research card, group report và báo cáo này; đọc `hidden_selfcheck.json` để đối chiếu với báo cáo của người 2.
- **Cách tự kiểm tra:**
  - Đối chiếu từng nhánh của `workflow.py` với bảng trong `docs/business_rules.md` và `docs/contracts.md`.
  - Xác nhận bằng test thật, không dựa vào lời AI: ma trận student 62/62, cổng host, crash 20/20.
  - Số liệu trong ADR và research card lấy từ `src/reports/benchmark.json`, kiểm tra run id có trong file và commit hash có trên `main`.
  - Khi benchmark lần đầu ra `single = 0.000`, kiểm lại nhánh thay vì dùng số đó.
  - URL paper MAST được kiểm lại vì bản cũ ghi sai.

## 6. Tự đánh giá

- workflow chạy theo 1 flow predictable, các step đều follow rule/policy nên chỉ cần code quyết định. Chỉ cần thêm 1 LLM hỗ trợ cho phần viết phản hồi. Truyền đầy đủ vì host là nới duy nhất gh tiền, vì vậy mọi thứ đều cần host tự kiểm. Trace không chứa thông tin nhạy cảm như PII, bearer, canary,..

- Đóng góp đúng vần việc, selfcheck và doublecheck cho kết quả của các thành viên khác 
...
