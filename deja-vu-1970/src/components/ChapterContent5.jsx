// src/components/ChapterContent5.jsx — Chapters 11-16, 18 bilingual.
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

const cpiObs = () => getSeries("cpi")?.observations || [];

function Condensed({ num, title, hypotheses, Q, hist, now, sameList, diffList, charts, rebuttal, concl, conclId, inv, conf }) {
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
      <Part label={lab("concl", lang)} color="concl"><p>{concl[lang]} {conclId ? <VerdictPill id={conclId} lang={lang} /> : null}</p></Part>
      <Part label={lab("inv", lang)} color="inv"><p>{inv[lang]}</p></Part>
      <Part label={lab("conf", lang)} color="conf"><p>{conf[lang]}</p></Part>
    </Shell>
  );
}

function Chapter11() {
  return <Condensed {...{
    num: "11",
    title: { vi: "Toàn cầu hóa, Trung Quốc và trật tự công nghiệp mới", en: "Globalization, China, and the new industrial order" },
    hypotheses: ["H12", "H13"],
    Q: { vi: "Reshoring, thuế quan và chính sách công nghiệp có đang tạo trần lạm phát cấu trúc cao hơn — và Trung Quốc là lực giảm phát hay lạm phát trong chế độ mới?", en: "Are reshoring, tariffs, and industrial policy creating a structurally higher inflation floor — and is China a deflationary or inflationary force in the new regime?" },
    hist: { vi: "1970s là thế giới công nghiệp phân mảnh, tập trung quốc gia. Hyper-globalization 1990-2015 (WTO, Trung Quốc gia nhập, chuỗi just-in-time) là cú sốc cung giảm phát kéo dài 25 năm. Chúng ta có thể đang tháo gỡ cú sốc đó.", en: "The 1970s were a fragmented, nationally-focused industrial world. The hyper-globalization of 1990–2015 (WTO, China entry, just-in-time supply chains) was a deflationary supply shock lasting 25 years. We may now be unwinding that shock." },
    now: { vi: "Thuế quan (Trump 1.0 và 2.0), CHIPS Act, IRA, export control semi tiên tiến, friend-shoring. Trung Quốc đồng thời: (i) chậm cấu trúc (bất động sản), (ii) tràn ngập một số thị trường (nickel, lithium), (iii) chi phối khác (tinh chế rare earth, solar). Tác động ròng lên lạm phát toàn cầu hai mặt.", en: "Tariffs (Trump 1.0 and 2.0), CHIPS Act, IRA, export controls on advanced semis, friend-shoring. China is simultaneously: (i) slowing structurally (property), (ii) flooding some markets (nickel, lithium), (iii) dominating others (rare earth refining, solar). The net effect on global inflation is two-sided." },
    sameList: [
      { vi: "Trở lại chính sách công nghiệp có chiến lược quốc gia (vang vọng 1970s) sau nhiều thập kỷ hyper-globalization.", en: "A return toward nationally-strategic industrial policy (1970s echo) after decades of hyper-globalization." },
      { vi: "Thuế quan và export control là người tăng giá trực tiếp.", en: "Tariffs and export controls as direct price-raisers." },
    ],
    diffList: [
      { vi: "Sụp bất động sản Trung Quốc là cú sốc giảm phát cho kim loại công nghiệp (thép, iron ore, đồng).", en: "China's property collapse is a deflationary shock to industrial metals (steel, iron ore, copper)." },
      { vi: "Dư thừa EV/solar/pin Trung Quốc là cú sốc giảm phát cho đầu tư kinh tế xanh.", en: "China's EV/solar/battery overcapacity is a deflationary shock to green-economy inputs." },
      { vi: "Nhưng vai trò Trung Quốc là tinh chế dominate của critical minerals là điểm nghẽt lạm phát nếu export control được dùng.", en: "But China's role as dominant refiner of critical minerals is an inflationary choke point if export controls are used." },
      { vi: "'Friend-shoring' (Mexico, Vietnam, Ấn Độ) là tái toàn cầu hóa đổi hướng, không đảo ngược.", en: "\"Friend-shoring\" (Mexico, Vietnam, India) is re-globalization redirected, not reversed." },
    ],
    charts: [
      { title: { vi: "Chỉ số hàng hóa rộng, thực (CPI-deflated)", en: "Broad commodity index, real (CPI-deflated)" }, series: [{ name: { vi: "Hàng hóa rộng thực", en: "Real broad commodities" }, data: filterRange(deflate(getSeries("broad_commodity")?.observations || [], cpiObs(), 2024), "1965-01-01") }], yFormat: "num", yLabel: { vi: "index ($2024)", en: "index (2024 $)" }, source: getSeries("broad_commodity")?.source, sourceUrl: getSeries("broad_commodity")?.source_url, updated: getSeries("broad_commodity")?.updated },
      { title: { vi: "Giá nickel thực ($/mt, $2024) — story dư cung Trung Quốc", en: "Real nickel ($/mt, 2024 dollars) — the China oversupply story" }, subtitle: { vi: "Đầu tư Indonesia + HPAL Trung Quốc sụp giá nickel hậu-2022 mặc dù cầu pin EV.", en: "Indonesia + Chinese HPAL investment collapsed nickel price post-2022 despite EV battery demand." }, series: [{ name: { vi: "Nickel thực", en: "Real nickel" }, data: filterRange(buildReal("nickel", cpiObs()), "1965-01-01") }], yFormat: "usd", yLabel: { vi: "$/mt (2024 thực)", en: "$/mt (2024 real)" }, source: getSeries("nickel")?.source, sourceUrl: getSeries("nickel")?.source_url, updated: getSeries("nickel")?.updated },
    ],
    rebuttal: { vi: "'Deglobalization' phóng đại cho dịch vụ và digital flows. Mexico/Vietnam/Ấn Độ hấp thụ sản xuất đổi hướng — chuỗi cung ứng toàn cầu đang được tái dây, không tháo dỡ. Tác động ròng lên lạm phát hàng hóa Mỹ phụ thuộc trọng số tương đối thuế quan (lạm phát) vs hiệu quả đổi hướng (giảm phát).", en: "\"Deglobalization\" is overstated for services and digital flows. Mexico/Vietnam/India are absorbing redirected manufacturing — the global supply chain is being rewired, not dismantled. The net effect on US goods inflation depends on the relative weight of tariffs (inflationary) vs redirected efficiency (deflationary)." },
    concl: { vi: "Mạnh về đảo ngược cấu trúc hyper-globalization. Khác biệt chi phối về Trung Quốc — không có tương đương 1970s vai trò hai mặt của Trung Quốc.", en: "Strong on the structural reversal of hyper-globalization. Differences dominate on China — there is no 1970s equivalent of China's two-sided role." },
    conclId: "globalization",
    inv: { vi: "Trần lạm phát cấu trúc cao hơn ủng hộ hàng hóa có ràng buộc nguồn cung (đồng, uranium, vàng). Yếu bất động sản Trung Quốc là rủi ro vĩnh viễn cho kim loại công nghiệp. Theo dõi: PPI Trung Quốc, công bố thuế quan, dòng FDI friend-shoring.", en: "Higher structural inflation floor favors commodities with supply constraints (copper, uranium, gold). China property weakness is a perpetual risk to industrial metals. Watch: China PPI, tariff announcements, friend-shoring FDI flows." },
    conf: { vi: "Trung bình — hướng rõ; quy mô và tác động ròng Trung Quốc tranh cãi.", en: "Medium — direction clear; magnitude and China net effect debated." },
  }} />;
}

