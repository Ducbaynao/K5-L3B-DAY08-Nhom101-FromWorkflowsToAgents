# Báo cáo cá nhân — Phạm Lý Ngọc Đức

## 1. Thông tin thành viên

- Họ tên: Phạm Lý Ngọc Đức
- MSSV: 2A202603991
- Email: 26ai.ducpln@vinuni.edu.vn
- GitHub: Ducbaynao

## 2. Phần việc phụ trách

Tôi phụ trách Shape B — Single Agent trong bài toán xử lý claim hoàn tiền của LogiX-VN. Phần việc của tôi gồm triển khai `run_claim` trong `src/lab8/shapes/single.py`, bổ sung test cá nhân trong `src/tests/test_single_extra.py` và ghi nhận tiến độ triển khai.

Tôi xây dựng một vòng ReAct có giới hạn 8 bước để đọc đơn hàng và tính mức bồi thường. Sau vòng lặp, code của shape chuyển quote cho host kiểm tra approval, trần hoàn tiền theo đơn và idempotency trước khi ghi ledger.

## 3. Đóng góp cụ thể

Tôi làm việc trên nhánh `feat/single`. Mã commit của phần đóng góp sẽ được bổ sung sau khi tôi thực hiện commit.

Tôi giữ nguyên chữ ký `run_claim(claim_id, *, seed, store_path, crash_at=None)`. Hàm mở SQLite bằng `connect`, tạo `Budget` và `Trace`, đọc claim qua `get_claim_view`, rồi trả kết quả bằng `finish()`. Tôi đóng kết nối trong `finally` để áp dụng cho cả lần chạy bình thường và lần chạy có crash. Claim không tồn tại trả `failed`; claim thiếu `order_id` trả `needs_info`. Hai trường hợp này có quote bằng 0.

Tôi triển khai đường đi `lookup_order → compute_compensation → final` bằng `run_react(max_steps=8, worker=True)`. Mỗi lượt quyết định gọi `mock_llm.complete` với cùng budget. Callback Python dựng action theo observation của runtime, còn số tiền lấy từ kết quả `compute_compensation`. Tôi dùng `order_id` và `principal_id` từ claim để tra đơn. Đơn không thấy hoặc nằm ngoài quyền truy cập trả `escalated`. Khi runtime hết giới hạn bước, tôi trả `failed` với lý do `step_cap` và quote bằng 0.

Tôi chuyển quote dương đầy đủ vào `issue_refund` cùng `crash_at`. Ví dụ T14 có quote 150.000đ và đã hoàn 30.000đ từ claim trước, host tính phần chênh 120.000đ để ghi ledger. Tôi ánh xạ kết quả host thành `resolved` khi chấp nhận, `denied` khi từ chối theo policy và `failed` khi có xung đột số tiền lúc retry. `InjectedCrash` được truyền ra ngoài hàm.

Tôi ghi trace cho bước đọc claim, quyết định ReAct, quote, lời gọi host, kết quả host và trạng thái kết thúc. Trước khi gọi host, tôi lưu trace để lần chạy bị crash vẫn có bằng chứng các bước đã thực hiện. Tôi giới hạn claim trong observation ở `claim_id`, `order_id` và `principal_id`. Trace sử dụng các trường được chọn lọc và giữ ticket thô, secret, header cùng thông tin cá nhân ngoài log.

Tôi bổ sung sáu hàm test, tương ứng 12 trường hợp chạy do có tham số hóa.

| Test đã thêm | Nội dung kiểm tra | Số trường hợp |
|---|---|---:|
| `test_single_early_exit` | Claim không tồn tại; order_id NULL hoặc rỗng; trạng thái, budget, trace, ledger và đóng kết nối | 3 |
| `test_single_react_reads_order_and_counts_calls` | Quote C-001/C-002 ở seed 55, tool chỉ đọc và số model/tool call | 2 |
| `test_single_react_escalates_invisible_order` | Đơn không tồn tại hoặc principal không sở hữu đơn | 2 |
| `test_single_step_cap_returns_failed_without_refund` | Lặp đủ 8 bước, trả failed/step_cap, có trace và không phát sinh refund | 1 |
| `test_single_crash_resumes_with_one_refund` | Ba điểm crash, đóng kết nối, trace và resume/retry giữ một refund | 3 |
| `test_single_retry_changed_quote_preserves_committed_refund` | Quote thay đổi khi retry tạo amount_conflict và giữ effect đã commit | 1 |

