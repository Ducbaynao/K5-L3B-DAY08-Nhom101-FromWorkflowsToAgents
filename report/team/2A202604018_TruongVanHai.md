# Báo cáo cá nhân — 2A202604018_TruongVanHai

## 1. Thông tin thành viên

- Họ tên: Trương Văn Hải
- MSSV: 2A202604018
- Email: truongvanhai868@gmail.com
- GitHub: haihai

## 2. Phần việc phụ trách

- Phụ trách vai trò **Ledger / Crash / Security + Báo cáo / Benchmark / ADR** (Người 4 theo [PHAN_VIEC.md](../../PHAN_VIEC.md)).
- Phụ trách thực thi kiểm thử an toàn va chạm và khôi phục trạng thái (Crash safety suite CP4), đảm bảo `crash_safety = 20/20` tại `src/reports/crash.json`.
- Viết bộ kiểm thử chuyên biệt về an toàn, ràng buộc phê duyệt và bảo mật dữ liệu tại `src/tests/test_safety_extra.py` chạy trên toàn bộ 3 shapes (workflow, single, orchestrator).
- Rà soát toàn bộ các tệp trace (`src/traces/`) và log xuất ra để đảm bảo tuyệt đối không rò rỉ `CANARY_SECRET_*`, `parent_secret`, token `Authorization` hay PII của người dùng.
- Thực thi benchmark 4 shape × 5 seed (`src/reports/benchmark.json`), hoàn thiện [decision_adr.md](decision_adr.md), [research_card.md](research_card.md) và [group_report.md](group_report.md).

## 3. Đóng góp cụ thể

1. **Thực thi và phân tích bài toán Crash & Ledger:**
   - Chạy kiểm thử crash tự động `python -m lab8.crash_test --count 20 --out reports/crash.json`, xác nhận đạt 20/20 kịch bản ngắt điện đột ngột trước/sau khi ghi sổ và trước/sau khi ghi checkpoint.
   - Chạy và phân tích bài học từ `lab8.demo.buggy_workflow`: chứng minh rằng một cờ checkpoint đơn lẻ (`checkpointed=1`) không thể thay thế cho cơ chế ledger bảo đảm tính duy nhất (`idempotency_key UNIQUE`), do khoảng trống (window) giữa side-effect và checkpoint sẽ gây ra lỗi thanh toán trùng lặp (double refund: 2 dòng thay vì 1).
2. **Xây dựng bộ test an toàn `src/tests/test_safety_extra.py`:**
   - Xây dựng 18 trường hợp kiểm thử (parametrize trên cả 3 shape: Workflow, Single ReAct, Orchestrator) bao gồm:
     - Từ chối phê duyệt đã hết hạn (`approval_expired`).
     - Từ chối phê duyệt gắn với claim khác (`approval_claim_mismatch`).
     - Từ chối phê duyệt đã bị thu hồi (`approval_revoked`).
     - Ràng buộc trần hoàn tiền theo đơn khi đơn đã hoàn đủ trước đó (`order_already_refunded`).
     - Kiểm tra hoàn bù khoản tiền chênh lệch đối với đơn đã có lịch sử bồi thường (T14 - top up difference).
     - Rà soát tính bí mật của Trace Contract v1 trên các claim nhạy cảm.
3. **Quét bảo mật và ranh giới an toàn dữ liệu:**
   - Quét regex tự động trên tất cả các file JSON trong thư mục `src/traces/`, xác nhận không tồn tại bất kỳ chuỗi `CANARY_SECRET_`, `parent_secret`, hay `Bearer` header nào.
4. **Benchmark và Tổng kết Đánh giá Kiến trúc:**
   - Chạy benchmark toàn diện 280 lượt thử nghiệm (`python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`).
   - Phân tích và điền phiếu nghiên cứu [research_card.md](research_card.md) theo bài báo MAST (NeurIPS 2025) về phân loại lỗi Verification Failure của Swarm tại seed 55 trên claim C-002.
   - Điền đầy đủ hồ sơ quyết định kiến trúc [decision_adr.md](decision_adr.md) và biên soạn báo cáo nhóm [group_report.md](group_report.md).

## 4. Bằng chứng

- File mã nguồn kiểm thử: [test_safety_extra.py](../../src/tests/test_safety_extra.py)
- File báo cáo crash: [crash.json](../../src/reports/crash.json) (kết quả `20/20`)
- File báo cáo benchmark: [benchmark.json](../../src/reports/benchmark.json) (đủ 4 shape, 5 seed, 14 claims)
- Kết quả kiểm thử tại `src/`:
  - `python -m pytest -q tests/test_safety_extra.py` → `18 passed`
  - `python -m pytest -q` (cổng host) → `108 passed, 248 deselected`
  - `python -m lab8.crash_test --count 20 --out reports/crash.json` → `crash_safety 20/20`
  - `python -m lab8.benchmark ...` → `workflow` (pass 1.000, cost 28.77 VND), `single` (pass 1.000, cost 31.56 VND), `orchestrator` (pass 1.000, cost 56.65 VND), `swarm` (pass 0.986, cost 49.57 VND, fail C-002 seed 55).
- Commit hash: `fe41178` (và các commit trên nhánh `feat/safety-tests`).

## 5. Công cụ AI đã dùng

- **Công cụ:** Antigravity (AI Assistant).
- **Mục đích sử dụng:**
  - Hỗ trợ phân tích mã nguồn hệ thống host durability (`durability.py`, `policy.py`).
  - Hỗ trợ xây dựng các kịch bản kiểm thử biên trong `test_safety_extra.py`.
  - Phân tích bảng số liệu từ `benchmark.json` và liên hệ với lý thuyết phân loại lỗi trong bài báo MAST (NeurIPS 2025) cho research card.
- **Cách tự kiểm tra kết quả:**
  - Trực tiếp chạy và kiểm tra đầu ra của `pytest`, `lab8.crash_test`, `lab8.benchmark`, và `lab8.check_submission`.
  - Quét thủ công và dùng script kiểm tra độc lập các file trace sinh ra để xác thực không rò rỉ secret.

## 6. Tự đánh giá

- Đã hoàn thành 100% nhiệm vụ của Người 4 theo phân công trong [PHAN_VIEC.md](../../PHAN_VIEC.md): tạo báo cáo `crash.json` 20/20, viết và kiểm chứng thành công bộ test an toàn `test_safety_extra.py`, quét sạch trace secret, thực thi benchmark và hoàn thiện toàn bộ hệ thống tài liệu báo cáo `decision_adr.md`, `research_card.md`, `group_report.md`.