function Chapter12() {
  return <Condensed {...{
    num: "12",
    title: { vi: "Thị trường lao động và nhân khẩu học", en: "Labor markets and demographics" },
    hypotheses: ["H14"],
    Q: { vi: "Vì sao tiền lương dính mặc dù lạm phát giảm — và thị trường lao động thắt hôm nay có cấu trúc tương tự 1970s?", en: "Why have wages stayed sticky despite falling inflation — and is today's tight labor market structurally similar to the 1970s?" },
    hist: { vi: "1970s: công đoàn mạnh (~25% khu vực tư), hợp đồng COLA wage-indexation phổ biến, boomer vào lao động. Wage-price spiral là cơ chế dai dẳng trung tâm của Great Inflation.", en: "1970s: strong unions (~25% private sector), widespread COLA wage-indexation contracts, boomer labor force entry. Wage–price spiral was the central persistence mechanism of Great Inflation." },
    now: { vi: "Công đoàn ~6% khu vực tư. Không hợp đồng COLA đáng kể. Nhưng: nhân khẩu già, di trú giảm, skill mismatch, participation thấp hơn (62.5% vs 67% tiền-2008). Tăng trưởng tiền lương kẹt khoảng 4-5% ngay cả khi lạm phát hạ.", en: "Unions ~6% private sector. No COLA contracts of significance. But: aging demographics, reduced immigration, skill mismatch, lower participation (62.5% vs 67% pre-2008). Wage growth stuck around 4–5% even as inflation fell." },
    sameList: [
      { vi: "Thị trường lao động thắt với tiền lương dính.", en: "Tight labor market with sticky wages." },
      { vi: "Lạm phát dịch vụ dính (ngành intensive-lao động).", en: "Sticky services inflation (labor-intensive sector)." },
    ],
    diffList: [
      { vi: "Không wage indexation. Bộ khuếch đại trung tâm 1970s vắng.", en: "No wage indexation. The central 1970s amplifier is absent." },
      { vi: "Cơ chế khác. Wage stickiness 1970s = quyền công đoàn; hôm nay = nhân khẩu + khan hiếm kỹ năng.", en: "Different mechanism. 1970s wage stickiness = union power; today's = demographics + skill scarcity." },
      { vi: "Trần participation. Boomer nghỉ hưu; không thể dễ dàng thu hút thêm lao động.", en: "Participation ceiling. Boomers retiring; cannot easily draw more workers in." },
    ],
    charts: [
      { title: { vi: "Tỷ lệ thất nghiệp & participation lực lượng lao động", en: "Unemployment rate & labor force participation" }, series: [{ name: { vi: "Thất nghiệp (%)", en: "Unemployment (%)" }, data: filterRange(getSeries("unemployment")?.observations || [], "1965-01-01") }, { name: { vi: "Participation (%)", en: "Participation (%)" }, data: filterRange(getSeries("participation")?.observations || [], "1965-01-01") }], yFormat: "pct", yLabel: "%", source: getSeries("unemployment")?.source, sourceUrl: getSeries("unemployment")?.source_url },
      { title: { vi: "Thu nhập giờ trung bình ($/giờ)", en: "Average hourly earnings ($/hr)" }, series: [{ name: "AHE", data: filterRange(getSeries("wage_ahe")?.observations || [], "2006-01-01") }], yFormat: "usd", yLabel: { vi: "$/giờ", en: "$/hr" }, source: getSeries("wage_ahe")?.source, sourceUrl: getSeries("wage_ahe")?.source_url },
    ],
    rebuttal: { vi: "Nhân khẩu có thể dai dẳng hơn quyền công đoàn 1970s. Boomer nghỉ hưu không thể đảo ngược; di trú giảm là lựa chọn chính sách có thể kéo dài. Wage stickiness hôm nay có thể chứng minh CẤU TRÚC HƠN phiên bản 1970s — gần kết quả nếu không cơ chế.", en: "Demographics could be more persistent than 1970s union power. Boomer retirements are irreversible; reduced immigration is a policy choice that could last. The wage stickiness today may prove MORE structural than the 1970s version — closer to the outcome if not the mechanism." },
    concl: { vi: "Kết quả tương tự (tiền lương dính) cho lý do hoàn toàn khác (nhân khẩu vs quyền công đoàn). Phân kỳ cơ chế tổng.", en: "Similar outcome (sticky wages) for completely different reasons (demographics vs union power). Mechanism divergence is total." },
    conclId: "labor",
    inv: { vi: "Lao động thắt cấu trúc ủng hộ trần lạm phát dịch vụ → ủng hộ luận đề Stagflation-lite. Theo dõi: tỷ lệ participation, chính sách di trú, khoảng cách tiền lương vs năng suất.", en: "Structurally tight labor supports services inflation floor → supports the Stagflation-lite thesis. Watch: participation rate, immigration policy, wage growth vs productivity gap." },
    conf: { vi: "Trung bình.", en: "Medium." },
  }} />;
}

