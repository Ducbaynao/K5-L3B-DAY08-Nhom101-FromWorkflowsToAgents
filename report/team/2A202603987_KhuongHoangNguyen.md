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
- **Bonus B3 — verifier/aggregator** (cho cả nhóm): `src/bonus/`, `src/tests/test_bonus_swarm_verified.py`, `report/team/bonus_report.md`.

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

**Bonus B3 — swarm + verifier bằng code** (commit `dc20097`)

- **Chọn topic:** chọn B3 vì nối thẳng vào ADR (vì sao chọn workflow thay vì swarm) và chạy được qua `--extra-shape`, nên grader chấm được trên hidden.
- **`src/bonus/swarm_verified.py`:** giữ nguyên luồng swarm, kể cả điểm yếu ở seed chia hết cho 5. Thêm `verify_facts` ngay sau bước quote:
  - đọc lại order qua `lookup_order`;
  - đối chiếu `delay_days`, `status`, `damage_verified` với dữ kiện đã dùng để quote;
  - nếu lệch thì quote lại bằng `compute_compensation` (tối đa 1 vòng) và ghi `verifier_override`.
- **Đặt verifier trước nhánh `proposal <= 0`**, không chỉ trước lệnh ghi. Lý do: để sửa được cả trường hợp swarm từ chối sai khi ticket nói thiếu số ngày trễ (B-002, B-008).
- **11 claim đối kháng** (`bonus/cases.jsonl`, `bonus/world.json`): nói quá, nói thiếu, nói dối hỏng hàng, nhiều con số, injection, ngay dưới ngưỡng, đơn hủy, approval thấp hơn quote, approval hết hạn.
  - Nhãn suy tay từ `business_rules.md`, mỗi claim có `label_note`; không sinh nhãn bằng `compensation.quote`.
  - Trước khi tin nhãn, tôi dự đoán tay 7 trial swarm sẽ fail ở seed 55. Lần chạy thử ra đúng 7 trial đó, và workflow đạt 55/55.
- **`bonus/b3_summary.py`:** đếm số lần verifier can thiệp và safety counts (trả sai, từ chối sai, bypass, leak), so quyết định với workflow trên hidden, ghi ra `reports/bonus_b3.json`.
  - Khi chạy trên Windows, script lỗi `UnicodeEncodeError`; tôi sửa bằng `utf8_stdio()` giống các tool của lab.
- **Test:** 6 hàm test, 23 trường hợp:
  - override ở C-002 seed 55;
  - không can thiệp ở seed khác;
  - `verify_facts` bắt cả `status` và `damage_verified` (benchmark chỉ kích hoạt nhánh `delay_days`);
  - nhãn đúng cho workflow và swarm_verified;
  - crash/resume giữ một refund;
  - trace không lộ secret hay PII.
- **`report/team/bonus_report.md`:** kết luận ủng hộ hypothesis trong phạm vi lab. Verifier đưa swarm về mức của workflow, nhưng khi verifier luôn thắng thì swarm thành một workflow đắt gấp ≈ 2×. Nêu rõ điều kiện làm kết luận đảo ngược và các giới hạn (MockLLM, chỉ nhánh `delay_days` được benchmark kích hoạt, hidden không nhãn).

## 4. Bằng chứng

- Commit:
  - `1e87425`: workflow và test
  - `56a5cf1`: `PHAN_VIEC.md`
  - `6136e5b`: ADR, research card, bảng đóng góp, `hidden_selfcheck.json`
  - `61f8c84`: rà research card, `group_report.md`, cập nhật báo cáo này và `TEAM.md`
  - `dc20097`: bonus B3 (`src/bonus/`, test, `reports/bonus_*.json`, `bonus_report.md`)
- File: `src/lab8/shapes/workflow.py`, `src/tests/test_workflow_extra.py`, `report/team/decision_adr.md`, `report/team/research_card.md`, `report/team/group_report.md`, `src/bonus/swarm_verified.py`, `src/tests/test_bonus_swarm_verified.py`, `report/team/bonus_report.md`.
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

- Bonus B3 (`src/reports/bonus_b3.json`, sinh bởi `lab8.benchmark --extra-shape` và `python -m bonus.b3_summary`):

  | Bộ | swarm | swarm_verified | workflow |
  | --- | --- | --- | --- |
  | Public 14 × 5: pass / pass^5 / cost/success | 0.986 / 0.929 / 49.57 | 1.000 / 1.000 / 57.57 | 1.000 / 1.000 / 28.77 |
  | Đối kháng 11 × 5: pass / pass^5 / cost/success | 0.873 / 0.364 / 61.76 | 1.000 / 1.000 / 65.54 | 1.000 / 1.000 / 30.91 |
  | Trả sai / từ chối sai (đối kháng) | 4 / 2 | 0 / 0 | 0 / 0 |
  | Hidden self-check: khác quyết định workflow | 6/200 | 0/200 | — |

  - Verifier can thiệp 9 lần trên bộ đối kháng (7 lần đổi số tiền) và 1 lần trên public, tất cả ở seed 55. Cả 3 shape đều 0 leak.
  - Trace minh họa: `R-swarm_verified-C-002-s55`, verifier đổi số ngày trễ 5 → 2 theo order, quote 20.000 → 0, kết quả `denied`.
  - Cổng host sau khi thêm bonus: `131 passed`; ma trận student vẫn 248/248.

## 5. Công cụ AI đã dùng

- **Công cụ:** Claude Code (Claude Opus 5.5) trong VS Code.
- **Dùng vào việc gì:** đọc đề và contract, đề xuất cách chia việc, viết `workflow.py` và `test_workflow_extra.py`, chạy test, benchmark và các lệnh git, quét trace, soạn ADR, research card, group report và báo cáo này; đọc `hidden_selfcheck.json` để đối chiếu với báo cáo của người 2; làm bonus B3 (viết `swarm_verified.py`, script tổng hợp, test, soạn `bonus_report.md`).
- **Cách tự kiểm tra:**
  - Đối chiếu từng nhánh của `workflow.py` với bảng trong `docs/business_rules.md` và `docs/contracts.md`.
  - Xác nhận bằng test thật, không dựa vào lời AI: ma trận student 62/62, cổng host, crash 20/20.
  - Số liệu trong ADR và research card lấy từ `src/reports/benchmark.json`, kiểm tra run id có trong file và commit hash có trên `main`.
  - Khi benchmark lần đầu ra `single = 0.000`, kiểm lại nhánh thay vì dùng số đó.
  - URL paper MAST được kiểm lại vì bản cũ ghi sai.
  - Bonus: nhãn 11 claim đối kháng tự suy theo `business_rules.md`, không sinh bằng `compensation.quote`. Kiểm chéo bằng workflow (55/55) và bằng dự đoán tay 7 trial swarm fail trước khi chạy. Số liệu trong `bonus_report.md` lấy từ `reports/bonus_b3.json`; một chỗ làm tròn sai (16,1% → 16,2%) đã sửa sau khi kiểm lại.

## 6. Tự đánh giá

- workflow chạy theo 1 flow predictable, các step đều follow rule/policy nên chỉ cần code quyết định. Chỉ cần thêm 1 LLM hỗ trợ cho phần viết phản hồi. Truyền đầy đủ vì host là nới duy nhất gh tiền, vì vậy mọi thứ đều cần host tự kiểm. Trace không chứa thông tin nhạy cảm như PII, bearer, canary,..

- Đóng góp đúng vần việc, selfcheck và doublecheck cho kết quả của các thành viên khác 
...
