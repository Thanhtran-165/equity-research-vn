# So sánh 6 Skill con của equity-research-vn — Bản đồ kiến trúc, dependency, risk và evidence maturity

**Trích dẫn canonical:** Tag `skill-harness-evaluator-v0.1.0-final-r2`
**Ngày:** 2026-07-31

---

## 1. Câu hỏi mà mỗi skill trả lời

| Skill | Câu hỏi chính |
|---|---|
| **vn-financial-data-collector** | Dữ liệu tài chính đáng tin cậy hiện có là gì? |
| **vn-fundamental-analysis** | Doanh nghiệp đang khỏe hay yếu, và vì sao? |
| **vn-valuation-engine** | Giá trị hợp lý nằm khoảng nào? |
| **vn-technical-analysis** | Giá và dòng tiền đang hành xử như thế nào? |
| **vn-news-digest** | Trong 30 ngày qua, điều gì đã thay đổi? |
| **vn-research-dashboard** | Làm thế nào tổng hợp toàn bộ evidence thành một sản phẩm đọc được? |

---

## 2. Kiến trúc 3 lớp

Hệ thống được chia thành ba lớp chức năng:

```text
LỚP TẠO EVIDENCE          LỚP DIỄN GIẢI/ĐỊNH GIÁ       LỚP TRUYỀN ĐẠT
─────────────────         ─────────────────────────     ─────────────────
collector (data)     →    fundamental (ratios)     →   dashboard
technical (giá)      →    valuation (fair value)       
news-digest (tin)                                       
```

- **Lớp tạo evidence:** collector, technical, news-digest — lấy hoặc tạo evidence từ thế giới bên ngoài (vnstock API, tin tức).
- **Lớp diễn giải/định giá:** fundamental, valuation — biến evidence thành nhận định tài chính.
- **Lớp truyền đạt:** dashboard — hợp nhất các nhận định thành sản phẩm cuối.

Vì lỗi ở mỗi lớp có tính chất khác nhau, không thể dùng một verifier chung cho cả sáu skill.

---

## 3. Dependency graph

```text
ticker → collector ──────────────┐
              │                  │
              └→ fundamental ────┤
                                 ↓
                            valuation
                                 │
valuation ──────────────────────┐│
technical ──────────────────────┤│
news-digest ────────────────────┤│
                                ↓
                           dashboard
```

### Phân loại dependency

```yaml
collector_consumers:
  direct_hard:
    - vn-fundamental-analysis    # thiếu input → không chạy đúng
    - vn-valuation-engine        # thiếu input → không chạy đúng
  indirect:
    - vn-research-dashboard      # nhận output tổng hợp qua các skill giữa
  operationally_independent:
    - vn-technical-analysis      # lấy giá trực tiếp, không cần collector output
    - vn-news-digest             # lấy tin trực tiếp, không cần collector output
```

Collector là nền tảng của **nhánh tài chính**, không phải toàn bộ pipeline.

### Loại quan hệ

```yaml
hard_dependency: 'thiếu input thì skill không thể chạy đúng'
  → collector → fundamental → valuation
  → 5 skill kia → dashboard (hard hoặc optional)

optional_integration: 'thiếu module thì dashboard vẫn tạo bản rút gọn'
  → news-digest → dashboard (optional)
  → technical → dashboard (optional nhưng khuyến nghị)

shared_entity: 'cùng dùng ticker nhưng không phụ thuộc output của nhau'
  → collector, technical, news-digest cùng nhận ticker nhưng không gọi nhau
```

---

## 4. Bảng so sánh 6 skill

| Skill | Lớp | Input | Output | Nguồn data | Mode |
|---|---|---|---|---|---|
| **collector** | Tạo evidence | Ticker CP | JSON data 5 năm | vnstock API + CafeF + QHCD | 1 |
| **fundamental** | Diễn giải | JSON từ collector | Ratios, DuPont, CAGR | JSON từ collector | 1 |
| **valuation** | Diễn giải | JSON + ratios | Fair value, target, 9 phương pháp | JSON từ collector + fundamental | 1 |
| **technical** | Tạo evidence | Ticker (giá thực) | Indicators, patterns, Tech Score | vnstock API (giá) | **2** (ACTIVE + PROFILE) |
| **news-digest** | Tạo evidence | Ticker | HTML digest, sentiment, events | vnstock + CafeF + VietnamBiz | 1 |
| **dashboard** | Truyền đạt | Output 5 skill kia | HTML dashboard hoàn chỉnh | Output từ 5 skill | 1 |

