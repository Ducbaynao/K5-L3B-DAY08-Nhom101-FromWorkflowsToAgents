# Decision record

Điền sau dấu `:` trên cùng dòng, không xóa nhãn. Giảng viên và `python -m lab8.check_submission` (chạy trong `src/`) đọc các dòng này bằng máy. Không đổi tên hay dời file này khỏi `report/team/`.
`Shape chọn` phải là đúng một trong: `workflow`, `single`, `orchestrator`, `swarm`. Đây là shape được chấm cổng hidden.

- Shape chọn: workflow
- Commit hash: fe41178
- Run id dẫn chứng: R-workflow-C-001-s11
- Pass rate / pass^5 / seed min-max / variance: 1.000 / 1.000 / 1.000 - 1.000 / 0.000000
- Cost per success (mô phỏng, VND): 28.77
- Crash safety: 20/20 (src/reports/crash.json)
- Secret leak / approval bypass: 0 leak / 0 bypass

Ví dụ một dòng đã điền: `- Shape chọn: workflow`, `- Crash safety: 20/20 (src/reports/crash.json)`.

## Vì sao shape này

Qua benchmark 70 trials trên 14 claims và 5 seed độc lập (11, 22, 33, 44, 55), Shape A (`workflow`) đạt hiệu năng tối ưu tuyệt đối: pass rate 1.000 (70/70 trials thành công), pass^5 đạt 1.000, phương sai giữa các seed bằng 0.000000. Đồng thời, workflow có chi phí vận hành rẻ nhất hệ thống với cost/success là 28.77 VND (thấp hơn Single 31.56 VND, Swarm 49.57 VND, và Orchestrator 56.65 VND). Nghiệp vụ xử lý claim bồi thường đơn hàng của LogiX-VN có luồng xử lý xác định theo các rule cố định (kiểm tra tồn tại claim, order scope, tính quote theo công thức, ủy quyền host xử lý trần bồi hoàn và idempotency). Do đó, workflow hoàn toàn loại bỏ được rủi ro ảo giác (hallucination) từ mô hình ngôn ngữ hoặc nguy cơ bị prompt injection qua nội dung ticket của người dùng (như trường hợp Swarm bị lừa ở seed 55 trên claim C-002 dẫn đến fail T02).

## Có đáng đổi lấy multi-agent không

Không đáng đổi lấy multi-agent (Orchestrator hoặc Swarm) cho bài toán claims xử lý bồi thường hiện tại. Bằng chứng số liệu từ `src/reports/benchmark.json` cho thấy:
1. Swarm có pass rate thấp hơn (0.986 so với 1.000 của Workflow), pass^5 chỉ đạt 0.929 và có seed variance = 0.000816 (do fail ở seed 55 trên claim C-002 khi tin vào ticket người dùng khai man). Chi phí của Swarm (49.57 VND) lại cao gấp 1.72 lần so với Workflow.
2. Orchestrator dù đạt pass rate 1.000 nhưng chi phí lên tới 56.65 VND (gấp gần 2 lần Workflow) do phải tốn chi phí gọi song song nhiều sub-investigators và tiêu thụ nhiều tool calls (5.57 tool calls/trial).

**Điều kiện làm quyết định kiến trúc đảo lại:** Quyết định sẽ đảo sang Multi-Agent (như Orchestrator) khi và chỉ khi:
- Miền bài toán mở rộng sang các yêu cầu điều tra đa nguồn không có cấu trúc cố định (ví dụ: đối soát chéo chứng từ vận chuyển từ nhiều bên thứ 3, xử lý hình ảnh hư hỏng hàng hóa kết hợp phân tích cảm xúc đàm phán).
- Nhiệm vụ phân tích phức tạp vượt quá khả năng biểu diễn của cây quyết định deterministic và đòi hỏi sự phân công chuyên biệt hóa (specialized agents) với năng lực reasoning sâu. Khi đó, chi phí cao hơn và độ trễ tăng thêm của multi-agent mới thực sự mang lại giá trị gia tăng vượt trội so với workflow đơn thuần.

## Trace và bằng chứng

Trace của nhóm tuân thủ nghiêm ngặt Trace Contract v1. Hệ thống chỉ ghi nhận các sự kiện vòng đời và dữ liệu đã được làm sạch:
- Các event được ghi nhận: `claim_lookup`, `order_lookup`, `compensation_computed`, `refund_submitted`, `crash` (nếu có crash), `completed`.
- Field cố ý **không** ghi: Không ghi nhận bất kỳ dữ liệu nhạy cảm nào bao gồm `CANARY_SECRET_*`, `parent_secret`, `Authorization` header, thông tin nhận dạng cá nhân (PII như SĐT, địa chỉ nhà, tên mặt hàng chi tiết), hoặc nội dung ticket người dùng thô chưa qua lọc.
- Đội ngũ bảo mật đã kiểm chứng bằng bộ test tự động `src/tests/test_safety_extra.py` và quét regex toàn bộ file trace trong `src/traces/`, xác nhận không tồn tại bất kỳ chuỗi `CANARY_SECRET_`, `Bearer`, hay `parent_secret` nào bị rò rỉ ra trace hay stdout.

## Giới hạn

MockLLM không phải model sản xuất (chỉ mô phỏng seed cố định để kiểm tra logic). Độ trễ (latency) được hệ thống đánh dấu là `unavailable`. Chi phí (cost) là tiền VND mô phỏng theo biểu giá token/tool call chuẩn hóa của lab, không phải hóa đơn API thực tế. Không sửa tay file JSON báo cáo dưới bất kỳ hình thức nào.