function Chapter13() {
  return <Condensed {...{
    num: "13",
    title: { vi: "Hệ thống tài chính và rủi ro thanh khoản", en: "Financial system and liquidity risk" },
    hypotheses: ["H18"],
    Q: { vi: "Hệ thống tài chính hóa hôm nay có dễ xảy ra liquidity event hơn hay ít hơn 1970s — và điều đó nói gì về biến động định kỳ?", en: "Is today's financialized system more or less prone to liquidity events than the 1970s — and what does that say about episodic volatility?" },
    hist: { vi: "Hệ thống tài chính 1970s tương đối đơn giản: ngân hàng, lương hưu defined-benefit, nhà đầu tư bán lẻ trái phiếu. Liquidity event hiếm và chủ yếu bank-specific (Franklin National 1974, Hunt silver 1980). Spike lãi suất Volcker chính kích khủng hoảng nợ Mỹ Latinh (1982).", en: "The 1970s financial system was relatively simple: banks, defined-benefit pensions, retail bondholders. Liquidity events were rare and mostly bank-specific (Franklin National 1974, Hunt silver 1980). The Volcker rate spike itself triggered Latin American debt crisis (1982)." },
    now: { vi: "Đòn bẩy hedge-fund, Treasury basis trade (~$1T theo BIS), private credit ($1.5T+), CTA, risk parity, ETF passive flow, volatility-targeting. Hệ thống nhanh và đòn bẩy hơn. Stress event gần: cash squeeze 3/2020, UK gilts 9/2022, SVB 3/2023, yen-vix 8/2024. Mỗi cái được giải quyết bởi central-bank backstop.", en: "Hedge-fund leverage, Treasury basis trade (~$1T per BIS), private credit ($1.5T+), CTAs, risk parity, ETF passive flow, volatility-targeting. The system is faster and more leveraged. Recent stress events: March 2020 cash squeeze, Sept 2022 UK gilts, March 2023 SVB, Aug 2024 yen-vix. Each was resolved by central-bank backstop." },
    sameList: [
      { vi: "Chu kỳ tăng lãi suất nhanh lịch sử kích sự cố tài chính.", en: "Rapid rate-tightening cycles historically precipitate financial accidents." },
      { vi: "Central-bank backstop là bộ ngắt mạch cuối cùng.", en: "Central-bank backstops as the ultimate circuit breaker." },
    ],
    diffList: [
      { vi: "Hệ thống đòn bẩy hơn và nhanh hơn đáng kể — cú sốc cho lan xa hơn.", en: "System is dramatically more leveraged and faster — a given shock propagates further." },
      { vi: "Toolkit ngân hàng trung ương phát triển hơn (repo, swap lines, BTFP) — backstop thường lệ.", en: "Central-bank toolkit is more developed (repo, swap lines, BTFP) — backstops are routine." },
      { vi: "'Mong manh nhưng dai dẳng' — stress event hiện đại giải quyết nhanh với can thiệp.", en: "\"Fragile but resilient\" — modern stress events resolve quickly with intervention." },
    ],
    charts: [
      { title: { vi: "Drawdown S&P 500 từ đỉnh rolling (%)", en: "S&P 500 drawdowns from rolling peak (%)" }, subtitle: { vi: "1973-74, 2008, 2020, 2022 nhìn thấy. Drawdown hiện đại nhanh hơn nhưng thường phục hồi nhanh hơn.", en: "1973–74, 2008, 2020, 2022 visible. Modern drawdowns are faster but often recover faster." }, series: [{ name: { vi: "Drawdown", en: "Drawdown" }, data: filterRange(drawdown(toMonthly(getSeries("sp500")?.observations || [])), "1965-01-01") }], zeroLine: true, yFormat: "pct", yLabel: { vi: "% từ đỉnh", en: "% from peak" }, source: getSeries("sp500")?.source, sourceUrl: getSeries("sp500")?.source_url },
      { title: { vi: "Dollar (DXY broad) vs vàng ($/oz)", en: "Dollar (DXY broad) vs gold ($/oz)" }, subtitle: { vi: "Sức dollar thường đỉnh trong liquidity event — nam châm risk-off.", en: "Dollar strength often peaks during liquidity events — a risk-off magnet." }, series: [{ name: { vi: "Gold ($/oz)", en: "Gold ($/oz)" }, data: filterRange(getSeries("gold")?.observations || [], "2020-01-01") }, { name: { vi: "DXY broad", en: "DXY broad" }, data: filterRange(toMonthly(getSeries("dxy")?.observations || []), "2020-01-01") }], yFormat: "num", yLabel: "value", source: getSeries("dxy")?.source, sourceUrl: getSeries("dxy")?.source_url },
    ],
    rebuttal: { vi: "'Mong manh nhưng dai dẳng' giả định ngân hàng trung ương luôn backstop. Nếu fiscal dominance (Ch.6) hạn chế linh hoạt Fed, hoặc stress event đánh trong (chính trị) backstop pause, pattern phá vỡ. Episode yen-vix 5/8/2024 cho thấy hệ thống hiện đại di chuyển nhanh thế nào — episode tiếp có thể lớn hơn nếu backstop bị trì hoãn.", en: "\"Fragile but resilient\" assumes central banks can always backstop. If fiscal dominance (Ch.6) limits Fed flexibility, or if a stress event hits during a (political) backstop pause, the pattern breaks. The 2024 Aug 5 yen-vix episode showed how fast the modern system moves — the next episode could be larger if a backstop is delayed." },
    concl: { vi: "Cơ chế đòn bẩy + sudden stop có mặt hơn bao giờ hết. Kết quả đến nay: biến động định kỳ, chứa được. Pattern đó có thể phá nếu backstop ngân hàng trung ương bị ràng buộc.", en: "Mechanism of leverage + sudden stop is more present than ever. Outcome so far: episodic, contained volatility. That pattern could break if the central-bank backstop is constrained." },
    conclId: "finleverage",
    inv: { vi: "Liquidity event ủng hộ cash + chất lượng (T-bills) tại thời điểm stress; phục hồi ủng hộ rủi ro. Hedge tail risk qua options hoặc vàng có giá trị kỳ vọng dương nếu biến động định kỳ cấu trúc. Theo dõi: vị trí basis trade Treasury, khảo sát đòn bẩy hedge-fund, chỉ báo stress repo.", en: "Liquidity events favor cash + quality (T-bills) at the moment of stress; recovery favors risk. Hedging tail risk via options or gold has positive expected value if episodic volatility is structural. Watch: Treasury basis-trade positioning, hedge-fund leverage surveys, repo market stress indicators." },
    conf: { vi: "Trung bình — mong manh rõ; pattern dai dẳng có thể nhưng không đảm bảo.", en: "Medium — fragility clear; resilience pattern likely but not guaranteed." },
  }} />;
}

