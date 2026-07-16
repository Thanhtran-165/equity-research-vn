// src/components/ChapterContent3.jsx
// Chapters 5-9, 11-16, 18 — bilingual, condensed but complete.
import { getSeries } from "../lib/data_loader.mjs";
import { filterRange, yoyPct, deflate, toMonthly, drawdown, rebase } from "../lib/transforms.mjs";
import { useLang } from "./LangProvider.jsx";
import { Part, ChartBlock, Shell, buildReal } from "./ChapterContent.jsx";
import { lab } from "../data/labels.mjs";
import { verdict2D, DEJAVU_DIMENSIONS } from "../data/dejavu_scores.mjs";

function VerdictPill({ id, lang }) {
  const d = DEJAVU_DIMENSIONS.find((x) => x.id === id);
  if (!d) return null;
  const v = verdict2D(d);
  const text = typeof v === "object" ? (v[lang] || v.vi || v.en) : v;
  const cls = typeof v === "object" ? v.cls : "medium";
  return <span className={`pill ${cls}`}>{text}</span>;
}

// Helper to render a chapter from a compact spec
function SpecChapter({ num, spec, lang }) {
  const cpi = getSeries("cpi");
  return (
    <Shell num={num} title={spec.title[lang]} hypotheses={spec.hypotheses} lang={lang}>
      {spec.parts.map((p, i) => (
        <Part key={i} label={lab(p.label, lang)} color={p.color}>
          {typeof p.body === "string" ? <p>{p.body[lang] || p.body}</p> : p.body}
        </Part>
      ))}
      {spec.charts?.map((ch, i) => (
        <Part key={`c${i}`} label={lab("data", lang)} color="data">
          <ChartBlock lang={lang} props={ch} />
        </Part>
      ))}
    </Shell>
  );
}

