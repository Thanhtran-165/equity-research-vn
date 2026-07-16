// src/data/scenarios.mjs — bilingual
export const SCENARIOS = [
  {
    id: "ai_productivity",
    name: { vi: "1 · AI Productivity Disinflation", en: "1 · AI Productivity Disinflation" },
    narrative: {
      vi: "AI nâng năng suất dịch vụ; chuỗi cung ứng ổn định; năng lượng bình ổn; Fed giảm dần. Đường 1990s-lite ĐẢO NGƯỢC 1970s.",
      en: "AI lifts services productivity; supply chains stable; energy calm; Fed cuts gradually. The 1990s-lite path that INVERTS the 1970s.",
    },
    trigger: {
      vi: "Năng suất nonfarm >2% YoY duy trì + lạm phát hàng hóa ổn định + shelter hạ.",
      en: "Sustained nonfarm productivity >2% YoY + stable goods inflation + easing shelter.",
    },
    confirmation: {
      vi: "Lạm phát dịch vụ core ex-shelter hạ về 3%; tăng trưởng ULC < tăng trưởng tiền lương.",
      en: "Core services ex-shelter falls toward 3%; unit labor cost growth < wage growth.",
    },
    invalidation: {
      vi: "Năng suất chậm; over-build capex dẫn đến write-down; tăng trưởng tiền lương >5%.",
      en: "Productivity slows; capex over-build leads to write-downs; wage growth stays >5%.",
    },
    asset_sensitivity: {
      vi: "Tích cực mega-cap tech, growth dài-hạn, trái phiếu lấy lại vai hedge; tiêu cực vàng, value, năng lượng.",
      en: "Bullish mega-cap tech, long-duration growth, bonds resume hedge role; bearish gold, value, energy.",
    },
    historical_analogue: {
      vi: "Bùng nổ năng suất internet cuối 1990s — giảm phát, không phải 1970s.",
      en: "Late 1990s internet-driven productivity boom — disinflationary, not 1970s.",
    },
    confidence: "Low",
  },
  {
    id: "stagflation",
    name: { vi: "2 · Stagflation-lite 1970s", en: "2 · 1970s-lite Stagflation" },
    narrative: {
      vi: "Cú sốc dầu/thực phẩm; phân mảnh chuỗi cung ứng; tiền lương dính; tăng trưởng yếu; Fed kẹt. Kết quả déjà vu trực tiếp nhất.",
      en: "Oil/food shock; supply chain fragmentation; sticky wages; weak growth; Fed boxed in. The most direct déjà vu outcome.",
    },
    trigger: {
      vi: "Brent >$120 duy trì; chỉ số thực phẩm +>15% YoY; thất nghiệp tăng cùng CPI >5%.",
      en: "Brent >$120 sustained; food index up >15% YoY; unemployment rising alongside CPI >5%.",
    },
    confirmation: {
      vi: "Khoảng cách headline/core mở rộng; lạm phát dịch vụ tăng tốc lại; tăng trưởng tiền lương >5%.",
      en: "Headline/core gap widens; services inflation re-accelerates; wage growth >5%.",
    },
    invalidation: {
      vi: "Giá năng lượng hạ; Trung Quốc xuất khẩu giảm phát; năng suất bất ngờ tăng.",
      en: "Energy prices fall; China exports deflation; productivity surprise up.",
    },
    asset_sensitivity: {
      vi: "Tiêu cực cổ phiếu & trái phiếu dài-hạn; tích cực hàng hóa, energy equities, vàng, TIPS.",
      en: "Bearish long-duration equities & bonds; bullish commodities, energy equities, gold, TIPS.",
    },
    historical_analogue: {
      vi: "Cấm vận 1973–74 + cú sốc kép 1979–80.",
      en: "1973–74 embargo + 1979–80 double shock.",
    },
    confidence: "Medium",
  },
  {
    id: "fiscal_dominance",
    name: { vi: "3 · Fiscal Dominance & Tái định giá trái phiếu", en: "3 · Fiscal Dominance & Bond Repricing" },
    narrative: {
      vi: "Thâm hụt lớn + phát hành Treasury nặng + cầu nước ngoài yếu → term premium tăng; lợi suất dài vẫn cao ngay cả khi Fed giảm.",
      en: "Large deficits + heavy Treasury issuance + weak foreign demand → term premium rises; long yields stay high even as Fed cuts.",
    },
    trigger: {
      vi: "Thâm hụt >6% GDP với thất nghiệp <5%; bid Treasury nước ngoài yếu trong auction.",
      en: "Deficit stays >6% GDP with unemployment <5%; foreign Treasury bid weakens in auctions.",
    },
    confirmation: {
      vi: "Lợi suất 10Y > Fed funds trong chu kỳ giảm; ACM term premium dương dai dẳng; DXY yếu.",
      en: "10Y yield > Fed funds during cutting cycle; ACM term premium persistently positive; DXY weak.",
    },
    invalidation: {
      vi: "Thâm hụt hẹp (thỏa hiệp chính trị); cầu nước ngoài hồi; term premium âm.",
      en: "Deficit narrows (political compromise); foreign demand recovers; term premium stays negative.",
    },
    asset_sensitivity: {
      vi: "Tiêu cực Treasury dài-hạn; tích cực vàng, tài sản thực, value, foreign equities (đa dạng FX).",
      en: "Bearish long-duration Treasuries; bullish gold, real assets, value, foreign equities (FX-diversified).",
    },
    historical_analogue: {
      vi: "Không có sạch ở Mỹ — gần repression tài chính hậu-WW2 hoặc dysfunction gilt Anh 1970s.",
      en: "None cleanly in US — closer to post-WW2 financial repression or UK 1970s gilt dysfunction.",
    },
    confidence: "Medium",
  },
  {
    id: "yen_carry",
    name: { vi: "4 · Yen-Carry Unwind", en: "4 · Yen-Carry Unwind" },
    narrative: {
      vi: "BOJ tăng; yen tăng nhanh; deleverage carry; trùng risk-off. Chế độ khuếch đại biến động.",
      en: "BOJ hikes; yen surges; leveraged carry unwinds; coincident risk-off. Volatility amplifier regime.",
    },
    trigger: {
      vi: "BOJ tăng >50bp tích lũy; USD/JPY phá vỡ dưới 150 với tốc độ.",
      en: "BOJ hikes >50bp cumulatively; USD/JPY breaks below 150 with speed.",
    },
    confirmation: {
      vi: "VIX spike >30; Treasury basis-trade unwind; outflow vốn Nhật tăng tốc.",
      en: "VIX spike >30; Treasury basis-trade unwinds; Japanese equity outflows accelerate.",
    },
    invalidation: {
      vi: "BOJ pause; chênh lệch lãi suất Mỹ-Nhật vẫn rộng; carry xây lại.",
      en: "BOJ pauses; US–JP rate differential stays wide; carry rebuilds.",
    },
    asset_sensitivity: {
      vi: "Tiêu cực tài sản rủi ro, carry funded JPY, Treasury (Nhật bán); tích cực yen, cash.",
      en: "Bearish risk assets, JPY-funded carry, Treasuries (Japanese selling); bullish yen, cash.",
    },
    historical_analogue: {
      vi: "5 Aug 2024 (preview); LTCM/yen 1998; yen surge Tohoku 2011.",
      en: "Aug 5, 2024 (preview); 1998 LTCM/yen; 2011 Tohoku yen surge.",
    },
    confidence: "Medium",
  },
  {
    id: "commodity_shock",
    name: { vi: "5 · Cú sốc nguồn cung hàng hóa", en: "5 · Commodity Supply Shock" },
    narrative: {
      vi: "Phong tỏa Hormuz, cú sốc thời tiết, cấm xuất khẩu, resource nationalism — thiếu hụt vật lý.",
      en: "Hormuz disruption, weather shock, export bans, resource nationalism — physical shortage.",
    },
    trigger: {
      vi: "Sự cố Hormuz; cấm xuất khẩu nhà xuất khẩu lớn; thất bại nông nghiệp El Niño/La Niña.",
      en: "Hormuz incident; major exporter export ban; El Niño/La Niña agricultural failure.",
    },
    confirmation: {
      vi: "Brent +30% trong 3 tháng; chỉ số hàng hóa rộng +15%; kỳ vọng lạm phát de-anchor ngắn.",
      en: "Brent +30% in 3 months; broad commodity index +15%; inflation expectations de-anchor briefly.",
    },
    invalidation: {
      vi: "Phóng SPR; thay thế; demand destruction ở giá cao; đình chiến.",
      en: "SPR release; substitution; demand destruction at high prices; ceasefire.",
    },
    asset_sensitivity: {
      vi: "Tích cực dầu, đồng, uranium, vàng, nông; tiêu cực cyclicals trừ energy, EM importer.",
      en: "Bullish oil, copper, uranium, gold, agri; bearish cyclicals excluding energy, EM importers.",
    },
    historical_analogue: {
      vi: "Cấm vận 1973; Iran 1979; nickel/lúa mì Ukraine 2022.",
      en: "1973 embargo; 1979 Iran; 2022 Ukraine grain/nickel.",
    },
    confidence: "Medium",
  },
  {
    id: "china_deflation",
    name: { vi: "6 · China Deflation Offset", en: "6 · China Deflation Offset" },
    narrative: {
      vi: "Trung Quốc xuất khẩu nhiều hơn (bất động sản yếu, dư thừa công nghiệp); kim loại công nghiệp dư cung; Mỹ vẫn lạm phát dịch vụ.",
      en: "China exports more (property weak, industrial overcapacity); industrial metals oversupplied; US keeps services inflation.",
    },
    trigger: {
      vi: "Bất động sản Trung Quốc suy yếu sâu; đẩy xuất khẩu; nickel/lithium Indonesia/Trung Quốc tràn ngập.",
      en: "China property destitution deepens; export push; Indonesia/Chinese nickel/lithium floods market.",
    },
    confirmation: {
      vi: "Kim loại công nghiệp giảm trong khi lạm phát dịch vụ Mỹ >4%; PPI Trung Quốc âm sâu.",
      en: "Industrial metals fall while US services inflation stays >4%; China PPI deeply negative.",
    },
    invalidation: {
      vi: "Kích thích Trung Quốc hồi sinh cầu bất động sản/kim loại; export control rare earth đảo ngược.",
      en: "China stimulus revives property/metal demand; export controls on rare earths reverse flow.",
    },
    asset_sensitivity: {
      vi: "Tích cực EM importer, người tiêu dùng, cổ phiếu Trung Quốc (cuối cùng); tiêu cực miner kim loại công nghiệp.",
      en: "Bullish EM importers, consumers, China equities (eventually); bearish industrial metals miners.",
    },
    historical_analogue: {
      vi: "Xuất khẩu giảm phát Trung Quốc 1997–2002 sau khủng hoảng tài chính châu Á.",
      en: "1997–2002 China deflation export following Asian financial crisis.",
    },
    confidence: "Medium",
  },
];
