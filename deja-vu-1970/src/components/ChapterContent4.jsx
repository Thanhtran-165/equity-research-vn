// src/components/ChapterContent4.jsx — Chapters 7-9, 11-16, 18 bilingual.
import { getSeries } from "../lib/data_loader.mjs";
import { filterRange, yoyPct, deflate, toMonthly, drawdown, rebase } from "../lib/transforms.mjs";
import { useLang } from "./LangProvider.jsx";
import { Part, ChartBlock, Shell, buildReal } from "./ChapterContent.jsx";
import { lab } from "../data/labels.mjs";
import { verdict2D, DEJAVU_DIMENSIONS } from "../data/dejavu_scores.mjs";
import Cite from "./Cite.jsx";

function VerdictPill({ id, lang }) {
  const d = DEJAVU_DIMENSIONS.find((x) => x.id === id);
  if (!d) return null;
  const v = verdict2D(d);
  const text = typeof v === "object" ? (v[lang] || v.vi || v.en) : v;
  const cls = typeof v === "object" ? v.cls : "medium";
  return <span className={`pill ${cls}`}>{text}</span>;
}

// Chapter 7 — Japan/yen
function Chapter07() {
  const { lang } = useLang();
  const jpy = getSeries("usd_jpy"); const boj = getSeries("boj_rate"); const jgb = getSeries("jgb10y"); const y10y = getSeries("y10y_treasury");
  const jpCpi = getSeries("japan_cpi");
  return (
    <Shell num="07" title={lang === "vi" ? "Nhật Bản, yen và carry trade" : "Japan, yen, and the carry trade"} hypotheses={["H7"]} lang={lang}>
      <Part label={lab("question", lang)} color="Q"><p>{lang === "vi" ? "BOJ bình thường hóa là story ngoại vi hay rủi ro thanh khoản trung tâm — và khuếch đại hay độc lập thúc đẩy sự kiện risk-off?" : "Is BOJ normalization a peripheral story or a central liquidity risk — and does it amplify or independently drive risk-off events?"}</p></Part>
      <Part label={lab("history", lang)} color="history"><p>{lang === "vi" ? "Nhật 1970s tăng trưởng qua cú sốc dầu nhờ cạnh tranh xuất khẩu. Plaza Accord (1985) phối hợp yen mạnh để giải quyết mất cân bằng Mỹ-Nhật; bubble tài sản tiếp theo và sụp 1990 định nghĩa 30 năm sau. Vai trò Nhật là chủ nợ lớn nhất thế giới và thị trường JGB lợi suất thấp làm nó trở thành tiền tệ funding nền tảng cho carry trades." : "Japan in the 1970s grew through the oil shocks via export competitiveness. The Plaza Accord (1985) coordinated yen appreciation to address US–Japan imbalances; the subsequent asset bubble and its 1990 collapse defined the next 30 years. Japan's role as the world's largest creditor and its low-yield JGB market made it the foundational funding currency for carry trades."}</p></Part>
      <Part label={lab("now", lang)} color="now"><p>{lang === "vi" ? "BOJ kết thúc lãi suất âm tháng 3/2024 và tăng lại tháng 7. USD/JPY phá 160 rồi đảo sắc. Spike VIX 5/8/2024 là preview carry-unwind sách giáo khoa. Nhật giữ >$1T Treasury Mỹ; chi phí hedge tăng giảm hấp thụ fixed income Mỹ cho nhà đầu tư Nhật." : "BOJ ended negative rates in March 2024 and hiked again in July. USD/JPY broke 160 then reversed sharply. The August 5, 2024 VIX spike was a textbook carry-unwind preview. Japan holds >$1T US Treasuries; rising hedging costs reduce the appeal of US fixed income for Japanese investors."} <Cite id="C003" lang={lang} /></p></Part>
      <Part label={lab("same", lang)} color="same"><ul>
        <li>{lang === "vi" ? "Thay đổi chế độ chính sách tiền tệ Nhật — vang vọng động thái Plaza theo chiều ngược (bình thường hóa yen yếu vs đánh giá lại yen mạnh)." : "Regime change in Japanese monetary policy — echoes Plaza dynamics in reverse (weak-yen normalization vs strong-yen revaluation)."}</li>
        <li>{lang === "vi" ? "Chênh lệch lãi suất Mỹ-Nhật là driver chính của dòng vốn." : "US–Japan rate differential as a primary driver of capital flows."}</li>
      </ul></Part>
      <Part label={lab("diff", lang)} color="diff"><ul>
        <li>{lang === "vi" ? "1985 là can thiệp phối hợp G5; 2024 là bình thường hóa BOJ đơn phương." : "1985 was coordinated G5 intervention; 2024 is unilateral BOJ normalization."}</li>
        <li>{lang === "vi" ? "Quy mô carry-trade khó đo hơn hôm nay (OTC derivatives, overlap basis trade); BoJ & BIS đã flag basis trade (~$1T) là rủi ro hệ thống cụ thể." : "Carry-trade size is harder to measure today (OTC derivatives, basis trade overlap); the BoJ & BIS have flagged the basis trade (~$1T) as a specific systemic risk."}</li>
        <li>{lang === "vi" ? "Lịch sử giảm phát Nhật làm BOJ di chuyển chậm và pre-communicate — ít có khả năng surprise hơn Volcker." : "Japan's deflationary history makes BOJ moves slow and pre-communicated — less likely to surprise than Volcker."}</li>
      </ul></Part>
      <Part label={lab("data", lang)} color="data">
        <ChartBlock lang={lang} props={{
          title: { vi: "USD/JPY (¥ mỗi $)", en: "USD/JPY (¥ per $)" },
          subtitle: { vi: "Đảo chiều 2024 sắc — preview carry-unwind sách giáo khoa 5/8.", en: "2024 reversal was sharp — a textbook carry-unwind preview on August 5." },
          series: [{ name: "USD/JPY", data: filterRange(toMonthly(jpy?.observations || []), "1970-01-01") }],
          shading: [{ from: "1985-09-01", to: "1987-12-31", label: "Plaza" }, { from: "2024-01-01", to: "2024-12-31", label: { vi: "BOJ tăng", en: "BOJ hikes" } }],
          yFormat: "num", yLabel: { vi: "JPY/$", en: "JPY/$" },
          source: jpy?.source, sourceUrl: jpy?.source_url, updated: jpy?.updated,
        }}/>
        <ChartBlock lang={lang} props={{
          title: { vi: "Lãi suất Mỹ 10Y vs JGB Nhật 10Y (%)", en: "US 10Y vs Japan 10Y JGB yield (%)" },
          series: [
            { name: "US 10Y", data: filterRange(toMonthly(y10y?.observations || []), "1990-01-01") },
            { name: "JP 10Y JGB", data: filterRange(jgb?.observations || [], "1990-01-01") },
          ],
          yFormat: "pct", yLabel: "%",
          source: `${y10y?.source}; ${jgb?.source}`, sourceUrl: y10y?.source_url, updated: jpy?.updated,
        }}/>
        <ChartBlock lang={lang} props={{
          title: { vi: "Lãi suất call/interbank Nhật (%)", en: "Japan call/interbank rate (%)" },
          subtitle: { vi: "BOJ kết thúc lãi suất âm tháng 3/2024 — tăng đầu tiên trong 17 năm.", en: "BOJ ended negative rates March 2024 — first hike in 17 years." },
          series: [{ name: { vi: "Lãi suất call Nhật", en: "Japan call rate" }, data: filterRange(boj?.observations || [], "1965-01-01") }],
          yFormat: "pct", yLabel: "%",
          source: boj?.source, sourceUrl: boj?.source_url, updated: boj?.updated,
        }}/>
        <ChartBlock lang={lang} props={{
          title: { vi: "CPI Nhật (YoY %)", en: "Japan CPI (YoY %)" },
          subtitle: { vi: "Lạm phát Nhật cuối cùng trở lại 2022–24 — kết thúc kỷ nguyên giảm phát.", en: "Japan inflation finally returned in 2022–24 — the end of the deflation era." },
          series: [{ name: { vi: "CPI Nhật YoY", en: "Japan CPI YoY" }, data: filterRange(yoyPct(jpCpi?.observations || []), "1965-01-01") }],
          zeroLine: true, yFormat: "pct", yLabel: { vi: "% YoY", en: "% YoY" },
          source: jpCpi?.source, sourceUrl: jpCpi?.source_url, updated: jpCpi?.updated,
        }}/>
      </Part>
      <Part label={lab("rebuttal", lang)} color="rebuttal"><p>{lang === "vi" ? "BOJ di chuyển chậm và pre-communicate. Carry unwind đến nay (5/8/2024) sắc nhưng ngắn — ngân hàng trung ương backstop thanh khoản nhanh. Quy mô carry-trade thực sự khó đo; ước tính BIS và học thuật biến thiên rộng. Narrative > bằng chứng về framing 'hệ thống'." : "BOJ moves slowly and pre-communicates. Carry unwinds so far (Aug 5, 2024) have been sharp but short — central banks backstopped liquidity quickly. The carry-trade size is genuinely hard to measure; BIS and academic estimates vary widely. Narrative > evidence on the \"systemic\" framing."}</p></Part>
      <Part label={lab("concl", lang)} color="concl"><p>{lang === "vi" ? "Cơ chế mạnh (kênh carry-unwind xác nhận thực nghiệm 5/8). Quy mô bất định — Nhật là khuếch đại risk-off, chưa phải driver độc lập khủng hoảng. " : "Mechanism strong (carry-unwind channel confirmed empirically on Aug 5). Magnitude uncertain — Japan is an amplifier of risk-off, not yet an independent driver of crisis. "}<VerdictPill id="japan" lang={lang} /></p></Part>
      <Part label={lab("inv", lang)} color="inv"><p>{lang === "vi" ? "Yen phục vụ như đèn cảnh báo tiền tệ funding. Giảm USD/JPY sắc trùng với episode risk-off. Theo dõi: họp BOJ, xu hướng chi phí hedge, quỹ đạo chênh lệch lãi suất Mỹ-Nhật." : "Yen serves as a funding-currency warning light. Sharp USD/JPY declines coincide with risk-off episodes. Watch: BOJ policy meetings, hedging-cost trends, US-JP rate differential trajectory."}</p></Part>
      <Part label={lab("conf", lang)} color="conf"><p><span className="confidence Medium">{lang === "vi" ? "Trung bình" : "Medium"}</span> {lang === "vi" ? "về cơ chế;" : "on mechanism;"} <span className="confidence Low">{lang === "vi" ? "Thấp" : "Low"}</span> {lang === "vi" ? "về quy mô phơi nhiễm carry tiềm ẩn." : "on magnitude of latent carry exposure."}</p></Part>
    </Shell>
  );
}

