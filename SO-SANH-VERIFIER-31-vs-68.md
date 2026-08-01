# So sánh hiệu quả verifier cũ (31 REQ) vs mới (68 REQ) — V4 Flash

> Ngày đo: 2026-08-01 · Báo cáo độc lập, mọi con số có output chạy thật kèm theo.
> KHÔNG sửa code — chỉ chạy, đo, báo cáo.

## 0. Cách đo (setup)

| Mục | Chi tiết |
|---|---|
| Verifier CŨ | `/tmp/verifier_old.py` — trích từ git commit `8ca86fe5f` (`scripts/independent_verifier.py`, 1412 dòng) + `requirements.yaml` 31 REQ |
| Verifier MỚI | `/tmp/newskill/independent_verifier.py` — bản tĩnh copy từ skill hiện tại (4160 dòng, 68 REQ) |
| Report thử nghiệm | `/Users/bobo/ZCodeProject/ctd_deploy/index.html` — report CTD đã deploy (1254 dòng, template CŨ) |
| Work dir | `/tmp/ctd_old_run/` — report + `data/` + `.task-state/` + `news_digest.json` + `company_profile.json` + `source-pack/` |

**3 ghi chú trung thực về cách đo:**

1. **Dùng bản sao tĩnh, không dùng file gốc.** Trong lúc đo, `requirements.yaml` ở skill bị một session khác sửa giữa chừng (mtime 11:23 → 11:48) → cùng 1 lệnh chạy lúc thì ra 31 REQ, lúc ra 68 REQ (kết quả như "tung xúc xắc"). Tôi cô lập bằng bản copy tĩnh rồi mới đo; mọi con số dưới đây đều chạy trên bản tĩnh, ổn định qua ≥2 lần lặp.
2. **REQ-062 ban đầu FAIL là lỗi setup của tôi**, không phải của verifier: tôi quên copy thư mục `source-pack/` (CSV nguồn) sang work dir. Copy xong → PASS. Không tính vào số liệu.
3. **REQ-050 là loại "advisory"** (khuyên bảo, không chặn deploy) → in dòng `⚠️ ADVISORY` chứ không PASS/FAIL. Vì vậy 68 REQ = 35 PASS + 32 FAIL + 1 ADVISORY. Không có REQ nào "mất tích".

---

## 1. Lớp A — Chạy trên report CTD thật (đã deploy, bản cũ)

### 1.1 Kết quả

| Verifier | PASS | FAIL | ADVISORY | Tổng REQ |
|---|---|---|---|---|
| CŨ (31 REQ) | 16 | 15 | 0 | 31 |
| MỚI (68 REQ) | 35 | 32 | 1 | 68 |

Output chạy thật (verifier MỚI, bản sạch):

```
✅ PASS = 35  ❌ FAIL = 32  (REQ-021: "32 requirement(s) failed — BLOCKED deploy")
REQ-050: ⚠️ ADVISORY (1 issue)
```

Output chạy thật (verifier CŨ, bản sạch): `✅ PASS = 16 · ❌ FAIL = 15`.

### 1.2 Verifier mới phát hiện thêm 17 REQ mà verifier cũ hoàn toàn không có

FAIL set của MỚI = FAIL set của CŨ (15 REQ, không mất REQ nào = **0 regression**) **cộng thêm đúng 17 REQ**:

REQ-007, 034, 036, 037, 038, 040, 042, 045, 047, 048, 049, 054, 057, 060, 061, 063, 064

Bằng chứng cụ thể (trích evidence trong output của verifier MỚI):

| REQ | Nội dung bắt được trên report cũ | Evidence trích từ output |
|---|---|---|
| REQ-060 | Số trong report tự mâu thuẫn nhau | `P/E 10.4× × EPS 7736.0 = 80,454 ≠ giá 71700.0 (lệch >5%)` |
| REQ-061 | ROE/ROA/vốn hóa không khớp tính lại | `ROE claim 0.26% ≠ recompute 8.3% (năm 2025)`; `vốn hóa claim 8,107.2 ≈ 8 tỷ ≠ price×shares 8,018 tỷ` |
| REQ-036 | CAGR không tính lại được từ data | `cagr_claims_found: 4` — claim CAGR không khớp recompute từ `financials.json` |
| REQ-054 | Chuỗi nhân quả không có bằng chứng | `causal_claims_found: 6, unverified: 3` |
| REQ-038 | Claim "đứng đầu/số 1" không có số liệu hỗ trợ | `claim 'Top 1' không có số liệu/nguồn hỗ trợ trong ±200 chars` |
| REQ-045 | Số dự kiến/tương lai không nguồn | `forecast_claims_with_numbers: 8, uncited: 7, max_tolerated: 2` |
| REQ-042 | Số vốn đầu tư không xuất hiện trong báo cáo | `investment_amount=800,000,000` không có trong narrative |
| REQ-031 | Claim drawdown không có data thật | `drawdown_claims_found: 1` — không dựa trên dữ liệu |
| REQ-040/047/048/049/057/063/064/007/034/037 | định danh, vĩ mô, quản trị, lợi suất lịch sử, cổ tức, phương pháp định giá, trend, PROFILE, năm-kỳ | lần lượt FAIL trên report cũ |

