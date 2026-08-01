# BÁO CÁO ĐA GÓC CẠNH VÀ HƯỚNG DẪN NÂNG CẤP `equity-research-vn` TRÊN ZCODE

**Đối tượng bàn giao:** model/agent tiếp theo làm việc trực tiếp trên ZCode  
**Source of truth cần nâng cấp:** `/Users/bobo/.zcode/skills/equity-research-vn`  
**Ngoài phạm vi:** `/Users/bobo/.codex/skills/equity-research-vn` và mọi bản sao khác  
**Ngày chụp hiện trạng:** 2026-08-01  
**Phiên bản tự khai báo:** 3.2.0  
**Mức trưởng thành tự khai báo:** `PRODUCTION_READY`  
**Kết luận kiểm toán:** chưa đủ bằng chứng để duy trì nhãn `PRODUCTION_READY` hoặc cho phép tự động triển khai báo cáo phục vụ quyết định đầu tư.

---

## 1. Mục tiêu của tài liệu

Tài liệu này không phải một bản nhận xét chung. Đây là hồ sơ bàn giao để model khác có thể:

1. hiểu đúng kiến trúc và nguồn thẩm quyền của skill trên ZCode;
2. phân biệt lỗi kỹ thuật với lỗi phương pháp nghiên cứu;
3. sửa theo thứ tự rủi ro, không chạy theo số lượng REQ hoặc số test xanh;
4. bổ sung kiểm thử có khả năng phát hiện sai, không chỉ chứng minh fixture chuẩn có thể PASS;
5. tái thẩm định độc lập trước khi đổi nhãn trưởng thành hoặc bật deploy cưỡng chế.

Không được hiểu tài liệu này là lệnh triển khai production. Model tiếp quản phải sửa trong phạm vi source ZCode, chạy qualification, tạo bằng chứng và dừng ở trạng thái đề nghị review cho đến khi chủ dự án phê duyệt.

---

## 2. Kết luận điều hành

### 2.1 Điểm hiện tại

| Góc đánh giá | Điểm hiện tại /100 | Nhận định ngắn |
|---|---:|---|
| Chất lượng học thuật và phương pháp nghiên cứu | **58** | Có khung phân tích thực hành tốt, nhưng công thức định giá có lỗi đơn vị/khái niệm và chưa có validation thực nghiệm đủ mạnh. |
| Độ tin cậy vận hành | **65** | Kiến trúc phase, registry và verifier khá sâu; vẫn có đường đi tạo “completed” giả, schema drift và gate deploy không thực sự chặn. |
| An toàn và quản trị | **48** | Có provenance và evidence intent, nhưng có shell injection, hook advisory, phạm vi hook hẹp và nhãn trưởng thành vượt quá bằng chứng. |
| Chất lượng sản phẩm/báo cáo | **74** | Cấu trúc nội dung, dashboard, guardrail và khả năng giải thích tương đối tốt; chất lượng trình bày không bù được sai phương pháp. |
| Khả năng tái lập và kiểm chứng | **61** | Có task-state, fixture và evidence, nhưng hợp đồng dữ liệu chưa thống nhất và một số tham chiếu học thuật/runtime chưa tự đủ. |
| **Điểm tổng hợp có trọng số** | **62** | Tốt cho bản nháp nghiên cứu có người kiểm soát; chưa phù hợp cho tự động hóa quyết định hoặc production không giám sát. |

Trọng số dùng cho điểm tổng hợp: học thuật 40%, vận hành 25%, an toàn/quản trị 15%, sản phẩm 10%, tái lập 10%. Đây là **đánh giá chuyên gia có bằng chứng**, không phải một thang đo đã được hiệu chuẩn thống kê.

### 2.2 Các đề nghị có thể cải thiện bao nhiêu?

| Mốc nâng cấp | Điểm kỳ vọng | Mức tăng so với hiện tại | Điều kiện bắt buộc |
|---|---:|---:|---|
| Hoàn thành Wave 1: correctness + security + contract | **73–76** | **+11 đến +14** | Sửa công thức, runner, schema, map, shell execution và deploy gate; có regression tests âm. |
| Hoàn thành Wave 1–3: thêm phương pháp nghiên cứu và empirical validation | **82–87** | **+20 đến +25** | Backtest walk-forward, hiệu chuẩn sentiment, forecast-vs-actual, bibliography và uncertainty policy. |
| Hoàn thành toàn bộ Wave 1–5 và qualification độc lập | **88–92** | **+26 đến +30** | Hai reviewer độc lập, cold runs đa ngành, mutation tests, shadow rollout và owner approval. |

Mức tăng trên là **ước lượng có điều kiện**, không phải cam kết. Không được cộng điểm chỉ vì thêm tài liệu, thêm REQ hoặc làm test fixture hiện có xanh hơn. Điểm chỉ tăng khi acceptance criteria tạo ra bằng chứng mới có khả năng bác bỏ hệ thống khi nó sai.

### 2.3 Phán quyết sử dụng

**Có thể dùng hiện tại:**

- tạo bản nháp equity research nội bộ;
- hỗ trợ analyst thu thập, cấu trúc và kiểm tra chéo dữ liệu;
- tạo báo cáo giáo dục/tham khảo nếu có người am hiểu tài chính rà lại công thức, dữ liệu và kết luận;
- thử nghiệm dashboard và quy trình evidence trong môi trường không production.

**Chưa được dùng hiện tại:**