---

## 5. Contract boundary — 6 skill là hệ thống contract-driven

### vn-financial-data-collector

```yaml
contract:
  required_inputs:
    - ticker cổ phiếu niêm yết (HOSE/HNX/UPCOM)
    - năm phân tích (quy tắc ≥tháng 4 → N-1)
  guaranteed_outputs:
    - JSON data 5 năm: revenue, net_profit, equity, total_assets, EPS, BVPS
    - cross-check 3 nguồn xác minh
  failure_conditions:
    - ticker không tồn tại hoặc đã hủy niêm yết
    - nguồn vnstock không khả dụng
    - kỳ dữ liệu chưa công bố
  downstream_consumers:
    - vn-fundamental-analysis (hard)
    - vn-valuation-engine (hard)
    - vn-research-dashboard (indirect)
```

### vn-fundamental-analysis

```yaml
contract:
  required_inputs:
    - JSON data 5 năm từ collector (schema cố định)
  guaranteed_outputs:
    - ROE/ROA/ROS, DuPont decomposition, CAGR
    - đánh giá xu hướng và chất lượng lợi nhuận
  failure_conditions:
    - thiếu kỳ dữ liệu (<5 năm)
    - đơn vị không nhất quán
  downstream_consumers:
    - vn-valuation-engine (hard)
    - vn-research-dashboard (hard)
```

### vn-valuation-engine

```yaml
contract:
  required_inputs:
    - normalized financial data (từ collector)
    - fundamental ratios (từ fundamental)
    - giá hiện tại
  guaranteed_outputs:
    - method-level estimates (9 phương pháp: PE/PB/EV-EBITDA/P-CF/DCF/Reverse DCF/DDM/Graham/DuPont)
    - convergence hoặc dispersion giữa phương pháp
    - valuation conclusion (fair value, target price)
    - limitations
  failure_conditions:
    - thiếu equity hoặc earnings denominator
    - đơn vị không nhất quán
    - không đủ kỳ lịch sử
  downstream_consumers:
    - vn-research-dashboard (hard)
```

### vn-technical-analysis

```yaml
contract:
  required_inputs:
    - ticker (lấy giá-khối lượng trực tiếp từ vnstock)
  guaranteed_outputs:
    - mode ACTIVE: MA/RSI/MACD/Bollinger, candlestick patterns, Tech Score, Verdict
    - mode PROFILE: 28-block profile (volatility, drawdown, VPCI/OBV/CMF, Wyckoff, archetype)
  failure_conditions:
    - dữ liệu giá không đủ (<52 tuần cho PROFILE)
    - nguồn vnstock giá không khả dụng
  downstream_consumers:
    - vn-research-dashboard (optional nhưng khuyến nghị)
```

### vn-news-digest

```yaml
contract:
  required_inputs:
    - ticker (lấy tin trực tiếp)
  guaranteed_outputs:
    - HTML news digest, sentiment score, 4 nhóm tin (kinh doanh/ngành/vĩ mô/công bố)
    - events timeline
  failure_conditions:
    - không có tin tức trong 30 ngày
    - nguồn tin không khả dụng
  downstream_consumers:
    - vn-research-dashboard (optional)
```

### vn-research-dashboard

```yaml
contract:
  required_inputs:
    - output từ fundamental + valuation (hard)
    - output từ technical + news-digest (optional)
    - data từ collector (indirect)
  guaranteed_outputs:
    - HTML dashboard hoàn chỉnh (Bloomberg/Fintech style, Chart.js, deploy được)
    - template-driven, design system shared (_viz-shared)
  failure_conditions:
    - thiếu output fundamental hoặc valuation (hard dependency)
    - data không nhất quán giữa modules
  downstream_consumers:
    - (end product, không có downstream)
```