## 4. Bằng chứng

Tôi ghi nhận kết quả kiểm tra trên nhánh `feat/single` ngày 17/11/2026, trước khi commit phần đóng góp.

| Hạng mục | Kết quả |
|---|---|
| Bộ pytest mặc định | 66 passed, 248 deselected |
| Ma trận student riêng Shape B | 62 passed, 252 deselected |
| File test cá nhân | 12 passed |
| Kiểm tra diff | `git diff --check` kết thúc thành công |

Các lệnh kiểm tra đã được chạy trong `src/`.

```powershell
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=traces/single-refund-host --tb=short
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=traces/single-refund-matrix -m student -o addopts= -k "single and not workflow and not orchestrator and not swarm" --tb=short
.\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider --basetemp=traces/single-refund-check -o addopts= tests/test_single_extra.py --tb=short
git diff --check
```

Tôi dùng biểu thức lọc trên để chọn riêng Shape B vì tên hàm `test_public_single_run_cases` cũng chứa từ `single`. Môi trường công cụ từng gặp lỗi quyền ở thư mục Temp mặc định, nên các lần kiểm tra sử dụng thư mục tạm trong workspace.

Tôi đã kiểm tra C-001 bằng lệnh CLI dưới đây hai lần trên cùng database.

```powershell
.\.venv\Scripts\python.exe -m lab8.run --shape single --claim-id C-001 --seed 11 --db data/single-c001.sqlite
```

Cả hai lần đều trả `resolved`, `proposal_amount=35000`, một refund 35.000đ và `committed_audit_count=1`. Run ID dẫn chứng là `R-single-C-001-s11`. Kết quả ghi nhận 3 model call, 3 tool call và chi phí mô phỏng 34,2 VND mỗi lần chạy. Database và trace được giữ ở máy local theo cấu hình `.gitignore`.

Tôi lưu phần triển khai tại [single.py](../../src/lab8/shapes/single.py), các test tại [test_single_extra.py](../../src/tests/test_single_extra.py) và lịch sử tiến độ tại [single-agent-progress.md](../../docs/single-agent-progress.md). Link commit sẽ được bổ sung khi có commit chứa các thay đổi này.

## 5. Công cụ AI đã dùng

Tôi sử dụng Codex để hỗ trợ đọc repo và plan, đối chiếu contract với runtime, triển khai phần single agent, bổ sung test và soạn báo cáo. Trong quá trình làm việc, Codex đã chạy các lệnh pytest, kiểm tra CLI C-001 và `git diff --check`; các kết quả thực tế được ghi ở mục 4.

Tôi dùng các test để đối chiếu phần code do AI hỗ trợ với yêu cầu của lab. Ma trận public kiểm tra các trường hợp nghiệp vụ, approval, trần hoàn tiền, retry và crash; test cá nhân kiểm thêm giới hạn bước, quyền truy cập, đóng kết nối và xung đột quote. Phần kiểm tra này là bằng chứng chạy được trong môi trường hiện tại. Tôi còn cần trực tiếp rà soát và tự giải thích lại code trước khi nộp bài, đặc biệt là callback quyết định, quote đầy đủ và transaction của host.

Trong code của lab, các lời gọi model sử dụng MockLLM theo seed. Chi phí ghi nhận là chi phí mô phỏng theo cấu hình của bài. Tôi chưa có kết quả hidden chính thức hoặc kết quả so sánh đầy đủ bốn kiến trúc để đưa vào phần đánh giá này.

## 6. Tự đánh giá

Tôi đánh giá phần single agent đã đáp ứng các yêu cầu được kiểm chứng bởi 62 case public và 12 trường hợp test cá nhân. Các kết quả cho thấy shape lấy dữ liệu đơn hàng qua tool có kiểm principal, tính quote qua code, chuyển thao tác ghi tiền cho host và giữ một refund khi resume/retry trong các kịch bản đã kiểm tra.

Tôi còn cần bổ sung commit hash và phối hợp tích hợp với nhóm. Khi có bộ `student_drop/`, tôi sẽ cùng nhóm kiểm các trial lỗi và dấu hiệu rò dữ liệu. Quyết định chọn kiến trúc cho toàn nhóm cần dựa trên benchmark chung của bốn shape và các điều kiện must-pass.
