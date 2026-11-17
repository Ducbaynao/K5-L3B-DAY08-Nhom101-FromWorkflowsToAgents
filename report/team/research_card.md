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
| SOURCE | Paper/blog, năm, URL, loại bằng chứng (benchmark, production report, blog kinh nghiệm) | Cemri et al., *Why Do Multi-Agent LLM Systems Fail?* (MAST), NeurIPS 2025 Datasets & Benchmarks, https://arxiv.org/abs/2503.13657. Loại bằng chứng: nghiên cứu thực nghiệm, gán nhãn lỗi trên trace của nhiều framework multi-agent |
| CLAIM | Một kết luận gốc của nguồn. Không viết rộng hơn phạm vi paper | Lỗi của hệ multi-agent gom được vào 3 nhóm (thiết kế/đặc tả hệ thống, lệch phối hợp giữa agent, kiểm chứng và kết thúc task); nhiều lỗi đến từ thiết kế hệ thống chứ không chỉ do model yếu, trong đó thiếu hoặc kiểm chứng sai là một nhóm lớn |
| BOUNDARY | Model / dataset / setup giới hạn kết luận đó | Paper đo trên LLM thật và task mở (code, toán, hỏi đáp). Lab dùng MockLLM theo seed, 14 claim public, luật hoàn tiền cố định và host chặn ghi; lỗi của swarm ở seed 55 là điểm yếu cố ý (`REFERENCE_WEAKNESS`), không phải lỗi phát sinh tự nhiên |
| HYPOTHESIS | Nếu đổi shape A→B (hoặc bật/tắt một thành phần), metric X sẽ đổi theo hướng nào, khoảng bao nhiêu | Đổi workflow (A) sang swarm (D): pass rate giảm khoảng 1 trial trên 70 (≈ 1.000 → 0.986), pass^5 giảm còn ≈ 0.93, variance tăng từ 0, cost/success tăng ≈ 70% vì swarm thêm call `peer`/`parse`; lỗi rơi vào nhóm kiểm chứng của MAST |
| METHOD | Biến giữ cố định: model, tools, seed, corpus, giá, evaluator. Biến duy nhất được thay đổi: … | Giữ cố định: MockLLM, tool read-only và host `durability`, 14 claim public, seed 11/22/33/44/55, `config/pricing.yaml`, evaluator `lab8.metrics`, SQLite mới mỗi trial. Biến duy nhất thay đổi: shape (`workflow` vs `swarm`) |
| FAILURE / METRIC | Một lỗi dự kiến và cách đo nó: pass rate, pass^5, variance, cost/success, leak, bypass | Lỗi dự kiến: swarm tin số ngày trễ trong ticket thay vì cột `delay_days` (không đối chiếu với nguồn sự thật) ở C-002 seed 55 → `resolved` thay vì `denied`. Đo bằng pass rate, pass^5, seed variance, cost/success trong `src/reports/benchmark.json` và lý do fail của trial `R-swarm-C-002-s55` |

## Kết quả ablation

- Lệnh đã chạy (copy nguyên văn): `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`
- Run id / file report: `src/reports/benchmark.json` (commit `12936a8`); trial fail duy nhất của swarm là `R-swarm-C-002-s55`; đối chứng workflow `R-workflow-C-002-s55` (`denied`, pass)
- Kết quả so với hypothesis (đúng / sai / không kết luận được), kèm số liệu: **đúng**. Workflow 70/70, pass 1.000, pass^5 1.000, variance 0, cost/success 28.77 VND. Swarm 69/70, pass 0.986, pass^5 0.929 (seed 55 = 0.929), variance 0.000816, cost/success 49.57 VND (+72%). Lỗi duy nhất là `status resolved != denied` ở C-002 seed 55, thuộc nhóm kiểm chứng của MAST (không đối chiếu số trong ticket với order). Vì lỗi này do lab cài sẵn, kết quả xác nhận cách đo bắt được lỗi kiểm chứng, chưa đủ để ước lượng tần suất lỗi đó trên LLM thật.
- Giới hạn: MockLLM không phải model sản xuất, latency là `unavailable`.

Muốn đi xa hơn một ablation để lấy điểm cộng thì xem [docs/bonus_topics.md](../../docs/bonus_topics.md).
