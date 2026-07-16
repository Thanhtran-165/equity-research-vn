"use client";
import { useLang } from "../../components/LangProvider.jsx";
import { DEJAVU_DIMENSIONS, overallDejavuScore, verdictCounts, verdict2D } from "../../data/dejavu_scores.mjs";
import { SCENARIOS } from "../../data/scenarios.mjs";
import { getSeries } from "../../lib/data_loader.mjs";
import { Chart } from "../../components/Chart.mjs";
import { filterRange, toMonthly, yoyPct, deflate } from "../../lib/transforms.mjs";

const VERDICT_PILL = {
  "Tương đồng mạnh": "strong", "Tương đồng trung bình": "medium", "Tương đồng yếu": "weak",
  "Tương đồng bề mặt": "surface", "Khác biệt chi phối": "divergent", "Không đủ bằng chứng": "insufficient",
};

export default function ScorecardPage() {
  const { lang } = useLang();
  const overall = overallDejavuScore();
  const dStats = overall.stats;
  const verdicts = verdictCounts();
  const pick = (obj) => (obj && typeof obj === "object" ? (obj[lang] || obj.vi || obj.en) : obj);
  const pillLabel = (v) => {
    const map = { vi: { "Tương đồng mạnh": "Tương đồng mạnh", "Tương đồng trung bình": "Tương đồng trung bình", "Tương đồng yếu": "Tương đồng yếu", "Tương đồng bề mặt": "Tương đồng bề mặt", "Khác biệt chi phối": "Khác biệt chi phối", "Không đủ bằng chứng": "Không đủ bằng chứng" }, en: { "Tương đồng mạnh": "Strong similarity", "Tương đồng trung bình": "Medium similarity", "Tương đồng yếu": "Weak similarity", "Tương đồng bề mặt": "Surface similarity", "Khác biệt chi phối": "Differences dominate", "Không đủ bằng chứng": "Insufficient evidence" } };
    return map[lang][v] || v;
  };
  const confLabel = (c) => ({ High: lang === "vi" ? "Cao" : "High", Medium: lang === "vi" ? "Trung bình" : "Medium", Low: lang === "vi" ? "Thấp" : "Low" })[c] || c;
  const renderChart = (props) => <div dangerouslySetInnerHTML={{ __html: Chart({ ...props, lang }) }} />;
  const debt = getSeries("federal_debt_total"); const fedfunds = getSeries("fedfunds");
  const gold = getSeries("gold"); const cpi = getSeries("cpi");
  const realGold = deflate(gold?.observations || [], cpi?.observations || [], 2024);
  const usdJpy = getSeries("usd_jpy");

  return (
    <div>
      <section className="hero" style={{padding: "40px 0 24px"}}>
        <div className="container">
          <span className="eyebrow">{lang === "vi" ? "Dashboard A · Déjà Vu Similarity Score" : "Dashboard A · Déjà Vu Similarity Score"}</span>
          <h1 style={{fontSize: 32}}>{lang === "vi" ? "Bảng điểm 16 chiều" : "The 16-dimension scorecard"}</h1>
          <p className="sub" style={{fontSize: 16}}>
            {lang === "vi"
              ? "Mỗi chiều chấm trên Hiện tượng, Cấu trúc, Cơ chế và Kết quả (mỗi cái 0-5). Trọng số 0.20·P + 0.30·S + 0.30·M + 0.20·O — cấu trúc và cơ chế mang nhiều trọng số hơn hiện tượng bề mặt vì đó là nơi phép so sánh thường phá."
              : "Each dimension scored on Phenomenon, Structure, Mechanism, and Outcome (each 0–5). Weighted 0.20·P + 0.30·S + 0.30·M + 0.20·O — structure and mechanism carry more weight than surface phenomenon because that's where analogies usually break."}
          </p>
        </div>
      </section>

      <section className="section" style={{paddingTop: 24}}>
        <div className="container">
          <div className="grid-3" style={{marginBottom: 24}}>
            <div className="stat">
              <div className="label">{lang === "vi" ? "Analogy Similarity (TB / 5)" : "Analogy Similarity (avg / 5)"}</div>
              <div className="value">{dStats.similarity.avg.toFixed(2)}</div>
              <div className="scorebar"><div className="scorebar-track"><div className="scorebar-fill" style={{width: `${(dStats.similarity.avg/5)*100}%`}}/></div></div>
              <div className="note">{lang === "vi" ? "Hai thời kỳ giống nhau đến đâu" : "How alike the two periods are"}</div>
            </div>
            <div className="stat">
              <div className="label">{lang === "vi" ? "Structural Break (TB / 5)" : "Structural Break (avg / 5)"}</div>
              <div className="value" style={{color: "var(--warn)"}}>{dStats.break.avg.toFixed(2)}</div>
              <div className="scorebar"><div className="scorebar-track"><div className="scorebar-fill" style={{width: `${(dStats.break.avg/5)*100}%`}}/></div></div>
              <div className="note">{lang === "vi" ? "Khác biệt phá phép so sánh đến đâu" : "How much differences break the analogy"}</div>
            </div>
            <div className="stat">
              <div className="label">{lang === "vi" ? "Regime Importance (TB / 5)" : "Regime Importance (avg / 5)"}</div>
              <div className="value" style={{color: "var(--accent)"}}>{dStats.importance.avg.toFixed(2)}</div>
              <div className="scorebar"><div className="scorebar-track"><div className="scorebar-fill" style={{width: `${(dStats.importance.avg/5)*100}%`}}/></div></div>
              <div className="note">{lang === "vi" ? "Quan trọng với thị trường hiện tại" : "Important for the current regime"}</div>
            </div>
          </div>
          <p style={{fontSize: 13, color: "var(--fg-muted)", marginBottom: 24}}>
            {lang === "vi"
              ? "Ba chỉ số độc lập. Cái cũ (3.29/5) đã trộn 'giống nhau', 'khác biệt lớn' và 'mức độ quan trọng' thành một con số vô nghĩa. Ví dụ: Nợ công S=1 (rất khác), B=5 (phá analogy cực mạnh), I=5 (quan trọng nhất)."
              : "Three independent indices. The old single score (3.29/5) conflated 'alike', 'different' and 'important' into one meaningless number. Example: Public debt S=1 (very different), B=5 (extreme break), I=5 (most important)."}
          </p>

          <div className="card">
            <h2 style={{marginTop: 0}}>{lang === "vi" ? "Phân tích từng chiều (3 chỉ số độc lập)" : "Per-dimension breakdown (3 independent indices)"}</h2>
            <p style={{fontSize: 12, color: "var(--fg-muted)"}}>S = Similarity (0=khác biệt, 5=giống). B = Break severity (0=analogy giữ, 5=analogy phá). I = Importance (0=không quan trọng, 5=trung tâm).</p>
            <table>
              <thead>
                <tr>
                  <th>{lang === "vi" ? "Chiều" : "Dimension"}</th>
                  <th className="num">S</th><th className="num">B</th><th className="num">I</th>
                  <th>{lang === "vi" ? "Phán quyết" : "Verdict"}</th>
                  <th>{lang === "vi" ? "Độ tin cậy" : "Confidence"}</th>
                </tr>
              </thead>
              <tbody>
                {DEJAVU_DIMENSIONS.map((d) => {
                  const v2 = verdict2D(d);
                  return (
                    <tr key={d.id}>
                      <td><strong>{pick(d.label)}</strong><div style={{fontSize: 11, color: "var(--fg-muted)"}}>{lang === "vi" ? "bằng chứng" : "evidence"}: {d.data_points.join(", ")}</div></td>
                      <td className="num"><strong style={{color: "var(--success)"}}>{d.similarity}</strong></td>
                      <td className="num"><strong style={{color: d.break >= 4 ? "var(--danger)" : "var(--warn)"}}>{d.break}</strong></td>
                      <td className="num"><strong style={{color: "var(--accent)"}}>{d.importance}</strong></td>
                      <td><span className={`pill ${v2.cls}`}>{pick(v2)}</span></td>
                      <td><span className={`confidence ${d.confidence}`}>{confLabel(d.confidence)}</span></td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>

          <h2 style={{marginTop: 40}}>{lang === "vi" ? "Vì sao mỗi chiều chấm như vậy" : "Why each dimension scored the way it did"}</h2>
          {DEJAVU_DIMENSIONS.map((d) => {
            const v2 = verdict2D(d);
            return (
              <div key={d.id} className="card" style={{marginBottom: 16}}>
                <div style={{display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 8}}>
                  <h3 style={{margin: 0}}>{pick(d.label)}</h3>
                  <div style={{display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap"}}>
                    <span style={{fontSize: 13}}>S=<strong style={{color: "var(--success)"}}>{d.similarity}</strong></span>
                    <span style={{fontSize: 13}}>B=<strong style={{color: "var(--warn)"}}>{d.break}</strong></span>
                    <span style={{fontSize: 13}}>I=<strong style={{color: "var(--accent)"}}>{d.importance}</strong></span>
                    <span className={`pill ${v2.cls}`}>{pick(v2)}</span>
                    <span className={`confidence ${d.confidence}`}>{confLabel(d.confidence)}</span>
                  </div>
                </div>
                <div style={{fontSize: 13, color: "var(--fg-muted)", margin: "6px 0"}}>{pick(d.rubric)}</div>
                <div style={{margin: "12px 0"}}>
                  <strong style={{fontSize: 13, color: "var(--success)"}}>{lang === "vi" ? "Lập luận." : "Reasoning."}</strong>{" "}
                  <span style={{fontSize: 14}}>{pick(d.reasoning)}</span>
                </div>
                <div>
                  <strong style={{fontSize: 13, color: "var(--danger)"}}>{lang === "vi" ? "Phản biện." : "Counterargument."}</strong>{" "}
                  <span style={{fontSize: 14}}>{pick(d.counterargument)}</span>
                </div>
              </div>
            );
          })}

          <h2 style={{marginTop: 40}}>{lang === "vi" ? "Bằng chứng hình ảnh tổng hợp" : "Aggregate visual evidence"}</h2>
          <div className="grid-2">
            {renderChart({ title: { vi: "Nợ liên bang / GDP (%)", en: "Federal debt / GDP (%)" }, subtitle: { vi: "Đứt gãy cấu trúc lớn nhất từ 1970s.", en: "The single biggest structural break from the 1970s." }, series: [{ name: { vi: "Nợ/GDP", en: "Debt/GDP" }, data: filterRange(debt?.observations || [], "1965-01-01") }], yFormat: "num", yLabel: { vi: "% GDP", en: "% of GDP" }, source: debt?.source, sourceUrl: debt?.source_url, updated: debt?.updated })}
            {renderChart({ title: { vi: "Vàng thực ($/oz, $2024)", en: "Real gold ($/oz, 2024 dollars)" }, subtitle: { vi: "Mua ngân hàng trung ương + lo ngại tài khóa — vàng phản ánh uy tín tiền tệ, không CPI.", en: "Central-bank buying + fiscal concern — gold reflects monetary credibility, not CPI." }, series: [{ name: { vi: "Vàng thực", en: "Real gold" }, data: filterRange(realGold, "1965-01-01") }], yFormat: "usd", yLabel: { vi: "$/oz (2024 thực)", en: "$/oz (2024 real)" }, source: gold?.source, sourceUrl: gold?.source_url, updated: gold?.updated })}
            {renderChart({ title: { vi: "Fed Funds rate (%)", en: "Fed Funds rate (%)" }, subtitle: { vi: "Hai chu kỳ thắt chặt lớn: Volcker (1979-81) và Powell (2022-24).", en: "Two great tightening cycles: Volcker (1979–81) and Powell (2022–24)." }, series: [{ name: "Fed Funds", data: filterRange(fedfunds?.observations || [], "1965-01-01") }], shading: [{ from: "1979-08-01", to: "1982-12-31", label: "Volcker" }, { from: "2022-03-01", to: "2024-12-31", label: "2022–24" }], yFormat: "pct", yLabel: "%", source: fedfunds?.source, sourceUrl: fedfunds?.source_url, updated: fedfunds?.updated })}
            {renderChart({ title: { vi: "USD/JPY (¥ mỗi $)", en: "USD/JPY (¥ per $)" }, subtitle: { vi: "Rủi ro carry unwind yen: đảo chiều 2024 là preview sách giáo khoa 5/8.", en: "Yen carry unwind risk: 2024 reversal was a textbook preview on Aug 5." }, series: [{ name: "USD/JPY", data: filterRange(toMonthly(usdJpy?.observations || []), "1970-01-01") }], yFormat: "num", yLabel: { vi: "JPY/$", en: "JPY/$" }, source: usdJpy?.source, sourceUrl: usdJpy?.source_url, updated: usdJpy?.updated })}
          </div>

          <h2 style={{marginTop: 40}}>{lang === "vi" ? "Sáu kịch bản · trigger & bác bỏ" : "Six scenarios · triggers & invalidations"}</h2>
          <p style={{fontSize: 14, color: "var(--fg-muted)"}}>{lang === "vi" ? "Không gán xác suất. Mỗi kịch bản liệt kê điều gì sẽ xác nhận hay bác bỏ." : "No probabilities assigned. Each scenario lists what would confirm or refute it."}</p>
          <div className="grid-2">
            {SCENARIOS.map((s) => (
              <div key={s.id} className="card" style={{marginBottom: 16}}>
                <h3 style={{marginTop: 0}}>{pick(s.name)}</h3>
                <p style={{fontSize: 13, color: "var(--fg-muted)"}}>{pick(s.narrative)}</p>
                <div style={{fontSize: 13, margin: "8px 0"}}><strong style={{color: "var(--warn)"}}>{lang === "vi" ? "Trigger." : "Trigger."}</strong> {pick(s.trigger)}</div>
                <div style={{fontSize: 13, margin: "4px 0"}}><strong style={{color: "var(--success)"}}>{lang === "vi" ? "Xác nhận." : "Confirmation."}</strong> {pick(s.confirmation)}</div>
                <div style={{fontSize: 13, margin: "4px 0"}}><strong style={{color: "var(--danger)"}}>{lang === "vi" ? "Bác bỏ." : "Invalidation."}</strong> {pick(s.invalidation)}</div>
                <div style={{fontSize: 13, margin: "4px 0"}}><strong>{lang === "vi" ? "Độ nhạy tài sản." : "Asset sensitivity."}</strong> {pick(s.asset_sensitivity)}</div>
                <div style={{fontSize: 13, margin: "4px 0"}}><strong>{lang === "vi" ? "Tương đồng lịch sử." : "Historical analogue."}</strong> {pick(s.historical_analogue)}</div>
                <div style={{fontSize: 13}}><span className={`confidence ${s.confidence}`}>{lang === "vi" ? "Độ tin cậy" : "Confidence"}: {confLabel(s.confidence)}</span></div>
              </div>
            ))}
          </div>
        </div>
      </section>
    </div>
  );
}