// Generic condensed chapter for 8, 9, 11-16, 18
function Condensed({ num, title, hypotheses, Q, hist, now, sameList, diffList, charts, rebuttal, concl, conclPill, inv, conf }) {
  const { lang } = useLang();
  return (
    <Shell num={num} title={title[lang]} hypotheses={hypotheses} lang={lang}>
      <Part label={lab("question", lang)} color="Q"><p>{Q[lang]}</p></Part>
      <Part label={lab("history", lang)} color="history"><p>{hist[lang]}</p></Part>
      <Part label={lab("now", lang)} color="now"><p>{now[lang]}</p></Part>
      <Part label={lab("same", lang)} color="same"><ul>{sameList.map((s, i) => <li key={i}>{s[lang]}</li>)}</ul></Part>
      <Part label={lab("diff", lang)} color="diff"><ul>{diffList.map((s, i) => <li key={i}>{s[lang]}</li>)}</ul></Part>
      {charts.length > 0 && <Part label={lab("data", lang)} color="data">{charts.map((ch, i) => <ChartBlock key={i} lang={lang} props={ch} />)}</Part>}
      <Part label={lab("rebuttal", lang)} color="rebuttal"><p>{rebuttal[lang]}</p></Part>
      <Part label={lab("concl", lang)} color="concl"><p><span className={`pill ${conclPill}`}>{lang === "vi" ? conclPillLabelVi(conclPill) : conclPillLabelEn(conclPill)}</span> {concl[lang]}</p></Part>
      <Part label={lab("inv", lang)} color="inv"><p>{inv[lang]}</p></Part>
      <Part label={lab("conf", lang)} color="conf"><p>{conf[lang]}</p></Part>
    </Shell>
  );
}
function conclPillLabelVi(p) { return { strong: "Tương đồng mạnh", medium: "Tương đồng trung bình", weak: "Tương đồng yếu", surface: "Tương đồng bề mặt", divergent: "Khác biệt chi phối", insufficient: "Không đủ bằng chứng" }[p] || p; }
function conclPillLabelEn(p) { return { strong: "Strong similarity", medium: "Medium similarity", weak: "Weak similarity", surface: "Surface similarity", divergent: "Differences dominate", insufficient: "Insufficient evidence" }[p] || p; }