- tự động đưa ra khuyến nghị mua/bán hoặc phân bổ vốn thực;
- tự động deploy công khai chỉ vì verifier báo PASS;
- coi median đa phương pháp là “giá trị hợp lý khoa học” khi chưa lọc tính áp dụng và tương quan giữa phương pháp;
- dùng Tech Score hoặc sentiment score như tín hiệu đã được chứng minh tạo alpha;
- công bố như một nghiên cứu học thuật có thể tái lập nếu chưa có bibliography, versioned dataset, phương pháp ước lượng và validation ngoài mẫu.

---

## 3. Phạm vi, nguồn thẩm quyền và phương pháp kiểm toán

### 3.1 Phạm vi duy nhất được phép sửa

Model tiếp quản chỉ được thay đổi các file cần thiết dưới:

```text
/Users/bobo/.zcode/skills/equity-research-vn
```

Hook liên quan nằm tại:

```text
/Users/bobo/.zcode/hooks/predeploy-gate.sh
```

Cấu hình đăng ký hook hiện hành nằm tại:

```text
/Users/bobo/.zcode/cli/config.json
```

Không đồng bộ sang Codex trong task này. Không lấy bản Codex làm source of truth. Nếu phát hiện khác biệt, ghi nhận riêng; không tự ý “sửa cho giống nhau”.

### 3.2 Bằng chứng đã kiểm tra

- Đọc toàn bộ entrypoint `SKILL.md` của bản ZCode.
- Đối chiếu `VERSION`, `requirements.yaml`, `requirements-phase-map.yaml`, 9 phase prompt, runner, independent verifier, test fixtures và hook deploy đang được đăng ký.
- Parse registry bằng YAML thay vì chỉ đếm chuỗi.
- Chạy các test hiện có đủ khả năng chạy độc lập trong snapshot; golden E2E báo `73 REQ`, `0 hard fails`, một advisory.
- Tái hiện đường chạy phase 2 có thể SKIP các artifact check nhưng vẫn tự ghi `completed` khi chưa có `result` thực.
- Kiểm tra trực tiếp các tài liệu công thức của valuation, fundamental, technical và news sentiment.

### 3.3 Kết quả kiểm tra cấu trúc registry

```text
requirements.yaml: 73 entries, 73 ID duy nhất
phase map:          78 lượt map, 74 giá trị duy nhất
unknown map ID:     "REQ-065 - REQ-069"
unmapped REQ:       0 (vì REQ-065 và REQ-069 còn được map lại ở phase 6)
```

Điểm quan trọng: “không có REQ bị unmapped trong hợp” không có nghĩa map đúng. Phase 3 đang parse một chuỗi sai thay vì hai ID do YAML viết hỏng.

### 3.4 Cách đọc mức độ nghiêm trọng

- **P0:** có thể tạo kết quả tài chính sai, trạng thái an toàn giả, lỗ hổng thực thi hoặc deploy trái policy.
- **P1:** làm suy yếu tính tái lập, khả năng kiểm tra hoặc tính nhất quán của pipeline; phải sửa trước qualification.
- **P2:** giới hạn chất lượng học thuật hoặc chất lượng sản phẩm; phải sửa trước khi gọi là research-grade.
- **P3:** cải thiện maintainability, tài liệu và trải nghiệm; không được ưu tiên trước P0/P1.

---

## 4. Chân dung kiến trúc hiện tại

Pipeline tự mô tả 9 phase tuần tự:

```text
Phase 0  Sponsor/API/fiscal year
   ↓
Phase 1  Data collection + provenance + period integrity
   ↓
Phase 2  Fundamental analysis
   ↓
Phase 3  Valuation
   ↓
Phase 4a Technical ACTIVE ─┐
Phase 4b Technical PROFILE ├─→ Phase 5 News → Phase 6 Dashboard → Phase 7 Verify/deploy
```

Các lớp chính:

| Lớp | Source chính | Vai trò |
|---|---|---|
| Orchestrator | `SKILL.md`, `scripts/run_phase.py` | Điều phối phase và trạng thái |
| Hợp đồng phase | `phases/*.md` | Prompt, input/output, guardrail của từng phase |
| Registry | `requirements.yaml`, `requirements-phase-map.yaml` | Danh mục kiểm soát và ánh xạ phase |
| State/evidence | `.task-state/task-state.json`, `.task-state/evidence/` | Giao tiếp giữa phase và bằng chứng |
| Verification | `scripts/independent_verifier.py` | Check artifact, data, narrative, runtime contract |
| Deploy control | `predeploy-gate.sh`, ZCode `PreToolUse` | Rerun verifier trước lệnh Vercel qua Bash |
| Research modules | `vn-*` subskills | Data, fundamental, valuation, technical, news, dashboard |

Thiết kế tách phase là hướng đúng: nó giảm context coupling và có chỗ để gắn hợp đồng. Vấn đề nằm ở việc **contract không được thực thi đồng nhất**, và verifier hiện mạnh về hình thức/nội dung artifact hơn về validity học thuật của mô hình.

---

## 5. Sổ phát hiện ưu tiên

### P0-01 — Công thức EV/EBITDA và quy đổi giá có lỗi đơn vị

**Bằng chứng:** `vn-valuation-engine/references/valuation_formulas.md` dùng:

```javascript
marketCap = price * shares_tỷ / 10
fairPrice = fairMarketCap * 10 / shares_tỷ
```

Nếu `price` là VND/cp và `shares_tỷ` là tỷ cổ phiếu, phép nhân trực tiếp đã cho kết quả **tỷ VND**. Hệ số `/10` và `*10` làm sai quy mô 10 lần.

**Tác động:** EV, EV/EBITDA, P/CF, P/S và fair price có thể sai hệ thống; đây là lỗi ảnh hưởng trực tiếp tới kết luận “rẻ/đắt”.

