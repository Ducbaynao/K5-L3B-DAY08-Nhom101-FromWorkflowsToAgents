# Phân việc Nhom101 (nháp)

> File nháp để chia việc trong buổi lab. Không phải deliverable. Mọi lệnh chạy trong `src/` sau khi đã activate venv.

## Nguyên tắc chung

- Mỗi người làm trên **nhánh riêng**, chỉ sửa **file của mình** (bảng dưới). Không sửa `metrics.py`, `durability.py`, `policy.py`, `config/`, `data/`.
- Trước khi mở PR / merge: `python -m pytest -q` phải xanh (cổng host) và test student của shape mình phải xanh.
- Mỗi người cần **≥ 1 commit có nội dung + ≥ 1 test** thêm hoặc sửa (bảng đóng góp trong `TEAM.md` yêu cầu). Test đặt trong file riêng tên mình phụ trách để tránh conflict.
- Không ghi claim row / order row thô vào trace hay `print`. Chỉ ghi dữ liệu đã qua `get_claim_view`, `lookup_order`, handoff đã sanitize.
- Tiền luôn do `compute_compensation` tính. Truyền **quote đầy đủ** vào `durability.issue_refund(conn, claim_id, quote, crash_at=crash_at)`. Không bắt `InjectedCrash`.
- Trả kết quả bằng `lab8.shapes.common.finish()` ở **mọi** nhánh return.

## Khung chung cho cả 3 shape

Bám theo `swarm_reference.py`, bỏ khối `REFERENCE_WEAKNESS`:

1. Không có claim → `failed`, `proposal_amount=0`.
2. Thiếu `order_id` → `needs_info`, không ghi ledger.
3. Đơn không thấy / principal không sở hữu → `escalated`.
4. Quote = 0 → `denied`, `proposal_amount=0`, **không** gọi `issue_refund`.
5. Quote > 0 → gọi `issue_refund`. `ok` → `resolved`. Không `ok` → `conflict` thì `failed`, còn lại `denied`. `proposal_amount` luôn là quote đầy đủ.

Người 1 viết workflow trước (~15 phút) để làm mẫu; người 2, 3 bắt đầu đọc `runtime.py` / `handoff.py` trong lúc chờ.

## Người 1: Workflow + integration

- **Nhánh:** `feat/workflow`
- **File sửa:** `src/lab8/shapes/workflow.py`
- **Test thêm:** `src/tests/test_workflow_extra.py` (ví dụ: ticket ghi "trễ 9 ngày" nhưng order trễ 2 ngày → `denied`)
- **Việc:**
  - [ ] CP2: viết workflow theo docstring, các bước Python cố định. MockLLM chỉ dùng để soạn reply (nếu có).
  - [ ] CP3: truyền `crash_at`, để `InjectedCrash` bay ra.
  - [ ] Integration: review và merge PR của người 2, 3, 4 vào `main`; sau mỗi lần merge chạy lại cổng host.
  - [ ] CP5: chạy benchmark 4 shape và `check_submission`.
- **Tự kiểm:** `python -m pytest -q -m student -o addopts= -k workflow` → 62 passed.

## Người 2: Single agent (ReAct)

- **Nhánh:** `feat/single`
- **File sửa:** `src/lab8/shapes/single.py`
- **Test thêm:** `src/tests/test_single_extra.py` (ví dụ: vòng lặp không quá 8 bước; model không gọi được `issue_refund`)
- **Việc:**
  - [ ] CP2: dùng `lab8.runtime.run_react` với `max_steps=8`. `decide` chỉ chọn tool đọc (`lookup_order`, `lookup_policy`, `lookup_refund_history`, `compute_compensation`). Sau vòng lặp, **code** lấy quote và gọi `issue_refund`.
  - [ ] Đảm bảo `decide` không tin số ngày trễ trong ticket.
  - [ ] CP3: truyền `crash_at`, không bắt `InjectedCrash`.
  - [ ] CP5: chạy hidden self-check cho cả 3 shape, ghi kết quả (`status=error`, `leak_suspect`) cho người 4.