function Chapter14() {
  const { lang } = useLang();
  const cape = getSeries("cape"); const gold = getSeries("gold");
  const realGold = buildReal("gold", cpiObs());
  return (
    <Shell num="14" title={lang === "vi" ? "Thị trường tài sản" : "Asset markets"} hypotheses={["H15", "H16", "H17", "H19"]} lang={lang}>
      <Part label={lab("question", lang)} color="Q"><p>{lang === "vi" ? "Cổ phiếu, trái phiếu, vàng và hàng hóa rộng đã hành xử thế nào trong hai chế độ — và định giá khởi đầu ngụ ý gì?" : "How have equities, bonds, gold, and broad commodities behaved in the two regimes — and what do starting valuations imply?"}</p></Part>
      <Part label={lab("history", lang)} color="history"><p>{lang === "vi" ? "1970s: cổ phiếu bắt đầu đắt (Nifty Fifty ~1972), giảm 48% thực qua 1974, trầm mặc một thập kỷ thực. Trái phiếu có lợi nhuận thực âm ~15 năm. Vàng đi từ $35 (1971) đến $850 (1980). Tương quan stock-bond dương (chế độ lạm phát) — trái phiếu thất bại làm hedge cổ phiếu." : "1970s: stocks began expensive (Nifty Fifty ~1972), fell 48% real through 1974, ground sideways for a decade in real terms. Bonds had negative real returns for ~15 years. Gold went from $35 (1971) to $850 (1980). Stock-bond correlation was positive (inflation regime) — bonds failed as equity hedge."}</p></Part>
      <Part label={lab("now", lang)} color="now"><p>{lang === "vi" ? "CAPE ~35 (2024) — trong số cao nhất từ trước đến nay, chỉ vượt bởi 2000 và 1929. Tập trung mega-cap ở đa thập kỷ cao. 2022 thấy cổ phiếu và trái phiếu giảm cùng (tương quan dương trở lại). Vàng đã breakout liên tục đến đỉnh nominal mới." : "CAPE ~35 (2024) — among the highest readings ever, exceeded only by 2000 and 1929. Mega-cap concentration at multi-decade highs. 2022 saw stocks and bonds fall together (positive correlation returned). Gold has broken out repeatedly to new nominal highs."}</p></Part>
      <Part label={lab("same", lang)} color="same"><ul>
        <li>{lang === "vi" ? "Tương quan stock-bond dương — trái phiếu ngừng hedge cổ phiếu." : "Stock-bond correlation turned positive — bonds no longer hedge equities."}</li>
        <li>{lang === "vi" ? "Tập trung cổ phiếu vài tên glamour (Nifty Fifty khi đó, mega-cap tech nay)." : "Equity concentration in a few glamour names (Nifty Fifty then, mega-cap tech now)."}</li>
        <li>{lang === "vi" ? "Vàng breakout bối cảnh lo ngại tài khóa." : "Gold breaking out against a backdrop of fiscal concern."}</li>
      </ul></Part>
      <Part label={lab("diff", lang)} color="diff"><ul>
        <li>{lang === "vi" ? "CAPE ~9 năm 1982 vs ~35 hôm nay — đầu đối lập của chu kỳ định giá." : "CAPE ~9 in 1982 vs ~35 today — opposite ends of the valuation cycle."}</li>
        <li>{lang === "vi" ? "Lợi suất trái phiếu thực âm sâu 2021 (chưa từng có) rồi dương sắc 2023." : "Real bond yields deeply negative in 2021 (unprecedented) then sharply positive in 2023."}</li>
        <li>{lang === "vi" ? "Lợi nhuận thực cổ phiếu forward 10 năm lịch sử theo dõi CAPE khởi đầu; CAPE hiện tại ngụ ý lợi nhuận thực thấp-đến-âm forward 10 năm." : "10-year forward real equity returns historically track starting CAPE; current CAPE implies low-to-negative forward real returns over 10y."}</li>
      </ul></Part>
      <Part label={lab("data", lang)} color="data">
        <ChartBlock lang={lang} props={{ title: { vi: "Shiller CAPE (P/E điều chỉnh chu kỳ)", en: "Shiller CAPE (cyclically-adjusted P/E)" }, series: [{ name: "CAPE", data: filterRange(cape?.observations || [], "1965-01-01") }], yFormat: "ratio", yLabel: "ratio", source: cape?.source, sourceUrl: cape?.source_url, updated: cape?.updated, note: { vi: "CAPE ~9 năm 1982 (rẻ); ~35 hôm nay (đắt). Lợi nhuận thực cổ phiếu forward 10 năm lịch sử tương quan ngược với CAPE khởi đầu.", en: "CAPE ~9 in 1982 (cheap); ~35 today (expensive). Forward 10y real equity returns historically correlate inversely with starting CAPE." } }}/>
        <ChartBlock lang={lang} props={{ title: { vi: "Giá vàng thực ($/oz, $2024)", en: "Real gold price ($/oz, 2024 dollars)" }, series: [{ name: { vi: "Vàng thực", en: "Real gold" }, data: filterRange(realGold, "1965-01-01") }], shading: [{ from: "1971-08-01", to: "1980-12-31", label: { vi: "Nixon→Volcker", en: "Nixon→Volcker" } }, { from: "2020-01-01", to: "2024-12-31", label: { vi: "Hậu-COVID", en: "Post-COVID" } }], yFormat: "usd", yLabel: { vi: "$/oz (2024 thực)", en: "$/oz (2024 real)" }, source: gold?.source, sourceUrl: gold?.source_url, updated: gold?.updated }}/>
      </Part>
      <Part label={lab("rebuttal", lang)} color="rebuttal"><p>{lang === "vi" ? "CAPE cao không đảm bảo lợi nhuận thấp nếu tăng trưởng earnings biện minh (luận đề năng suất AI, Ch.8). Lợi nhuận thực cổ phiếu âm 1970s là cày xay nhiều năm; lợi nhuận thực dương hôm nay có thể kéo dài nếu AI giao. Tín hiệu định giá khởi đầu là phát biểu xác suất, không dự báo." : "High CAPE doesn't guarantee low returns if earnings growth justifies it (AI productivity thesis, Ch.8). 1970s negative real equity returns were a multi-year grind; today's positive real returns could persist if AI delivers. The starting-valuation signal is a probability statement, not a forecast."}</p></Part>
      <Part label={lab("concl", lang)} color="concl"><p>{lang === "vi" ? "Tương quan stock-bond và tập trung vần; định giá khởi đầu đối lập diametrical. Lợi nhuận tài sản forward 10 năm khó khớp 1982-99 (giải pháp 1970s) vì điểm khởi đầu hôm nay đắt, không rẻ. " : "Stock-bond correlation and concentration rhyme; starting valuations are diametrically opposite. Forward 10y asset returns are unlikely to match 1982–99 (the 1970s resolution) because today's starting point is expensive, not cheap. "}<VerdictPill id="equities" lang={lang} /></p></Part>
      <Part label={lab("inv", lang)} color="inv"><p>{lang === "vi" ? "Đa dạng hóa vào tài sản thực (vàng, hàng hóa, TIPS, quốc tế) phòng thủ hơn tại định giá hôm nay so với bất kỳ thời điểm nào từ 2000. Hedge trái phiếu có thể trở lại NẾU lạm phát chứa; nếu fiscal dominance kéo dài, có thể không." : "Diversification into real assets (gold, commodities, TIPS, international) is more defensible at today's valuations than at any time since 2000. The bond hedge may return IF inflation is contained; if fiscal dominance persists, it may not."}</p></Part>
      <Part label={lab("conf", lang)} color="conf"><p><span className="confidence Medium">{lang === "vi" ? "Trung bình" : "Medium"}</span> {lang === "vi" ? "về hướng;" : "on the direction;"} <span className="confidence Low">{lang === "vi" ? "Thấp" : "Low"}</span> {lang === "vi" ? "về thời gian." : "on timing."}</p></Part>
    </Shell>
  );
}