**Sửa bắt buộc:** tạo unit contract có kiểu/đơn vị rõ ràng, xóa các magic factor, thêm dimensional-analysis tests và golden examples bằng số nhỏ có thể tính tay.

**Acceptance criteria:** với `price_vnd=20,000`, `shares_billion=1.5`, market cap phải bằng `30,000 billion VND`; phép round-trip market cap → fair price phải trả lại đúng `20,000 VND/cp` trong sai số làm tròn đã khai báo.

### P0-02 — DCF trộn FCFF và FCFE

**Bằng chứng:** tài liệu gọi `CFO - CapEx` là FCFF, chiết khấu bằng WACC rồi trừ nợ ròng.

`CFO - CapEx` gần với dòng tiền cho cổ đông trước khi điều chỉnh vay ròng trong nhiều cách trình bày, không phải công thức FCFF chuẩn. FCFF và FCFE phải có cầu nối nhất quán:

```text
FCFF = EBIT × (1 − T) + D&A − CapEx − ΔNWC
FCFE = CFO − CapEx + Net Borrowing
```

**Tác động:** có thể double-count hoặc bỏ sót tài trợ nợ; giá trị doanh nghiệp và vốn chủ sở hữu bị trộn.

**Sửa bắt buộc:** chọn rõ FCFF hoặc FCFE cho từng ngành/doanh nghiệp; định nghĩa cầu nối enterprise value → equity value; cấm nhãn FCFF nếu input chỉ có CFO-CapEx; thêm reconciliation test.

**Acceptance criteria:** cùng một bộ giả định nhất quán, FCFF bridge và FCFE bridge phải cho equity value xấp xỉ nhau trong tolerance định trước; mọi output phải ghi dòng tiền, discount rate, terminal model và đơn vị.

### P0-03 — Runner có thể ghi phase `completed` dù chỉ SKIP kiểm tra

**Bằng chứng:** `scripts/run_phase.py` chỉ chạy REQ có method `command` ở phase 0–5; các method khác được in `SKIP`. Nếu các command còn lại không fail, hàm trả `True` và `mark_phase_completed()` vẫn chạy.

Phase 2 hiện map REQ-061/064 là artifact checks, vì vậy có thể SKIP cả hai rồi tự ghi completed dù chưa có `result` phân tích cơ bản.

**Tác động:** REQ-068 và toàn pipeline có thể dựa trên trạng thái giả; “all phases complete” không chứng minh phase đã sinh output đúng.

**Sửa bắt buộc:** trạng thái chỉ được chuyển `completed` sau khi:

1. output contract của phase validate thành công;
2. evidence cho tất cả mandatory REQ thuộc phase tồn tại;
3. mọi SKIP được phân loại `deferred` rõ ràng và không đủ quyền hoàn tất phase;
4. status transition là atomic và có reason/evidence hash.

**Acceptance criteria:** phase không có `result`, thiếu key hoặc chỉ có deferred checks phải kết thúc `blocked`/`incomplete`, tuyệt đối không `completed`.

### P0-04 — Shell injection qua TICKER/REPORT

**Bằng chứng:** cả runner và independent verifier thay `$TICKER`, `$REPORT` trực tiếp vào chuỗi command rồi gọi `subprocess.run(..., shell=True)`.

**Tác động:** input có ký tự shell có thể thực thi lệnh ngoài ý muốn; REPORT path có khoảng trắng/metacharacter cũng làm check sai.

**Sửa bắt buộc:** bỏ `shell=True`; registry command phải chuyển thành argv có schema, hoặc mỗi method gọi hàm Python cụ thể. Validate ticker bằng allowlist `^[A-Z][A-Z0-9]{1,9}$`; resolve report thành absolute path và kiểm tra nằm trong work dir cho phép.

**Acceptance criteria:** mutation inputs chứa `;`, `&&`, `$()`, backtick, newline, quote và path traversal đều bị reject trước execution; test đặt canary file phải chứng minh không có side effect.

### P0-05 — REQ-021 nói “chặn deploy”, nhưng hook mặc định cho qua

**Bằng chứng ZCode hiện hành:** hook được đăng ký ở `/Users/bobo/.zcode/cli/config.json` cho `PreToolUse` với matcher `Bash`. Tuy nhiên `/Users/bobo/.zcode/hooks/predeploy-gate.sh` mặc định `EQUITY_GATE_MODE=advisory`; khi verifier FAIL, nhánh advisory vẫn `exit 0` và in rõ “Deploy allowed”.

Các đường fail-open khác:

- không tìm thấy HTML → exit 0;
- không tìm thấy verifier → exit 0;
- chỉ bắt lệnh Bash chứa mẫu Vercel; công cụ deploy khác hoặc wrapper không khớp có thể lọt;
- comment nói kiểm hash verifier + requirements, nhưng code chỉ kiểm hash verifier;
- chọn file HTML đầu tiên theo glob, không chứng minh đó là payload thật sẽ deploy;
- không suy ra được ticker thì mặc định `MSN`, có thể verify nhầm mã.

**Tác động:** policy được mô tả là mandatory/critical nhưng enforcement thực tế là cảnh báo.

**Sửa bắt buộc:** không được lặng lẽ đổi production mode ngay. Trước hết xây test matrix cho hook, chạy shadow/advisory để đo false positive; sau owner approval mới đặt enforced. Ở enforced, mọi điều kiện mơ hồ phải fail closed, bind exact deploy directory + artifact hash + ticker + requirement/verifier hash.