const cpiObs = () => getSeries("cpi")?.observations || [];

function Chapter08() {
  return <Condensed {...{
    num: "08",
    title: { vi: "AI và cách mạng năng suất", en: "AI and the productivity revolution" },
    hypotheses: ["H9", "H10"],
    Q: { vi: "AI có phải là general-purpose technology tiếp theo theo mô hình vi xử lý — và có nâng năng suất đủ nhanh để giảm phát, hay chu kỳ capex đẩy theo hướng ngược trước?", en: "Is AI the next general-purpose technology in the mold of the microprocessor — and does it lift productivity fast enough to disinflation, or does its capex cycle push the other way first?" },
    hist: { vi: "Giai đoạn 1975–85 thương mại hóa vi xử lý (Intel 4004 năm 1971, PC năm 1981). Capex nặng; lợi ích năng suất mất một thập kỷ để hiển thị trong dữ liệu tổng hợp (nghịch lý Solow: 'máy tính ở khắp nơi trừ thống kê năng suất'). Tặng thưởng năng suất đầy đủ đến 1995–2004, không phải 1970s.", en: "The 1975–85 period commercialized the microprocessor (Intel 4004 in 1971, PC in 1981). Capex was heavy; productivity gains took a decade to show in aggregate data (Solow paradox: \"computers everywhere except the productivity statistics\"). The full productivity dividend arrived in 1995–2004, not the 1970s." },
    now: { vi: "Capex AI hyperscaler ~$200B+/năm. Năng suất tăng tốc lại 2023–24 (>2% YoY). Nhưng lag capex→năng suất thực; ràng buộc điện và lưới (Ch.9) là điểm nghẽn vật lý mà 1970s không đối mặt ở cùng quy mô.", en: "Hyperscaler AI capex ~$200B+/yr. Productivity re-accelerated in 2023–24 (>2% YoY). But the capex→productivity lag is real; the electricity and grid constraint (Ch.9) is a physical bottleneck the 1970s didn't face at the same scale." } ,
    // Note: C004 (AI capex $200B) and C009 (electricity 4-8%) cited inline in the chapter prose below.
    sameList: [
      { vi: "Chu kỳ capex nặng trong công nghệ general-purpose mới.", en: "Heavy capex cycle in a new general-purpose technology." },
      { vi: "Lag adoption giữa capex và năng suất đo được.", en: "Adoption lag between capex and measurable productivity." },
      { vi: "Thiết kế lại workflow + organizational capital cần cho lợi ích đầy đủ.", en: "Workflow redesign + organizational capital needed for full benefit." },
    ],
    diffList: [
      { vi: "Capex AI tập trung ~5 hyperscaler vs đầu tư semiconductor phân tán hơn 1970s.", en: "AI capex is concentrated in ~5 hyperscalers vs more diffuse semiconductor investment in 1970s." },
      { vi: "Ràng buộc điện/lưới là giới hạn vật lý cứng — vi xử lý 1975 không cần nhà máy điện mới.", en: "The electricity/grid constraint is a hard physical limit (Ch.9) — microprocessors in 1975 didn't need new power plants." },
      { vi: "Lợi ích năng suất có thể tập trung dịch vụ vs tập trung sản xuất 1975–95.", en: "Productivity benefits may concentrate in services vs manufacturing-centric 1975–95." },
    ],
    charts: [
      { title: { vi: "Năng suất nonfarm (YoY %)", en: "Nonfarm business productivity (YoY %)" }, subtitle: { vi: "Tăng tốc 2023–24 vang vọng bùng nổ 1995–2004 — nhưng mẫu ngắn.", en: "Re-acceleration in 2023–24 echoes the 1995–2004 productivity boom — but the sample is short." }, series: [{ name: { vi: "Năng suất YoY", en: "Productivity YoY" }, data: filterRange(yoyPct(getSeries("productivity")?.observations || []), "1965-01-01") }], zeroLine: true, yFormat: "pct", yLabel: { vi: "% YoY", en: "% YoY" }, source: getSeries("productivity")?.source, sourceUrl: getSeries("productivity")?.source_url, updated: getSeries("productivity")?.updated },
      { title: { vi: "Unit Labor Cost (YoY %)", en: "Unit Labor Cost (YoY %)" }, subtitle: { vi: "Nếu AI nâng năng suất, tăng trưởng ULC sẽ chậm dưới tiền lương — test giảm phát.", en: "If AI lifts productivity, ULC growth should slow below wage growth — the disinflation test." }, series: [{ name: "ULC YoY", data: filterRange(yoyPct(getSeries("ulc")?.observations || []), "1965-01-01") }], zeroLine: true, yFormat: "pct", yLabel: { vi: "% YoY", en: "% YoY" }, source: getSeries("ulc")?.source, sourceUrl: getSeries("ulc")?.source_url, updated: getSeries("ulc")?.updated },
      { title: { vi: "Giá uranium thực ($/lb, $2024)", en: "Real uranium ($/lb, 2024 dollars)" }, subtitle: { vi: "Hàng hóa phơi nhiễm trực tiếp nhất cầu điện-AI + restart lò phản ứng.", en: "The commodity most directly exposed to AI-electricity + reactor restart demand." }, series: [{ name: { vi: "Uranium thực", en: "Real uranium" }, data: filterRange(buildReal("uranium", cpiObs()), "1965-01-01") }], yFormat: "usd", yLabel: { vi: "$/lb (2024 thực)", en: "$/lb (2024 real)" }, source: getSeries("uranium")?.source, sourceUrl: getSeries("uranium")?.source_url, updated: getSeries("uranium")?.updated },
    ],
    rebuttal: { vi: "Capex boom lạm phát TRƯỚC, giảm phát SAU. Capex kéo điện, đồng, lao động, semi ngắn hạn; tặng năng suất đến năm sau. Phép so sánh vi xử lý-AI cũng phá vì vi xử lý 1970s không có cùng cầu điện, đất hiếm, lao động AI kỹ năng — chu kỳ capex hôm nay intensive-hàng hóa hơn.", en: "Capex booms are inflationary first, disinflationary later. The capex pulls on electricity, copper, labor, and semis in the short run; the productivity dividend arrives years later. A microprocessor-AI analogy also breaks because 1970s microprocessors did not have the same demand for electricity, rare earths, and skilled AI labor — the capex cycle today is more commodity-intensive." },
    concl: { vi: "Vần chu kỳ capex mạnh; vần nghịch lý năng suất có thể; điểm nghẽn điện là ràng buộc mới. Kết quả bất định — bùng nổ năng suất thực sự sẽ ĐẢO NGƯỢC kết quả 1970s (giảm phát thay vì lạm phát).", en: "Capex-cycle rhyme is strong; productivity-paradox rhyme is likely; the electricity bottleneck is a new constraint. Outcome uncertain — a genuine productivity boom would INVERT the 1970s outcome (disinflation rather than inflation)." },
    conclPill: "medium",
    inv: { vi: "Nếu năng suất AI hiện thực hóa (Kịch bản 1), mega-cap tech + growth dài thắng, và tương đồng 1970s đảo ngược. Nếu chậm (khuếch đại Kịch bản 2), capex overhang + ràng buộc hàng hóa ủng hộ luận đề stagflation. Theo dõi: năng suất vs ULC, utilization capex hyperscaler, inference unit economics AI.", en: "If AI productivity materializes (Scenario 1), mega-cap tech + long-duration growth win, and the 1970s analogy inverts. If it stalls (Scenario 2 amplifier), the capex overhang plus commodity constraints favor the stagflation thesis. Watch: productivity vs unit labor cost, hyperscaler capex utilization, AI inference unit economics." },
    conf: { vi: "Thấp — bằng chứng 1-2 năm dữ liệu năng suất; tác động năng suất AI là bất định quan trọng nhất trong nghiên cứu này.", en: "Low — evidence is one to two years of productivity data; AI productivity impact is the single most consequential uncertainty in this study." },
  }} />;
}