// Chapters 15, 16, 18 — table-based, simpler
function Chapter15() {
  const { lang } = useLang();
  const items = lang === "vi" ? [
    ["Xung đột ME = cấm vận 1973", "Hiện tượng tương tự nhưng truyền dẫn yếu hơn đáng kể — sản lượng Mỹ, cường độ dầu thấp hơn, SPR, độ sâu hedge."],
    ["Cú sốc lạm phát = Great Inflation", "Quy mô tương đương chỉ sóng 1973-74; bộ khuếch đại 1970s (wage indexation, công đoàn, kỳ vọng de-anchor) vắng."],
    ["Fed tăng = Volcker", "Quy mô tích lũy tương tự; stance thực tương tự; kết quả TỐT HƠN (không suy thoái). Và tùy chọn đi 20% đã đóng bởi toán nợ."],
    ["Gold breakout = chạy 1971-80", "Hiện tượng tương tự; cơ chế khác (mua ngân hàng trung ương + lo ngại tài khóa, không kết thúc convertibility Bretton Woods)."],
    ["AI = cách mạng vi xử lý", "Vần chu kỳ capex thực; tác động năng suất chưa chứng minh; ràng buộc điện mới. Kết quả bất định."],
    ["Yen yếu = Plaza Accord", "Chiều ngược — Plaza là phối hợp yen mạnh; hôm nay là bình thường hóa BOJ đơn phương."],
    ["Deglobalization = phân mảnh 1970s", "Hướng vần; nhưng Mexico/Vietnam/India hấp thụ thương mại đổi hướng (tái toàn cầu hóa), và digital/dịch vụ vẫn mở rộng."],
    ["Cắt OPEC+ = cấm vận 1973", "NGƯỢC — cấm vận là vũ khí chính trị giảm nguồn cung cho nước cụ thể; cắt OPEC+ là quản lý giá và shale Mỹ chặn hiệu ứng."],
  ] : [
    ["ME conflict = 1973 embargo", "Phenomenon similar but transmission is materially weaker — US production, lower oil intensity, SPR, hedging depth."],
    ["Inflation surge = Great Inflation", "Magnitude comparable to 1973–74 wave only; the 1970s amplifiers (wage indexation, union power, de-anchored expectations) are absent."],
    ["Fed hikes = Volcker", "Cumulative magnitude similar; real stance similar; outcome BETTER (no recession). And the option to go to 20% is closed by debt arithmetic."],
    ["Gold breakout = 1971–80 run", "Phenomenon similar; mechanism different (central-bank buying + fiscal concern, not the end of Bretton Woods convertibility)."],
    ["AI = microprocessor revolution", "Capex-cycle rhyme is real; productivity impact unproven; electricity constraint new. Outcome uncertain."],
    ["Yen weakness = Plaza Accord", "Reverse direction — Plaza was coordinated strong yen; today's is unilateral BOJ normalization."],
    ["Deglobalization = 1970s fragmentation", "Direction rhymes; but Mexico/Vietnam/India are absorbing redirected trade (re-globalization), and digital/services flows still expanding."],
    ["OPEC+ cuts = 1973 embargo", "OPPOSITE — embargo was a political weapon reducing supply to specific countries; OPEC+ cuts are price management and US shale caps their effect."],
  ];
  return (
    <Shell num="15" title={lang === "vi" ? "Tương đồng giả — nơi tiêu đề gây hiểu lầm" : "False similarities — where headlines mislead"} lang={lang}>
      <p style={{fontSize: 17}}>{lang === "vi" ? "Phép so sánh quyến rũ nhất là cái phá ở lớp cơ chế. Tám phép song song thường-cited không sống sót kiểm tra:" : "The most seductive analogies are the ones that break at the mechanism layer. Eight commonly-cited parallels that don't survive scrutiny:"}</p>
      <div className="card">
        <table><thead><tr><th>{lang === "vi" ? "\"Giống...\"" : "\"Just like...\""}</th><th>{lang === "vi" ? "Vì sao phép so sánh phá" : "Why the analogy breaks"}</th></tr></thead>
          <tbody>{items.map(([k, v]) => (<tr key={k}><td style={{fontWeight: 600, verticalAlign: "top"}}>"{k}"</td><td>{v}</td></tr>))}</tbody>
        </table>
      </div>
      <Part label={lang === "vi" ? "Pattern" : "The pattern"} color="rebuttal"><p>{lang === "vi" ? "Mỗi tương đồng giả đúng ở lớp hiện tượng và sai (hoặc một phần) ở lớp cơ chế. Đó là lý do bảng điểm trọng số cấu trúc và cơ chế 0.30 mỗi cái vs hiện tượng 0.20. Tương đồng bề mặt là thứ dễ giả mạo nhất." : "Each false similarity is true at the phenomenon layer and false (or partial) at the mechanism layer. This is exactly why the scorecard weights structure and mechanism at 0.30 each vs phenomenon at 0.20. Surface resemblance is the easiest thing to fake."}</p></Part>
    </Shell>
  );
}

