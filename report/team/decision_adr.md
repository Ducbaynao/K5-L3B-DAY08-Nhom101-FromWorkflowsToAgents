# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: 12936a8
- Run id dẫn chứng: R-workflow-C-001-s11
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000-1.000 / 0.000000
- Cost per success (mô phỏng, VND): 28.77
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 leak / 0 bypass

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

So trên cùng corpus (14 claim public `C-001`…`C-014`), cùng 5 seed `11,22,33,44,55`, cùng bảng giá mô phỏng và một SQLite mới cho mỗi trial (`src/reports/benchmark.json`, commit `12936a8`):

| Shape | Pass | pass^5 | Seed min–max | Variance | Cost/success (VND) | Model call / trial | Tool call / trial |
| --- | --- | --- | --- | --- | --- | --- | --- |
| workflow | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | **28.77** | 1.00 | 2.79 |
| single | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 31.56 | 2.71 | 2.79 |
| orchestrator | 1.000 | 1.000 | 1.000–1.000 | 0.000000 | 56.65 | 1.00 | 5.57 |
| swarm | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 3.00 | 4.66 |

Ba shape nhóm viết hòa nhau về chất lượng (70/70 trial), nên quyết định nằm ở cost và mức tự chủ. Workflow rẻ nhất và là shape **ít tự chủ nhất**: thứ tự bước do code cố định, tiền do `compute_compensation` tính từ cột `delay_days` của order, host (`durability.issue_refund`) là nơi duy nhất ghi ledger, còn MockLLM chỉ soạn câu trả lời (1 call/trial). Ticket không bao giờ được parse, nên kiểu lỗi của swarm ở `R-swarm-C-002-s55` (tin "trễ 5 ngày" trong ticket thay vì 2 ngày trong order, trả `resolved` thay vì `denied`) không thể xảy ra với workflow; `src/tests/test_workflow_extra.py` khóa điều này trên cả 5 seed. Tự kiểm trên `student_drop/` (40 claim × 5 seed): workflow 0 trial `error`, 0 `leak_suspect`.

## Có đáng đổi lấy multi-agent không

Không, với task hiện tại. Không shape multi-agent nào pass cao hơn workflow, mà đều đắt hơn: orchestrator 56.65 VND (≈ 1.97×, do 5.57 tool call/trial vì investigator đọc lại order, policy, refund history), swarm 49.57 VND (≈ 1.72×) kèm variance 0.000816 và pass^5 0.929. Single cũng không đáng: cùng pass nhưng 2.71 model call/trial và 6.86 bước so với 4.43.

Quyết định đảo lại khi:
- Có claim mà luật không viết được thành nhánh cố định (ví dụ đọc ảnh hàng hỏng, đối chiếu chứng từ của hãng vận chuyển). Khi đó cần investigator đọc dữ liệu không cấu trúc; orchestrator là bước tiếp theo vì vẫn giữ tool chỉ đọc và host là người ghi duy nhất.
- Các bước điều tra độc lập và chậm (gọi API ngoài) đến mức chạy song song tiết kiệm latency hơn phần cost tăng thêm. Lab này latency `unavailable` nên chưa đo được.
- Pass rate của workflow trên bộ hidden rơi dưới 0.75 vì nhánh code thiếu trường hợp, trong khi shape khác qua được. Theo self-check thì chưa thấy dấu hiệu này.

## Trace và bằng chứng

Trace workflow (`src/traces/<run_id>.json`, `lab8.trace.Trace`) ghi các event: `claim` (chỉ `claim_id` và `has_order_id`), `lookup_order` (order view đã qua allowlist `ORDER_FIELDS`; nhánh không visible chỉ ghi `reason`), `quote` (kết quả `compute_compensation`), `issue_refund` (`ok`, `reason` của host), `crash` (khi có `crash_at`, rồi ném lại `InjectedCrash`), `decision` (status, proposal, reason). Ví dụ `R-workflow-C-001-s11`: `claim → lookup_order → quote → issue_refund → decision`.

Cố ý **không** ghi: chữ trong ticket (dữ liệu người dùng, có thể chứa injection hoặc PII), `parent_secret`, `raw_headers`, SĐT, địa chỉ, tên hàng, internal note. Workflow không bao giờ `SELECT *` bảng claims/orders: chỉ đọc qua `get_claim_view` và `lookup_order`, nên các field đó không có trong bộ nhớ của shape để lỡ ghi ra. Shape không `print` gì ra stdout và không ghi file nào ngoài trace.

Bằng chứng: `test_workflow_extra.py` quét trace của cả 14 claim (không có `CANARY_`, `Bearer`, chữ ticket); `test_safety_extra.py` kiểm approval hết hạn / thu hồi / của claim khác, `order_already_refunded`, T14 và secret trên cả 3 shape; benchmark và hidden self-check báo 0 `leak_suspect`.

## Giới hạn

MockLLM không phải model sản xuất; kết quả cost là VND mô phỏng theo `config/pricing.yaml`, không phải hóa đơn API. Latency để `unavailable`. Bộ public chỉ có 14 claim, nên 1.000 trên public chưa chứng minh pass ≥ 0.75 trên hidden; điểm hidden do grader của giảng viên chấm. Không sửa JSON trong `src/reports/` bằng tay.
