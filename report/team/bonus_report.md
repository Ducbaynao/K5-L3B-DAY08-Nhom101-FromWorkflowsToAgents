# Bonus report: B3

- Topic + nguồn (tên, năm, slide): B3 · Verifier/aggregator chống khuếch đại lỗi — Google Research 2026, *Towards a Science of Scaling Agent Systems* (error amplification), slide 17 (Evaluator–optimizer), 22 (Reflection), 42.
- CLAIM của nguồn (1 câu): agent độc lập khuếch đại lỗi tới 17,2×, còn orchestration tập trung (có điểm kiểm soát chung) giảm xuống 4,4×.
- BOUNDARY (model / dataset / setup): nguồn đo trên LLM thật, nhiều benchmark agent và nhiều topology. LogiX dùng MockLLM theo seed, luật hoàn tiền cố định, host chặn ghi; lỗi duy nhất của swarm là điểm yếu cài sẵn (seed chia hết cho 5 tin số ngày trễ trong ticket). Lab không đo được hệ số khuếch đại, chỉ đo được verifier có chặn lỗi trước khi thành quyết định hay không.
- HYPOTHESIS trên LogiX: thêm verifier bằng code (đối chiếu `delay_days`, `status`, `damage_verified` với order có cấu trúc, quote lại tối đa 1 vòng) đưa swarm về pass 1.000, pass^5 1.000, variance 0 trên cả bộ public và bộ đối kháng, với cost/success tăng ≤ 20% so với swarm nhưng vẫn ≥ 1,5× workflow. Viết sau một lần chạy thử trên bộ đối kháng, trước khi chạy các lệnh dưới.
- Biến cố định / biến thay đổi: cố định MockLLM, tool read-only, host `durability`, seed `11,22,33,44,55`, `config/pricing.yaml`, evaluator `lab8.metrics.trial_pass`, SQLite mới mỗi trial (chạy qua `--extra-shape`). Biến thay đổi duy nhất giữa `swarm` và `swarm_verified`: bước `verify_facts` (+1 tool đọc, +1 tool quote khi lệch). `workflow` là mốc so sánh.
- Lệnh tái lập (copy-paste được, chạy trong `src/`):
  - `python -m lab8.benchmark --shapes workflow,swarm,swarm_verified --extra-shape swarm_verified=bonus.swarm_verified:run_claim --seeds 11,22,33,44,55 --out reports/bonus_benchmark.json`
  - `python -m lab8.benchmark --shapes workflow,swarm,swarm_verified --extra-shape swarm_verified=bonus.swarm_verified:run_claim --cases bonus/cases.jsonl --world bonus/world.json --seeds 11,22,33,44,55 --out reports/bonus_benchmark_cases.json`
  - (cần `student_drop/` ở gốc repo) `python -m lab8.benchmark --shapes swarm,swarm_verified --extra-shape swarm_verified=bonus.swarm_verified:run_claim --cases ../student_drop/hidden_claims.jsonl --world ../student_drop/hidden_world_state.json --seeds 11,22,33,44,55 --out reports/bonus_hidden_selfcheck.json`
  - `python -m bonus.b3_summary` (đọc ba file trên và `traces/`, ghi `reports/bonus_b3.json`)
  - `python -m pytest -q tests/test_bonus_swarm_verified.py` (23 test)
- File report + run id: `src/reports/bonus_b3.json` (tổng hợp), `bonus_benchmark.json`, `bonus_benchmark_cases.json`, `bonus_hidden_selfcheck.json`. Trace minh họa: `R-swarm_verified-C-002-s55`, `R-swarm_verified-B-002-s55`.

## Kết quả

Bộ đối kháng `bonus/cases.jsonl` có 11 claim, nhãn viết tay theo `docs/business_rules.md`; mỗi claim có `label_note` ghi cách suy nhãn. Các loại: ticket nói quá, nói thiếu, nói dối hỏng hàng, nhiều con số trong một câu, injection, ngay dưới ngưỡng 3 ngày, đơn hủy, approval thấp hơn quote, approval hết hạn. Workflow (không đọc ticket) đạt 55/55 trên bộ này, dùng làm kiểm tra chéo cho nhãn.

| Bộ | Shape | Pass | pass^5 | Seed min–max | Variance | Cost/success (VND) | Trả sai | Từ chối sai | Bypass | Leak | Verifier can thiệp |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Public 14×5 | workflow | 1.000 | 1.000 | 1.000–1.000 | 0 | 28.77 | 0 | 0 | 0 | 0 | – |
| | swarm | 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 1 | 0 | 0 | 0 | – |
| | swarm_verified | 1.000 | 1.000 | 1.000–1.000 | 0 | 57.57 | 0 | 0 | 0 | 0 | 1 (1 đổi tiền) |
| Đối kháng 11×5 | workflow | 1.000 | 1.000 | 1.000–1.000 | 0 | 30.91 | 0 | 0 | 0 | 0 | – |
| | swarm | 0.873 | 0.364 | 0.364–1.000 | 0.064793 | 61.76 | 4 | 2 | 0 | 0 | – |
| | swarm_verified | 1.000 | 1.000 | 1.000–1.000 | 0 | 65.54 | 0 | 0 | 0 | 0 | 9 (7 đổi tiền) |

