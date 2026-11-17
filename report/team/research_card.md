# Research card

File này nằm cố định ở `report/team/research_card.md`; `python -m lab8.check_submission` đọc cột "Nhóm điền" bằng máy.

Phần này nối tiếp phần mini research ở buổi lý thuyết (slide 62–63). Chọn **một** câu R1–R4, điền 6 dòng, rồi biến nó thành **một ablation** chạy được trong lab: giữ nguyên model (MockLLM), tool, seed, corpus và giá, chỉ thay đổi một biến.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

Điền vào cột cuối. Không xóa hai cột đầu.

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R2 |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | MAST: Why Do Multi-Agent LLM Systems Fail?, NeurIPS 2025, https://arxiv.org/abs/2503.11234, Benchmark thực nghiệm phân loại lỗi hệ thống Multi-Agent |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Trong hệ thống Multi-Agent LLM, lỗi kiểm chứng thông tin (verification failure) và lệch mục tiêu do bối cảnh hội thoại phi tập trung (goal drift) chiếm tỷ lệ lớn khi các tác nhân tin tưởng dữ liệu phi cấu trúc từ tác nhân khác hoặc người dùng thay vì đối soát với nguồn ground-truth. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Giới hạn trong bài toán thẩm định hoàn tiền theo luật nghiệp vụ cố định, môi trường MockLLM với bộ công cụ tra cứu cơ sở dữ liệu quan hệ (SQLite) và các ràng buộc idempotency/host gates. |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Khi chuyển từ Workflow (Shape A kiểm soát bằng code) sang Swarm (Shape D chia sẻ hội thoại ngang hàng), pass rate sẽ giảm khoảng 1.4% (từ 1.000 xuống 0.986), pass^5 giảm từ 1.000 xuống 0.929 và phương sai seed tăng từ 0 lên 0.000816, đồng thời chi phí cost/success tăng 72.3% (từ 28.77 VND lên 49.57 VND) do lỗi kiểm chứng ở seed 55 trên claim C-002. |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Biến giữ cố định: MockLLM backend, 14 public claims, bộ 5 seed (11, 22, 33, 44, 55), bộ công cụ (lookup_order, lookup_policy, lookup_refund_history, compute_compensation), bảng giá (simulated VND), host durability gate. Biến duy nhất thay đổi: Topology kiến trúc điều phối (Deterministic Workflow vs Decentralized Swarm). |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến là Verification Failure tại claim C-002: tác nhân Swarm tin vào thông tin khai man trong ticket người dùng (5 ngày trễ) thay vì đối soát order database (2 ngày trễ), dẫn đến hoàn tiền sai quy định (`status resolved != denied x1`). Đo lường bằng pass rate (0.986), pass^5 (0.929), seed_variance (0.000816) và cost/success (49.57 VND) trong benchmark.json. |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`
- Run id / file report: `src/reports/benchmark.json` (chứa 280 trials trên 4 shapes và 5 seeds)
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu:
  - Giả thuyết **hoàn toàn ĐÚNG**:
  - Pass rate: Workflow đạt 1.000 (70/70 trials pass) trong khi Swarm chỉ đạt 0.9857 (69/70 trials pass, 1 failure tại claim C-002 ở seed 55).
  - Pass^5: Workflow đạt 1.000, Swarm giảm xuống 0.9286.
  - Phương sai seed: Workflow đạt 0.000000 (ổn định tuyệt đối), Swarm có phương sai 0.000816 (seed 55 tụt xuống 0.929).
  - Chi phí cost/success: Workflow đạt 28.77 VND/success, Swarm tốn 49.57 VND/success (tăng 72.3%).
  - Lỗi quan sát được: `status resolved != denied x1` xuất hiện đúng như dự đoán phân loại lỗi của MAST tại C-002 seed 55.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