---

## 6. Primary risk của từng skill

```yaml
vn-financial-data-collector:
  primary_risk: sai nguồn, sai kỳ, sai đơn vị
  → mọi downstream bị nhiễm lỗi data

vn-fundamental-analysis:
  primary_risk: công thức đúng nhưng diễn giải sai nguyên nhân
  → ROE cao do leverage chứ không phải efficiency

vn-valuation-engine:
  primary_risk: giả định hoặc denominator sai làm fair value sai lớn
  → PE nhân 100, PB thiếu, DCF discount rate phi thực tế

vn-technical-analysis:
  primary_risk: overfitting và biến indicator thành khuyến nghị chắc chắn
  → RSI<30 không tự động nghĩa là BUY

vn-news-digest:
  primary_risk: trùng tin, sai ticker, sentiment thiếu ngữ cảnh
  → tin cũ được tính thành sentiment hiện tại

vn-research-dashboard:
  primary_risk: trình bày đẹp nhưng che giấu missing hoặc conflicting evidence
  → chart đẹp nhưng data thiếu kỳ, không hiển thị rõ
```

Mỗi risk có tính chất khác nhau → cần verifier khác nhau cho từng skill.

---

## 7. Product criticality vs Evidence maturity — hai trục riêng

```yaml
product_criticality:
  vn-financial-data-collector: CRITICAL          # nền tảng data, lỗi lan truyền
  vn-fundamental-analysis: CRITICAL              # cốt lõi phân tích
  vn-valuation-engine: CRITICAL                  # lớp định giá cốt lõi
  vn-technical-analysis: OPTIONAL_DECISION_SUPPORT  # hỗ trợ timing
  vn-news-digest: OPTIONAL_CONTEXT               # bổ sung thời sự
  vn-research-dashboard: CRITICAL_DELIVERY_LAYER # sản phẩm cuối

evidence_maturity:
  vn-financial-data-collector: TRANSITIVE                    # test ngầm qua downstream
  vn-fundamental-analysis: DIRECT_BUT_HISTORICALLY_COMPLEX   # 12 phase, nhiều remediation
  vn-valuation-engine: DIRECT_BUT_HISTORICALLY_COMPLEX       # 7 phase, nhiều remediation
  vn-technical-analysis: SPECIALIZED_DIRECT                  # Phase 3 qualify chain chuyên biệt
  vn-news-digest: INTEGRATION                                # test qua phase5/7 PIT
  vn-research-dashboard: END_TO_END_INTEGRATION              # test qua pipeline tổng
```

**Một skill quan trọng không đồng nghĩa được harness kiểm chứng sâu.** Collector là CRITICAL về sản phẩm nhưng chỉ TRANSITIVE về evidence — nó được kiểm tra gián tiếp qua việc downstream skills verify data nó cung cấp.

---

## 8. Harness coverage type (thay cho số file)

> Các nhãn evidence maturity dưới đây là taxonomy kiến trúc dành riêng cho báo cáo này, dùng để mô tả cách từng skill được kiểm tra. Chúng không thay thế evaluator maturity chính thức của `equity-research-vn` (`FUNCTIONAL_WITH_GENERALIZATION_EVIDENCE`) hoặc `skill-harness-evaluator` (`FUNCTIONAL_MACHINE`).

```yaml
vn-financial-data-collector:
  coverage_type: TRANSITIVE
  limitation: chưa có canonical standalone qualification
  note: 'Exercised indirectly qua contracts downstream (fundamental, valuation)'

vn-fundamental-analysis:
  coverage_type: DIRECT_HISTORICAL_AND_INTEGRATION
  note: 'Lịch sử remediation phức tạp (phase1→5R3b), verifier coverage sâu'

vn-valuation-engine:
  coverage_type: DIRECT_HISTORICAL_AND_INTEGRATION
  note: 'Lịch sử remediation (phase4F→6R2), verifier coverage sâu'

vn-technical-analysis:
  coverage_type: DIRECT_SPECIALIZED_QUALIFICATION
  note: 'Phase 3 qualify chain chuyên biệt, fixture rộng, authority chain riêng'

vn-news-digest:
  coverage_type: INTEGRATION_ONLY
  note: 'Test qua phase7-pit (8 PIT, 64/64 PASS)'

vn-research-dashboard:
  coverage_type: END_TO_END_INTEGRATION
  note: 'Test qua pipeline tổng (phase6/7 agent-eval)'
```