// ===== Chapter 5 =====
export function Chapter05() {
  const { lang } = useLang();
  const ff = getSeries("fedfunds"); const coreCpi = getSeries("core_cpi");
  const realFF = (() => {
    const f = ff?.observations || []; const cc = yoyPct(coreCpi?.observations || []);
    return f.map((r) => {
      const cAt = cc.find((x) => x.date.slice(0,7) === r.date.slice(0,7));
      return cAt ? { date: r.date, value: r.value - cAt.value } : null;
    }).filter(Boolean);
  })();
  return (
    <Shell num="05" title={lang === "vi" ? "Fed, Volcker và chính sách stop–go" : "Fed, Volcker, and stop–go policy"} hypotheses={["H4", "H5"]} lang={lang}>
      <Part label={lab("question", lang)} color="Q"><p>{lang === "vi"
        ? "Fed hôm nay có thể lặp lại quyết tâm chống lạm phát của Volcker, hay khả năng chịu lãi suất của nền kinh tế giảm xa đến mức Volcker-tương đương là không thể về tài khóa?"
        : "Could the Fed today repeat Volcker's anti-inflation resolve, or has the economy's interest-rate tolerance fallen so far that a Volcker-equivalent is fiscally impossible?"}</p></Part>
      <Part label={lab("history", lang)} color="history"><p>{lang === "vi"
        ? "Arthur Burns (1970–78) thực hành stop-go: thắt chặt rồi nhượng bộ áp lực chính trị, tạo tâm lý 'Great Inflation'. G. William Miller (1978–79) tiếp tục pattern. Paul Volcker (1979–87) phá vỡ: monetary targeting, ~20% funds rate, hai suy thoái (1980, 1981–82), và phá hủy kỳ vọng lạm phát. Chi phí cao nhưng premium uy tín tồn tại đến nay."
        : "Arthur Burns (1970–78) practiced stop-go: tightening then yielding to political pressure, generating the \"Great Inflation\" psychology. G. William Miller (1978–79) continued the pattern. Paul Volcker (1979–87) broke it: monetary targeting, ~20% funds rate, two recessions (1980, 1981–82), and the destruction of inflation expectations. The cost was steep but the credibility premium persists to this day."}</p></Part>
      <Part label={lab("now", lang)} color="now"><p>{lang === "vi"
        ? "Fed 2022–24 tăng 525bp — tương đương quy mô tích lũy với thắt chặt Volcker, nhưng đỉnh ~5.5% vs ~20% Volcker. Theo thuật ngữ thực, stance tương tự. Quan trọng: lạm phát hạ không suy thoái — kết quả tốt hơn 1979–82."
        : "The 2022–24 Fed hiked 525bp — comparable in cumulative magnitude to Volcker's tightening, but peaking at ~5.5% vs Volcker's ~20%. In real terms the stance was similar. Crucially, inflation fell without recession — a better outcome than 1979–82."}</p></Part>
      <Part label={lab("same", lang)} color="same"><ul>
        <li>{lang === "vi" ? "Chu kỳ thắt chặt sắc against cú sốc lạm phát lớn." : "Sharp tightening cycle against a major inflation shock."}</li>
        <li>{lang === "vi" ? "Lãi suất chính sách thực rõ ràng dương — định nghĩa hoạt động của chính sách hạn chế." : "Real policy rate turned clearly positive — the operative definition of restrictive policy."}</li>
        <li>{lang === "vi" ? "Uy tín ngân hàng trung ương triển khai như công cụ chống lạm phát chính." : "Central-bank credibility deployed as the primary anti-inflation tool."}</li>
      </ul></Part>
      <Part label={lab("diff", lang)} color="diff"><ul>
        <li><strong>{lang === "vi" ? "Mức nợ." : "Debt level."}</strong> {lang === "vi" ? "Nợ liên bang/GDP ~30% năm 1980 vs ~120% hôm nay — cùng lãi suất danh nghĩa có chi phí phục vụ tài khóa ~4×." : "Federal debt/GDP ~30% in 1980 vs ~120% today — same nominal rate has ~4× the fiscal servicing cost."}</li>
        <li><strong>{lang === "vi" ? "Không stop-go kiểu Burns." : "No Burns-style stop-go."}</strong> {lang === "vi" ? "Fed 2022 giữ vững; Fed 1974 nhượng bộ. Ký ức tổ chức về 1970s là tài sản uy tín." : "The 2022 Fed held the line; the 1974 Fed caved. The institutional memory of the 1970s is itself a credibility asset."}</li>
        <li><strong>{lang === "vi" ? "Kỳ vọng neo." : "Expectations anchored."}</strong> {lang === "vi" ? "Phần khó của trận Volcker — neo lại kỳ vọng — đã làm xong." : "The hard part of the Volcker fight — re-anchoring expectations — was already done."}</li>
        <li><strong>{lang === "vi" ? "Forward guidance & truyền thông." : "Forward guidance & communications."}</strong> {lang === "vi" ? "Toolkit Fed hiện đại phát triển hơn nhiều." : "Modern Fed toolkit is far more developed."}</li>
      </ul></Part>
      <Part label={lab("data", lang)} color="data">
        <ChartBlock lang={lang} props={{
          title: { vi: "Fed Funds effective rate (%)", en: "Fed Funds effective rate (%)" },
          series: [{ name: "Fed Funds", data: filterRange(ff?.observations || [], "1965-01-01") }],
          shading: [{ from: "1979-08-01", to: "1982-12-31", label: { vi: "Cú sốc Volcker", en: "Volcker shock" } }, { from: "2022-03-01", to: "2024-12-31", label: { vi: "Tăng hậu-COVID", en: "Post-COVID hikes" } }],
          yFormat: "pct", yLabel: "%",
          source: ff?.source, sourceUrl: ff?.source_url, updated: ff?.updated,
        }}/>
        <ChartBlock lang={lang} props={{
          title: { vi: "Real Fed Funds (Fed Funds − core CPI YoY, %)", en: "Real Fed Funds (Fed Funds − core CPI YoY, %)" },
          subtitle: { vi: "Cả hai episode đẩy lãi suất chính sách thực rõ ràng dương — test hoạt động của restrictiveness.", en: "Both episodes pushed real policy rates clearly positive — the operative test of restrictiveness." },
          series: [{ name: "Real FF", data: filterRange(realFF, "1965-01-01") }],
          shading: [{ from: "1979-08-01", to: "1982-12-31", label: "Volcker" }, { from: "2022-03-01", to: "2024-12-31", label: "2022–24" }],
          zeroLine: true, yFormat: "pct", yLabel: "%",
          source: `${ff?.source} + ${coreCpi?.source}`, sourceUrl: ff?.source_url, updated: ff?.updated,
          note: { vi: "Real FF = Fed Funds danh nghĩa − core CPI YoY. Dương = hạn chế thực.", en: "Real FF = nominal Fed Funds − core CPI YoY. Positive = restrictive in real terms." },
        }}/>
      </Part>
      <Part label={lab("rebuttal", lang)} color="rebuttal">
        <p>{lang === "vi"
          ? "Lý do 20% funds rate không thể hôm nay không phải ý chí chính trị — là toán tài khóa. Ở 120% nợ/GDP, chi phí lãi của 20% funds rate sẽ tiêu bội số doanh thu liên bang trong một năm. Tùy chọn cú sốc kiểu Volcker đã nghỉ hưu bởi build-up nợ. Nghĩa là: nếu lạm phát tăng tốc lại, công cụ Fed hạn chế hơn 1979 — uy tín phải làm nhiều việc hơn với đạn dược lãi suất ít hơn."
          : "The reason a 20% funds rate is impossible today is not political will — it is fiscal math. At 120% debt/GDP, the interest expense of a 20% funds rate would consume a multiple of federal revenue within a year. The option of a Volcker-style shock has been retired by the debt build-up. This means: if inflation re-accelerates, the Fed's tools are more constrained than in 1979 — credibility is doing more of the work with less rate ammunition."}</p>
      </Part>
      <Part label={lab("concl", lang)} color="concl">
        <p>{lang === "vi"
          ? "Fed 2022 uy tín cao hơn và kết quả tốt hơn Volcker — setup hôm nay phân kỳ thuận lợi khỏi tham chiếu 1979–82. Nhưng bộ tùy chọn cho cú sốc tương lai hẹp hơn (ràng buộc nợ). Déjà vu trong rủi ro, không phải đường đã thực hiện. "
          : "The 2022 Fed had higher credibility and a better outcome than Volcker — meaning today's setup diverges favorably from the 1979–82 reference. But the option set for a future shock is narrower (debt constraint). The déjà vu is in the risk, not the realized path. "}<VerdictPill id="monetary" lang={lang} /></p>
      </Part>
      <Part label={lab("inv", lang)} color="inv">
        <p>{lang === "vi"
          ? "Nếu uy tín giữ, lợi suất danh nghĩa có thể normalize không xoáy nợ — trái phiếu lấy lại vai hedge. Nếu sóng lạm phát thứ hai đến, toolkit chính sách hạn chế ủng hộ tài sản thực (vàng, TIPS, hàng hóa) hơn trái phiếu danh nghĩa dài."
          : "If credibility holds, nominal yields can normalize without a debt spiral — bonds resume hedge role. If a second inflation wave arrives, the constrained policy toolkit favors real assets (gold, TIPS, commodities) over long-duration nominal bonds."}</p>
      </Part>
      <Part label={lab("conf", lang)} color="conf">
        <p><span className="confidence Medium">{lang === "vi" ? "Trung bình" : "Medium"}</span> {lang === "vi" ? "— lập luận uy tín vững nhưng chưa test bởi sóng thứ hai; ràng buộc nợ là số học nhưng ý nghĩa chính sách tranh cãi." : "— credibility argument is sound but untested by a second wave; debt constraint is arithmetic but its policy implications are debated."}</p>
      </Part>
    </Shell>
  );
}