- **Verifier can thiệp đúng chỗ swarm lệch.** Mọi override đều ở seed 55 và đều trên trường `delay_days`.
  - 7 lần đổi tiền: chặn 4 lần trả sai (B-001, B-004, B-006, B-010), cứu 2 lần từ chối sai (B-002, B-008, ticket nói thiếu), và sửa `proposal_amount` của B-011.
  - B-011: approval đã hết hạn nên host vẫn chặn ghi, nhưng swarm báo quote 30.000 thay vì 0.
  - 2 lần không đổi tiền: B-007 (damage 150.000 lớn hơn phí ship nên số ngày không ảnh hưởng) và B-009.
  - Ở seed 11–44, verifier không can thiệp lần nào (`test_verifier_is_silent_when_swarm_trusts_the_db`).
- **Trace minh họa `R-swarm_verified-C-002-s55`:** `model_override {delay_days: 5}` → `verifier_override {fields: {delay_days: {used: 5, structured: 2}}, amount_before: 20000, amount_after: 0}` → `quote` → `denied`. Cùng claim, cùng seed, swarm trả 20.000.
- **Hidden `student_drop/`** (không nhãn, 40 claim × 5 seed):
  - swarm khác quyết định của workflow ở 6/200 trial, đều ở seed 55: 5 lần trả tiền khi workflow từ chối, 1 lần ngược lại.
  - swarm_verified khớp workflow 200/200, với 6 override.
  - Cả hai đều 0 error, 0 leak_suspect.
  - Khớp workflow không đồng nghĩa với đúng nhãn; điểm hidden do grader giảng viên chấm.
- **Cost:** verifier thêm ≈ 0,9 tool call mỗi trial (public 5.53 so với 4.66). Cost/success so với swarm tăng 16,2% trên public và 6,1% trên bộ đối kháng (swarm có ít lần thành công hơn nên cost/success của nó đã bị đẩy lên). So với workflow: 2,0× (public) và 2,1× (đối kháng).

## Kết luận

**Ủng hộ hypothesis**, trong phạm vi lab.
- Verifier đưa swarm về đúng mức chất lượng của workflow (pass, pass^5, variance) trên cả hai bộ có nhãn, và về đúng quyết định của workflow trên hidden.
- Cái giá: cost/success +6–16% so với swarm, ≈ 2× workflow.

**Câu "verifier đã thay phần quyết định thì swarm còn giữ gì?"** Gần như không còn gì về tiền.
- Trong cài đặt này, mỗi khi swarm và dữ liệu có cấu trúc khác nhau thì dữ liệu có cấu trúc thắng. Khi chúng giống nhau thì verifier không làm gì.
- Vậy quyết định tiền thực chất do `compute_compensation` trên order row, giống workflow. Hai call `peer` / `parse` của swarm chỉ còn là chi phí.
- Thứ còn lại là tín hiệu: sự kiện `verifier_override` đánh dấu ticket mâu thuẫn với DB, có thể chuyển cho bộ phận kiểm tra gian lận. Nhưng tín hiệu này chỉ xuất hiện khi swarm tình cờ tin ticket (seed 55). Workflow parse ticket rồi so sánh trực tiếp sẽ cho tín hiệu đó ổn định hơn và rẻ hơn.
- Kết luận này củng cố ADR: trên task có nguồn sự thật có cấu trúc, verifier biến swarm thành một workflow đắt hơn.

**Kết luận đảo ngược khi:**
- Lỗi của agent nằm ở phần code không kiểm được: đọc ảnh hỏng hàng, diễn giải chứng từ không cấu trúc. Lúc đó verifier bằng code không có gì để đối chiếu, và swarm hoặc orchestrator mới có giá trị riêng.
- Order row có thể sai hoặc cũ: verifier sẽ lan truyền lỗi của DB.
- Lỗi rơi vào trường verifier không kiểm. Verifier chỉ kiểm 3 trường dùng để quote; nếu policy có thêm điều kiện mới (ví dụ `carrier`) mà verifier không được cập nhật thì nó bỏ lọt.

## Giới hạn

- **MockLLM, không phải model thật:** lỗi của swarm là điểm yếu cài sẵn (chỉ `delay_days`, chỉ seed chia hết cho 5), nên benchmark chỉ kích hoạt nhánh `delay_days` của verifier. Nhánh `status` và `damage_verified` chỉ được kiểm bằng unit test (`test_verify_facts_catches_every_quoted_field`), không qua benchmark.
- **Không đo được hệ số khuếch đại lỗi** 17,2× / 4,4× của nguồn: lab có một nguồn lỗi duy nhất và không có chuỗi agent truyền lỗi cho nhau.
- **Latency `unavailable`.** Cost là VND mô phỏng theo `config/pricing.yaml`.
- **Bộ đối kháng nhỏ** (11 claim, cùng một principal), do nhóm tự viết. Workflow đạt 55/55 cho thấy nhãn nhất quán với luật, nhưng workflow và nhãn cùng dựa trên cách nhóm đọc `business_rules.md`.
- **Hidden không có nhãn:** chỉ so được với quyết định của workflow, không phải pass rate.
