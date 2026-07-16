"use client";
import { useLang } from "../components/LangProvider.jsx";
import { getSeries, sourceStats } from "../lib/data_loader.mjs";
import { DEJAVU_DIMENSIONS, weightedScore, overallDejavuScore, verdictCounts, topSimsAndDiffs } from "../data/dejavu_scores.mjs";
import { COMMODITY_SCORECARD, commodityWeighted } from "../data/commodity_scores.mjs";
import { Chart } from "../components/Chart.mjs";
import { yoyPct, deflate, toMonthly, filterRange, rebase } from "../lib/transforms.mjs";

export default function Home() {
  const { t, lang } = useLang();
  const stats = sourceStats();
  const cpi = getSeries("cpi");
  const oil = getSeries("oil_brent");
  const gold = getSeries("gold");
  const broadComm = getSeries("broad_commodity");
  const dxy = getSeries("dxy");

  const overall = overallDejavuScore();
  const verdicts = verdictCounts();
  const { strongest, weakest } = topSimsAndDiffs();
  const dStats = overall.stats || { similarity: {avg:0}, break: {avg:0}, importance: {avg:0} };

  // Use the long-history oil series for the historical chart (covers 1973 & 1979 shocks)
  const oilLong = getSeries("oil_wti_long");
  const realOil = deflate((oilLong?.observations || oil?.observations || []), cpi?.observations || [], 2024);
  const cpiYoy = yoyPct(cpi?.observations || []);
  const coreCpi = getSeries("core_cpi");

  const renderChart = (props) => <div dangerouslySetInnerHTML={{ __html: Chart({ ...props, lang }) }} />;

  const pick = (obj) => (obj && typeof obj === "object" ? (obj[lang] || obj.vi || obj.en) : obj);
  const pillLabel = (v) => {
    const map = { vi: { "Tương đồng mạnh": "Tương đồng mạnh", "Tương đồng trung bình": "Tương đồng trung bình", "Tương đồng yếu": "Tương đồng yếu", "Tương đồng bề mặt": "Tương đồng bề mặt", "Khác biệt chi phối": "Khác biệt chi phối", "Không đủ bằng chứng": "Không đủ bằng chứng" }, en: { "Tương đồng mạnh": "Strong similarity", "Tương đồng trung bình": "Medium similarity", "Tương đồng yếu": "Weak similarity", "Tương đồng bề mặt": "Surface similarity", "Khác biệt chi phối": "Differences dominate", "Không đủ bằng chứng": "Insufficient evidence" } };
    return map[lang][v] || v;
  };
  const pillClass = { "Tương đồng mạnh": "strong", "Tương đồng trung bình": "medium", "Tương đồng yếu": "weak", "Tương đồng bề mặt": "surface", "Khác biệt chi phối": "divergent", "Không đủ bằng chứng": "insufficient" };
  const confLabel = { High: lang === "vi" ? "Cao" : "High", Medium: lang === "vi" ? "Trung bình" : "Medium", Low: lang === "vi" ? "Thấp" : "Low" };

  const regimes = lang === "vi" ? [
    { title: "1 · AI Productivity Disinflation", body: "AI nâng năng suất; chuỗi cung ứng ổn định; năng lượng bình ổn; Fed giảm dần. Đường '1990s-lite' ĐẢO NGƯỢC 1970s.", conf: "Xác nhận: năng suất nonfarm >2%, ULC phẳng, core services ex-shelter hạ." },
    { title: "2 · Stagflation-lite 1970s", body: "Cú sốc dầu/thực phẩm; phân mảnh chuỗi cung ứng; tiền lương dính; tăng trưởng yếu; Fed kẹt. Kết quả déjà vu trực tiếp nhất.", conf: "Xác nhận: khoảng cách headline/core mở rộng; thất nghiệp tăng trong khi CPI >4%." },
    { title: "3 · Fiscal Dominance & Tái định giá trái phiếu", body: "Thâm hụt lớn + phát hành Treasury nặng + cầu nước ngoài yếu → term premium tăng; lợi suất dài vẫn cao ngay cả khi Fed giảm.", conf: "Xác nhận: 10Y > Fed funds trong cắt; ACM term premium dương dai dẳng; dollar yếu." },
    { title: "4 · Yen-Carry Unwind / Cú sốc hàng hóa", body: "BOJ tăng; yen tăng nhanh; deleverage carry; trùng gián đoạn hàng hóa (Hormuz, thời tiết). Chế độ khuếch đại biến động.", conf: "Xác nhận: USD/JPY phá vỡ dưới 140 với tốc độ; VIX spike >30; index hàng hóa +15% trong 3T." },
  ] : [
    { title: "1 · AI Productivity Disinflation", body: "AI lifts productivity; supply chains stable; energy calm; Fed cuts gradually. The \"1990s-lite\" path that INVERTS the 1970s.", conf: "Confirmation: nonfarm productivity >2%, unit labor cost flattening, core services ex-shelter falling." },
    { title: "2 · 1970s-lite Stagflation", body: "Oil or food shocks; fragmented supply chains; wages sticky; growth weak; Fed boxed in. The most direct déjà vu outcome.", conf: "Confirmation: headline/core gap re-widens; unemployment rises while CPI stays >4%." },
    { title: "3 · Fiscal Dominance & Bond Repricing", body: "Large deficits + heavy Treasury issuance + weak foreign demand → term premium rises; long yields stay high even as Fed cuts.", conf: "Confirmation: 10Y yield > Fed funds even during cuts; ACM term premium persistently positive; dollar weak." },
    { title: "4 · Yen-Carry Unwind / Commodity Shock", body: "BOJ hikes; yen surges; leveraged carry unwinds; coincident commodity disruption (Hormuz, weather). Volatility amplifier regime.", conf: "Confirmation: USD/JPY breaks below 140 with speed; VIX spike > 30; commodity index +15% in 3M." },
  ];

  return (
    <div>
      <section className="hero">
        <div className="container">
          <span className="eyebrow">{lang === "vi" ? "Nghiên cứu vĩ mô lịch sử · v1.4 · cập nhật" : "Macro-historical research · v1.4 · updated"} {stats.fetched_at?.slice(0,10)}</span>
          <h1>{t("hero_title")}</h1>
          <p className="sub">{t("hero_sub")}</p>
          <div className="thesis">
            <strong>{t("hero_thesis_label")}</strong> {t("hero_thesis")}<em>{t("hero_thesis_emph")}</em>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <h2>{lang === "vi" ? "Tóm tắt nhanh" : "At a glance"}</h2>
          <div className="grid-3">
            <div className="stat">
              <div className="label">{lang === "vi" ? "Analogy Similarity (TB / 5)" : "Analogy Similarity (avg / 5)"}</div>
              <div className="value">{dStats.similarity.avg.toFixed(2)}</div>
              <div className="note">{lang === "vi" ? "Hai thời kỳ giống nhau đến đâu (thấp = khác biệt)" : "How alike the two periods are (low = different)"}</div>
            </div>
            <div className="stat">
              <div className="label">{lang === "vi" ? "Structural Break Severity (TB / 5)" : "Structural Break Severity (avg / 5)"}</div>
              <div className="value" style={{color: "var(--warn)"}}>{dStats.break.avg.toFixed(2)}</div>
              <div className="note">{lang === "vi" ? "Khác biệt phá phép so sánh đến đâu (cao = analogy thất bại)" : "How much differences break the analogy (high = analogy fails)"}</div>
            </div>
            <div className="stat">
              <div className="label">{lang === "vi" ? "Regime Importance (TB / 5)" : "Regime Importance (avg / 5)"}</div>
              <div className="value" style={{color: "var(--accent)"}}>{dStats.importance.avg.toFixed(2)}</div>
              <div className="note">{lang === "vi" ? "Biến số quan trọng với thị trường hiện tại (cao = theo dõi chặt)" : "How important this variable is now (high = watch closely)"}</div>
            </div>
          </div>
          <p style={{fontSize: 13, color: "var(--fg-muted)", marginTop: 12}}>
            {lang === "vi"
              ? "Ba chỉ số độc lập — không gộp thành một con số. Ví dụ: Nợ công có Similarity=1 (rất khác), Break=5 (phá analogy cực mạnh), Importance=5 (quan trọng nhất). Cái cũ 4.5/5 đã trộn lẫn ba khái niệm này."
              : "Three independent indices — not collapsed to one number. Example: Public debt has Similarity=1 (very different), Break=5 (extreme analogy break), Importance=5 (most important). The old 4.5/5 conflated these three concepts."}
          </p>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <h2>{lang === "vi" ? "Hai episode lạm phát" : "Two inflation episodes"}</h2>
          <p>{lang === "vi"
            ? "Great Inflation 1970s thấy CPI headline đỉnh trên 14% năm 1980; cú sốc 2021–22 đỉnh gần 9%. Déjà vu cấp bề mặt rõ ràng. Câu hỏi cấu trúc là liệu wage–price dynamics, kỳ vọng và quyền công đoàn — bộ khuếch đại dai dẳng 1970s — có mặt hôm nay."
            : "The 1970s Great Inflation saw headline CPI peak above 14% in 1980; the 2021–22 surge peaked near 9%. Surface-level déjà vu is obvious. The structural question is whether wage–price dynamics, expectations, and union power — the amplifiers of 1970s persistence — are present today."}</p>
          {renderChart({
            title: { vi: "CPI headline vs core Mỹ, year-over-year", en: "US headline vs core CPI, year-over-year" },
            subtitle: { vi: "1965–hiện tại. 1973–80 và 2021–24 highlight.", en: "1965–present. 1973–80 and 2021–24 highlighted." },
            series: [
              { name: { vi: "Headline CPI YoY", en: "Headline CPI YoY" }, data: filterRange(cpiYoy, "1965-01-01") },
              { name: { vi: "Core CPI YoY", en: "Core CPI YoY" }, data: filterRange(yoyPct(coreCpi?.observations || []), "1965-01-01") },
            ],
            shading: [
              { from: "1973-01-01", to: "1980-12-31", label: { vi: "Lạm phát 1970s", en: "1970s inflation" } },
              { from: "2021-01-01", to: "2024-12-31", label: { vi: "Lạm phát hậu-COVID", en: "Post-COVID inflation" } },
            ],
            zeroLine: true, yFormat: "pct", yLabel: { vi: "% YoY", en: "% YoY" },
            source: cpi?.source, sourceUrl: cpi?.source_url, updated: cpi?.updated,
            note: { vi: "Headline gồm thực phẩm & năng lượng; core loại trừ. Biến động headline phản ánh cú sốc hàng hóa trong cả hai episode.", en: "Headline includes food & energy; core strips them. Volatility of headline reflects commodity shocks in both episodes." },
          })}
        </div>
      </section>

      <section className="section">
        <div className="container">
          <h2>{lang === "vi" ? "Giá dầu thực — bộ khuếch đại cú sốc, khi đó và nay" : "Real oil price — the shock amplifier, then and now"}</h2>
          <p>{lang === "vi"
            ? "Trong $2024 deflated, Brent 2022 spike đến vùng đỉnh 1979-80. Nhưng GDP Mỹ hôm nay tiêu thụ ~60% ít dầu mỗi đơn vị output, và Mỹ là nhà sản xuất đầu ngành. Truyền dẫn cú sốc đến tăng trưởng và lạm phát cấu trúc yếu hơn."
            : "In CPI-deflated 2024 dollars, Brent in 2022 spiked to roughly the 1979–80 peak territory. But US GDP today consumes ~60% less oil per unit output, and the US is the world's largest producer. The shock's transmission to growth and inflation is structurally weaker."}</p>
          {renderChart({
            title: { vi: "Giá dầu thô thực — WTI spot, lịch sử dài (CPI-deflated, $2024/bbl)", en: "Real crude oil — WTI spot, long history (CPI-deflated, 2024 dollars)" },
            subtitle: { vi: "WTI spot từ 1946. Cú sốc 1973–74 và 1979–80 nay thực sự nhìn thấy.", en: "WTI spot from 1946. 1973–74 and 1979–80 shocks now actually visible." },
            series: [{ name: { vi: "WTI spot thực ($2024/bbl)", en: "Real WTI spot ($2024/bbl)" }, data: filterRange(realOil, "1965-01-01") }],
            shading: [
              { from: "1973-10-01", to: "1974-03-31", label: { vi: "Cấm vận 1973", en: "1973 embargo" } },
              { from: "1979-01-01", to: "1980-12-31", label: { vi: "Iran 1979", en: "Iran 1979" } },
              { from: "2022-02-01", to: "2022-12-31", label: { vi: "Ukraine", en: "Ukraine" } },
            ],
            yFormat: "usd", yLabel: { vi: "$/bbl (2024 thực)", en: "$/bbl (2024 real)" },
            source: (oilLong?.source || "FRED WTISPLC") + " · deflated by " + (cpi?.source || "CPI"), sourceUrl: oilLong?.source_url || "https://fred.stlouisfed.org/series/WTISPLC", updated: oilLong?.updated || oil?.updated,
            note: { vi: "Sửa P0: POILBREUSDM (Brent IMF) chỉ có giá trị thực từ ~1990, không phủ 1973. Dùng WTISPLC (1946–nay). Giá thực = nominal ÷ CPI × CPI(2024).", en: "P0 fix: POILBREUSDM (IMF Brent) only has usable values from ~1990, doesn't cover 1973. Using WTISPLC (1946–present). Real = nominal ÷ CPI × CPI(2024)." },
          })}

          <h3 style={{marginTop: 32}}>{lang === "vi" ? "Cụm hàng hóa chiến lược — rebase 100" : "The strategic commodity cluster — rebased to 100"}</h3>
          <p>{lang === "vi"
            ? "So sánh surge 2020s qua các hàng hóa chiến lược chính. Tất cả rebase 100 tại 1/2020. Đồng, uranium, vàng đều phá cấu trúc cao hơn — chủ đề điện khí hóa + uy tín tiền tệ."
            : "Comparing the 2020s surge across the key strategic commodities. All rebased to 100 at January 2020. Copper, uranium, and gold have all broken structurally higher — the electrification + monetary-credibility theme."}</p>
          {renderChart({
            title: { vi: "Hàng hóa chiến lược rebase (1/2020 = 100)", en: "Strategic commodities rebased (Jan 2020 = 100)" },
            subtitle: { vi: "Đồng, uranium, vàng, chỉ số hàng hóa rộng.", en: "Copper, uranium, gold, broad commodity index." },
            series: [
              { name: { vi: "Đồng", en: "Copper" }, data: filterRange(rebase(getSeries("copper")?.observations || [], "2020-01-01"), "2020-01-01") },
              { name: { vi: "Uranium", en: "Uranium" }, data: filterRange(rebase(getSeries("uranium")?.observations || [], "2020-01-01"), "2020-01-01") },
              { name: { vi: "Vàng", en: "Gold" }, data: filterRange(rebase(gold?.observations || [], "2020-01-01"), "2020-01-01") },
              { name: { vi: "Hàng hóa rộng", en: "Broad commodities" }, data: filterRange(rebase(broadComm?.observations || [], "2020-01-01"), "2020-01-01") },
            ],
            yFormat: "num", yLabel: { vi: "index (1/2020=100)", en: "index (Jan 2020=100)" },
            source: "FRED + World Bank CMO", sourceUrl: "https://fred.stlouisfed.org", updated: gold?.updated,
          })}
          {renderChart({
            title: { vi: "Dollar (DXY broad) vs vàng ($/oz)", en: "Dollar (DXY broad) vs gold ($/oz)" },
            subtitle: { vi: "Vàng tăng mặc dù dollar mạnh 2024 phá tương quan nghịch sách giáo khoa — tín hiệu uy tín tiền tệ.", en: "Gold rising despite dollar strength in 2024 broke the textbook inverse correlation — a monetary-credibility signal." },
            series: [
              { name: { vi: "Vàng ($/oz)", en: "Gold ($/oz)" }, data: filterRange(gold?.observations || [], "2020-01-01") },
              { name: { vi: "DXY broad", en: "DXY broad" }, data: filterRange(toMonthly(dxy?.observations || []), "2020-01-01") },
            ],
            yFormat: "num", yLabel: "value",
            source: `${gold?.source}; ${dxy?.source}`, sourceUrl: gold?.source_url, updated: gold?.updated,
          })}
        </div>
      </section>

      <section className="section">
        <div className="container">
          <h2>{lang === "vi" ? "Nơi vần — và nơi phá" : "Where it rhymes — and where it breaks"}</h2>
          <div className="grid-2">
            <div className="card">
              <h3 style={{marginTop: 0, color: "var(--success)"}}>{lang === "vi" ? "Năm tương đồng cao nhất (Similarity)" : "Five highest similarity"}</h3>
              <ol>
                {strongest.map((d) => (
                  <li key={d.id} style={{marginBottom: 12}}>
                    <strong>{pick(d.label)}</strong> <span className="pill strong">S={d.similarity}</span> <span style={{fontSize: 11, color: "var(--fg-muted)"}}>(B={d.break}, I={d.importance})</span>
                    <div style={{fontSize: 13, color: "var(--fg-muted)", marginTop: 2}}>{pick(d.reasoning).slice(0, 150)}…</div>
                  </li>
                ))}
              </ol>
            </div>
            <div className="card">
              <h3 style={{marginTop: 0, color: "var(--danger)"}}>{lang === "vi" ? "Năm đứt gãy mạnh nhất (Break)" : "Five biggest breaks"}</h3>
              <ol>
                {weakest.map((d) => (
                  <li key={d.id} style={{marginBottom: 12}}>
                    <strong>{pick(d.label)}</strong> <span className="pill divergent">B={d.break}</span> <span style={{fontSize: 11, color: "var(--fg-muted)"}}>(S={d.similarity}, I={d.importance})</span>
                    <div style={{fontSize: 13, color: "var(--fg-muted)", marginTop: 2}}>{pick(d.counterargument).slice(0, 150)}…</div>
                  </li>
                ))}
              </ol>
            </div>
          </div>
          <p style={{marginTop: 16, fontSize: 13, color: "var(--fg-muted)"}}>
            {lang === "vi"
              ? "S = Similarity (giống nhau), B = Break severity (phá analogy), I = Importance (quan trọng hiện tại). Điểm S thấp KHÔNG nghĩa 'ổn' — thường vì vấn đề hôm nay tồi hơn (nợ). Phá analogy cao (B cao) nghĩa là kết quả lịch sử không áp dụng được. Xem"
              : "S = Similarity, B = Break severity, I = Importance. Low S does NOT mean 'fine' — often because today's problem is worse (debt). High B means the historical outcome doesn't apply. See"} <a href="/scorecard">{lang === "vi" ? "bảng điểm đầy đủ" : "full scorecard"}</a>.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <h2>{lang === "vi" ? "Bốn chế độ mà phép so sánh gợi ý" : "Four regimes the analogy suggests"}</h2>
          <div className="grid-2">
            {regimes.map((r, i) => (
              <div key={i} className="card">
                <h3 style={{marginTop: 0}}>{r.title}</h3>
                <p style={{fontSize: 14}}>{r.body}</p>
                <p style={{fontSize: 13, color: "var(--fg-muted)"}}>{r.conf}</p>
              </div>
            ))}
          </div>
          <p style={{marginTop: 16, fontSize: 14}}><a href="/scorecard">{lang === "vi" ? "→ Dashboard kịch bản đầy đủ với trigger, xác nhận, bác bỏ" : "→ Full scenario dashboard with triggers, confirmations, invalidations"}</a></p>
        </div>
      </section>

      <section className="section">
        <div className="container">
          <h2>{lang === "vi" ? "Footprint dữ liệu" : "Data footprint"}</h2>
          <div className="grid-4">
            <div className="stat"><div className="label">{lang === "vi" ? "Series sơ cấp" : "Primary series"}</div><div className="value">{stats.ok}</div></div>
            <div className="stat"><div className="label">{lang === "vi" ? "Provider dữ liệu" : "Data providers"}</div><div className="value">{Object.keys(stats.providers).filter(p => p !== "None").length}</div></div>
            <div className="stat"><div className="label">{lang === "vi" ? "Chiều so sánh" : "Dimensions"}</div><div className="value">{DEJAVU_DIMENSIONS.length}</div></div>
            <div className="stat"><div className="label">{lang === "vi" ? "Hàng hóa" : "Commodities"}</div><div className="value">{COMMODITY_SCORECARD.length}</div></div>
          </div>
          <p style={{fontSize: 13, color: "var(--fg-muted)", marginTop: 12}}>
            {lang === "vi"
              ? "Mỗi biểu đồ trích nguồn; mỗi nhận định gắn nhãn độ tin cậy. Không dữ liệu giả, không giá trị placeholder. Nơi thiếu series sơ cấp, biểu đồ nói rõ. Xem"
              : "Every chart cites its source; every claim carries a confidence label. No fabricated data, no placeholder values. Where a primary series was unavailable the chart states so explicitly. See"} <a href="/sources">{lang === "vi" ? "registry nguồn" : "source registry"}</a> {lang === "vi" ? "và" : "and"} <a href="/about">{lang === "vi" ? "phương pháp" : "methodology"}</a>.
          </p>
        </div>
      </section>
    </div>
  );
}
