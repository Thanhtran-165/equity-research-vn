// src/data/dejavu_scores.mjs
// Déjà Vu Score — redesigned per P0.1 review.
// Three INDEPENDENT indices instead of one conflated score:
//   - similarity: 0-5, how alike the two periods are (low = different)
//   - break: 0-5, how severely the differences break the analogy (high = analogy fails)
//   - importance: 0-5, how important this variable is for the current regime (high = watch closely)
// Old single score conflated "alike", "different", "important". These three are orthogonal.
//
// The OLD verdict label is replaced by a 2D position on (similarity, break).

export const DEJAVU_DIMENSIONS = [
  {
    id: "geopolitics",
    label: { vi: "Địa chính trị & Trung Đông", en: "Geopolitics & Middle East" },
    similarity: 3, break: 3, importance: 4,
    data_points: ["oil_brent", "oil_wti", "oil_wti_long"],
    rubric: {
      vi: "Cả hai giai đoạn: xung đột ME lớn (Yom Kippur 1973 / Gaza 2023–24, Biển Đỏ, Iran). Hiện tượng tương tự; cấu trúc truyền dẫn yếu hơn (Mỹ sản xuất ròng, SPR, LNG, OPEC+).",
      en: "Both periods: major ME conflict (1973 Yom Kippur / 2023–24 Gaza, Red Sea, Iran). Phenomenon similar; transmission structure weaker (US net producer, SPR, LNG, OPEC+).",
    },
    reasoning: {
      vi: "Trùng lặp xung đột bề mặt (similarity=3). Truyền dẫn cú sốc giảm — embargo→suy thoái không còn tự động. Phản ứng giá chủ yếu là geopolitical-risk premium, không phải thiếu hụt vật lý.",
      en: "Surface conflict overlap (similarity=3). Shock transmission reduced — embargo→recession no longer automatic. Price reaction mostly geopolitical-risk premium, not physical shortage.",
    },
    counterargument: {
      vi: "Phong tỏa Hormuz vẫn có thể tạo thiếu hụt vật lý bất kể sản lượng Mỹ — dầu toàn cầu có thể thay thế, khám phá giá toàn cầu.",
      en: "A Hormuz closure could still create a physical shortage regardless of US production — global oil is fungible, price discovery is global.",
    },
    confidence: "Medium",
  },
  {
    id: "oil",
    label: { vi: "Dầu & hệ năng lượng", en: "Oil & energy system" },
    similarity: 2, break: 4, importance: 4,
    data_points: ["oil_brent", "oil_wti", "oil_wti_long", "natgas_hh"],
    rubric: {
      vi: "1970s dầu là điểm nghẽn; giờ là điện. Cường độ dầu/GDP giảm ~60% từ 1970. Mỹ sản xuất 13+ mb/d (vs 8 mb/d 1970).",
      en: "1970s oil was the binding bottleneck; today electricity is. Oil intensity of GDP down ~60% since 1970. US produces 13+ mb/d (vs 8 mb/d in 1970).",
    },
    reasoning: {
      vi: "Dầu không còn hàng hóa hệ thống duy nhất (similarity=2). Phá vỡ analogy mạnh (break=4) vì cơ chế đã thay đổi. Vẫn quan trọng (importance=4) như kênh lạm phát.",
      en: "Oil is no longer the single systemic commodity (similarity=2). Analogy break is strong (break=4) because the mechanism changed. Still important (importance=4) as an inflation channel.",
    },
    counterargument: {
      vi: "Diesel, petrochem và nông nghiệp vẫn phụ thuộc dầu; chế độ $100+ kéo dài với cầu yếu vẫn nén biên.",
      en: "Diesel, petrochem, agriculture still depend on oil; sustained $100+ regime with weak demand still compresses margins.",
    },
    confidence: "High",
  },
  {
    id: "commodities",
    label: { vi: "Hàng hóa (rộng)", en: "Commodities (broad)" },
    similarity: 4, break: 3, importance: 4,
    data_points: ["broad_commodity", "copper", "uranium"],
    rubric: {
      vi: "Pink Sheet broad commodity index thực tăng 2021–22 tương tự 1973–74 và 1979. Resource nationalism, capex thấp 2015–20, phân mảnh thương mại địa chính trị.",
      en: "Pink Sheet broad commodity index real surge 2021–22 similar to 1973–74 and 1979. Resource nationalism, low capex 2015–20, geopolitical trade fragmentation.",
    },
    reasoning: {
      vi: "Hiện tượng và cơ chế đều tương tự (similarity=4). Chu kỳ nay đa dạng hơn (đồng, uranium, lithium cho điện khí hóa/AI) vs tập trung dầu 1970s.",
      en: "Phenomenon and mechanism both similar (similarity=4). Today's cycle more diversified (copper, uranium, lithium for electrification/AI) vs oil-centric 1970s.",
    },
    counterargument: {
      vi: "Suy yếu bất động sản Trung Quốc + dư cung nickel HPAL Indonesia chặn tăng kim loại công nghiệp.",
      en: "China property slowdown + Indonesia nickel HPAL oversupply cap industrial-metals upside.",
    },
    confidence: "Medium",
  },
  {
    id: "inflation",
    label: { vi: "Lạm phát", en: "Inflation" },
    similarity: 3, break: 4, importance: 4,
    data_points: ["cpi", "core_cpi", "pce", "core_pce"],
    rubric: {
      vi: "CPI headline Mỹ đỉnh ~9% 2022 — tương đương 1973–74 (12%) nhưng thấp hơn nhiều 1979–80 (14%). Lạm phát core dính hơn dự kiến. Nhưng bộ khuếch đại 1970s (wage indexation, công đoàn, kỳ vọng de-anchor) vắng.",
      en: "US headline CPI peaked ~9% in 2022 — comparable to 1973–74 (12%) but well below 1979–80 (14%). Core stickier than expected. But 1970s amplifiers (wage indexation, unions, expectation de-anchoring) are absent.",
    },
    reasoning: {
      vi: "Hiện tượng tương tự (similarity=3) nhưng cơ chế dai dẳng phá vỡ analogy (break=4). Kết quả đến nay: lạm phát hạ không suy thoái — phân kỳ khỏi 1979–82.",
      en: "Phenomenon similar (similarity=3) but persistence mechanism breaks the analogy (break=4). Outcome so far: inflation fell without recession — diverges from 1979–82.",
    },
    counterargument: {
      vi: "Quán tính shelter, thâm hụt tài khóa và thắt chặt di trú vẫn giữ core dính; sóng thứ hai không loại trừ nếu cú sốc hàng hóa lặp lại.",
      en: "Shelter inertia, fiscal deficits, immigration tightening keep core sticky; a second wave cannot be ruled out if commodity shocks recur.",
    },
    confidence: "High",
  },
  {
    id: "monetary",
    label: { vi: "Chính sách tiền tệ & uy tín", en: "Monetary policy & credibility" },
    similarity: 3, break: 4, importance: 4,
    data_points: ["fedfunds", "term_premium"],
    rubric: {
      vi: "Fed tăng 525 bp 2022–23 (tích lũy tương tự Volcker). Đỉnh 5.5% vs ~20% Volcker. Kết quả: lạm phát hạ không suy thoái — TỐT HƠN 1979–82. Uy tín Fed cao hơn (không stop-go Burns).",
      en: "Fed hiked 525 bp 2022–23 (cumulative similar to Volcker). Peak 5.5% vs ~20% Volcker. Outcome: inflation fell without recession — BETTER than 1979–82. Fed credibility higher (no Burns stop-go).",
    },
    reasoning: {
      vi: "Phenomenon tương tự (similarity=3) — cùng thắt chặt chống cú sốc. Phá vỡ (break=4) vì outcome khác (không suy thoái, không cần Volcker-shock). Tùy chọn Volcker-tương đương đã đóng bởi nợ (xem dimension 'debt').",
      en: "Phenomenon similar (similarity=3) — same anti-shock tightening. Break (break=4) because outcome differs (no recession, no Volcker-shock needed). The Volcker-equivalent option is closed by debt (see 'debt' dimension).",
    },
    counterargument: {
      vi: "Nợ/GDP cao hơn nghĩa là khả năng chịu lãi suất của nền kinh tế thấp hơn; 'higher-for-longer' mà Volcker duy trì được có thể vỡ gì đó hôm nay.",
      en: "Higher debt/GDP means the economy's interest-rate tolerance is lower; a 'higher-for-longer' that Volcker could sustain might break something today.",
    },
    confidence: "Medium",
  },
  {
    id: "fiscal",
    label: { vi: "Thái độ tài khóa & thâm hụt", en: "Fiscal stance & deficit" },
    similarity: 4, break: 3, importance: 5,
    data_points: ["deficit", "federal_debt_total", "interest_expense"],
    rubric: {
      vi: "Thâm hụt ~6% GDP 2023–24 với thất nghiệp ~4% — cấu trúc bất thường (thường xuất hiện trong suy thoái). Thâm hụt 1970s nhỏ hơn theo chu kỳ.",
      en: "Deficit ~6% GDP in 2023–24 with unemployment ~4% — structurally unusual (normally appears in recession). 1970s deficits were smaller relative to cycle.",
    },
    reasoning: {
      vi: "Thái độ tài khóa mở rộng mạnh (similarity=4). Phá vỡ một phần (break=3) vì cơ chế fiscal dominance chưa tất yếu. Quan trọng (importance=5) — rủi ro trung tâm cho chế độ hiện tại.",
      en: "Strong expansionary fiscal stance (similarity=4). Partial break (break=3) because fiscal dominance mechanism is not yet inevitable. Important (importance=5) — central risk for the current regime.",
    },
    counterargument: {
      vi: "Status dự trữ + độ sâu TIPs + thiếu dollar vẫn hấp thụ Treasury; 'fiscal dominance' là rủi ro, chưa phải sự thật.",
      en: "Reserve-currency status + TIPs depth + dollar shortage still absorb Treasuries; 'fiscal dominance' is a risk, not yet a fact.",
    },
    confidence: "Medium",
  },
  {
    id: "debt",
    label: { vi: "Gánh nặng nợ công & tư", en: "Public & private debt overhang" },
    similarity: 1, break: 5, importance: 5,
    data_points: ["federal_debt_total", "household_debt", "corporate_debt", "mortgage_30y"],
    rubric: {
      vi: "Nợ liên bang/GDP ~120%+ vs ~30% năm 1980. Hộ gia đình, doanh nghiệp, chính phủ đều cao hơn. Đây là đứt gãy cấu trúc lớn nhất TỪ 1970s — periods KHÔNG giống nhau.",
      en: "Federal debt/GDP ~120%+ vs ~30% in 1980. Household, corporate, sovereign all higher. This is the biggest structural break FROM 1970s — the periods are NOT alike.",
    },
    reasoning: {
      vi: "Hai thời kỳ KHÔNG giống (similarity=1). Phá vỡ analogy cực mạnh (break=5) — Volcker có thể 20% với nợ 30%; cùng nước đi tại 120% không thể chịu nổi về tài khóa. Quan trọng (importance=5) — biến số trung tâm.",
      en: "The two periods are NOT alike (similarity=1). Analogy break is extreme (break=5) — Volcker could go 20% with debt at 30%; same move at 120% is fiscally intolerable. Important (importance=5) — central variable.",
    },
    counterargument: {
      vi: "Quản trị duration (phát hành Treasury dài 2020) + mortgage cố định bảo vệ dòng tiền ngắn hạn; private credit dai dẳng hơn bề ngoài.",
      en: "Duration management (long Treasury issuance in 2020) + fixed-rate mortgages insulate short-term cash flows; private credit more resilient than it looks.",
    },
    confidence: "High",
  },
  {
    id: "japan",
    label: { vi: "Nhật Bản / yen", en: "Japan / yen carry" },
    similarity: 3, break: 3, importance: 3,
    data_points: ["usd_jpy", "boj_rate", "jgb10y"],
    rubric: {
      vi: "BOJ bình thường hóa + USD/JPY > 150 vang vọng động thái Plaza cuối-1980 theo chiều ngược (yen yếu nay, mạnh khi đó). YCC exit Aug 2024.",
      en: "BOJ normalization + USD/JPY > 150 echoes late-1980s Plaza dynamics in reverse (yen weak today, strong then). YCC exit Aug 2024.",
    },
    reasoning: {
      vi: "Cơ chế carry-unwind mạnh (similarity=3). Phá vỡ một phần (break=3) — Plaza là phối hợp G5, 2024 đơn phương. Quan trọng vừa (importance=3) — amplifier, chưa driver độc lập.",
      en: "Carry-unwind mechanism strong (similarity=3). Partial break (break=3) — Plaza was G5 coordinated, 2024 is unilateral. Moderately important (importance=3) — amplifier, not yet independent driver.",
    },
    counterargument: {
      vi: "BOJ di chuyển chậm và pre-communicate; Nhật vẫn thiếu hụt chênh lệch lãi suất vs Mỹ; carry unwind trật tự đến nay.",
      en: "BOJ moves slowly and pre-communicates; Japan still in rate-differential deficit vs US; carry unwind orderly so far.",
    },
    confidence: "Medium",
  },
  {
    id: "currency",
    label: { vi: "Chế độ tiền tệ & dollar", en: "Currency regime & dollar" },
    similarity: 3, break: 3, importance: 3,
    data_points: ["dxy", "gold"],
    rubric: {
      vi: "DXY ~100s, thử nghiệm thanh toán BRICS, mua vàng ngân hàng trung ương. Vang vọng hậu Bretton Woods nhưng cơ chế khác (de-dollarization dự trữ vs kết thúc convertibility vàng).",
      en: "DXY ~100s, BRICS payment experiments, central-bank gold buying. Echoes post-Bretton Woods but mechanism differs (de-dollarization of reserves vs end of gold convertibility).",
    },
    reasoning: {
      vi: "Hiện tượng một phần (similarity=3). Phá vỡ một phần (break=3) — không có sự kiện tương đương Nixon-shock. Quan trọng vừa (importance=3).",
      en: "Phenomenon partial (similarity=3). Partial break (break=3) — no Nixon-shock-equivalent event. Moderately important (importance=3).",
    },
    counterargument: {
      vi: "Adoption stablecoin + CBDC có thể tăng tốc nếu Mỹ vũ khí hóa dollar; mua vàng ngân hàng trung ương (1.000+ tấn/năm) là tín hiệu không tầm thường.",
      en: "Stablecoin adoption + CBDCs could accelerate if US weaponizes dollar; gold central-bank buying (1,000+ tons/yr) is a non-trivial signal.",
    },
    confidence: "Low",
  },
  {
    id: "productivity",
    label: { vi: "Năng suất & công nghệ", en: "Productivity & technology" },
    similarity: 3, break: 3, importance: 4,
    data_points: ["productivity", "ulc"],
    rubric: {
      vi: "Chu kỳ capex AI vang vọng capex semiconductor/PC 1975–85. Năng suất nonfarm tăng tốc lại 2023–24 (>2% YoY) tương tự giữa-1990s/cuối-1970s.",
      en: "AI capex cycle echoes semiconductor/PC capex 1975–85. Nonfarm productivity re-accelerated 2023–24 (>2% YoY) similar to mid-1990s/late-1970s.",
    },
    reasoning: {
      vi: "Capex-cycle rhyme (similarity=3). Phá vỡ một phần (break=3) vì ràng buộc điện mới. Quan trọng cao (importance=4) — năng suất AI là lực có thể ĐẢO NGƯỢC 1970s outcome.",
      en: "Capex-cycle rhyme (similarity=3). Partial break (break=3) because of new electricity constraint. High importance (importance=4) — AI productivity could INVERT the 1970s outcome.",
    },
    counterargument: {
      vi: "Lợi ích AI có thể tập trung (biên mega-cap) thay vì khuếch tán; bằng chứng năng suất vẫn 1–2 năm dữ liệu.",
      en: "AI benefits may concentrate (mega-cap margins) rather than diffuse; productivity evidence still 1–2 years of data.",
    },
    confidence: "Low",
  },
  {
    id: "ai",
    label: { vi: "AI vs cách mạng vi xử lý", en: "AI vs microprocessor revolution" },
    similarity: 3, break: 3, importance: 4,
    data_points: ["productivity"],
    rubric: {
      vi: "Capex AI/GPU/cloud $200B+/năm tương tự build-out vi xử lý cuối-1970s. Nhưng tác động năng suất AI chưa chứng minh; vi xử lý có lợi ích workflow rõ hơn vào 1985.",
      en: "AI/GPU/cloud capex $200B+/yr similar to late-1970s semiconductor build-out. But AI productivity lift unproven; microprocessors had clearer workflow gains by 1985.",
    },
    reasoning: {
      vi: "Cấu trúc capex tương tự (similarity=3). Phá vỡ (break=3) vì inference economics + ràng buộc điện mới. Quan trọng (importance=4) — bất định quan trọng nhất.",
      en: "Capex structure similar (similarity=3). Break (break=3) due to inference economics + new electricity constraint. Important (importance=4) — the most consequential uncertainty.",
    },
    counterargument: {
      vi: "Inference economics + ràng buộc điện có thể chặn tác động năng suất AI; capex có thể over-build như telecom 2000–01.",
      en: "Inference economics + electricity constraint may cap AI productivity impact; capex could become over-build like 2000–01 telecom.",
    },
    confidence: "Low",
  },
  {
    id: "labor",
    label: { vi: "Thị trường lao động & nhân khẩu", en: "Labor market & demographics" },
    similarity: 2, break: 3, importance: 4,
    data_points: ["unemployment", "participation", "wage_ahe"],
    rubric: {
      vi: "Thất nghiệp ~4%, participation hậu-COVID ~62.5% (vs 67% tiền-2008). Nhân khẩu già, di trú thắt. 1970s có boomer vào + công đoàn mạnh.",
      en: "Unemployment ~4%, participation post-COVID ~62.5% (vs 67% pre-2008). Aging demographics, immigration tighter. 1970s had boomer entry + strong unions.",
    },
    reasoning: {
      vi: "Outcome tương tự (wage dính) nhưng cơ chế HOÀN TOÀN khác (similarity=2, break=3). Hôm nay: nhân khẩu + skill mismatch. Quan trọng (importance=4) — wage stickiness structural.",
      en: "Similar outcome (sticky wages) but COMPLETELY different mechanism (similarity=2, break=3). Today: demographics + skill mismatch. Important (importance=4) — wage stickiness is structural.",
    },
    counterargument: {
      vi: "Boomer nghỉ hưu + di trú giảm có thể tạo khan hiếm lao động dai dẳng giữ tiền lương cấu trúc cao — gần kết quả 1970s hơn người ta nghĩ.",
      en: "Boomer retirement + reduced immigration could create persistent labor scarcity keeping wages structurally higher — closer to 1970s outcome than people think.",
    },
    confidence: "Medium",
  },
  {
    id: "globalization",
    label: { vi: "Toàn cầu hóa & chuỗi cung ứng", en: "Globalization & supply chains" },
    similarity: 4, break: 3, importance: 4,
    data_points: ["broad_commodity"],
    rubric: {
      vi: "Reshoring, friend-shoring, thuế quan, export control, chính sách công nghiệp (CHIPS, IRA). ĐẢO NGƯỢC cấu trúc hyper-globalization 1990s–2010s — trở lại phân mảnh mức 1970s.",
      en: "Reshoring, friend-shoring, tariffs, export controls, industrial policy (CHIPS, IRA). Structural REVERSAL of 1990s–2010s hyper-globalization — return to 1970s-level fragmentation.",
    },
    reasoning: {
      vi: "Đảo ngược cấu trúc mạnh (similarity=4). Phá vỡ một phần (break=3) — Mexico/Vietnam/India hấp thụ redirect. Quan trọng (importance=4) — trần lạm phát cấu trúc cao hơn.",
      en: "Strong structural reversal (similarity=4). Partial break (break=3) — Mexico/Vietnam/India absorb the redirect. Important (importance=4) — higher structural inflation floor.",
    },
    counterargument: {
      vi: "Deglobalization một phần — dịch vụ, digital flows vẫn mở rộng; 'friend-shoring' là tái toàn cầu hóa đổi hướng.",
      en: "Deglobalization partial — services, digital flows still expanding; 'friend-shoring' is re-globalization redirected.",
    },
    confidence: "Medium",
  },
  {
    id: "finleverage",
    label: { vi: "Đòn bẩy tài chính & rủi ro thanh khoản", en: "Financial leverage & liquidity risk" },
    similarity: 4, break: 3, importance: 4,
    data_points: ["fedfunds", "sp500"],
    rubric: {
      vi: "Treasury basis trade (~$1T), đòn bẩy hedge-fund, private credit ($1.5T+), CTA, risk parity. Hệ thống đòn bẩy hơn và nhanh hơn 1970s. Stress events gần: cash squeeze 3/2020, UK gilts 9/2022, SVB 3/2023, yen-vix 8/2024.",
      en: "Treasury basis trade (~$1T), hedge-fund leverage, private credit ($1.5T+), CTAs, risk parity. System more leveraged and faster than 1970s. Recent stress: 3/2020 cash squeeze, 9/2022 UK gilts, 3/2023 SVB, 8/2024 yen-vix.",
    },
    reasoning: {
      vi: "Cơ chế đòn bẩy + sudden stop có mặt hơn (similarity=4). Phá vỡ (break=3) — 'mong manh nhưng dai dẳng'. Quan trọng (importance=4) — backstop có thể bị ràng buộc.",
      en: "Leverage + sudden stop mechanism more present (similarity=4). Break (break=3) — 'fragile but resilient'. Important (importance=4) — backstop may be constrained.",
    },
    counterargument: {
      vi: "Stress event đã giải quyết nhanh bởi ngân hàng trung ương; 'mong manh nhưng dai dẳng' là pattern gần đây.",
      en: "Stress events resolved quickly by central banks; 'fragile but resilient' is the recent pattern.",
    },
    confidence: "Medium",
  },
  {
    id: "equities",
    label: { vi: "Cổ phiếu & định giá", en: "Equities & valuation" },
    similarity: 2, break: 4, importance: 4,
    data_points: ["cape", "sp500"],
    rubric: {
      vi: "CAPE ~35 (2024) vs ~9 năm 1982 — định giá khởi đầu đối lập diametrical. 1970s bắt đầu đắt (Nifty Fifty) kết thúc rẻ. 2020s bắt đầu đắt và tập trung hơn.",
      en: "CAPE ~35 (2024) vs ~9 in 1982 — start-of-period valuations diametrically opposite. 1970s began expensive (Nifty Fifty) ended cheap. 2020s began expensive and got more concentrated.",
    },
    reasoning: {
      vi: "Định giá khởi đầu KHÔNG giống (similarity=2). Phá vỡ mạnh (break=4) — đầu đối lập chu kỳ định giá. Quan trọng (importance=4) — CAPE cao ngụ ý forward returns thấp.",
      en: "Starting valuations NOT alike (similarity=2). Strong break (break=4) — opposite ends of valuation cycle. Important (importance=4) — high CAPE implies low forward returns.",
    },
    counterargument: {
      vi: "CAPE cao không đảm bảo lợi nhuận thấp nếu tăng trưởng earnings biện minh (luận đề AI).",
      en: "High CAPE doesn't guarantee low returns if earnings growth justifies it (AI thesis).",
    },
    confidence: "Medium",
  },
  {
    id: "bonds",
    label: { vi: "Trái phiếu & tương quan cổ phiếu-trái phiếu", en: "Bonds & stock-bond correlation" },
    similarity: 3, break: 3, importance: 4,
    data_points: ["y10y_treasury"],
    rubric: {
      vi: "Tương quan stock-bond RETURN (không phải yield change) dương sau 2020 — trái phiếu ngừng hedge cổ phiếu, đúng pattern 1970s. Lợi suất thực âm sâu 2021 rồi dương sắc 2023.",
      en: "Stock-bond RETURN correlation (not yield change) turned positive after 2020 — bonds stopped hedging equities, exactly the 1970s pattern. Real yields deeply negative in 2021 then sharply positive by 2023.",
    },
    reasoning: {
      vi: "Hiện tượng một phần (similarity=3). Phá vỡ một phần (break=3). Quan trọng (importance=4) — nếu fiscal dominance kéo dài, tương quan dương có thể cấu trúc.",
      en: "Phenomenon partial (similarity=3). Partial break (break=3). Important (importance=4) — if fiscal dominance persists, positive correlation may be structural.",
    },
    counterargument: {
      vi: "Nếu lạm phát chứa, tương quan có thể âm lại; 1970s kéo dài 15+ năm, hôm nay có thể ngắn hơn.",
      en: "If inflation contained, correlation may turn negative again; 1970s lasted 15+ years, today may be shorter.",
    },
    confidence: "Medium",
  },
];