function Chapter16() {
  const { lang } = useLang();
  const items = lang === "vi" ? [
    ["Mức nợ", "Nợ liên bang/GDP ~120% vs ~30% năm 1980. Lãi suất tương đương Volcker không thể về tài khóa. Đây là đứt gãy cấu trúc lớn nhất.", "Cao"],
    ["Vị thế năng lượng Mỹ", "Mỹ là nhà sản xuất dầu + khí đầu ngành. 1970s Mỹ là nhập khẩu swing. Cùng cú sốc ME = truyền dẫn khác.", "Cao"],
    ["Uy tín Fed", "Stop-go kiểu Burns không trong tầm nhìn. Ký ức tổ chức về 1970s là tài sản uy tín.", "Cao"],
    ["Kỳ vọng lạm phát", "Kỳ vọng 5 năm không bao giờ de-anchor 2021-22. Phần khó của trận Volcker đã làm xong.", "Cao"],
    ["Quyền công đoàn", "Unionization khu vực tư ~6% vs ~25% 1970s. Cơ chế wage-price spiral phần lớn vắng.", "Cao"],
    ["Wage indexation", "Hợp đồng COLA bao phủ ~60% 1970s; <10% hôm nay. Không truyền dẫn tự động từ giá đến tiền lương.", "Cao"],
    ["Trung Quốc lực giảm phát", "Yếu bất động sản TQ + dư thừa kinh tế xanh chặn tăng kim loại công nghiệp — không tương đương 1970s.", "Trung bình"],
    ["Tốc độ adoption công nghệ", "Adoption internet ~10 năm; AI có thể nhanh hơn. Tặng thưởng năng suất có thể đến sớm hơn kỷ nguyên vi xử lý.", "Thấp"],
    ["Toolkit hedge hiện đại", "TIPS, options, ETFs, swap lines, repo facilities — hộ gia đình & tổ chức có nhiều cách hedge hơn 1970s.", "Trung bình"],
    ["Dư cung critical minerals", "Nickel, lithium, một số rare earths dư cung (Indonesia/Trung Quốc). Không phải mọi hàng hóa 'chiến lược' đều khan hiếm.", "Trung bình"],
    ["BOJ bình thường hóa trật tự", "BOJ di chuyển chậm và pre-communicate; carry unwind đến nay sắc nhưng ngắn. Chưa phải khủng hoảng hệ thống.", "Trung bình"],
    ["Fiscal dominance là rủi ro, không sự thật", "Status dự trữ + độ sâu TIPs + thiếu dollar vẫn hấp thụ Treasury.", "Trung bình"],
    ["Vàng ≠ chứng minh khủng hoảng tiền tệ", "Vàng tăng phản ánh nhiều thứ (lợi suất thực, mua ngân hàng trung ương, địa chính trị) — không tự chứng minh khủng hoảng dollar.", "Trung bình"],
    ["CAPE cao ≠ khởi đầu rẻ 1970s", "Lợi nhuận thực cổ phiếu forward 10 năm lịch sử tương quan ngược CAPE; CAPE cao hôm nay ngụ ý kết quả khác 1982.", "Cao"],
    ["Index hàng hóa ≠ tất cả hàng hóa", "Index hàng hóa rộng nặng năng lượng; luận đề supercycle nay là kim loại + uranium + điện khí hóa, không dầu-centric.", "Trung bình"],
  ] : [
    ["Debt level", "Federal debt/GDP ~120% vs ~30% in 1980. A Volcker-equivalent rate is fiscally impossible. This is the single biggest structural break.", "High"],
    ["US energy position", "US is the world's largest oil + gas producer. 1970s US was a swing importer. Same ME shock = different transmission.", "High"],
    ["Fed credibility", "Burns-style stop-go is not in prospect. Institutional memory of the 1970s is itself a credibility asset.", "High"],
    ["Inflation expectations", "5-year expectation never de-anchored in 2021–22. The hard part of the Volcker fight was already done.", "High"],
    ["Union power", "Private-sector unionization ~6% vs ~25% in 1970s. Wage–price spiral mechanism is largely absent.", "High"],
    ["Wage indexation", "COLA contracts covered ~60% of workers in 1970s; <10% today. No automatic transmission from prices to wages.", "High"],
    ["China as deflationary force", "China property weakness + green-economy overcapacity cap industrial-metals upside — no 1970s equivalent.", "Medium"],
    ["Tech adoption speed", "Internet-era adoption was ~10 years; AI adoption may be faster. Productivity dividend could arrive sooner than microprocessor era.", "Low"],
    ["Modern hedging toolkit", "TIPS, options, ETFs, swap lines, repo facilities — households and institutions have more ways to hedge than in 1970s.", "Medium"],
    ["Critical minerals oversupply", "Nickel, lithium, some rare earths are oversupplied (Indonesia/China). Not every \"strategic\" commodity is actually scarce.", "Medium"],
    ["BOJ normalization orderly", "BOJ moves slowly and pre-communicates; carry unwinds so far have been sharp but short. Not yet a systemic crisis.", "Medium"],
    ["Fiscal dominance is a risk, not a fact", "Reserve-currency status + TIPS market depth + dollar shortage still absorb Treasuries.", "Medium"],
    ["Gold ≠ monetary crisis proof", "Gold rising reflects many things (real yields, central-bank buying, geopolitics) — does not by itself prove a dollar crisis.", "Medium"],
    ["CAPE high ≠ 1970s cheap start", "Forward 10y real equity returns historically inversely related to CAPE; today's high CAPE implies different outcome than 1982.", "High"],
    ["Commodity index ≠ all commodities", "Broad commodity indices are energy-heavy; today's supercycle thesis is metals + uranium + electrification, not oil-centric.", "Medium"],
  ];
  return (
    <Shell num="16" title={lang === "vi" ? "Điều gì phá vỡ phép so sánh" : "What breaks the comparison"} lang={lang}>
      <p style={{fontSize: 17}}>{lang === "vi" ? "15 khác biệt cấu trúc làm suy yếu — hoặc đảo ngược — phép so sánh 1970s. Độ tin cậy về chính sự khác biệt:" : "Fifteen structural differences that materially weaken — or invert — the 1970s analogy. Confidence in the difference itself:"}</p>
      <div className="card"><table><thead><tr><th>{lang === "vi" ? "Khác biệt" : "Difference"}</th><th>{lang === "vi" ? "Cách phá phép so sánh" : "How it breaks the analogy"}</th><th>{lang === "vi" ? "Độ tin cậy" : "Confidence"}</th></tr></thead>
        <tbody>{items.map(([k, v, c]) => (<tr key={k}><td style={{fontWeight: 600, verticalAlign: "top", minWidth: 160}}>{k}</td><td>{v}</td><td><span className={`confidence ${c === "Cao" ? "High" : c === "Trung bình" ? "Medium" : "Low"}`}>{c}</span></td></tr>))}</tbody>
      </table></div>
      <Part label={lang === "vi" ? "Ngụ ý" : "The implication"} color="concl"><p>{lang === "vi" ? "Phép so sánh 1970s không 'sai' — là chưa hoàn thiện. Nó flag chính xác vần cấp chế độ (biến động lạm phát, cú sốc cung, chính sách trong hộp) nhưng đánh giá thấp bao nhiêu tùy chọn chính sách và kinh tế đã thu hẹp (nợ) và bao nhiêu cấu trúc cung/cầu đã dịch chuyển (năng lượng, Trung Quốc, tài chính hóa). Đọc phép so sánh tốt nghĩa là giữ cả vần và đứt gãy trong tâm trí cùng lúc." : "The 1970s analogy is not \"wrong\" — it's incomplete. It correctly flags regime-level rhyme (inflation volatility, supply shocks, policy in a box) but understates how much the policy and economic option set has narrowed (debt) and how much the supply/demand structure has shifted (energy, China, financialization). Reading the analogy well means holding both the rhyme and the breaks in mind at once."}</p></Part>
    </Shell>
  );
}