- **Tự kiểm:** `python -m pytest -q -m student -o addopts= -k single` → 62 passed.

## Người 3: Orchestrator + handoff

- **Nhánh:** `feat/orchestrator`
- **File sửa:** `src/lab8/shapes/orchestrator.py`
- **Test thêm:** `src/tests/test_orchestrator_extra.py` (ví dụ: handoff trong trace không chứa `parent_secret` / `CANARY_SECRET_`; `allowed_tools` toàn tool đọc)
- **Việc:**
  - [ ] CP2: dựng handoff bằng `lab8.handoff.make_handoff`, `facts` không chứa claim row hay header. Chạy `run_readonly_investigators`. Orchestrator tính quote từ order view và gọi `issue_refund`.
  - [ ] CP3: trace ghi **handoff đã sanitize**, không ghi parent context. Truyền `crash_at`.
  - [ ] CP5: viết `report/team/research_card.md`.
- **Tự kiểm:** `python -m pytest -q -m student -o addopts= -k orchestrator` → 62 passed.

## Người 4: Ledger / crash / security + báo cáo

- **Nhánh:** `feat/safety-tests`
- **File sửa:** `src/tests/test_safety_extra.py`, `src/reports/crash.json` (do tool sinh, **không sửa tay**)
- **Việc (bắt đầu ngay, không cần chờ shape):**
  - [ ] CP4: `python -m lab8.crash_test --count 20 --out reports/crash.json` → `crash_safety = 20/20`, commit file.
  - [ ] Chạy `python -m lab8.demo.buggy_workflow`, ghi lại vì sao checkpoint không thay được ledger (dùng cho report).
  - [ ] Viết test chạy trên cả 3 shape (parametrize): approval hết hạn / bị thu hồi, approval của claim khác (`approval_claim_mismatch`), đơn đã hoàn đủ (`order_already_refunded`), T14 hoàn phần chênh.
  - [ ] Khi shape nào merge: quét `traces/` của shape đó tìm `CANARY_SECRET_`, SĐT, địa chỉ, tên hàng.
  - [ ] Đăng ký bonus topic với giảng viên **trước 15:30** (nếu nhóm làm bonus).
  - [ ] CP5: điền `report/team/decision_adr.md` (shape chọn, commit hash, run id, số liệu từ `benchmark.json`) và `report/team/group_report.md`.

## Mốc thời gian

| Giờ | Mốc | Ai |
| --- | --- | --- |
| 13:45 | Workflow mẫu đẩy lên nhánh | Người 1 |
| 14:30 | 3 shape qua 62 test student (CP2) | 1, 2, 3 |
| 14:30 | `crash.json` 20/20 + test safety đầu tiên | 4 |
| 15:15 | T11, T12 xanh trên 3 shape, merge hết vào `main` (CP3) | 1 merge |
| 15:30 | Rà approval / secret xong (CP4) | 4 + chủ shape sửa lỗi |
| 16:15 | Benchmark 4 shape × 5 seed, hidden self-check | 1, 2 |
| 17:00 | ADR, research card, group report, báo cáo cá nhân, `check_submission` 0 FAIL | Cả nhóm |

## Lệnh hay dùng

```text
python -m pytest -q
python -m pytest -q -m student -o addopts= -k <shape>
python -m lab8.run --shape <shape> --claim-id C-001 --seed 11 --db data/run.sqlite
python -m lab8.crash_test --count 20 --out reports/crash.json
python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json
python -m lab8.check_submission
```

## Cuối buổi, mỗi người

- [ ] Copy `report/team/MSSV_HoTen.md` thành file riêng (MSSV + họ tên không dấu), ghi phần việc, công cụ AI đã dùng và cách tự kiểm tra.
- [ ] Điền dòng của mình trong bảng đóng góp `TEAM.md` (commit hash + tên test).
