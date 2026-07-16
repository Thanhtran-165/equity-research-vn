// src/data/commodity_scores.mjs — bilingual
export const COMMODITY_SCORECARD = [
  {
    id: "oil",
    label: { vi: "Dầu thô", en: "Crude Oil" },
    category: { vi: "Năng lượng", en: "Energy" },
    hist_similarity: 4, inflation_role: 5, supply_elasticity: 1, lead_time: 5,
    supply_concentration: 3, china_exposure: 3, geopolitical_exposure: 5,
    ai_electrification: 1, oversupply_risk: 2, confidence: "High",
    narrative: {
      vi: "Vẫn là hàng hóa có vai trò lạm phát hệ thống quan trọng nhất, nhưng cường độ dầu/GDP thấp hơn ~60% so với 1970 và Mỹ là nhà sản xuất đầu ngành. Hormuz/trừng phạt Nga/Iran thúc đẩy premium địa chính trị.",
      en: "Still the most systemically important commodity for inflation, but oil intensity is ~60% below 1970 and US is now top producer. Hormuz/Russia/Iran sanctions drive the geopolitical premium.",
    },
    breaks_analogy: {
      vi: "Shale Mỹ + SPR + LNG giảm truyền dẫn cú sốc đáng kể vs cấm vận 1973.",
      en: "US shale + SPR + LNG materially reduce shock transmission vs 1973 embargo.",
    },
    data_keys: ["oil_brent", "oil_wti"],
  },
  {
    id: "natgas",
    label: { vi: "Khí tự nhiên / LNG", en: "Natural Gas / LNG" },
    category: { vi: "Năng lượng", en: "Energy" },
    hist_similarity: 3, inflation_role: 3, supply_elasticity: 2, lead_time: 4,
    supply_concentration: 3, china_exposure: 2, geopolitical_exposure: 4,
    ai_electrification: 4, oversupply_risk: 3, confidence: "Medium",
    narrative: {
      vi: "Khủng hoảng khí châu Âu 2022 cho thấy LNG có thể là vũ khí địa chính trị. Henry Hub tách khỏi TTF. Cầu điện data-center là tầng cầu cấu trúc mới.",
      en: "2022 Europe gas crisis showed LNG could be a geopolitical weapon. Henry Hub decoupled from TTF. Data-center power demand is a structural new demand layer.",
    },
    breaks_analogy: {
      vi: "Thị trường khí khu vực (Mỹ vs EU vs Asia) — không có giá thanh toán bù trừ toàn cầu như dầu.",
      en: "Regional gas markets (US vs EU vs Asia) — no single global clearing price like oil.",
    },
    data_keys: ["natgas_hh"],
  },
  {
    id: "coal",
    label: { vi: "Than", en: "Coal" },
    category: { vi: "Năng lượng", en: "Energy" },
    hist_similarity: 2, inflation_role: 2, supply_elasticity: 3, lead_time: 3,
    supply_concentration: 3, china_exposure: 5, geopolitical_exposure: 3,
    ai_electrification: 2, oversupply_risk: 3, confidence: "Medium",
    narrative: {
      vi: "Than có 'phục hưng' 2021–22 nhưng suy giảm cấu trúc kéo dài. Trung Quốc + Ấn Độ vẫn 70%+ cầu. Chính sách phi carbon hóa chặn tăng dài hạn.",
      en: "Coal had a 'renaissance' 2021–22 but structural decline persists. China + India still 70%+ of demand. Decarbonization policy caps long-term upside.",
    },
    breaks_analogy: {
      vi: "Không tương đồng 1970s như hàng hóa 'chiến lược' — vai trò than đang thu hẹp, không mở rộng.",
      en: "No 1970s parallel as a 'strategic' commodity — coal's role is shrinking, not growing.",
    },
    data_keys: ["coal"],
  },
  {
    id: "gold",
    label: { vi: "Vàng", en: "Gold" },
    category: { vi: "Kim loại quý", en: "Precious" },
    hist_similarity: 5, inflation_role: 2, supply_elasticity: 1, lead_time: 5,
    supply_concentration: 3, china_exposure: 2, geopolitical_exposure: 4,
    ai_electrification: 0, oversupply_risk: 1, confidence: "Medium",
    narrative: {
      vi: "Déjà vu trực tiếp nhất: Nixon-shock 1971 vàng $35→$850 vào 1980; 2024 vàng $2,600+ khi ngân hàng trung ương mua 1.000+ tấn/năm. Vàng phản ánh uy tín TIỀN TỆ, không phải CPI.",
      en: "Closest direct déjà vu: 1971 Nixon-shock gold $35→$850 by 1980; 2024 gold $2,600+ as central banks buy 1,000+ tons/yr. Gold reflects MONETARY credibility, not CPI.",
    },
    breaks_analogy: {
      vi: "Lợi suất thực âm sâu 2021 → dương 2023, nhưng vàng vẫn tăng — phá mô hình real-yield sách giáo khoa. Gợi ý bid uy tín tài khóa/tiền tệ, không pure rates.",
      en: "Real yields deeply negative in 2021 → positive in 2023, yet gold kept rising — breaking the textbook real-yield model. Suggests fiscal/monetary credibility bid, not pure rates.",
    },
    data_keys: ["gold"],
  },
  {
    id: "silver",
    label: { vi: "Bạc", en: "Silver" },
    category: { vi: "Kim loại quý", en: "Precious" },
    hist_similarity: 3, inflation_role: 1, supply_elasticity: 2, lead_time: 3,
    supply_concentration: 2, china_exposure: 3, geopolitical_exposure: 2,
    ai_electrification: 4, oversupply_risk: 2, confidence: "Low",
    narrative: {
      vi: "Kim loại lai: tiền tệ + công nghiệp (solar PV ~15% cầu). Bạc 2024 >$30 vang vọng spike Hunt brothers 1979–80 (không thao túng).",
      en: "Hybrid metal: monetary + industrial (solar PV ~15% of demand). 2024 silver >$30 evokes 1979–80 Hunt brothers spike (without the manipulation).",
    },
    breaks_analogy: {
      vi: "Cầu solar PV cấu trúc và tăng; 1979 là suy đoán-driven.",
      en: "Solar PV demand is structural and growing; 1979 was speculation-driven.",
    },
    data_keys: ["silver"],
  },
  {
    id: "copper",
    label: { vi: "Đồng", en: "Copper" },
    category: { vi: "Kim loại công nghiệp", en: "Base / Industrial" },
    hist_similarity: 3, inflation_role: 2, supply_elasticity: 1, lead_time: 5,
    supply_concentration: 4, china_exposure: 5, geopolitical_exposure: 3,
    ai_electrification: 5, oversupply_risk: 2, confidence: "Medium",
    narrative: {
      vi: "'Đồng là dầu mới' (H25) — điện khí hóa, lưới, EV, data-center đều cầu đồng. Nhưng grade quặng giảm, permitting dài (10–15 năm), Chile/Peru/Congo tập trung.",
      en: "'Copper is the new oil' (H25) — electrification, grid, EV, data-center all demand copper. But ore grades declining, permitting long (10–15y), Chile/Peru/Congo concentrated.",
    },
    breaks_analogy: {
      vi: "Đồng thiếu ngân hàng nguồn cung kiểu OPEC; nguồn cung phân mảnh. Bất động sản Trung Quốc (50% cầu) có thể bù cầu AI/lưới.",
      en: "Copper lacks oil's central-bank-of-supply (OPEC); supply is fragmented. China property (50% of demand) can offset AI/grid demand.",
    },
    data_keys: ["copper"],
  },
  {
    id: "aluminum",
    label: { vi: "Nhôm", en: "Aluminum" },
    category: { vi: "Kim loại công nghiệp", en: "Base / Industrial" },
    hist_similarity: 2, inflation_role: 2, supply_elasticity: 3, lead_time: 3,
    supply_concentration: 5, china_exposure: 5, geopolitical_exposure: 2,
    ai_electrification: 4, oversupply_risk: 3, confidence: "Medium",
    narrative: {
      vi: "Ngượng năng lượng (~14 MWh/tấn); Trung Quốc 55%+ sản lượng. Lưới + truyền tải + EV + aerosapce cầu. Chi phí carbon tăng.",
      en: "Energy-intensive (~14 MWh/ton); China is 55%+ of production. Grid + transmission + EV + aerospace demand. Carbon-cost rising.",
    },
    breaks_analogy: {
      vi: "Trung Quốc có thể xoay nguồn cung; restart smelter nhanh hơn greenfield mỏ đồng.",
      en: "China can swing supply; smelter restarts are faster than greenfield copper mines.",
    },
    data_keys: ["aluminum"],
  },
  {
    id: "nickel",
    label: { vi: "Nickel", en: "Nickel" },
    category: { vi: "Kim loại công nghiệp", en: "Base / Industrial" },
    hist_similarity: 2, inflation_role: 1, supply_elasticity: 4, lead_time: 3,
    supply_concentration: 5, china_exposure: 5, geopolitical_exposure: 2,
    ai_electrification: 3, oversupply_risk: 5, confidence: "Medium",
    narrative: {
      vi: "Indonesia + đầu tư HPAL Trung Quốc tràn ngập thị trường nickel Class-2 2022–24; giá sụp. Class-1 (pin) chặt hơn. Thị trường hai tầng.",
      en: "Indonesia + Chinese HPAL investment flooded Class-2 nickel market 2022–24; price collapsed. Class-1 (battery) tighter. Two-tier market.",
    },
    breaks_analogy: {
      vi: "Ví dụ rõ nhất về dư cung do Trung Quốc phá vỡ narrative tăng giá.",
      en: "Clearest example of China-induced oversupply breaking the bullish narrative.",
    },
    data_keys: ["nickel"],
  },
  {
    id: "tin",
    label: { vi: "Thiếc", en: "Tin" },
    category: { vi: "Kim loại công nghiệp", en: "Base / Industrial" },
    hist_similarity: 1, inflation_role: 1, supply_elasticity: 2, lead_time: 3,
    supply_concentration: 5, china_exposure: 4, geopolitical_exposure: 3,
    ai_electrification: 3, oversupply_risk: 3, confidence: "Low",
    narrative: {
      vi: "Hàn (điện tử/semi) là cầu chủ đạo. Myanmar + Indonesia chi phối nguồn cung. Chặt nhưng thị trường nhỏ — dễ bị squeeze suy đoán (tin LME 2022).",
      en: "Solder (electronics/semis) is dominant demand. Myanmar + Indonesia dominate supply. Tight but small market — vulnerable to speculative squeezes (2022 LME tin).",
    },
    breaks_analogy: {
      vi: "Thị trường nhỏ; không tương đồng 1970s.",
      en: "Tiny market; no 1970s parallel.",
    },
    data_keys: ["tin"],
  },
  {
    id: "uranium",
    label: { vi: "Uranium", en: "Uranium" },
    category: { vi: "Hạt nhân", en: "Nuclear" },
    hist_similarity: 4, inflation_role: 1, supply_elasticity: 1, lead_time: 5,
    supply_concentration: 5, china_exposure: 3, geopolitical_exposure: 4,
    ai_electrification: 5, oversupply_risk: 1, confidence: "Medium",
    narrative: {
      vi: "Hàng hóa tiêu biểu của chế độ AI-điện (H27). Build-out hạt nhân 1970s vang vọng; nay SMR + cầu PPA hyperscaler AI + restart lò phản ứng (Nhật, châu Âu). Tập trung Kazakhstan/Russia/Niger.",
      en: "Quintessential commodity of the AI-electricity regime (H27). 1970s nuclear build-out echoed; today SMRs + AI hyperscaler PPA demand + reactor restarts (Japan, Europe). Kazakhstan/Russia/Niger concentration.",
    },
    breaks_analogy: {
      vi: "Chu kỳ hợp đồng dài (utility procure 5–10y trước) — giá spot ≠ kinh tế producer. Bottleneck enrichment (Russia) đặc trưng hôm nay.",
      en: "Long contract cycle (utility procure 5–10y forward) — spot price ≠ producer economics. Enrichment bottleneck (Russia) is unique to today.",
    },
    data_keys: ["uranium"],
  },
  {
    id: "agriculture",
    label: { vi: "Nông sản (rộng)", en: "Agriculture (broad)" },
    category: { vi: "Nông nghiệp", en: "Agriculture" },
    hist_similarity: 4, inflation_role: 4, supply_elasticity: 2, lead_time: 3,
    supply_concentration: 3, china_exposure: 3, geopolitical_exposure: 4,
    ai_electrification: 0, oversupply_risk: 2, confidence: "Medium",
    narrative: {
      vi: "Truyền dẫn xã hội/lạm phát mạnh nhất (mùa vụ Soviet 1972–74, wheat Ukraine 2022). Tỷ lệ stock-to-use thấp hơn bề ngoài; El Niño/La Niña + cấm xuất khẩu tăng biến động.",
      en: "Strongest social/inflation transmission (1972–74 Soviet harvest, 2022 Ukraine wheat). Stock-to-use ratios are lower than they look; El Niño/La Niña + export bans add volatility.",
    },
    breaks_analogy: {
      vi: "Tỷ lệ stock-to-use wheat/corn/soy khỏe hơn 1972; nguồn cung phân bón đa dạng hơn ngoài Belarus/Russia.",
      en: "Wheat/corn/soy stock-to-use ratios healthier than 1972; fertilizer supply more diversified outside Belarus/Russia.",
    },
    data_keys: ["wheat", "corn", "soybean", "sugar", "coffee", "cocoa"],
  },
  {
    id: "fertilizer",
    label: { vi: "Phân bón", en: "Fertilizer" },
    category: { vi: "Nông nghiệp", en: "Agriculture" },
    hist_similarity: 3, inflation_role: 3, supply_elasticity: 1, lead_time: 4,
    supply_concentration: 5, china_exposure: 3, geopolitical_exposure: 5,
    ai_electrification: 0, oversupply_risk: 3, confidence: "Medium",
    narrative: {
      vi: "Ngượng năng lượng (urea/ammonia từ khí). Spike 2022 là câu chuyện trực tiếp potash Russia+Belarus + khí. Kết nối lạm phát năng lượng ↔ lương thực.",
      en: "Energy-intensive (urea/ammonia from natgas). 2022 spike was a direct Russia+Belarus potash + natgas story. Links energy ↔ food inflation.",
    },
    breaks_analogy: {
      vi: "Công suất phosphate mới (Morocco, Saudi) + công nghệ tái chế có thể nới nguồn cung trung hạn.",
      en: "New phosphate capacity (Morocco, Saudi) + recycling tech could ease medium-term supply.",
    },
    data_keys: ["fertilizer"],
  },
  {
    id: "broad",
    label: { vi: "Chỉ số hàng hóa rộng", en: "Broad Commodity Index" },
    category: { vi: "Tổng hợp", en: "Composite" },
    hist_similarity: 4, inflation_role: 4, supply_elasticity: 2, lead_time: 4,
    supply_concentration: 3, china_exposure: 4, geopolitical_exposure: 4,
    ai_electrification: 3, oversupply_risk: 2, confidence: "High",
    narrative: {
      vi: "Chỉ số hàng hóa rộng thực (FRED PALLFNFINDEXM) tăng 2021–22 ≈ 1973–74 về quy mô. Là một lớp, hàng hóa lấy lại vai trò inflation-hedge sau 20 năm underperform.",
      en: "Real broad-commodity index (FRED PALLFNFINDEXM) surge 2021–22 ≈ 1973–74 in magnitude. As a class, commodities regained inflation-hedge status after 20 years of underperformance.",
    },
    breaks_analogy: {
      vi: "Index nặng năng lượng; luận đề supercycle nay là kim loại + uranium + điện khí hóa, không cùng driver như dầu 1970s.",
      en: "Index is energy-heavy; today's supercycle thesis is metals + uranium + electrification, not the same drivers as 1970s oil.",
    },
    data_keys: ["broad_commodity"],
  },
];

