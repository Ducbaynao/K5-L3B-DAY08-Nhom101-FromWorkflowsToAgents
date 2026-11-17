# Báo cáo nhóm — Lab 8 LogiX-VN

Tối đa 5 trang ngoài phụ lục. Số liệu lấy từ file trong `src/reports/`, không chép tay từ terminal.

## 1. Thông tin nhóm

- Tên nhóm: Nhom101
- Lớp: L3B
- Repo: `K5-L3B-DAY08-Nhom101-FromWorkflowsToAgents`
- Nhánh nộp: `feat/safety-tests` (sẵn sàng merge `main`)
- Commit chốt: fe41178 (tham chiếu cùng `report/team/decision_adr.md`)
- Thành viên:
  1. Nguyễn Khương — Shape A `workflow` + Integration
  2. Phạm Lý Ngọc Đức (2A202603991) — Shape B `single` (ReAct agent)
  3. Cao Thanh Tùng (2A202603982) — Shape C `orchestrator` + Handoff / Allowlist
  4. Trương Văn Hải (2A202604018) — Ledger / Crash / Security + Báo cáo / Benchmark / ADR

## 2. Mục tiêu và cách tiếp cận

Hệ thống thẩm định và bồi thường tự động của LogiX-VN đối mặt với các yêu cầu khắt khe: tính chính xác nghiệp vụ (chỉ hoàn tiền khi đơn hợp lệ và giao trễ), tính bất biến và an toàn tài chính (không hoàn tiền vượt trần đơn hàng, không double refund khi crash/resume), và tính bảo mật (không rò rỉ secret/PII qua trace hay handoff).

Nhóm tiếp cận bài toán theo tư duy tiến hóa kiến trúc từ đơn giản đến phức tạp:
1. **Shape A — Deterministic Workflow:** Chuỗi pipeline mã nguồn thuần túy bằng Python, không phụ thuộc vào suy luận tự do của LLM, đảm bảo tính tất định và chi phí tối thiểu.
2. **Shape B — Single Agent (ReAct):** Tác nhân tự động sử dụng vòng lặp ReAct tối đa 8 bước để tra cứu thông tin qua read-only tools, nhưng việc tính tiền và ghi sổ được chốt chặn bởi code Python.
3. **Shape C — Orchestrator + Sub-investigators:** Mô hình phân cấp tách biệt tác nhân điều phối và các tác nhân điều tra chuyên biệt, giao tiếp qua cấu trúc handoff an toàn.
4. **Shape D — Swarm (Reference):** Hệ thống đa tác nhân ngang hàng chia sẻ message board để so sánh hiệu năng và phát hiện rủi ro phân rã bối cảnh.

## 3. Giải pháp

### 3.1. Ranh giới Code / Model và An toàn tài chính
- **Tiền bồi thường luôn tính bằng code:** Tuyệt đối không để LLM tự tính hoặc đề xuất số tiền hoàn. Hàm Python `compute_compensation` trực tiếp đối soát số ngày giao trễ thực tế từ cơ sở dữ liệu `orders` (bỏ qua nội dung mô tả chủ quan trong `ticket`).
- **Host Ledger Gate:** Tác nhân chỉ đề xuất toàn bộ quote (`proposed_vnd`). Việc kiểm tra approval, tính toán trần bồi thường theo đơn hàng (`cap_per_order`), khấu trừ số tiền đã hoàn trước đó (T14 - hoàn phần chênh lệch) và ghi nhận giao dịch thuộc toàn quyền của host qua `durability.issue_refund`.
- **Idempotency & Crash-Safety:** Sử dụng khóa định danh duy nhất `refund:{claim_id}` trong cơ sở dữ liệu SQLite với giao dịch nguyên tử (`BEGIN IMMEDIATE`). Khi hệ thống gặp sự cố (`InjectedCrash`), giao dịch hoặc đã hoàn tất hoặc rollback hoàn toàn, ngăn chặn triệt để hiện tượng double refund khi replay/resume.

### 3.2. Bảo mật Handoff và Trace Contract v1
- **Sanitized Handoff:** Trong Shape C, Orchestrator chỉ truyền cho các sub-investigators các thuộc tính đã được làm sạch qua allowlist (`handoff.v1`), chỉ cấp quyền sử dụng các công cụ chỉ đọc (`READONLY_TOOLS`).
- **Bảo mật Trace:** Trace chỉ ghi nhận các sự kiện tiến trình nghiệp vụ (`claim_lookup`, `order_lookup`, `compensation_computed`, `refund_submitted`, `crash`). Tuyệt đối không lưu vết các chuỗi bí mật như `CANARY_SECRET_*`, `parent_secret`, mã ủy quyền `Authorization: Bearer ...` hoặc dữ liệu PII của khách hàng.

## 4. Kết quả

### 4.1. Bảng so sánh 4 Shape trên bộ dữ liệu Public (14 claims × 5 seeds)

Dữ liệu kết xuất từ `src/reports/benchmark.json`:

| Shape | Pass Rate | Pass^5 | Seed Variance | Min - Max Seed | Cost/Success (VND) | Mean Steps | Mean Model Calls | Mean Tool Calls |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **workflow** | **1.000** (70/70) | **1.000** | **0.000000** | 1.000 - 1.000 | **28.77** | 4.43 | 1.00 | 2.79 |
| **single** | **1.000** (70/70) | **1.000** | **0.000000** | 1.000 - 1.000 | 31.56 | 6.86 | 2.71 | 2.79 |
| **orchestrator** | **1.000** (70/70) | **1.000** | **0.000000** | 1.000 - 1.000 | 56.65 | 2.86 | 1.00 | 5.57 |
| **swarm** | 0.986 (69/70) | 0.929 | 0.000816 | 0.929 - 1.000 | 49.57 | 2.80 | 3.00 | 4.66 |

*Ghi chú:* Swarm fail 1 trial tại claim C-002 ở seed 55 với lỗi `status resolved != denied x1` do tin vào thông tin ticket khách hàng báo trễ 5 ngày trong khi thực tế chỉ trễ 2 ngày (không đủ điều kiện bồi thường).

### 4.2. Kết quả Crash Safety
- Chạy qua công cụ chuẩn `lab8.crash_test`: **`crash_safety = 20/20`** (kết xuất tại `src/reports/crash.json`).
- Kiểm tra toàn bộ 20 kịch bản ngắt điện đột ngột tại các thời điểm nhạy cảm: `before_effect`, `after_effect_before_checkpoint`, `after_checkpoint`, và các kịch bản retry/idempotency.

## 5. Khó khăn và cách xử lý

1. **Checkpoint đơn lẻ không thay thế được Ledger:**
   - Khi chạy thử nghiệm `python -m lab8.demo.buggy_workflow`, hệ thống ghi nhận `unsafe refund rows: 2`. Lý do là hệ thống lưu vết trạng thái bằng cờ `checkpointed=1` nhưng không có ràng buộc khóa duy nhất ở tầng cơ sở dữ liệu. Khi crash xảy ra sau tác vụ chuyển tiền nhưng trước khi checkpoint, tiến trình resume sẽ ghi đè và chuyển tiền lần 2.
   - *Cách xử lý:* Host ledger áp dụng ràng buộc khóa `idempotency_key UNIQUE` cho mỗi claim (`refund:{claim_id}`) kết hợp transaction nguyên tử, giúp loại bỏ hoàn toàn lỗi double-spending.
2. **Nguy cơ rò rỉ Canary Secret:**
   - Các trường `parent_secret` và token ủy quyền trong claim row rất dễ bị vô tình đưa vào prompt hoặc log trace debug.
   - *Cách xử lý:* Sử dụng hàm `get_claim_view` để tách lớp dữ liệu, lọc bỏ hoàn toàn các trường nhạy cảm trước khi đưa vào context hoặc ghi trace.
3. **Bài toán hoàn tiền bù chênh lệch (T14):**
   - Đơn hàng O-515 đã được hoàn trước 30.000 VND, claim mới có mức phê duyệt là 150.000 VND. Nếu agent tự trừ tiền hoặc chỉ yêu cầu 120.000 VND thì vi phạm contract; nếu host không trừ thì sẽ chi thừa ngân sách.
   - *Cách xử lý:* Agent gửi trọn vẹn quote 150.000 VND; host tính toán `amount = min(proposed - already_refunded, approved, paid - already_refunded)` và thực hiện chuyển đúng khoản chênh lệch 120.000 VND.

## 6. Tổng hợp đóng góp

- **Nguyễn Khương:** Triển khai Shape A `workflow.py`, bổ sung test `test_workflow_extra.py`, phụ trách tích hợp và chạy cổng host.
- **Phạm Lý Ngọc Đức (2A202603991):** Triển khai Shape B `single.py` với vòng lặp ReAct ≤ 8 bước, bổ sung 12 kịch bản test tại `test_single_extra.py`.
- **Cao Thanh Tùng (2A202603982):** Triển khai Shape C `orchestrator.py`, hiện thực hóa cơ chế handoff bảo mật `handoff.v1`, bổ sung test tại `test_orchestrator_handoff.py`.
- **Trương Văn Hải (2A202604018):** Phụ trách an toàn ledger, crash test suite (`reports/crash.json` 20/20), quét bảo mật trace không rò rỉ secret, bổ sung bộ test an toàn `test_safety_extra.py` (18 tests), thực thi benchmark 4 shape, hoàn thiện `decision_adr.md`, `research_card.md` và báo cáo nhóm.

## 7. Hạn chế và hướng cải thiện

- **Môi trường giả lập:** Mô hình sử dụng MockLLM với phản hồi xác định theo seed, không phản ánh trọn vẹn độ bất định, độ trễ mạng (latency được ghi nhận là `unavailable`) và các sắc thái ngôn ngữ thực tế như Gemini/GPT-4 trong môi trường sản xuất.
- **Mở rộng đa miền:** Hệ thống hiện tối ưu cho bài toán xử lý bồi thường đơn hàng có cấu trúc bảng chặt chẽ. Hướng cải thiện tiếp theo là bổ sung cơ chế kiểm chứng tài liệu đa phương thức (hình ảnh gói hàng rách hỏng, biên bản giao nhận quét scan) trước khi chuyển vào pipeline xử lý tài chính.

## 8. Tài liệu tham khảo

1. Google Research 2026, *Towards a Science of Scaling Agent Systems*.
2. MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?*.
3. AgentArch, AACL 2026, *Design Principles for LLM Agent Topologies*.
4. EMNLP 2026, *Rethinking Evaluation of MAS Efficiency*.