function Chapter09() {
  return <Condensed {...{
    num: "09",
    title: { vi: "Điện, data center và điểm nghẽn vật lý mới", en: "Electricity, data centers, and the new physical bottleneck" },
    hypotheses: ["H11"],
    Q: { vi: "Điện có phải là ràng buộc vật lý của kỷ nguyên AI — như dầu của 1970s — và điều đó ngụ ý gì cho phức hàng hóa?", en: "Is electricity the binding physical constraint of the AI era — the way oil was of the 1970s — and what does that imply for the commodity complex?" },
    hist: { vi: "Dầu là hàng hóa trung tâm 1970s vì là đầu vào cho hầu hết vận tải, sưởi và phần lớn điện. Cường độ dầu/GDP cao. Hiệu ứng cấm vận đến từ vai dầu là đầu vào vật lý phổ biến của nền kinh tế.", en: "Oil was the central commodity of the 1970s because it was the input to virtually all transport, heating, and a large share of electricity. Oil intensity of GDP was high. The embargo's effect came from oil's role as the universal physical input to the economy." },
    now: { vi: "Cầu điện AI dự báo vượt 4-8% tiêu thụ điện Mỹ vào 2030 (vs <2% hôm nay cho data center). Build-out lưới đối mặt lead time dài (biến áp, truyền tải, permitting 5-10 năm). Khí, hạt nhân, uranium, đồng, nhôm đều feed vào mở rộng điện.", en: "AI electricity demand is forecast to top 4–8% of US power consumption by 2030 (vs <2% today for data centers). Grid build-out faces long lead times (transformers, transmission, permitting 5–10y). Gas, nuclear, uranium, copper, aluminum all feed into electricity expansion." },
    sameList: [
      { vi: "Một đầu vào vật lý (điện hôm nay, dầu khi đó) trở thành điểm nghẽn cho ngành tăng trưởng dẫn đầu.", en: "A single physical input (electricity today, oil then) becomes the bottleneck for the leading growth sector." },
      { vi: "Lead time dài phản ứng nguồn cung (nhà máy lọc/đồng rồi; lưới/hạt nhân/data center nay).", en: "Long lead times on supply response (refineries/oil fields then; grid/nuclear/data centers now)." },
      { vi: "Địa chính trị hóa đầu vào (OPEC rồi; critical minerals + enrichment uranium nay).", en: "Geopoliticization of the input (OPEC then; critical minerals + uranium enrichment now)." },
    ],
    diffList: [
      { vi: "Điện không globally tradable như dầu — ràng buộc lưới khu vực, không giá thanh toán toàn cầu.", en: "Electricity is not globally tradable like oil — regional grid constraints, no global clearing price." },
      { vi: "Nhiều tùy chọn generation (khí, hạt nhân, solar, wind, pin) vs độc quyền nguồn đơn dầu.", en: "Multiple generation options (gas, nuclear, solar, wind, batteries) vs oil's single-source dominance." },
      { vi: "Cầu điện AI vẫn nhỏ so với tổng (<5%) vs vai trò gần phổ biến của dầu 1970s.", en: "AI electricity demand is still small relative to total (<5%) vs oil's near-universal 1970s role." },
    ],
    charts: [
      { title: { vi: "Nhôm & đồng thực ($2024/mt)", en: "Real aluminum & copper (2024 $/mt)" }, subtitle: { vi: "Cả kim loại lưới + data-center. Đồng dẫn; nhôm theo smelting intensive-điện.", en: "Both grid + data-center metals. Copper leads; aluminum follows electricity-intensive smelting." }, series: [{ name: { vi: "Đồng thực ($/mt)", en: "Real copper ($/mt)" }, data: filterRange(buildReal("copper", cpiObs()), "1965-01-01") }, { name: { vi: "Nhôm thực ($/mt)", en: "Real aluminum ($/mt)" }, data: filterRange(buildReal("aluminum", cpiObs()), "1965-01-01") }], yFormat: "usd", yLabel: { vi: "$/mt (2024 thực)", en: "$/mt (2024 real)" }, source: getSeries("copper")?.source, sourceUrl: getSeries("copper")?.source_url },
    ],
    rebuttal: { vi: "Điện không ràng buộc như dầu 1970s vì (a) khu vực, (b) nhiều nguồn, (c) cầu AI phần nhỏ tổng. Framing 'dầu mới' gợi cảm nhưng phóng đại. Ràng buộc thực là tốc độ build-out lưới — không nguồn cung điện trừu tượng.", en: "Electricity is not as binding as 1970s oil because (a) it's regional, (b) it has multiple sources, (c) AI demand is a small share of total. The \"new oil\" framing is evocative but overstated. The real constraint is grid build-out speed — not electricity supply in the abstract." },
    concl: { vi: "Hiện tượng vần (điểm nghẽn vật lý đơn); cơ chế khác (khu vực, đa nguồn). Ngụ ý hàng hóa thực nhưng phân tán hơn: đồng + uranium + khí + nhôm đều đóng vai, vs độc quyền dầu.", en: "Phenomenon rhymes (single physical bottleneck); mechanism differs (regional, multi-source). The commodity implication is real but more diffuse: copper + uranium + gas + aluminum all play a role, vs oil's solo dominance." },
    conclPill: "medium",
    inv: { vi: "Điểm nghẽn điện ủng hộ uranium (baseload cho PPA hyperscaler AI), đồng (lưới + EV + data center), nhôm (truyền tải + lightweighting), khí tự nhiên (peaker + LNG). Mỗi cái có ràng buộc nguồn cung đặc thù — xem bảng điểm hàng hóa.", en: "Electricity bottleneck favors uranium (baseload for AI hyperscaler PPAs), copper (grid + EV + data center), aluminum (transmission + lightweighting), and natural gas (peaker + LNG). Each has idiosyncratic supply constraints — see commodity scorecard." },
    conf: { vi: "Trung bình — hướng điểm nghẽn rõ; quy mô phụ thuộc hiện thực hóa cầu AI.", en: "Medium — bottleneck direction is clear; magnitude depends on AI demand realization." },
  }} />;
}

// Chapters 11-18 to follow in ChapterContent5
export const Chapters7to18 = {
  "07": Chapter07,
  "08": Chapter08,
  "09": Chapter09,
};