// Redesigned per P0.2 review: NOT a single average.
// Four orthogonal sub-scores, each 0-5, each meaningful on its own:
//   1. historical_analogy  — how much today's setup rhymes with 1970–80 for this commodity
//   2. supply_tightness    — how scarce/inelastic is supply (HIGH = bullish structural pressure)
//   3. structural_demand   — how strong is the new-demand driver (AI/electrification) (HIGH = bullish)
//   4. oversupply_risk     — how likely a supply glut (HIGH = bearish risk)
// Direction note: high supply_tightness AND high structural_demand AND low oversupply_risk
//   = bullish combination. A single "average" was meaningless because columns had opposite signs.
//
// Supply tightness is built from: low elasticity (inverted), long lead time, supply concentration,
// geopolitical exposure. Low elasticity → tight supply, so we invert.

export function commoditySubScores(c) {
  // Invert supply_elasticity: low elasticity (1) = very tight (5); high (5) = loose (1)
  const tightFromElasticity = 6 - (c.supply_elasticity || 3);
  const tightnessComponents = [tightFromElasticity, c.lead_time, c.supply_concentration, c.geopolitical_exposure];
  const supply_tightness = +(tightnessComponents.reduce((s, x) => s + x, 0) / tightnessComponents.length).toFixed(2);

  const structural_demand = +(((c.ai_electrification || 0) + (c.china_exposure || 0)) / 2).toFixed(2);
  const historical_analogy = +(c.hist_similarity || 0).toFixed(2);
  const oversupply_risk = +(c.oversupply_risk || 0).toFixed(2);

  // Net bullishness signal (qualitative): tight + demand high, oversupply low.
  const net_bullish = +(supply_tightness + structural_demand - oversupply_risk).toFixed(2);

  return { historical_analogy, supply_tightness, structural_demand, oversupply_risk, net_bullish };
}