// ===== Chapter 6 — DEBT =====
export function Chapter06() {
  const { lang } = useLang();
  const debt = getSeries("federal_debt_total"); const deficit = getSeries("deficit");
  const tp = getSeries("term_premium"); const y10y = getSeries("y10y_treasury");
  return (
    <Shell num="06" title={lang === "vi" ? "Nợ Mỹ, Treasury và fiscal dominance" : "US debt, Treasury, and fiscal dominance"} hypotheses={["H6"]} lang={lang}>
      <Part label={lab("question", lang)} color="Q"><p>{lang === "vi"
        ? "Tư thế tài khóa Mỹ đã đủ lớn để làm suy yếu độc lập chính sách tiền tệ — và term premium có thể tăng ngay cả khi Fed giảm?"
        : "Has US fiscal posture grown large enough to compromise the independence of monetary policy — and could term premium rise even as the Fed cuts?"}</p></Part>
      <Part label={lab("history", lang)} color="history"><p>{lang === "vi"
        ? "Nợ liên bang/GDP ~30% năm 1980, giảm qua cuối 1990s, rồi tăng đều qua 2008, COVID và hậu-2020 đến ~120%+ hôm nay. Chi phí lãi nay là khoản ngân sách top-line. 1970s gánh nặng nợ nhẹ; fiscal dominance không phải ràng buộc cho Volcker."
        : "Federal debt/GDP was ~30% in 1980, fell through the late 1990s, then rose steadily through 2008, COVID, and the post-2020 era to ~120%+ today. Interest expense is now a top-line budget item. In the 1970s the debt burden was light; fiscal dominance was not a binding constraint on Volcker."}</p></Part>
      <Part label={lab("now", lang)} color="now"><p>{lang === "vi"
        ? "Thâm hụt ~6% GDP với thất nghiệp ~4% — cấu trúc bất thường; thâm hụt lớn thế này thường xuất hiện trong suy thoái. Phát hành Treasury nặng; bid nước ngoài hỗn hợp. ACM term premium, âm sâu phần lớn 2010s, đã tròn lại về vùng dương."
        : "Deficit ~6% of GDP with unemployment ~4% — structurally unusual; deficits this large normally appear in recession. Treasury issuance is heavy; foreign bid is mixed. The ACM term premium, deeply negative for most of 2010s, has re-rounded toward positive territory."}</p></Part>
      <Part label={lab("same", lang)} color="same"><ul>
        <li>{lang === "vi" ? "Phát hành danh nghĩa nặng trong episode lạm phát cao." : "Heavy nominal issuance during a high-inflation episode."}</li>
        <li>{lang === "vi" ? "Lợi suất dài tăng ngay cả khi lãi suất chính sách ngân hàng trung ương đỉnh (vang vọng back-up 1970s)." : "Long yields rising even as the central bank's policy rate peaks (echoes of the 1970s back-up)."}</li>
      </ul></Part>
      <Part label={lab("diff", lang)} color="diff"><ul>
        <li><strong>{lang === "vi" ? "Quy mô nợ." : "Debt scale."}</strong> {lang === "vi" ? "Nợ/GDP cao hơn 4× so với 1980; cùng lãi suất có chi phí phục vụ 4×." : "4× higher debt/GDP than 1980; same rate has 4× the servicing cost."}</li>
        <li><strong>{lang === "vi" ? "Nắm giữ nước ngoài." : "Foreign holdings."}</strong> {lang === "vi" ? "Tỷ trọng nợ Treasury nắm giữ nước ngoài đã plateau; thử nghiệm thanh toán BRICS gợi ý đa dạng hóa." : "Share of Treasury debt held abroad has plateaued; BRICS payment experiments hint at diversification."}</li>
        <li><strong>{lang === "vi" ? "Bảng cân đối Fed." : "Federal Reserve balance sheet."}</strong> {lang === "vi" ? "QT, không QE — Fed không còn người mua price-insensitive." : "QT, not QE — the Fed is no longer a price-insensitive buyer."}</li>
      </ul></Part>
      <Part label={lab("data", lang)} color="data">
        <ChartBlock lang={lang} props={{
          title: { vi: "Nợ liên bang nắm giữ công chúng / GDP (%)", en: "Federal debt held by public / GDP (%)" },
          series: [{ name: { vi: "Nợ/GDP", en: "Debt/GDP" }, data: filterRange(debt?.observations || [], "1965-01-01") }],
          yFormat: "num", yLabel: { vi: "% GDP", en: "% of GDP" },
          source: debt?.source, sourceUrl: debt?.source_url, updated: debt?.updated,
        }}/>
        <ChartBlock lang={lang} props={{
          title: { vi: "ACM term premium 10 năm (%)", en: "ACM 10-year term premium (%)" },
          subtitle: { vi: "Âm phần lớn 2010s; xoay dương hậu-2022 — tín hiệu fiscal dominance.", en: "Negative for most of 2010s; turning positive post-2022 — the fiscal-dominance signal." },
          series: [{ name: { vi: "Term premium", en: "Term premium" }, data: filterRange(toMonthly(tp?.observations || []), "1965-01-01") }],
          zeroLine: true, yFormat: "pct", yLabel: "%",
          source: tp?.source, sourceUrl: tp?.source_url, updated: tp?.updated,
        }}/>
        <ChartBlock lang={lang} props={{
          title: { vi: "Đường cong lợi suất Treasury Mỹ: 2Y, 10Y, 30Y (%)", en: "US Treasury yield curve: 2Y, 10Y, 30Y (%)" },
          subtitle: { vi: "Inversion 2022 (2Y > 10Y) đi trước pause chu kỳ 2023–24 — tín hiệu cuối chu kỳ cổ điển.", en: "2022 inversion (2Y > 10Y) preceded the 2023–24 cycle pause — classic late-cycle signal." },
          series: [
            { name: "2Y", data: filterRange(toMonthly(getSeries("y2y_treasury")?.observations || []), "1965-01-01") },
            { name: "10Y", data: filterRange(toMonthly(y10y?.observations || []), "1965-01-01") },
            { name: "30Y", data: filterRange(toMonthly(getSeries("y30y_treasury")?.observations || []), "1965-01-01") },
          ],
          yFormat: "pct", yLabel: "%",
          source: y10y?.source, sourceUrl: y10y?.source_url, updated: y10y?.updated,
        }}/>
        <ChartBlock lang={lang} props={{
          title: { vi: "Thâm hụt liên bang (% GDP)", en: "Federal deficit (% GDP)" },
          subtitle: { vi: "Thâm hụt ~6% GDP ở thất nghiệp ~4% cấu trúc bất thường — thường thâm hụt mức suy thoái.", en: "Deficit ~6% GDP at unemployment ~4% is structurally unusual — normally a recession-level deficit." },
          series: [{ name: { vi: "Thâm hụt/GDP", en: "Deficit/GDP" }, data: filterRange(deficit?.observations || [], "1965-01-01") }],
          zeroLine: true, yFormat: "pct", yLabel: { vi: "% GDP (âm = thặng dư)", en: "% GDP (negative = surplus)" },
          source: deficit?.source, sourceUrl: deficit?.source_url, updated: deficit?.updated,
        }}/>
      </Part>
      <Part label={lab("rebuttal", lang)} color="rebuttal">
        <p>{lang === "vi"
          ? "Status dự trữ + thiếu hụt dollar nước ngoài + độ sâu thị trường TIPs vẫn hấp thụ Treasury ở lợi suất thực thấp. 'Fiscal dominance' là rủi ro để flag, chưa phải sự thật. Thâm hụt 2024 có thể hẹp nếu tăng trưởng giữ; chi phí lãi/GDP tăng nhưng vẫn dưới đỉnh 1980s/1990s so với doanh thu."
          : "Reserve-currency status + dollar shortage abroad + TIPS market depth still absorb Treasuries at low real yields. \"Fiscal dominance\" is a risk to flag, not yet a fact. The 2024 deficit could narrow if growth holds; interest expense/GDP is rising but still below its 1980s/1990s peak relative to revenue."}</p>
      </Part>
      <Part label={lab("concl", lang)} color="concl">
        <p>{lang === "vi"
          ? "Về quy mô — mức nợ hôm nay là đứt gãy cấu trúc lớn nhất TỪ 1970s. Vấn đề 1970s là lạm phát với nợ nhẹ; vấn đề hôm nay là rủi ro lạm phát với nợ nặng — kết hợp khó hơn đáng kể. "
          : "On the magnitude — today's debt level is the single biggest structural break FROM the 1970s. The 1970s problem was inflation with light debt; today's problem is inflation risk with heavy debt — a materially harder combination. "}<VerdictPill id="fiscal" lang={lang} /> <VerdictPill id="debt" lang={lang} /></p>
      </Part>
      <Part label={lab("inv", lang)} color="inv">
        <p>{lang === "vi"
          ? "Fiscal dominance ủng hộ tài sản thực (vàng, TIPS, hàng hóa, cổ phiếu với pricing power) hơn Treasury danh nghĩa dài. Theo dõi: 10Y trong chu kỳ giảm, indirect takedown auction nước ngoài, xu hướng term premium."
          : "Fiscal dominance favors real assets (gold, TIPS, commodities, equities with pricing power) over long-duration nominal Treasuries. Watch: 10Y during cutting cycles, foreign auction indirect takedown, term premium trend."}</p>
      </Part>
      <Part label={lab("conf", lang)} color="conf">
        <p><span className="confidence Medium">{lang === "vi" ? "Trung bình" : "Medium"}</span> {lang === "vi" ? "— số học rõ; câu hỏi là chính sách và thị trường thích nghi thế nào." : "— the arithmetic is clear; the question is how policy and markets adapt."}</p>
      </Part>
    </Shell>
  );
}

export { SpecChapter };
