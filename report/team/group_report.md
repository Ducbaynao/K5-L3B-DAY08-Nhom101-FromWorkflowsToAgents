# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: Nhom101 (lớp L3B)
- Thành viên: xem `TEAM.md` — Khương Hoàng Nguyên (workflow + integration), Phạm Lý Ngọc Đức (single), Cao Thanh Tùng (orchestrator), Trương Văn Hải (ledger/crash/security)
- Commit chốt (trùng `report/team/decision_adr.md`): `12936a8`. Các commit sau đó chỉ sửa tài liệu và thêm `src/reports/hidden_selfcheck.json`, không đổi code shape, test, `benchmark.json` hay `crash.json`.

## 2. Mục tiêu và cách tiếp cận

**Bài toán.** Xử lý claim hoàn phí vận chuyển bằng bốn kiến trúc cùng chữ ký `run_claim`, rồi chọn kiến trúc ít tự chủ nhất mà vẫn làm được việc. Nhóm đọc yêu cầu thành một ranh giới cứng: **số tiền, approval và chống ghi trùng do code quyết; model chỉ đọc và soạn chữ; chữ trong ticket là dữ liệu chứ không phải lệnh.**

**Chia việc** (bản nháp phân việc ở commit `56a5cf1`, đã xóa sau khi hoàn thành). Sau CP1, nhóm thấy ba shape chạy song song được vì:
- mỗi shape là một file riêng;
- test student tách theo shape (62 test mỗi shape, mỗi trial một SQLite riêng);
- crash suite chỉ gọi host (`durability.issue_refund`), không cần shape nào.

Vì vậy:
- 3 người viết 3 shape trên 3 nhánh `feat/*`;
- người 4 làm crash suite và test an toàn ngay từ đầu;
- người 1 merge, giữ cổng host xanh, chạy benchmark ở CP5. Benchmark là điểm gom duy nhất vì cần đủ 4 shape trên cùng code.