// Aggregate stats per index
export function dejavuStats() {
  const sims = DEJAVU_DIMENSIONS.map((d) => d.similarity);
  const breaks = DEJAVU_DIMENSIONS.map((d) => d.break);
  const imps = DEJAVU_DIMENSIONS.map((d) => d.importance);
  const avg = (a) => +(a.reduce((s, x) => s + x, 0) / a.length).toFixed(2);
  return {
    similarity: { avg: avg(sims), values: sims },
    break: { avg: avg(breaks), values: breaks },
    importance: { avg: avg(imps), values: imps },
    n: DEJAVU_DIMENSIONS.length,
  };
}

// 2D verdict: position on similarity × break grid
export function verdict2D(d) {
  // High similarity + low break → strong analogy
  // High similarity + high break → surface rhyme, mechanism diverges
  // Low similarity + high break → analogy fails
  // Low similarity + low break → different but unimportant break
  if (d.similarity >= 3.5 && d.break <= 2.5) return { vi: "Tương đồng mạnh", en: "Strong similarity", cls: "strong" };
  if (d.similarity >= 3.5 && d.break >= 3.5) return { vi: "Tương đồng bề mặt", en: "Surface similarity", cls: "surface" };
  if (d.similarity >= 2.5 && d.break <= 3.0) return { vi: "Tương đồng trung bình", en: "Medium similarity", cls: "medium" };
  if (d.break >= 3.5) return { vi: "Khác biệt chi phối", en: "Differences dominate", cls: "divergent" };
  return { vi: "Tương đồng yếu", en: "Weak similarity", cls: "weak" };
}

// For backwards compat with any callers expecting old fields
export function weightedScore(d) {
  // legacy: returns a blended number for display; not used for the headline anymore.
  return +((d.similarity + (5 - d.break) + d.importance) / 3).toFixed(2);
}

export function overallDejavuScore() {
  const s = dejavuStats();
  return { avg: s.similarity.avg, n: s.n, scores: s.similarity.values, stats: s };
}

export function verdictCounts() {
  const counts = {};
  for (const d of DEJAVU_DIMENSIONS) {
    const v = verdict2D(d).vi;
    counts[v] = (counts[v] || 0) + 1;
  }
  return counts;
}

export function topSimsAndDiffs() {
  // "Strongest echoes" = highest similarity
  // "Biggest breaks" = highest break severity
  const bySim = [...DEJAVU_DIMENSIONS].sort((a, b) => b.similarity - a.similarity);
  const byBreak = [...DEJAVU_DIMENSIONS].sort((a, b) => b.break - a.break);
  return {
    strongest: bySim.slice(0, 5),
    weakest: byBreak.slice(0, 5),
  };
}