function Chapter18() {
  const { lang } = useLang();
  const answers = lang === "vi" ? [
    ["Hôm nay giống 1970-80 đến đâu?", "Hỗn hợp / vần cấp chế độ (điểm TB ~3.3/5). Cùng chế độ, cơ chế khác."],
    ["Giống 1970s hay đầu 1980s hơn?", "Giống giữa-1970s: hậu-cú sốc, lạm phát dính, chính sách hạn chế, nhưng trước giải pháp. Chúng ta chưa có giải pháp Volcker."],
    ["Năm tương đồng mạnh nhất?", "Thái độ tài khóa, đòn bẩy tài chính, đảo ngược toàn cầu hóa, mức nợ (như vấn đề), chu kỳ hàng hóa rộng."],
    ["Năm khác biệt lớn nhất?", "Uy tín Fed, vị thế năng lượng Mỹ, neo kỳ vọng, vắng công đoàn/wage-indexation, CAPE khởi đầu."],
    ["Đâu phép so sánh thất bại nhất?", "Mức nợ công — tùy chọn phản ứng chính sách đã mất. Đây là phân kỳ lớn nhất."],
    ["AI: lực giảm phát hay lạm phát capex?", "Cả hai, theo thứ tự. Capex lạm phát trước (hàng hóa, điện), giảm phát năng suất sau — NẾU hiện thực hóa. Độ tin cậy thấp."],
    ["Nợ Mỹ thay đổi phản ứng chính phủ bao nhiêu?", "Đáng kể. Volcker-tương đương không thể về tài khóa. Uy tín phải làm nhiều việc hơn với đạn dược lãi suất ít hơn."],
    ["Yen carry: rủi ro trung tâm hay khuếch đại?", "Khuếch đại. Cơ chế xác nhận 5/8/2024. Quy mô bất định; phụ thuộc tốc độ BOJ và overlap với cú sốc khác."],
    ["Dầu vẫn hàng hóa hệ thống quan trọng nhất?", "Không. Là một trong nhiều. Điện (qua đồng, uranium, khí, nhôm) là ràng buộc cho kỷ nguyên AI."],
    ["Đồng thực sự 'dầu mới'?", "Sự thật một phần. Cầu điện khí hóa thực; nhưng bất động sản TQ (50% cầu) và nguồn cung phân mảnh (không OPEC) chặn phép so sánh."],
    ["Uranium hàng hóa tiêu biểu kỷ nguyên AI?", "Khả dĩ. PPA hyperscaler AI + restart lò phản ứng + chu kỳ hợp đồng dài + tập trung enrichment Nga. Độ tin cậy trung bình."],
    ["Hàng hóa nào khan hiếm thực sự?", "Uranium, đồng (dài hạn), vàng (bid tiền tệ). Mỗi cái với lưu ý — xem bảng điểm hàng hóa."],
    ["Cái nào có narrative nhưng không khan hiếm?", "Nickel (dư cung Indonesia), lithium (dư cung TQ), một số rare earth."],
    ["Phụ thuộc TQ nhất?", "Đồng, nhôm, iron ore, nickel, lithium — tất cả >50% cầu hoặc nguồn cung TQ."],
    ["Phơi nhiễm địa chính trị nhất?", "Dầu (Hormuz, trừng phạt), uranium (enrichment Nga), khí (điểm nghẽn LNG), lúa mì (Biển Đen)."],
    ["Hưởng lợi AI/điện khí hóa lớn nhất?", "Uranium, đồng, nhôm, bạc (solar), thiếc (điện tử)."],
    ["Trái phiếu dài vẫn hedge?", "Bất định. Nếu lạm phát chứa và uy tín giữ, có. Nếu fiscal dominance kéo dài, không. Chế độ tương quan dương 2022 có thể cấu trúc."],
    ["Vàng phản ánh gì hôm nay?", "Chủ yếu uy tín tiền tệ + mua ngân hàng trung ương + lo ngại tài khóa, KHÔNG CPI. Vàng tăng mặc dù lợi suất thực dương 2024 phá mô hình sách giáo khoa."],
    ["Chế độ trung tâm phù hợp nhất?", "Tăng trưởng nominal cao, biến động lạm phát, bộ tùy chọn chính sách hạn chế, liquidity event định kỳ, hàng hóa là lớp chiến lược."],
    ["Chỉ báo nào theo dõi?", "Hàng tháng: CPI, core PCE, tiền lương, dầu, vàng, USD/JPY, JGB, 10Y, term premium, credit spread, tồn kho hàng hóa. Hàng quý: năng suất, thâm hụt, capex AI, cầu điện, capex khai khoáng."],
  ] : [
    ["How similar is today to 1970–80?", "Mixed / regime-level rhyme (score ~3.3/5 avg). Same regime, different mechanics."],
    ["More like the 1970s or early 1980s?", "More like mid-1970s: post-shock, sticky inflation, restrictive policy, but before the resolution. We have NOT had the Volcker resolution."],
    ["Five strongest echoes?", "Fiscal stance, financial leverage, globalization reversal, debt level (as problem), broad commodity cycle."],
    ["Five biggest breaks?", "Fed credibility, US energy position, expectation anchoring, union/wage-indexation absence, starting CAPE."],
    ["Where the analogy fails most?", "Public debt level — the policy response option is gone. This is the single biggest divergence."],
    ["AI: disinflation force or capex inflation?", "Both, in sequence. Capex inflationary first (commodities, electricity), productivity disinflation later — IF it materializes. Low confidence."],
    ["How much does US debt change policy?", "Materially. A Volcker-equivalent is fiscally impossible. Credibility must do more of the work with less rate ammunition."],
    ["Yen carry: central risk or amplifier?", "Amplifier. Confirmed mechanism on Aug 5, 2024. Magnitude uncertain; depends on BOJ pace and overlap with other shocks."],
    ["Is oil still the most systemic commodity?", "No. It's one of several. Electricity (via copper, uranium, gas, aluminum) is the binding constraint for the AI era."],
    ["Is copper really 'the new oil'?", "Partial truth. Electrification demand is real; but China property (50% of demand) and fragmented supply (no OPEC) cap the analogy."],
    ["Is uranium the quintessential AI-era commodity?", "Plausibly yes. AI hyperscaler PPAs + reactor restarts + long contract cycle + Russia enrichment concentration. Medium confidence."],
    ["Which commodities are genuinely scarce?", "Uranium, copper (long term), gold (monetary bid). Each with caveats — see commodity dashboard."],
    ["Which have narrative but no scarcity?", "Nickel (Indonesia oversupply), lithium (China oversupply), some rare earths."],
    ["Most China-dependent?", "Copper, aluminum, iron ore, nickel, lithium — all >50% China demand or supply."],
    ["Most geopolitically exposed?", "Oil (Hormuz, sanctions), uranium (Russia enrichment), gas (LNG chokepoints), wheat (Black Sea)."],
    ["Biggest AI/electrification beneficiaries?", "Uranium, copper, aluminum, silver (solar), tin (electronics)."],
    ["Are long bonds still a hedge?", "Uncertain. If inflation contained and credibility holds, yes. If fiscal dominance persists, no. The 2022 positive-correlation regime may be structural."],
    ["What does gold reflect today?", "Mostly monetary credibility + central-bank buying + fiscal concern, NOT CPI. Gold rising despite positive real yields in 2024 broke the textbook model."],
    ["Best-fitting central regime?", "Higher nominal growth, inflation volatility, restricted policy option set, episodic liquidity events, commodity as a strategic layer."],
    ["What indicators to monitor?", "Monthly: CPI, core PCE, wage, oil, gold, USD/JPY, JGB, 10Y, term premium, credit spreads, commodity inventories. Quarterly: productivity, deficit, AI capex, electricity demand, mining capex."],
  ];
  return (
    <Shell num="18" title={lang === "vi" ? "Kết luận — hai mươi câu trả lời trực tiếp" : "Conclusion — twenty direct answers"} lang={lang}>
      <p style={{fontSize: 17}}>{lang === "vi" ? "Hai mươi câu hỏi kết luận bắt buộc (§21), trả lời trực tiếp:" : "The twenty mandatory closing questions (§21), answered directly:"}</p>
      <div className="card"><table><thead><tr><th>#</th><th>{lang === "vi" ? "Câu hỏi" : "Question"}</th><th>{lang === "vi" ? "Trả lời" : "Answer"}</th></tr></thead>
        <tbody>{answers.map(([q, a], i) => (<tr key={i}><td className="num">{i+1}</td><td style={{fontWeight: 600, verticalAlign: "top", minWidth: 220}}>{q}</td><td>{a}</td></tr>))}</tbody>
      </table></div>
      <Part label={lang === "vi" ? "Tóm tắt trung thực" : "The honest summary"} color="concl"><p>{lang === "vi" ? "Hôm nay KHÔNG phải lặp lại 1970-1980. Là cùng CHẾ ĐỘ — cú sốc cung, biến động lạm phát, chính sách trong hộp, hàng hóa chiến lược, liquidity event định kỳ, cách mạng năng suất đang hình thành — hoạt động qua CƠ CHẾ KHÁC dưới CHÍNH SÁCH HẠN CHẾ HƠN với TÀI CHÍNH HÓA NHIỀU HƠN. Khác biệt đơn lớn nhất là mức nợ, loại bỏ tùy chọn Volcker. Cơ hội đơn lớn nhất là năng suất AI, có thể đảo ngược kết quả 1970s. Rủi ro đơn lớn nhất là fiscal dominance cộng liquidity event ngân hàng trung ương không thể backstop." : "Today is not a repeat of 1970–1980. It is the same regime — supply shocks, inflation volatility, policy in a box, strategic commodities, episodic liquidity, a nascent productivity revolution — operating through different mechanisms under more constrained policy with more financialization. The biggest single difference is the debt level, which removes the Volcker option. The biggest single opportunity is AI productivity, which could invert the 1970s outcome. The biggest single risk is fiscal dominance plus a liquidity event the central bank cannot backstop."}<br/><br/>{lang === "vi" ? "Đọc nghiên cứu này tốt nghĩa là giữ ba thứ trong tâm trí cùng lúc: vần chế độ, đứt gãy cấu trúc, và kịch bản điều kiện. Lịch sử gieo vần; không phải lặp lại." : "Reading this study well means holding three things in mind at once: the regime rhyme, the structural breaks, and the conditional scenarios. History rhymes; it does not have to repeat."}</p></Part>
    </Shell>
  );
}

export { Chapter11, Chapter12, Chapter13, Chapter14, Chapter15, Chapter16, Chapter18 };