**Acceptance criteria:** verifier FAIL, artifact thiếu/ambiguous, hash mismatch, ticker không xác định, deploy payload không trùng manifest hoặc hook timeout đều phải block trong enforced mode; test phải kiểm exit code thực.

### P1-01 — YAML phase map bị hỏng cú pháp ngữ nghĩa

**Bằng chứng:** phase 3 viết:

```yaml
reqs: [REQ-016, REQ-025, REQ-060, REQ-063, REQ-065
- REQ-069]
```

PyYAML parse thành một ID lạ `REQ-065 - REQ-069`.

**Sửa bắt buộc:** sửa list, thêm validator kiểm `map_ids ⊆ registry_ids`, exact ownership, duplicate policy và phase validity.

### P1-02 — Contract giữa phase prompt và REQ-068 không thống nhất

**Bằng chứng:** verifier yêu cầu:

- phase 0 `result.investment_amount` và `result.fiscal_year_type`;
- phase 2 `result.cagr`;
- phase 6 `result.artifact_path`.

Trong khi prompt phase 0 đặt `investment_amount` top-level và example thiếu `fiscal_year_type` trong result; phase 2 xuất `cagr_revenue`/`cagr_npat`; phase 6 chủ yếu yêu cầu trả raw HTML, chưa có giao thức ghi file/state rõ và tự đủ.

**Sửa bắt buộc:** định nghĩa một JSON Schema duy nhất cho task-state; phase prompt, init script, fixture, runner và verifier đều sinh/đọc từ cùng schema/version.

### P1-03 — Early command verifier bỏ qua `expect_min`/`expect_max`

Runner chỉ so exit code, trong khi một số REQ command cần kiểm giá trị output. REQ-002 yêu cầu số kỳ tối thiểu nhưng early gate không thực thi ngưỡng như independent verifier.

**Sửa bắt buộc:** dùng chung một verification engine; không duy trì hai cách diễn giải registry khác nhau.

### P1-04 — Source authority và version drift

Hiện có các mâu thuẫn:

- `SKILL.md` nói 73 REQ nhưng vẫn nói 67 evidence files;
- bảng kiến trúc nói “8 phase files” dù thực tế có 9 file;
- `VERSION` vẫn mô tả hardening 67 REQ và tự gắn `PRODUCTION_READY`;
- `phase7-deploy.md` vẫn ghi 67 REQ;
- priority summary không liệt kê đầy đủ registry mới, trong đó REQ-069 và REQ-073 bị bỏ khỏi index tổng hợp.

**Sửa bắt buộc:** sinh các con số và index từ registry, không copy tay; maturity phải là output của qualification manifest chứ không phải chuỗi tĩnh tự khai báo.

### P1-05 — Golden test xanh nhưng coverage không chạm các failure mode quan trọng

Golden E2E hiện đạt 73 REQ, 0 hard fail. Điều đó chỉ chứng minh fixture chuẩn khớp với verifier hiện tại. Nó không phát hiện:

- công thức EV/EBITDA sai nếu fixture và expected cùng dùng một công thức;
- FCFF/FCFE semantic mismatch;
- phase completed giả;
- shell injection;
- advisory hook cho deploy;
- file deploy thực tế khác file được verify;
- look-ahead, survivorship hoặc overfit ở Tech Score.

**Sửa bắt buộc:** thêm oracle độc lập, mutation tests, metamorphic tests, property-based unit tests và end-to-end negative paths.

---

## 6. Đánh giá học thuật và chất lượng nghiên cứu

### 6.1 Dữ liệu và provenance — 72/100

**Điểm mạnh:** có sponsor tier, cross-check, period/fiscal-year guard, split audit, peer provenance, cảnh báo zero-data và ý thức không bịa khi thiếu dữ liệu.

**Khoảng trống:** chưa có data dictionary đủ chặt cho từng field; chưa version toàn bộ upstream snapshot; chưa biểu diễn rõ restatement, point-in-time availability và ngày công bố so với kỳ kế toán. Nếu dùng dữ liệu sửa lại sau này để backtest quá khứ sẽ sinh look-ahead.

**Nâng cấp:** mỗi observation cần `value`, `unit`, `period_start/end`, `as_of_date`, `published_at`, `source_id`, `retrieved_at`, `restatement_status`, `fiscal_basis`, `confidence`. Tạo reconciliation giữa BCTC, cổ phiếu lưu hành và corporate actions.

### 6.2 Phân tích cơ bản/kế toán — 62/100

**Điểm mạnh:** recompute thay vì tin ratio stale; có DuPont, CAGR theo chu kỳ, cash conversion, CCC có điều kiện, DuPont 5 bước và SGR.

**Khoảng trống chính:**

- ROE/ROA dùng số dư cuối kỳ thay vì vốn chủ/tài sản bình quân;
- EPS lịch sử chưa bắt buộc weighted-average diluted shares;
- chưa tách lợi nhuận cốt lõi với one-off, fair-value gain, disposal, capitalized cost;
- chưa có accrual ratio, working-capital bridge, cash-tax và interest coverage policy đủ rõ;
- ngưỡng “ROE >15% tốt” quá chung, không điều chỉnh ngành/chu kỳ/rủi ro;
- câu “đáy ROE là điểm mua, ROE sẽ phục hồi” là suy luận quyết định quá mạnh, thiếu điều kiện bác bỏ.

**Nâng cấp:** dùng average balance; thêm normalized earnings bridge; phân tầng ngành; mọi narrative causal phải có competing explanations, falsification trigger và confidence.

### 6.3 Định giá — 44/100

Đây là khu vực yếu nhất vì có lỗi có thể làm sai trực tiếp fair value.