Điểm quan trọng: **report cũ vốn dĩ đã chứa nhiều sai lệch mà verifier cũ không hề check** — ví dụ CAGR LNST ghi 13.3% trong khi tính lại từ data là **138.6%** (lệch 125 điểm phần trăm). Verifier cũ không có REQ-036 nên không bao giờ thấy.

---

## 2. Lớp B — Mutation test: bịa 10 lỗi vào report cũ, chạy cả 2 verifier

### 2.1 Bảng kết quả chính thức

| # | Lỗi bịa vào report | Verifier CŨ | Verifier MỚI | Chênh |
|---|---|---|---|---|
| M1 | Doanh thu 2025: 30,699 → 25,000 (sửa cả text lẫn JS chart) *(control)* | ✅ BẮT | ✅ BẮT | = |
| M2 | Doanh thu 2021: 9,078 → 8,000 (chỉ sửa text) *(control)* | ❌ LỌT | ❌ LỌT | = |
| M3 | Vẽ khống 1 chuỗi JS `max_drawdown = -28.5` + claim "giá sụt giảm 50%" | ❌ LỌT (**bị lừa**) | ✅ BẮT | **+1** |
| M4 | Upside vs fair value: 13.3% → 50% | ❌ LỌT | ❌ LỌT | = |
| M5 | Thêm câu nhân quả "LNST tăng 50% **nhờ** quản trị tốt hơn" (không bằng chứng) | ❌ LỌT | ✅ BẮT | **+1** |
| M6 | Giá để nguyên 71,700 nhưng ghi `price_fetched_at` 47 ngày trước | ❌ LỌT (**bị lừa**) | ✅ BẮT | **+1** |
| M7 | Đổi URL 3 bài tin tức sang domain `.xyz` giả | ❌ LỌT | ✅ BẮT | **+1** |
| M8 | Sửa task-state: phase 2 (fundamental) → `pending` (bỏ bước) | ❌ LỌT | ✅ BẮT | **+1** |
| M9 | KPI "ROE (2025)" 8.65% → 24% | ❌ LỌT | ❌ LỌT | = |
| M10 | Chèn claim peer "HBC P/E 25x (peer)" (data thật 15.2) | ❌ LỌT | ❌ LỌT | = |
| **Tổng** | | **1/10** | **6/10** | **+5** |

### 2.2 Bằng chứng chạy thật cho từng trường hợp chênh

**M3 — verifier CŨ bị LỪA (còn tệ hơn lọt):** FAIL của CŨ giảm 15 → **14** trên bản bịa. REQ-031 (drawdown) baseline FAIL, sau khi chèn chuỗi giả thì **PASS**. Root cause trong code CŨ (`/tmp/verifier_old.py:1084`): check chỉ cần HTML **có chứa chuỗi** `max_drawdown|drawdownData|maxDrawdown` là PASS — không đọc giá trị, không xem nguồn. Verifier MỚI thì ngược lại: chỉ tin narrative + `verified-dashboard-data.json`, claims phát hiện tăng 1 → 2 (claim bịa lọt vào danh sách) → FAIL.

**M6 — verifier CŨ bị LỪA lần nữa:** FAIL 15 → 14, REQ-028 (chart render-readiness) baseline FAIL → PASS vì script bịa `const DATA = {...}` thỏa mãn check. Đồng thời vẫn KHÔNG bắt được giá cũ. Verifier MỚI: REQ-030 (price freshness) PASS → FAIL, evidence: `{"price_value": 71700, "has_price_fetched_at": true, ..., "freshness": {"sources_checked": ...}}` — tuổi data > 7 ngày → FAIL.

**M5:** REQ-054 (causal chain) — `causal_claims_found: 6 → 7`, `unverified: 3 → 4` — câu bịa bị đếm vào nhóm "không có bằng chứng" → FAIL.

**M7:** REQ-044 (news authenticity) PASS → FAIL — `total_articles: 3`, domain `.xyz` nằm ngoài whitelist → `fake_unreachable > 0` → FAIL.

**M8:** REQ-068 (phase completion) PASS → FAIL — task-state sau khi sửa: `{'phase0_sponsor': 'completed', 'phase1_data': 'completed', 'phase2_fundamental': 'pending', ...}` → FAIL.

**M1 (control):** cả 2 cùng bắt — REQ-022: `revenue_ty[2025]: ground_truth=30,699.1 not found (DATA-array miss + context-anchored failed)`. Cùng nội dung, cả 2 verifier (G-series đã backport về bản cũ).

### 2.3 Điều chỉnh trung thực so với lần đo đầu tiên

Lần chạy đầu tôi báo **MỚI 8/10**. Sau khi soi từng bằng chứng chi tiết, **2 trong số đó là artifact của cách đo**, con số chính xác là **6/10**:

- **M4 không phải "CAGR bịa" như tôi tưởng.** Số "13.3%" đầu tiên trong file là label **"Upside vs fair value"** (không phải CAGR LNST). Verifier MỚI FAIL set giống hệt baseline, chữ "50%" không xuất hiện trong output → mutation này **không được phát hiện**. REQ-036 FAIL baseline là do các claim CAGR khác (REQ-036 vốn không check "upside %"). REQ-065 (tone) tính upside từ **target price** chứ không validate claim upside % → gap thật còn sót.
- **M9 không phải "ROE bịa bị bắt".** KPI sau khi sửa: `ROE (2025) ... >24<span>%</span>` (đã verify trong file). Nhưng REQ-061 FAIL baseline và FAIL M9 với **cùng** 2 lỗi cũ (`ROE claim 0.26% ≠ recompute 8.3%`, vốn hóa lệch) — chữ "24" không được nhắc tới. Root cause: pattern ROE tại `independent_verifier.py:3623` là `\bROE\b[^.\d]{0,30}?(\d[\d.,]*)\s*%` — **không thể vượt qua "(2025)"** vì `[^.\d]` loại chữ số, nên "ROE (2025) 24%" vô hình với check. REQ-033 (cross-section) cũng không thấy vì nó chỉ quét các `<section id="sec-...">` (report cũ không có section nào).

Tức là: bảng 2.1 là con số **sau hiệu chỉnh** — MỚI 6/10, không phải 8/10.

### 2.4 4 trường hợp cùng LỌT — phân loại

| Mutation | Nguyên nhân gốc | Mức độ |
|---|---|---|
| M2 (sửa text 1 con số lịch sử) | Report cũ **nhúng số thật vào JS chart arrays** — sửa text mà không sửa JS thì REQ-022 vẫn thấy số khớp. Đặc thù thiết kế report cũ; trên pipeline mới, REQ-026 (chart DATA = data files) + REQ-060 (cross-footing) làm giảm rủi ro. | Gap thiết kế, cần chấp nhận |
| M4 (upside % bịa) | Không REQ nào validate "Upside vs fair value %" = median(targets)/price − 1. | Gap thật, vá được |
| M9 (KPI ROE bịa) | Regex REQ-061 không vượt được "(2025)" giữa chừng; REQ-033 chỉ quét section của template mới. | Gap thật, vá được (1 dòng regex) |
| M10 (peer claim bịa) | REQ-032 (`verify_peer_provenance`, line 1514) chỉ quét section `sec-peer` — report cũ không có section → PASS vô điều kiện (`no sec-peer section — nothing to check`). | Gap phụ thuộc format; trên template mới section luôn tồn tại nên sẽ kích hoạt |

---

## 3. Kết luận

1. **6 đợt hardening tạo ra sự khác biệt đo được, theo 2 lớp:**
   - **Lớp A (report thật):** verifier mới phát hiện thêm **17 REQ-fail** mà verifier cũ không có khả năng phát hiện (16 PASS/15 FAIL → 35 PASS/32 FAIL), **0 regression** (không REQ nào từ PASS thành FAIL mới — mọi FAIL cũ vẫn FAIL).
   - **Lớp B (bịa 10 lỗi):** **1/10 → 6/10** (chênh +5). Nghiêm trọng hơn: trên 2 mutation (M3, M6) verifier cũ **bị lừa thành PASS** (FAIL giảm 15→14) — tức không chỉ lọt mà còn bị kẻ bịa "dắt mũi" — trong khi verifier mới vẫn FAIL. Đây là bằng chứng trực tiếp cho các fix FIX-3a (drawdown), P2 (giá cũ) và REQ-068/044/054.

2. **Nói thẳng: chênh là +5/10, không phải 8/10.** 2 con số đầu tôi báo nhầm do probe dính vào các REQ vốn đã FAIL sẵn vì lý do khác (M4, M9). Cũng có 2 lỗi (M2, M10) mà **cả 2 verifier đều không bắt được** — M2 do đặc thù report cũ nhúng số thật vào JS, M10 do REQ-032 chỉ kích hoạt khi report có section peer (template mới thì có).

3. **Độ mạnh thêm là thật, nhưng không phải 100%.** Verifier mới bắt được các lớp lỗi cốt lõi (số liệu, CAGR, causal, giá cũ, tin giả, bỏ phase, định danh, vốn hóa…) nhưng còn 3 gap vá được dễ dàng nếu muốn harden tiếp:
   - REQ-061: sửa pattern ROE cho phép năm "(20xx)" giữa keyword và số → bắt được KPI ROE.
   - REQ-032: khi không có `sec-peer`, fallback quét peer claims ở toàn bộ narrative.
   - REQ mới (hoặc mở rộng REQ-065): validate claim "Upside vs fair value %" với recompute từ target price.

4. **Khuyến nghị:** nếu mục tiêu là "verifier mạnh hơn bao nhiêu" → câu trả lời ngắn gọn: **trên report thật: +17 phát hiện, 0 regression; trên 10 lỗi bịa: 1/10 → 6/10 (chênh +5), và verifier cũ có thể bị dắt mũi thành PASS trong khi verifier mới không**. Hardening đã đáng giá; phần còn lại là 3 vá nhỏ ở mục 3.