Số lượng artifact (verifier files, test files, fixtures) chỉ mô tả khối lượng, không chứng minh test độc lập, mutation sensitivity, specificity, oracle correctness, hay coverage thực tế.

---

## 9. Kết luận kiến trúc

Hệ thống được chia thành ba lớp: lớp tạo evidence, lớp diễn giải/định giá và lớp truyền đạt. Collector, technical và news-digest tạo hoặc lấy evidence từ thế giới bên ngoài; fundamental và valuation biến evidence thành nhận định; dashboard hợp nhất các nhận định thành sản phẩm cuối.

Vì lỗi ở mỗi lớp có tính chất khác nhau — sai data (collector), diễn giải sai (fundamental), denominator sai (valuation), overfitting (technical), sentiment thiếu ngữ cảnh (news), che giấu missing (dashboard) — không thể dùng một verifier chung cho cả sáu skill.

Mỗi skill cần verifier riêng, với failure mode và primary risk phù hợp với lớp chức năng của nó. Đây là lý do `equity-research-vn` được thiết kế thành 6 skill con có contract boundary rõ ràng, thay vì một skill khổng lồ.

---

## Phụ lục: Provenance

```yaml
source_baseline:
  canonical_tag: skill-harness-evaluator-v0.1.0-final-r2
  canonical_commit: 252798ea6b1ee845eda63d1202db49289cf44978

sources:
  vn_financial_data_collector:
    - vn-financial-data-collector/SKILL.md (trigger, workflow, contract)
    - skill-harness-evaluator-authority/final-acceptance/canonical-evidence-index.yaml (TRANSITIVE coverage)

  vn_fundamental_analysis:
    - vn-fundamental-analysis/SKILL.md (trigger, DuPont, CAGR)
    - skill-harness-evaluator-authority/run-registry.yaml (12 phase dirs, 48 verifier)
    - skill-harness-evaluator-authority/final-acceptance/canonical-evidence-index.yaml (DIRECT_HISTORICAL coverage)

  vn_valuation_engine:
    - vn-valuation-engine/SKILL.md (9 phương pháp: PE/PB/EV-EBITDA/P-CF/DCF/Reverse DCF/DDM/Graham/DuPont)
    - skill-harness-evaluator-authority/run-registry.yaml (7 phase dirs, 51 verifier)
    - skill-harness-evaluator-authority/final-acceptance/canonical-evidence-index.yaml (DIRECT_HISTORICAL coverage)

  vn_technical_analysis:
    - vn-technical-analysis/SKILL.md (2 mode ACTIVE+PROFILE, 28 blocks PROFILE)
    - skill-harness-evaluator-authority/completion-recovery-execution-v0.14.0/recovery-execution-results.yaml
      (Phase 3 qualify chain: 410 fixtures, 184 canonical, 33 mutations, authority chain)

  vn_news_digest:
    - vn-news-digest/SKILL.md (4 nhóm tin, sentiment, vnstock API)
    - skill-harness-evaluator-authority/evidence-archive-manifest.yaml
      (phase7-pit: 8 PIT, 64/64 PASS — trong archive member agent-eval/cohort-c/phase7-pit/)

  vn_research_dashboard:
    - vn-research-dashboard/SKILL.md (template, _viz-shared, Chart.js)
    - skill-harness-evaluator-authority/evidence-archive-manifest.yaml
      (phase6/7 end-to-end integration — trong archive member agent-eval/cohort-c/)

documentation_set:
  REPORT-SKILL-COMPARISON:
    purpose: 'Hệ thống gồm những thành phần nào và rủi ro nằm ở đâu'
  REPORT-BEFORE-AFTER-HARNESS:
    purpose: 'Quy trình nghiệm thu các thành phần đó đã thay đổi như thế nào'
```