Ngoài P0-01/P0-02, còn các vấn đề:

- gộp mean/median/P25–P75 của nhiều phương pháp tương quan như thể là các ước lượng độc lập;
- chưa có applicability gate đủ cứng: phương pháp không phù hợp vẫn có thể đi vào median;
- WACC/beta là rule-of-thumb chưa có citation, estimation window, frequency, index, risk-free date, ERP source và shrinkage policy;
- ngân hàng/tổ chức tài chính không nên dùng corporate WACC/FCFF như doanh nghiệp công nghiệp; nên ưu tiên cost of equity, residual income/excess return hoặc DDM phù hợp;
- terminal value chưa có sanity cap so với tổng EV và chưa reconcile g với tăng trưởng kinh tế dài hạn;
- chưa theo dõi forecast error để hiệu chỉnh trọng số/confidence theo ngành.

**Nâng cấp:** valuation method registry theo ngành với `eligible`, `reason`, `inputs`, `unit_contract`, `uncertainty`, `historical_error`; aggregation theo model applicability và error history, không phải median cơ học.

### 6.4 Technical ACTIVE/PROFILE — 48/100 cho ACTIVE, 70/100 cho PROFILE

PROFILE có định hướng mô tả và guardrail tốt hơn. ACTIVE dùng Tech Score cộng các tín hiệu rời rạc nhưng chưa chứng minh giá trị dự báo.

Thiếu:

- walk-forward/out-of-sample backtest;
- transaction cost, slippage, liquidity/capacity;
- chống look-ahead và survivorship bias;
- multiple-testing correction và benchmark rõ;
- confidence interval, turnover, drawdown, regime stability;
- định nghĩa “alpha” đúng theo mô hình có intercept/risk factors; `stock_perf - beta × market_perf` không đủ để gọi là Jensen alpha.

**Nâng cấp:** mặc định ACTIVE là “descriptive signal composite — unvalidated”, không gọi là alpha hay signal có lợi thế cho đến khi qualification thực nghiệm đạt. Tách hẳn research backtest khỏi report renderer.

### 6.5 Tin tức và sentiment — 52/100

**Điểm mạnh:** có cửa sổ thời gian, link nguồn, impact, category breakdown và cố gắng nối tin với thesis.

**Khoảng trống:**

- scoring chủ quan, chưa có labeled corpus và inter-rater agreement;
- cùng một sự kiện được nhiều báo đăng có thể được thưởng điểm như nhiều bằng chứng độc lập;
- “LNST tăng” không tự động bullish nếu thấp hơn kỳ vọng hoặc chất lượng lợi nhuận kém;
- source reliability và originality chưa được mô hình hóa;
- example có score 62 nhưng verdict BULLISH, trong khi threshold tài liệu có thể xếp ≥60 vào STRONG BULLISH: contract không nhất quán;
- không có event-study/out-of-sample calibration để chứng minh score liên hệ với abnormal return hoặc forecast revision.

**Nâng cấp:** cluster theo event trước khi tính điểm; tách fact/surprise/expectation/price-reaction; hiệu chuẩn trên corpus có nhãn và báo precision/recall/calibration, không chỉ một điểm -100…+100.

### 6.6 Suy luận, uncertainty và khả năng bác bỏ — 57/100

Pipeline có nhiều guardrail dữ liệu nhưng còn dùng câu kết luận xác định. Research-grade cần phân loại claim:

| Loại claim | Yêu cầu tối thiểu |
|---|---|
| Fact | nguồn, ngày, kỳ, đơn vị, as-of |
| Derived metric | công thức, input IDs, rounding, recompute evidence |
| Estimate | model version, assumptions, range/sensitivity |
| Inference | chuỗi lý luận, competing explanation, confidence |
| Forecast | horizon, base rate, scenario probability, invalidation trigger |
| Recommendation-like statement | suitability guardrail, risk/capacity, human approval; mặc định cấm tự động |

Mỗi thesis nên có “điều gì sẽ khiến thesis sai” thay vì chỉ catalyst hỗ trợ.

### 6.7 Citation và nền tảng học thuật — 50/100

Các reference nội bộ hữu ích cho thao tác, nhưng chưa có bibliography đủ để truy ngược tới chuẩn kế toán, textbook valuation, phương pháp asset pricing, backtest protocol hoặc nghiên cứu sentiment. Cần bổ sung citation registry versioned và phân biệt:

- chuẩn/công thức được chấp nhận;
- heuristic nội bộ;
- giả định theo thị trường Việt Nam;
- kết quả thực nghiệm của chính dự án.

Không được “học thuật hóa” bằng cách thêm danh sách tài liệu mà không nối từng rule quan trọng tới nguồn hoặc test.

---

## 7. Lộ trình nâng cấp đề nghị

### Wave 0 — Đóng băng hiện trạng và thiết lập source authority

**Mục tiêu:** tránh sửa nhầm bản, mất bằng chứng hoặc tạo drift mới.

Việc cần làm:

1. đọc `/Users/bobo/.zcode/AGENTS.md` trước khi sửa;
2. tạo snapshot manifest của source ZCode: path, size, SHA-256, version, timestamp;
3. ghi rõ canonical root; thêm check từ chối chạy nếu root là `.codex`;
4. thống nhất versioning cho registry, task-state schema, verifier và methodology;
5. hạ nhãn trưởng thành xuống trạng thái trung thực như `QUALIFICATION_REQUIRED` cho đến khi hoàn tất gate — việc đổi nhãn cần owner approval nếu được coi là policy change.