**Thứ tự.**
1. Workflow làm trước để làm mẫu (cùng khung với swarm, bỏ khối `REFERENCE_WEAKNESS`).
2. Orchestrator và single làm song song, bám khung đó.
3. Merge theo thứ tự workflow (PR #1) → orchestrator (`c58c4c4`) → single (PR #2) → safety-tests (PR #3). Sau mỗi lần merge chạy lại cổng host và ma trận student.

## 3. Giải pháp

Ba shape dùng chung một chuỗi nghiệp vụ, chỉ khác ai điều khiển các bước đọc:

```text
get_claim_view ─► thiếu order_id? ─► lookup_order (kiểm principal) ─► compute_compensation ─► quote > 0? ─► durability.issue_refund(quote đầy đủ, crash_at)
   │ không có        │ needs_info         │ không thấy / sai chủ: escalated      │ quote = 0: denied            │ host: resolved / denied (policy_denied) / failed (conflict)
   ▼ failed
```

| | A `workflow` | B `single` | C `orchestrator` |
| --- | --- | --- | --- |
| Ai chọn bước đọc | Code, thứ tự cố định | Vòng `run_react(max_steps=8, worker=True)`; callback `decide` chọn `lookup_order` → `compute_compensation` → `final` | Orchestrator dựng handoff; `run_readonly_investigators` chạy 4 tool đọc |
| Tool đọc | `get_claim_view`, `lookup_order`, `compute_compensation` | như A, gọi qua ReAct | `lookup_order`, `lookup_policy`, `lookup_refund_history`, `compute_compensation` |
| Model (MockLLM) | 1 call `draft` (soạn trả lời) | 1 call `decide` mỗi bước ReAct (≈ 2.7/trial) | 1 call `draft` |
| Ai tính tiền | `compute_compensation` | `compute_compensation` (lấy từ observation, không từ model) | `compute_compensation` do investigator chạy |
| Ai ghi tiền | Host | Host, gọi sau vòng lặp | Host, do orchestrator gọi |

**Ranh giới code / model** (theo `docs/architecture.md`):
- Lọc principal, policy hiện hành, trần theo đơn, approval đúng claim, idempotency `refund:{claim_id}`: tất cả nằm trong code và host.
- Không shape nào parse số ngày trễ từ ticket. Đây là chỗ swarm sai ở seed 55.
- Cả ba truyền **quote đầy đủ** vào `issue_refund`. Host tự trừ phần các claim trước đã nhận. Nếu shape tự trừ thì T14 sẽ ra 90.000 thay vì 120.000.

**Crash.**
- Cả ba truyền `crash_at` vào host. Khi gặp `InjectedCrash`: ghi trace (workflow, orchestrator ghi event `crash`; single flush trace trước khi gọi host) rồi ném lại, không nuốt.
- Resume dựa vào ledger, không dựa vào checkpoint. `python -m lab8.demo.buggy_workflow` cho thấy checkpoint đơn lẻ vẫn có thể trả tiền hai lần.

**Handoff (orchestrator).**
- `make_handoff` với `facts={}` và chỉ tool đọc. Allowlist của `lab8.handoff` từ chối tool ghi và bỏ field thừa (có test `test_handoff_rejects_write_tools_and_drops_extra_facts`).
- Trace ghi handoff đã sanitize qua `safe_dump`, không ghi parent context.
- Nhóm không dùng LLM để tóm tắt context thay cho allowlist: tóm tắt không phải redaction.

**Trace** (`lab8.trace.Trace`, contract v1).

| Shape | Event |
| --- | --- |
| workflow | `claim → lookup_order → quote → issue_refund → decision` (+ `crash`) |
| single | `tool(get_claim_view) → react_step… → quote → host_call → host_result → decision` |
| orchestrator | `handoff → investigator → quote → decision` (+ `crash`) |

Cả ba **cố ý không ghi**: chữ ticket, `parent_secret`, `raw_headers`, SĐT, địa chỉ, tên hàng, internal note. Không shape nào `SELECT *` bảng claims/orders. Đơn hàng chỉ đọc qua `lookup_order` (allowlist `ORDER_FIELDS`), nên các field nhạy cảm không bao giờ vào bộ nhớ shape.

## 4. Kết quả

**Bộ public** — `src/reports/benchmark.json`, 14 claim × 5 seed (11, 22, 33, 44, 55), giá mô phỏng `config/pricing.yaml`, SQLite mới mỗi trial:

| Shape | Pass rate | pass^5 | Seed min–max | Variance | Cost/success (VND) | Mean steps | p95 steps | Model call/trial | Tool call/trial |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| workflow | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | **28.77** | 4.43 | 5 | 1.00 | 2.79 |
| single | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 31.56 | 6.86 | 8 | 2.71 | 2.79 |
| orchestrator | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 56.65 | 2.86 | 3 | 1.00 | 5.57 |
| swarm | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80 | 3 | 3.00 | 4.66 |

- Swarm fail đúng một trial: `R-swarm-C-002-s55` (`status resolved != denied`). Ticket ghi "trễ 5 ngày", order ghi 2 ngày. Workflow ở cùng claim, cùng seed (`R-workflow-C-002-s55`) trả `denied`.
- "Steps" là số event trong trace, nên phản ánh cách mỗi shape ghi trace nhiều hơn là số lượt suy luận. So cost mới công bằng hơn.

**Crash safety:** `src/reports/crash.json` = **20/20**: 5 điểm `before_effect`, 7 `after_effect_before_checkpoint`, 5 `after_checkpoint`, và 3 kịch bản thêm: `amount_conflict_on_retry`, `retry_without_approval`, `swarm_after_effect_before_checkpoint`. Mỗi kịch bản sau resume còn đúng một refund và một audit `refund_committed`.

**Test:**
- Cổng host `python -m pytest -q`: **108 passed**. Gồm 54 test gốc và 54 test nhóm thêm trong `test_workflow_extra.py`, `test_single_extra.py`, `test_orchestrator_handoff.py`, `test_safety_extra.py`.
- Ma trận student: **248/248** (62 mỗi shape).
- `test_safety_extra.py` chạy trên cả 3 shape: approval hết hạn, bị thu hồi, của claim khác (`approval_claim_mismatch`); đơn đã hoàn đủ (`order_already_refunded`); T14 hoàn phần chênh; trace không lộ secret.

**Tự kiểm trên `student_drop/`** — `src/reports/hidden_selfcheck.json`, 40 claim × 5 seed × 3 shape = 600 trial:

| Shape | Trial | `error` | `leak_suspect` | resolved / denied / escalated / needs_info |
| --- | --- | --- | --- | --- |
| workflow | 200 | 0 | 0 | 90 / 95 / 10 / 5 |
| single | 200 | 0 | 0 | 90 / 95 / 10 / 5 |
| orchestrator | 200 | 0 | 0 | 90 / 95 / 10 / 5 |

- Ba shape cho **cùng một status ở cả 600 cặp** (claim, seed), và không claim nào đổi status giữa các seed.
- Hai người chạy độc lập (Đức trên máy mình, Nguyên trên nhánh tích hợp) ra cùng con số.
- Bộ này không có nhãn, nên con số trên chỉ chứng minh shape chạy hết, trace đúng contract và không có dấu hiệu lộ secret. Pass rate hidden do grader của giảng viên chấm.

**Quyết định kiến trúc:** chọn **workflow**. Lý do và điều kiện đảo quyết định: `report/team/decision_adr.md`. Phiếu nghiên cứu (R2, MAST) và ablation workflow vs swarm: `report/team/research_card.md`.

## 5. Khó khăn và cách xử lý

| Vấn đề | Bằng chứng | Cách xử lý |
| --- | --- | --- |
| `-k single` chọn nhầm test của shape khác: tên `test_public_single_run_cases` chứa chữ "single" | `-k single` ra `62 failed, 180 passed` khi single còn là stub | Lọc `-k "single and not workflow and not orchestrator and not swarm"`, hoặc đếm theo id `[single]` |
| Nhánh `feat/workflow` ở máy tích hợp lệch `main` (có commit riêng, chưa có code single), không fast-forward được | Benchmark lần đầu ra `single 0.000 … status failed != resolved x35` | Bỏ hai file report vừa sinh sai, merge `main` vào nhánh, chạy lại: 248/248 rồi mới benchmark. Bài học: chạy benchmark trên đúng commit đã merge đủ |
| Commit `78eae11` ("revert other members reports…") đưa ADR, research card và group report về mẫu trống | `check_submission`: `8 FAIL` (7 dòng ADR + research card) | Điền lại từ `benchmark.json`. So với bản trước còn sửa bốn chỗ sai: tên event trace không khớp code, commit hash không trỏ đúng code được chấm, URL paper MAST sai (`2503.11234` → `2503.13657`), câu "đã quét regex toàn bộ trace" không có bằng chứng. Kết quả: `0 FAIL, 0 WARN` |
| Windows: lỗi quyền ở thư mục Temp mặc định khi chạy pytest (máy của Đức) | Ghi trong báo cáo cá nhân của Đức | Dùng `--basetemp` trong workspace. Benchmark dùng `ignore_cleanup_errors`, và các shape đều đóng SQLite trong `finally` để không khóa file |
| `git pull` timeout tới github.com | `Failed to connect to github.com port 443` | Kiểm local đã có commit cần thiết, chạy test trên đó, pull lại trước khi benchmark |

## 6. Tổng hợp đóng góp

Chi tiết đóng góp của từng thành viên nằm trong `TEAM.md` (bảng đóng góp) và báo cáo cá nhân `report/team/MSSV_HoTen.md`.

| Thành viên | Phần chính | Commit | Test |
| --- | --- | --- | --- |
| Khương Hoàng Nguyên | Workflow, chia việc, integration, benchmark, ADR, research card, group report | `1e87425`, `6136e5b` | `test_workflow_extra.py` |
| Phạm Lý Ngọc Đức | Single (ReAct ≤ 8 bước), hidden self-check | `3943c48` | `test_single_extra.py` |
| Cao Thanh Tùng | Orchestrator + handoff | `c58c4c4` | `test_orchestrator_handoff.py` |
| Trương Văn Hải | Crash suite 20/20, test an toàn trên 3 shape, rà trace | `5e383b3` | `test_safety_extra.py` |

## 7. Hạn chế và hướng cải thiện

- **MockLLM không phải model sản xuất.** Latency `unavailable`; cost là VND mô phỏng, không phải hóa đơn API.
- **Single chưa thật sự "tự chủ".** Callback `decide` của single là luật Python cố định. MockLLM chỉ được gọi để tính budget, không ảnh hưởng hành động. Vì vậy so sánh single với workflow ở đây đo **chi phí của vòng ReAct** (thêm ≈ 1.7 model call và 2.4 bước mỗi trial), chưa đo **rủi ro** khi model thật chọn tool. Với LLM thật, single có thể chọn sai tool hoặc tin ticket, và đó là lý do thêm để chọn workflow.
- **Bộ public nhỏ** (14 claim). Ba shape nhóm viết đều 1.000, nên public không phân biệt được chúng về chất lượng, chỉ phân biệt về cost. Hidden self-check cũng không có nhãn.
- **Ba shape cùng dùng `compute_compensation`**, nên việc chúng khớp nhau 600/600 trên hidden không phải kiểm chứng độc lập. Nếu luật trong `compensation.quote` thiếu một trường hợp thì cả ba cùng sai.
- **Điều kiện làm kết luận thay đổi:**
  - Claim cần đọc dữ liệu không cấu trúc (ảnh hàng hỏng, chứng từ hãng vận chuyển) → orchestrator với investigator chỉ đọc.
  - Bước điều tra chậm và độc lập, chạy song song có lợi về latency.
  - Workflow dưới 0.75 trên hidden trong khi shape khác qua.
- **Cải thiện tiếp:**
  - Thêm test metamorphic cho workflow: đổi chữ ticket, giữ order → kết quả không đổi.
  - Đo bonus ablation thêm investigator (R1) để tách tác động của topology khỏi số call.

## 8. Tài liệu tham khảo

- Đề bài và contract của lab: `README.md`, `CHECKPOINTS.md`, `docs/business_rules.md`, `docs/contracts.md`, `docs/architecture.md`, `docs/metrics.md`.
- Cemri et al., *Why Do Multi-Agent LLM Systems Fail?* (MAST), NeurIPS 2025 Datasets & Benchmarks, https://arxiv.org/abs/2503.13657 — dùng cho research card (R2).
- Shape tham chiếu `src/lab8/shapes/swarm_reference.py` (khung chung; khối `REFERENCE_WEAKNESS` không được copy).
- Công cụ AI đã dùng: ghi ở mục 5 báo cáo cá nhân của từng thành viên.
