"use client";
import { useLang } from "../../components/LangProvider.jsx";
import { COMMODITY_SCORECARD, commoditySubScores, commodityVerdict } from "../../data/commodity_scores.mjs";
import { getSeries } from "../../lib/data_loader.mjs";
import { Chart } from "../../components/Chart.mjs";
import { filterRange, deflate, yoyPct } from "../../lib/transforms.mjs";

const ATTRS = [
  { key: "hist_similarity", vi: "Tương đồng lịch sử", en: "Hist sim" },
  { key: "inflation_role", vi: "Vai trò lạm phát", en: "Infl role" },
  { key: "supply_elasticity", vi: "Độ co giãn cung", en: "Supply elast." },
  { key: "lead_time", vi: "Lead time", en: "Lead time" },
  { key: "supply_concentration", vi: "Tập trung nguồn cung", en: "Supply concentr." },
  { key: "china_exposure", vi: "Phơi nhiễm TQ", en: "China exp." },
  { key: "geopolitical_exposure", vi: "Phơi nhiễm địa chính trị", en: "Geopol. exp." },
  { key: "ai_electrification", vi: "AI/điện khí hóa", en: "AI/elec." },
  { key: "oversupply_risk", vi: "Rủi ro dư cung", en: "Over-supply" },
];

export default function CommoditiesPage() {
  const { lang } = useLang();
  const cpi = getSeries("cpi");
  const pick = (obj) => (obj && typeof obj === "object" ? (obj[lang] || obj.vi || obj.en) : obj);
  const confLabel = (c) => ({ High: lang === "vi" ? "Cao" : "High", Medium: lang === "vi" ? "Trung bình" : "Medium", Low: lang === "vi" ? "Thấp" : "Low" })[c] || c;
  const renderChart = (props) => <div dangerouslySetInnerHTML={{ __html: Chart({ ...props, lang }) }} />;
  const buildReal = (key) => { const s = getSeries(key); return s ? deflate(s.observations, cpi?.observations || [], 2024) : []; };
  const buildNominal = (key) => getSeries(key)?.observations || [];

  return (
    <div>
      <section className="hero" style={{padding: "40px 0 24px"}}>
        <div className="container">
          <span className="eyebrow">{lang === "vi" ? "Dashboard B · Commodity Déjà Vu" : "Dashboard B · Commodity Déjà Vu"}</span>
          <h1 style={{fontSize: 32}}>{lang === "vi" ? "Hàng hóa như lớp chiến lược" : "Commodities as the strategic layer"}</h1>
          <p className="sub" style={{fontSize: 16}}>
            {lang === "vi"
              ? "1970s dầu là điểm nghẽn binding. Ràng buộc hôm nay rộng hơn: điện, đồng, uranium, và chính trị critical minerals. Mỗi hàng hóa dưới chấm trên chín thuộc tính cộng độ tin cậy."
              : "In the 1970s oil was the binding bottleneck. Today's constraint is broader: electricity, copper, uranium, and the politics of critical minerals. Each commodity below is scored across nine attributes plus confidence."}
          </p>
        </div>
      </section>

      <section className="section" style={{paddingTop: 24}}>
        <div className="container">
          <div className="card">
            <h2 style={{marginTop: 0}}>{lang === "vi" ? "Bảng điểm hàng hóa — 4 sub-score độc lập" : "Commodity scorecard — 4 independent sub-scores"}</h2>
            <p style={{fontSize: 12, color: "var(--fg-muted)"}}>
              {lang === "vi"
                ? "Sửa P0: không cộng trung bình các biến khác chiều. 4 sub-score: Analogy (déjà vu lịch sử), Tightness (cung khan hiếm — elasticità đảo + lead time + concentration + geopol), Demand (cầu cấu trúc AI/điện khí hóa + China), Oversupply (rủi ro dư cung). Bullish = Tightness cao + Demand cao + Oversupply thấp."
                : "P0 fix: no averaging across opposite-sign variables. 4 sub-scores: Analogy (historical déjà vu), Tightness (supply scarcity — inverted elasticity + lead time + concentration + geopol), Demand (structural AI/electrification demand + China), Oversupply (glut risk). Bullish = high Tightness + high Demand + low Oversupply."}
            </p>
            <table style={{fontSize: 13}}>
              <thead>
                <tr>
                  <th>{lang === "vi" ? "Hàng hóa" : "Commodity"}</th>
                  <th className="num" title={lang === "vi" ? "Déjà vu lịch sử" : "Historical déjà vu"}>{lang === "vi" ? "Analogy" : "Analogy"}</th>
                  <th className="num" title={lang === "vi" ? "Cung khan hiếm" : "Supply scarcity"}>{lang === "vi" ? "Tight" : "Tight"}</th>
                  <th className="num" title={lang === "vi" ? "Cầu cấu trúc" : "Structural demand"}>{lang === "vi" ? "Demand" : "Demand"}</th>
                  <th className="num" title={lang === "vi" ? "Rủi ro dư cung" : "Oversupply risk"}>{lang === "vi" ? "Over" : "Over"}</th>
                  <th className="num" title={lang === "vi" ? "Tín hiệu bullish net" : "Net bullish signal"}>{lang === "vi" ? "Net" : "Net"}</th>
                  <th>{lang === "vi" ? "Phán quyết" : "Verdict"}</th>
                  <th>{lang === "vi" ? "Độ tin cậy" : "Conf."}</th>
                </tr>
              </thead>
              <tbody>
                {COMMODITY_SCORECARD.map((c) => {
                  const s = commoditySubScores(c);
                  const v = commodityVerdict(c);
                  const cellColor = (v, bullish = true) => {
                    if (bullish) return v >= 4 ? "var(--success)" : v >= 3 ? "var(--accent)" : "var(--fg-muted)";
                    return v >= 4 ? "var(--danger)" : v >= 3 ? "var(--warn)" : "var(--fg-muted)";
                  };
                  const netColor = s.net_bullish >= 7 ? "var(--success)" : s.net_bullish >= 5 ? "var(--accent)" : s.net_bullish <= 3 ? "var(--danger)" : "var(--fg-muted)";
                  return (
                    <tr key={c.id}>
                      <td><strong>{pick(c.label)}</strong><div style={{fontSize: 10, color: "var(--fg-muted)"}}>{pick(c.category)}</div></td>
                      <td className="num" style={{color: "var(--chart-line-5)", fontWeight: 600}}>{s.historical_analogy.toFixed(1)}</td>
                      <td className="num" style={{color: cellColor(s.supply_tightness), fontWeight: 600}}>{s.supply_tightness.toFixed(1)}</td>
                      <td className="num" style={{color: cellColor(s.structural_demand), fontWeight: 600}}>{s.structural_demand.toFixed(1)}</td>
                      <td className="num" style={{color: cellColor(s.oversupply_risk, false), fontWeight: 600}}>{s.oversupply_risk.toFixed(1)}</td>
                      <td className="num"><strong style={{color: netColor}}>{s.net_bullish.toFixed(1)}</strong></td>
                      <td><span className={`pill ${v.cls}`}>{pick(v)}</span></td>
                      <td><span className={`confidence ${c.confidence}`}>{confLabel(c.confidence)}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            <p style={{fontSize: 11, color: "var(--fg-muted)"}}>
              {lang === "vi" ? "Net = Tight + Demand − Oversupply. Cao = cấu trúc bullish (khan hiếm + cầu mạnh + ít dư cung)." : "Net = Tight + Demand − Oversupply. High = structurally bullish (scarce + strong demand + low glut)."}
            </p>
          </div>

          <h2 style={{marginTop: 40}}>{lang === "vi" ? "Giá thực của hàng hóa chiến lược" : "Real prices of the strategic commodities"}</h2>
          <p style={{fontSize: 14}}>{lang === "vi" ? "CPI-deflated về $2024 — tiết lộ hàng hóa nào thực sự breakout vs cái nào chỉ di chuyển nominal." : "CPI-deflated to 2024 dollars — reveals which commodities have actually broken out vs which are nominal-only moves."}</p>

          {renderChart({ title: { vi: "Dầu thô thực — WTI spot lịch sử dài ($2024/bbl)", en: "Real crude oil — WTI spot long history (2024 $/bbl)" }, subtitle: { vi: "Sửa P0: dùng WTISPLC (1946–nay) để phủ cả cú sốc 1973 và 1979. POILBREUSDM chỉ có giá trị từ ~1990.", en: "P0 fix: using WTISPLC (1946–present) to cover both 1973 and 1979 shocks. POILBREUSDM only has values from ~1990." }, series: [{ name: { vi: "WTI spot thực", en: "Real WTI spot" }, data: filterRange(buildReal("oil_wti_long"), "1965-01-01") }], shading: [{ from: "1973-10-01", to: "1974-03-31", label: { vi: "Cấm vận 1973", en: "1973 embargo" } }, { from: "1979-01-01", to: "1980-12-31", label: { vi: "Iran 1979", en: "Iran 1979" } }, { from: "2022-02-01", to: "2022-12-31", label: { vi: "Ukraine", en: "Ukraine" } }], yFormat: "usd", yLabel: { vi: "$/bbl (2024 thực)", en: "$/bbl (2024 real)" }, source: getSeries("oil_wti_long")?.source || "FRED WTISPLC", sourceUrl: getSeries("oil_wti_long")?.source_url || "https://fred.stlouisfed.org/series/WTISPLC", note: { vi: "Sửa P0.5: chuỗi POILBREUSDM ngắn (557 obs từ ~1990) không phủ 1973/1979. WTISPLC (WTI spot, 798 obs từ 1946) là backbone lịch sử.", en: "P0.5 fix: POILBREUSDM series too short (557 obs from ~1990) doesn't cover 1973/1979. WTISPLC (WTI spot, 798 obs from 1946) is the historical backbone." } })}
          {renderChart({ title: { vi: "Vàng thực ($/oz, $2024)", en: "Real gold ($/oz, 2024 dollars)" }, series: [{ name: { vi: "Vàng thực", en: "Real gold" }, data: filterRange(buildReal("gold"), "1965-01-01") }], yFormat: "usd", yLabel: { vi: "$/oz (2024 thực)", en: "$/oz (2024 real)" }, source: getSeries("gold")?.source, sourceUrl: getSeries("gold")?.source_url })}
          {renderChart({ title: { vi: "Đồng thực ($/mt, $2024)", en: "Real copper ($/mt, 2024 dollars)" }, series: [{ name: { vi: "Đồng thực", en: "Real copper" }, data: filterRange(buildReal("copper"), "1965-01-01") }], yFormat: "usd", yLabel: { vi: "$/mt (2024 thực)", en: "$/mt (2024 real)" }, source: getSeries("copper")?.source, sourceUrl: getSeries("copper")?.source_url })}
          {renderChart({ title: { vi: "Uranium thực ($/lb, $2024)", en: "Real uranium ($/lb, 2024 dollars)" }, series: [{ name: { vi: "Uranium thực", en: "Real uranium" }, data: filterRange(buildReal("uranium"), "1965-01-01") }], yFormat: "usd", yLabel: { vi: "$/lb (2024 thực)", en: "$/lb (2024 real)" }, source: getSeries("uranium")?.source, sourceUrl: getSeries("uranium")?.source_url })}
          {renderChart({ title: { vi: "Hàng hóa nông nghiệp thực ($2024)", en: "Real agricultural commodities (2024 dollars)" }, subtitle: { vi: "Lúa mì, ngô, đậu nành. Mùa vụ Soviet 1972-74 + cú sốc Ukraine 2022 đều nhìn thấy.", en: "Wheat, corn, soybean. 1972–74 Soviet harvest + 2022 Ukraine shocks both visible." }, series: [{ name: { vi: "Lúa mì ($/mt)", en: "Wheat ($/mt)" }, data: filterRange(buildReal("wheat"), "1965-01-01") }, { name: { vi: "Ngô ($/mt)", en: "Corn ($/mt)" }, data: filterRange(buildReal("corn"), "1965-01-01") }, { name: { vi: "Đậu nành ($/mt)", en: "Soybean ($/mt)" }, data: filterRange(buildReal("soybean"), "1965-01-01") }], yFormat: "usd", yLabel: { vi: "$/mt (2024 thực)", en: "$/mt (2024 real)" }, source: getSeries("wheat")?.source, sourceUrl: getSeries("wheat")?.source_url })}
          {renderChart({ title: { vi: "Kim loại công nghiệp thực: nickel, thiếc, nhôm ($2024)", en: "Real industrial metals: nickel, tin, aluminum (2024 dollars)" }, subtitle: { vi: "Dư cung nickel từ Indonesia nhìn thấy hậu-2022; đồng & nhôm dai dẳng hơn.", en: "Nickel oversupply from Indonesia visible post-2022; copper & aluminum more resilient." }, series: [{ name: { vi: "Nickel ($/mt)", en: "Nickel ($/mt)" }, data: filterRange(buildReal("nickel"), "1965-01-01") }, { name: { vi: "Thiếc ($/mt)", en: "Tin ($/mt)" }, data: filterRange(buildReal("tin"), "1965-01-01") }, { name: { vi: "Nhôm ($/mt)", en: "Aluminum ($/mt)" }, data: filterRange(buildReal("aluminum"), "1965-01-01") }], yFormat: "usd", yLabel: { vi: "$/mt (2024 thực)", en: "$/mt (2024 real)" }, source: getSeries("nickel")?.source, sourceUrl: getSeries("nickel")?.source_url })}
          {renderChart({ title: { vi: "Tỷ lệ vàng/bạc", en: "Gold/silver ratio" }, subtitle: { vi: "Tỷ lệ cao = vàng outperform bạc (bid tiền tệ); thấp = bạc/công nghiệp outperform.", en: "High ratio = gold outperforming silver (monetary bid); low ratio = silver/industrial outperforming." }, series: [{ name: { vi: "Tỷ lệ vàng/bạc", en: "Gold/silver ratio" }, data: filterRange(getSeries("gold")?.observations.map((o) => { const silv = getSeries("silver")?.observations.find((s) => s.date === o.date); return silv && silv.value ? { date: o.date, value: o.value / silv.value } : null; }).filter(Boolean), "1965-01-01") }], yFormat: "ratio", yLabel: { vi: "oz bạc / oz vàng", en: "oz silver / oz gold" }, source: "World Bank CMO Pink Sheet", sourceUrl: "https://www.worldbank.org/en/research/commodity-markets" })}
          {renderChart({ title: { vi: "Bạc thực ($/oz, $2024)", en: "Real silver ($/oz, 2024 dollars)" }, subtitle: { vi: "Kim loại lai: tiền tệ + công nghiệp solar PV. Breakout 2024 vang vọng 1979-80.", en: "Hybrid metal: monetary + solar PV industrial demand. 2024 breakout evokes 1979–80." }, series: [{ name: { vi: "Bạc thực", en: "Real silver" }, data: filterRange(buildReal("silver"), "1965-01-01") }], yFormat: "usd", yLabel: { vi: "$/oz (2024 thực)", en: "$/oz (2024 real)" }, source: getSeries("silver")?.source, sourceUrl: getSeries("silver")?.source_url })}
          {renderChart({ title: { vi: "Khí tự nhiên Henry Hub thực ($/MMBtu, $2024)", en: "Real natural gas Henry Hub ($/MMBtu, 2024 dollars)" }, series: [{ name: { vi: "Khí thực", en: "Real natgas" }, data: filterRange(buildReal("natgas_hh"), "1965-01-01") }], yFormat: "usd", yLabel: { vi: "$/MMBtu (2024 thực)", en: "$/MMBtu (2024 real)" }, source: getSeries("natgas_hh")?.source, sourceUrl: getSeries("natgas_hh")?.source_url })}
          {renderChart({ title: { vi: "Hàng hóa mềm thực: cà phê, cocoa, đường ($2024)", en: "Real soft commodities: coffee, cocoa, sugar (2024 dollars)" }, series: [{ name: { vi: "Cà phê ($/kg)", en: "Coffee ($/kg)" }, data: filterRange(buildReal("coffee"), "1965-01-01") }, { name: { vi: "Cocoa ($/kg)", en: "Cocoa ($/kg)" }, data: filterRange(buildReal("cocoa"), "1965-01-01") }, { name: { vi: "Đường ($/kg × 10)", en: "Sugar ($/kg × 10)" }, data: filterRange(buildReal("sugar").map((o) => ({ date: o.date, value: o.value * 10 })), "1965-01-01") }], yFormat: "usd", yLabel: { vi: "$/kg (2024 thực, đường × 10)", en: "$/kg (2024 real, sugar × 10)" }, source: getSeries("coffee")?.source, sourceUrl: getSeries("coffee")?.source_url })}

          <h2 style={{marginTop: 40}}>{lang === "vi" ? "Tường thuật từng hàng hóa" : "Per-commodity narrative"}</h2>
          {COMMODITY_SCORECARD.map((c) => {
            const s = commoditySubScores(c);
            const v = commodityVerdict(c);
            return (
              <div key={c.id} className="card" style={{marginBottom: 16}}>
                <div style={{display: "flex", justifyContent: "space-between", alignItems: "baseline", flexWrap: "wrap", gap: 8}}>
                  <h3 style={{margin: 0}}>{pick(c.label)} <span style={{fontSize: 12, color: "var(--fg-muted)"}}>· {pick(c.category)}</span></h3>
                  <div style={{fontSize: 12, display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center"}}>
                    <span className={`pill ${v.cls}`}>{pick(v)}</span>
                    <span>An.<strong>{s.historical_analogy.toFixed(1)}</strong></span>
                    <span>Tight<strong style={{color: "var(--success)"}}>{s.supply_tightness.toFixed(1)}</strong></span>
                    <span>Dem.<strong style={{color: "var(--accent)"}}>{s.structural_demand.toFixed(1)}</strong></span>
                    <span>Over<strong style={{color: "var(--danger)"}}>{s.oversupply_risk.toFixed(1)}</strong></span>
                    <span className={`confidence ${c.confidence}`}>{confLabel(c.confidence)}</span>
                  </div>
                </div>
                <p style={{fontSize: 14, marginTop: 10}}>{pick(c.narrative)}</p>
                <p style={{fontSize: 13, color: "var(--fg-muted)"}}><strong>{lang === "vi" ? "Phá phép so sánh:" : "Breaks analogy:"}</strong> {pick(c.breaks_analogy)}</p>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