**Không làm:** deploy, đồng bộ Codex, xóa archive/incident, reset worktree hoặc dùng số test lịch sử làm chứng nhận.

### Wave 1 — Correctness, security và contract integrity

Thứ tự sửa:

1. unit contract + EV/EBITDA/P-CF/P-S/fair-price conversions;
2. tách FCFF/FCFE và equity bridge;
3. thay shell command interpolation;
4. sửa phase map và validator;
5. tạo `task-state.schema.json`, đồng bộ phase prompt/init/fixture/verifier;
6. sửa state machine để SKIP/deferred không thể tạo completed;
7. hợp nhất early/final verification semantics;
8. sửa deploy gate fail-open, artifact binding và hash coverage;
9. sinh counts/index/docs từ registry.

**Gate Wave 1:** mọi P0/P1 có regression test âm; không có shell execution từ input; mọi phase transition validate schema; hook test matrix chứng minh behavior từng mode.

### Wave 2 — Nâng chuẩn phương pháp nghiên cứu

1. data dictionary và point-in-time provenance;
2. average balances, diluted weighted shares, normalized earnings, accruals;
3. sector-specific accounting/valuation registry;
4. WACC/cost-of-equity estimation protocol có ngày và nguồn;
5. valuation applicability + uncertainty + model reconciliation;
6. claim taxonomy và falsification fields;
7. citation registry/bibliography nối trực tiếp tới methodology.

**Gate Wave 2:** bộ case tính tay và case ngành (ngân hàng, thép/chu kỳ, bán lẻ, BĐS/nhà thầu) được reviewer tài chính độc lập xác nhận.

### Wave 3 — Empirical validation

1. Technical ACTIVE: walk-forward, purged time split nếu cần, cost/slippage, liquidity, benchmark, confidence interval và regime analysis.
2. Sentiment: event clustering, labeled corpus, hai người gán nhãn, agreement, calibration, event study.
3. Valuation: lưu target-as-of và so với realized/consensus outcome; theo dõi error/bias theo ngành và horizon.
4. Fundamental forecasts: backtest dự báo doanh thu/LNST/margin, không dùng dữ liệu công bố sau as-of.

**Gate Wave 3:** mọi claim về predictive value phải có out-of-sample result; nếu không đạt, đổi nhãn thành descriptive và không dùng trong verdict đầu tư.

### Wave 4 — Artifact, narrative và governance

1. đồng bộ 73 REQ và số phase ở mọi tài liệu;
2. generate documentation/index từ canonical registry;
3. hiển thị rõ as-of, data coverage, missingness, scenario assumptions và limitation;
4. tách fact/inference/estimate bằng cấu trúc machine-readable và UI;
5. accessibility, mobile, reduced motion, keyboard và runtime render tests;
6. loại internal meta khỏi narrative nhưng vẫn giữ evidence machine-readable ngoài phần độc giả.

### Wave 5 — Qualification và rollout

1. cold isolated runs trên cohort tối thiểu: ngân hàng, chứng khoán, thép chu kỳ, bán lẻ, BĐS, nhà thầu, doanh nghiệp mới/ít lịch sử;
2. negative/mutation corpus: split, restatement, non-calendar FY, missing CFO, zero data, stale peer, ticker/path độc hại, report đa file;
3. chạy hai reviewer độc lập, không đọc kết quả của nhau trước khi hoàn tất:
   - **Flash:** black-box, adversarial, end-user path, artifact/runtime/deploy bypass;
   - **Pro:** white-box, kiến trúc, phương pháp tài chính, schema/security/maintainability;
4. thêm whole-pipeline review để bắt lỗi tương tác giữa phase;
5. shadow rollout, đo false positive/negative; owner phê duyệt mới bật enforced;
6. production smoke test chỉ sau qualification, và phải bind đúng artifact hash.

---

## 8. Backlog theo file cho model thực thi

| File/nhóm file | Việc phải làm | Mức |
|---|---|---:|
| `vn-valuation-engine/references/valuation_formulas.md` | Sửa toàn bộ unit conversion; FCFF/FCFE; thêm ví dụ tính tay và dimensional checks | P0 |
| `vn-valuation-engine/SKILL.md` | Thay median cơ học bằng applicability/weighting; cấm method không phù hợp đi vào consensus | P1/P2 |
| `vn-valuation-engine/references/wacc_estimates.md` | Gắn nguồn/ngày; định nghĩa estimation protocol; tách financial institutions | P2 |
| `scripts/run_phase.py` | Bỏ `shell=True`; sửa state transition; dùng shared verifier semantics | P0 |
| `scripts/independent_verifier.py` | Bỏ command interpolation; chia module; schema validation; artifact/manifest binding | P0/P1 |
| `requirements-phase-map.yaml` | Sửa REQ-065/069; thêm map validator | P1 |
| `requirements.yaml` | Chuẩn hóa priority index; thêm methodology-critical requirements sau khi design review | P1/P2 |
| `phases/*.md` | Đồng bộ input/output với JSON Schema; thêm uncertainty/falsification | P1/P2 |
| `scripts/init_task_state.py` + fixture | Sinh state theo schema/version duy nhất | P1 |
| `vn-fundamental-analysis/*` | Average balance, diluted shares, normalization/accruals, ngành | P2 |
| `vn-technical-analysis/*` | Đổi claim ACTIVE thành unvalidated cho tới khi backtest; bổ sung empirical protocol | P2 |
| `vn-news-digest/*` | Event dedupe, surprise vs expectation, calibration, threshold consistency | P2 |
| `/Users/bobo/.zcode/hooks/predeploy-gate.sh` | Fail-closed enforced mode, exact artifact/ticker/manifest, full hash set, testable exit codes | P0 |
| `/Users/bobo/.zcode/cli/config.json` | Chỉ chỉnh nếu cần sau test và owner approval; không tự động bật enforcement | Governance |
| `SKILL.md`, `VERSION`, `phase7-deploy.md` | Xóa số đếm hardcode; maturity theo manifest; đồng bộ 73/9 | P1 |
| `scripts/tests/` | Unit oracle, mutation, state machine, injection, hook, point-in-time, multi-sector cold E2E | P0–P2 |