// Legacy alias kept for backwards compat — returns the net bullish score (NOT an average).
export function commodityWeighted(c) {
  return commoditySubScores(c).net_bullish;
}

// Per-commodity verdict based on the 4 sub-scores.
// Returns one of 5 verdicts (bilingual {vi, en}):
//   - "scarce": structural shortage — high tightness + high demand + low oversupply
//   - "tight": cycle tightness — high tightness but not structural
//   - "oversupply": oversupply risk dominates
//   - "geopol": primarily a geopolitical exposure story
//   - "narrative": narrative-only, evidence insufficient
export function commodityVerdict(c) {
  const s = commoditySubScores(c);
  if (s.oversupply_risk >= 4) {
    return { vi: "Dư cung", en: "Oversupply risk", cls: "weak" };
  }
  if (s.supply_tightness >= 4 && s.structural_demand >= 3.5 && s.oversupply_risk <= 2.5) {
    return { vi: "Thiếu cung cấu trúc", en: "Structurally scarce", cls: "strong" };
  }
  if (s.supply_tightness >= 3.5) {
    return { vi: "Thắt chặt chu kỳ", en: "Cycle tight", cls: "medium" };
  }
  if (c.geopolitical_exposure >= 4 && s.supply_tightness >= 3) {
    return { vi: "Phụ thuộc địa chính trị", en: "Geopolitically exposed", cls: "surface" };
  }
  return { vi: "Narrative chưa đủ bằng chứng", en: "Narrative-only, evidence thin", cls: "insufficient" };
}
