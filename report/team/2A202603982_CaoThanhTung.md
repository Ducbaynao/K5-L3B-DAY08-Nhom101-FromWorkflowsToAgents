# Báo cáo cá nhân — 2A202603982_CaoThanhTung


## 1. Thông tin thành viên

- Họ tên: Cao Thanh Tùng
- MSSV: 2A202603982
- Email: 26ai.tungct@vinuni.edu.vn
- GitHub: TungCTT

## 2. Phần việc phụ trách

- Phụ trách role **Orchestrator + Handoff** (Shape C — `src/lab8/shapes/orchestrator.py`).
- Đảm bảo ranh giới bảo mật `handoff.v1` (`lab8.handoff.make_handoff`, chỉ cấp `READONLY_TOOLS`), tuân thủ `Trace contract v1` và cơ chế crash/idempotency với host (`durability.issue_refund`).
- Viết bộ test kiểm chứng riêng cho orchestrator và handoff tại `src/tests/test_orchestrator_handoff.py`.

## 3. Đóng góp cụ thể

- **Cài đặt `src/lab8/shapes/orchestrator.py`:**
  - Đọc claim qua `get_claim_view` (không dùng `SELECT *`), xử lý đầy đủ các nhánh `unknown_claim` (`failed`), thiếu `order_id` (`needs_info`), không visible/sai principal (`escalated`), `quote <= 0` (`denied` không ghi ledger), và `quote > 0` gọi `durability.issue_refund` với **full quote** để host tự kiểm tra approval và trừ phần đã hoàn của các claim trước (T13, T14).
  - Tạo gói `handoff.v1` chỉ chứa các trường trong allowlist và chỉ cấp `READONLY_TOOLS` cho `run_readonly_investigators`.
  - Truyền `crash_at` vào `issue_refund`; khi gặp `InjectedCrash` thì ghi event `crash` vào trace, flush `trace.write()` và re-raise (không nuốt exception).
- **Thêm test `src/tests/test_orchestrator_handoff.py`:** gồm 4 test kiểm tra Trace contract v1 & không rò rỉ secret, T14 full quote, crash-resume idempotency, và từ chối write tool / lọc extra facts trong `make_handoff`.
- **Commit chính (hash):** `c58c4c4`

## 4. Bằng chứng

- File code: `src/lab8/shapes/orchestrator.py`
- File test: `src/tests/test_orchestrator_handoff.py`
- Kết quả chạy kiểm thử tại `src/`:
  - `python -m pytest -q tests/test_orchestrator_handoff.py` → `4 passed`
  - `python -m pytest -q` (cổng host) → `58 passed, 248 deselected`
  - `python -m pytest -q -m student -o addopts= -k orchestrator` → `62 passed, 244 deselected`
- Commit link / run id benchmark: c58c4c4a79f98c4c7a8e0c06bfd74b2ffb15455a

## 5. Công cụ AI đã dùng

- **Công cụ:** Antigravity (trợ lý lập trình AI).
- **Mục đích sử dụng:** Phân tích cấu trúc đề bài và contract (`business_rules.md`, `contracts.md`, `handoff.py`, `runtime.py`), gợi ý cài đặt `orchestrator.py`, viết khung test `test_orchestrator_handoff.py` và rà soát các mục báo cáo.
- **Cách tự kiểm tra kết quả:** Đọc đối chiếu trực tiếp mã nguồn với `docs/business_rules.md`, `docs/contracts.md`, chạy `python -m pytest -q`, `python -m pytest -q tests/test_orchestrator_handoff.py` và `python -m pytest -q -m student -o addopts= -k orchestrator` để xác nhận tất cả test đều xanh.

## 6. Tự đánh giá

- Hoàn thành đúng tiến độ phần cài đặt Shape C (`orchestrator`) qua toàn bộ 62/62 test student, giữ xanh cổng host (58/58) và bổ sung 4 test kiểm chứng bảo mật handoff, trace và crash-resume.