Khuyến nghị tách `independent_verifier.py` thành các module nhỏ theo domain nhưng giữ một CLI tương thích. Không refactor lớn trước khi khóa behavior bằng characterization tests.

---

## 9. Test matrix bắt buộc

### 9.1 Correctness/unit tests

- market cap và fair price round-trip ở nhiều scale;
- EV bridge có/không nợ ròng, minority interest, cash;
- FCFF/FCFE reconciliation;
- average ROE/ROA và weighted-average diluted EPS;
- split/restatement/corporate-action reconciliation;
- terminal value share và `g < discount rate` hard gate;
- banking method eligibility.

### 9.2 State/contract tests

- thiếu result → không completed;
- thiếu một required key → blocked;
- deferred/SKIP → không completed;
- phase chạy lại idempotent;
- concurrent/partial write không làm hỏng state;
- schema version mismatch → fail rõ ràng;
- fixture và phase prompt đều validate cùng schema.

### 9.3 Security tests

- malicious ticker/path/command tokens không tạo side effect;
- report path ngoài work dir bị chặn;
- symlink traversal bị chặn hoặc canonicalize;
- registry command không thể mở rộng shell;
- verifier timeout/error không biến thành PASS.

### 9.4 Deploy hook tests

| Tình huống | Shadow | Advisory | Enforced |
|---|---:|---:|---:|
| Verifier PASS, exact artifact | allow + log | allow + log | allow + signed evidence |
| Verifier FAIL | allow + log | allow + warning | **block** |
| Artifact thiếu/ambiguous | log | warning | **block** |
| Ticker không xác định | log | warning | **block** |
| Verifier/requirements/schema hash mismatch | log | warning | **block** |
| Deploy directory khác manifest | log | warning | **block** |
| Timeout/exception | log | warning | **block** |

### 9.5 Empirical tests

- Technical walk-forward theo thời gian, không random split;
- báo gross và net performance sau chi phí;
- bootstrap/confidence interval và benchmark;
- sentiment inter-rater agreement và calibration curve;
- event deduplication trước scoring;
- valuation forecast errors theo ngành/horizon;
- point-in-time audit: input nào cũng phải có `available_at <= as_of`.

### 9.6 Artifact/runtime tests

- browser render thật, không chỉ regex HTML;
- chart instances/data shape/nonzero logic;
- console error/unhandled rejection;
- desktop/mobile/reduced-motion/keyboard;
- nguồn/citation mở được hoặc được đánh dấu unavailable;
- production payload hash đúng manifest đã verify.

---

## 10. Definition of Done

Chỉ được đề nghị nâng mức trưởng thành khi **tất cả** điều kiện sau đạt:

- [ ] Canonical target được khóa là `.zcode`, không file Codex nào bị sửa.
- [ ] P0-01 đến P0-05 có fix và regression tests âm.
- [ ] Registry 73/73 unique; phase map không unknown, không duplicate ngoài policy, không unmapped.
- [ ] Mọi phase output validate bằng một versioned JSON Schema.
- [ ] Không còn `shell=True` với dữ liệu do user/artifact kiểm soát.
- [ ] SKIP/deferred không thể tạo trạng thái completed.
- [ ] Unit tests độc lập xác nhận valuation conversions và FCFF/FCFE bridge.
- [ ] Fundamental methods dùng average balances/weighted shares hoặc ghi lý do không khả dụng.
- [ ] Method eligibility theo ngành được thực thi, không chỉ mô tả.
- [ ] Tech ACTIVE không mang claim predictive nếu chưa đạt out-of-sample gate.
- [ ] Sentiment đã event-dedupe và threshold/verdict nhất quán.
- [ ] Hook enforced fail-closed đã được kiểm thử, nhưng chỉ bật sau owner approval.
- [ ] Cold cohort và mutation suite chạy sạch trong môi trường tách biệt.
- [ ] Flash và Pro hoàn tất review độc lập; whole-pipeline review không còn blocker.
- [ ] Báo cáo cuối ghi exact commands, exit codes, hashes, artifacts và unresolved risks.
- [ ] Không dùng “73/73 PASS” như bằng chứng duy nhất cho `PRODUCTION_READY`.

---

## 11. Yêu cầu đầu ra cho model nâng cấp

Model tiếp quản phải tạo các artifact sau, ưu tiên machine-readable:

1. `UPGRADE-PLAN.md`: scope, assumptions, dependency graph, risk order.
2. `baseline-manifest.json`: hashes và versions trước sửa.
3. `methodology-spec.md`: unit contracts, accounting/valuation/technical/sentiment protocols và citations.
4. `task-state.schema.json`: canonical state contract.
5. `requirements-lint.py` hoặc tương đương: registry/map/priority/version checks.
6. code + tests cho từng P0/P1, mỗi fix gắn ID phát hiện.
7. `qualification-manifest.json`: commands, exit codes, environment, hashes, cohort outcomes.
8. hai prompt review độc lập Flash/Pro và hai báo cáo không chia sẻ trước.
9. `CLOSEOUT.md`: supported/prohibited uses, residual risk, recommendation và owner decisions còn chờ.

Tên file có thể điều chỉnh theo convention hiện có, nhưng nội dung và traceability không được mất.

---

## 12. Prompt nguyên khối để giao cho model ZCode tiếp theo

Sao chép nguyên khối dưới đây vào task nâng cấp:

```text
BẠN ĐANG NÂNG CẤP SKILL equity-research-vn TRÊN ZCODE.

CANONICAL SOURCE DUY NHẤT:
/Users/bobo/.zcode/skills/equity-research-vn

HOOK/CẤU HÌNH LIÊN QUAN:
/Users/bobo/.zcode/hooks/predeploy-gate.sh
/Users/bobo/.zcode/cli/config.json

TUYỆT ĐỐI KHÔNG:
- sửa, đồng bộ hoặc lấy /Users/bobo/.codex/skills/equity-research-vn làm target;
- deploy production;
- bật enforced mode hoặc đổi policy cấu hình mà chưa có test matrix và owner approval;
- xóa incident/archive/evidence hoặc reset worktree;
- tuyên bố PRODUCTION_READY chỉ vì verifier/golden fixture PASS;
- tối ưu số REQ trước khi sửa correctness và methodology.

TRƯỚC KHI SỬA:
1. Đọc /Users/bobo/.zcode/AGENTS.md.
2. Đọc toàn bộ báo cáo:
   /Users/bobo/ZCodeProject/BAO-CAO-DA-GOC-NANG-CAP-EQUITY-RESEARCH-VN-ZCODE.md
3. Chụp baseline manifest gồm path, size, SHA-256, version và timestamp.
4. Kiểm tra lại hiện trạng vì source có thể đã thay đổi; phân loại mỗi phát hiện là CONFIRMED, CHANGED hoặc NOT REPRODUCED.
5. Lập plan theo Wave 0→5; ưu tiên P0/P1.

MỤC TIÊU WAVE 1 BẮT BUỘC:
- sửa lỗi đơn vị market cap/fair price và toàn bộ dependent formulas;
- tách đúng FCFF/FCFE, discount rate và EV→equity bridge;
- loại shell=True/interpolation với TICKER/REPORT;
- sửa requirements-phase-map và thêm registry linter;
- tạo một task-state JSON Schema, đồng bộ phase prompts/init/fixture/verifier;
- không cho SKIP/deferred tạo completed;
- dùng cùng verification semantics cho early/final checks;
- sửa deploy gate theo fail-closed design, exact artifact/manifest/hash binding;
- đồng bộ 73 REQ, 9 phase và maturity text bằng generated metadata.

MỤC TIÊU NGHIÊN CỨU:
- average balances, diluted weighted shares, normalized earnings/accruals;
- sector-specific method applicability;
- WACC/cost-of-equity protocol có nguồn/ngày;
- valuation uncertainty và forecast-error tracking;
- Tech ACTIVE phải được gọi là unvalidated/descriptive cho đến khi walk-forward OOS đạt;
- sentiment phải event-dedupe, tách surprise so với expectation và được hiệu chuẩn;
- mọi claim phải phân loại fact/derived/estimate/inference/forecast và có invalidation trigger phù hợp.

CÁCH LÀM:
- Khóa behavior cũ bằng characterization tests trước refactor lớn.
- Mỗi fix phải có test có khả năng FAIL trên bản cũ và PASS trên bản mới.
- Dùng oracle tính tay/độc lập; không để fixture và expected cùng sinh từ một công thức.
- Ghi exact command, exit code, hash và artifact.
- Bảo toàn mọi WIP không liên quan.
- Khi gặp quyết định policy hoặc có thể ảnh hưởng production, dừng và xin owner xác nhận.

QUALIFICATION:
- cold runs đa ngành;
- negative/mutation/security tests;
- browser/runtime artifact tests;
- Flash black-box/adversarial và Pro white-box/architecture chạy độc lập, không đọc kết quả nhau trước khi hoàn tất;
- thêm whole-pipeline review;
- báo residual risks và supported/prohibited uses.

ĐẦU RA CUỐI:
- diff theo finding ID;
- test/qualification manifest;
- hai báo cáo review độc lập;
- closeout trung thực;
- đề nghị maturity, không tự kích hoạt production.
```

---

## 13. Kết luận cuối cho người tiếp quản

`equity-research-vn` trên ZCode đã vượt xa một prompt đơn giản: nó có kiến trúc phase, registry, evidence và verifier đáng kể. Điểm yếu cốt lõi không phải thiếu thêm check giao diện, mà là **một số nền tảng phương pháp và enforcement chưa đúng với lời tuyên bố của hệ thống**.

Thứ tự đúng là:

```text
Đúng công thức và đơn vị
→ đúng contract và state transition
→ an toàn thực thi và deploy
→ chuẩn hóa phương pháp nghiên cứu
→ validation ngoài mẫu
→ review độc lập toàn pipeline
→ owner quyết định maturity/activation
```

Nếu model tiếp quản chỉ sửa các con số 67→73, thêm REQ hoặc làm golden fixture xanh, dự án gần như không tăng chất lượng thực. Nếu hoàn tất các wave với bằng chứng bác bỏ đủ mạnh, mức cải thiện thực tế có thể đạt khoảng **+26 đến +30 điểm**, đưa skill từ bản nháp nghiên cứu có kiểm soát lên vùng **88–92/100**. Vẫn cần duy trì giới hạn: đây là công cụ hỗ trợ nghiên cứu, không phải hệ thống tự chịu trách nhiệm cho quyết định đầu tư.
