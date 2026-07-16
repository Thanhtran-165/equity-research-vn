// src/components/ChapterContent2.jsx — Chapters 3, 4 bilingual.
import { getSeries } from "../lib/data_loader.mjs";
import { filterRange, yoyPct, deflate, toMonthly } from "../lib/transforms.mjs";
import { useLang } from "./LangProvider.jsx";
import { Part, ChartBlock, Shell, buildReal } from "./ChapterContent.jsx";
import { lab } from "../data/labels.mjs";
import { verdict2D, DEJAVU_DIMENSIONS } from "../data/dejavu_scores.mjs";
import Cite from "./Cite.jsx";

// Helper to render a dimension's verdict pill from the 3-index system (not hardcoded).
function VerdictPill({ id, lang }) {
  // Find the dimension by id in DEJAVU_DIMENSIONS, then render verdict2D.
  // Dynamic import avoided — import DEJAVU_DIMENSIONS at top.
  const d = DEJAVU_DIMENSIONS.find((x) => x.id === id);
  if (!d) return null;
  const v = verdict2D(d);
  const text = typeof v === "object" ? (v[lang] || v.vi || v.en) : v;
  const cls = typeof v === "object" ? v.cls : "medium";
  return <span className={`pill ${cls}`}>{text}</span>;
}

// ============== CHAPTER 3 — OIL ==============
export function Chapter03() {
  const { lang } = useLang();
  const cpi = getSeries("cpi"); const oilLong = getSeries("oil_wti_long"); const oil = getSeries("oil_brent");
  // Use long-history WTI to cover 1973 & 1979 shocks (POILBREUSDM only from ~1990)
  const realOil = deflate((oilLong?.observations || oil?.observations || []), cpi?.observations || [], 2024);
  const oilSrc = oilLong?.source || oil?.source;
  const oilUrl = oilLong?.source_url || oil?.source_url;
  return (
    <Shell num="03" title={lang === "vi" ? "Trung Đông, dầu và địa chính trị năng lượng" : "Middle East, oil, and energy geopolitics"} hypotheses={["H2"]} lang={lang}>
      <Part label={lab("question", lang)} color="Q"><p>{lang === "vi"
        ? "Xung đột Trung Đông hôm nay có thể truyền dẫn cú sốc dầu nghiêm trọng như cấm vận 1973 hay cách mạng 1979 — hay chủ yếu là geopolitical-risk premium?"
        : "Can today's Middle East conflicts transmit an oil shock as severe as the 1973 embargo or 1979 revolution — or are they mostly geopolitical-risk premium?"}</p></Part>
      <Part label={lab("history", lang)} color="history"><p>{lang === "vi"
        ? "Ba cú sốc tuần tự: cấm vận OAPEC 1973 (dầu tăng gấp bốn lên $12/bbl), cách mạng Iran 1979 (xuất khẩu Iran sụp), và chiến tranh Iran–Iraq 1980 (sản lượng cả hai giảm). Dầu là ràng buộc của nền kinh tế OECD — cường độ dầu cao, sản lượng Mỹ giảm, không có shale. Kết quả: CPI headline tăng hai lần và đóng góp vào chế độ Great Inflation."
        : "Three sequential shocks: the 1973 OAPEC embargo (oil quadrupled to $12/bbl), the 1979 Iranian Revolution (Iranian exports collapsed), and the 1980 Iran–Iraq War (both producers' output fell). Oil was the binding constraint of the OECD economy — oil intensity was high, US production was falling, and there was no shale. The result: headline inflation spiked twice and contributed to the Great Inflation regime."}</p></Part>
      <Part label={lab("now", lang)} color="now"><p>{lang === "vi"
        ? "Tấn công Houthi Biển Đỏ (cuối 2023), trao đổi tên lửa trực tiếp Iran–Israel (2024), repricing rủi ro Hormuz. Nhưng: Mỹ là nhà sản xuất đầu ngành (~13 mb/d), cường độ dầu/GDP giảm ~60% từ 1970, SPR lớn, OPEC+ rộng hơn nhưng công suất dự phòng mỏng, LNG đa dạng hóa nguồn khí, thị trường futures phát triển cho phép hedge. Kênh truyền dẫn khác, không phải biến mất."
        : "Red Sea Houthi attacks (late 2023), direct Iran–Israel missile exchanges (2024), Hormuz risk repricing. But: the US is the world's largest producer (~13 mb/d), oil intensity of GDP has fallen ~60% since 1970, the SPR is large, OPEC has become OPEC+ (broader but with thinner spare capacity), LNG has diversified gas supply, and developed futures markets allow hedging. The transmission channel is different, not gone."}</p></Part>
      <Part label={lab("same", lang)} color="same"><ul>
        <li>{lang === "vi" ? "Xung đột Trung Đông đang hoạt động có tiềm năng gián đoạn dòng dầu." : "Active Middle East conflict with potential to disrupt oil flows."}</li>
        <li>{lang === "vi" ? "Công suất dự phòng OPEC+ mỏng (~3 mb/d 2024)." : "OPEC+ spare capacity thin (~3 mb/d in 2024)."}</li>
        <li>{lang === "vi" ? "Trừng phạt Nga & Iran phân mảnh thị trường dầu toàn cầu." : "Russia and Iran sanctions fragment the global oil market."}</li>
        <li>{lang === "vi" ? "Eo Hormuz vẫn là điểm thất bại đơn nhất mang ~20% dầu đường biển." : "Strait of Hormuz remains a single point of failure carrying ~20% of seaborne oil."}</li>
      </ul></Part>
      <Part label={lab("diff", lang)} color="diff"><ul>
        <li>{lang === "vi" ? "Mỹ nay xuất khẩu ròng; nguồn cung nội địa là chất ổn định vĩ mô." : "US now net exporter; domestic supply is a macro stabilizer."}</li>
        <li>{lang === "vi" ? "Cường độ dầu/GDP thấp hơn ~60% — cùng spike giá ít thiệt hại CPI/GDP hơn." : "Oil intensity of GDP ~60% lower — same price spike does less CPI/GDP damage."}</li>
        <li>{lang === "vi" ? "SPR + cơ chế phát hành phối hợp IEA hấp thụ cú sốc." : "SPR + IEA coordinated release mechanism absorbs shocks."}</li>
        <li>{lang === "vi" ? "LNG, tái tạo, adoption EV vĩnh viễn giảm độc quyền dầu về năng lượng." : "LNG, renewables, and EV adoption permanently reduce oil's monopoly on energy."}</li>
      </ul></Part>
      <Part label={lab("data", lang)} color="data">
        <ChartBlock lang={lang} props={{
          title: { vi: "Giá dầu thô thực — WTI spot, lịch sử dài (CPI-deflated, $2024/bbl)", en: "Real crude oil — WTI spot, long history (CPI-deflated, 2024 $/bbl)" },
          subtitle: { vi: "Sửa P0: WTISPLC (1946–nay) phủ cả cú sốc 1973 và 1979. POILBREUSDM chỉ có giá trị từ ~1990.", en: "P0 fix: WTISPLC (1946–present) covers both 1973 and 1979 shocks. POILBREUSDM only has values from ~1990." },
          series: [{ name: { vi: "WTI spot thực ($2024/bbl)", en: "Real WTI spot ($2024/bbl)" }, data: filterRange(realOil, "1965-01-01") }],
          shading: [
            { from: "1973-10-01", to: "1974-03-31", label: { vi: "Cấm vận 1973", en: "1973 embargo" } },
            { from: "1979-01-01", to: "1980-12-31", label: { vi: "Iran 1979", en: "Iran 1979" } },
            { from: "2022-02-01", to: "2022-12-31", label: { vi: "Ukraine", en: "Ukraine" } },
          ],
          yFormat: "usd", yLabel: { vi: "$/bbl (2024 thực)", en: "$/bbl (2024 real)" },
          source: oilSrc, sourceUrl: oilUrl, updated: oilLong?.updated || oil?.updated,
          note: { vi: "Sửa P0.5: POILBREUSDM (Brent IMF) chỉ 557 obs từ ~1990, không phủ 1973/1979. WTISPLC (798 obs từ 1946) là backbone lịch sử.", en: "P0.5 fix: POILBREUSDM (IMF Brent) only 557 obs from ~1990, doesn't cover 1973/1979. WTISPLC (798 obs from 1946) is the historical backbone." },
        }}/>
      </Part>
      <Part label={lab("rebuttal", lang)} color="rebuttal"><p>{lang === "vi"
        ? "Lập luận 'cường độ dầu thấp hơn' giả định giá clear trơn tru. Phong tỏa Hormuz sẽ tạo thiếu hụt vật lý bất kể sản lượng Mỹ — dầu có thể thay thế và khám phá giá toàn cầu. Gián đoạn 5–10 mb/d trong 60 ngày có thể đẩy Brent quá $150 ngay cả trong thế giới giàu shale. Truyền dẫn yếu hơn, không phải biến mất."
        : "The \"lower oil intensity\" argument assumes prices clear smoothly. A Hormuz closure would create a physical shortage regardless of US production — oil is fungible and price discovery is global. A 5–10 mb/d disruption for 60 days could push Brent past $150 even in a shale-rich world. The transmission is weaker, not absent."}</p></Part>
      <Part label={lab("concl", lang)} color="concl"><p>{lang === "vi"
        ? "Hiện tượng tương tự (xung đột ME + rủi ro dầu). Cơ chế khác biệt đáng kể (sản lượng Mỹ, cường độ thấp hơn, độ sâu hedge). Kết quả: dầu nay là một trong nhiều nguồn đóng góp lạm phát, không phải hàng hóa hệ thống duy nhất. "
        : "The phenomenon is similar (ME conflict + oil risk). The mechanism is materially different (US production, lower intensity, hedging depth). Outcome: oil is now one of several inflation contributors, not the systemic commodity. "}<VerdictPill id="geopolitics" lang={lang} /></p></Part>
      <Part label={lab("inv", lang)} color="inv"><p>{lang === "vi"
        ? "Dầu vẫn là hedge beta cao chống leo thang ME và chỉ báo xác nhận cho kịch bản Stagflation. Nhưng energy equities không còn là cách duy nhất — uranium, đồng và LNG cung cấp phơi nhiễm khác cho ràng buộc hôm nay."
        : "Oil remains a high-beta hedge against ME escalation and a confirmation indicator for the Stagflation scenario. But energy equities are no longer the only way — uranium, copper, and LNG offer different exposures to today's binding constraints."}</p></Part>
      <Part label={lab("conf", lang)} color="conf"><p><span className="confidence High">{lang === "vi" ? "Cao" : "High"}</span> {lang === "vi" ? "về dịch chuyển cấu trúc;" : "on the structural shift;"} <span className="confidence Medium">{lang === "vi" ? "Trung bình" : "Medium"}</span> {lang === "vi" ? "về triển vọng spike do Hormuz." : "on the prospect of a Hormuz-driven spike."}</p></Part>
    </Shell>
  );
}

// ============== CHAPTER 4 — INFLATION ==============
export function Chapter04() {
  const { lang } = useLang();
  const cpi = getSeries("cpi"); const coreCpi = getSeries("core_cpi");
  const pce = getSeries("pce"); const corePce = getSeries("core_pce"); const exp = getSeries("inflation_expectation");
  return (
    <Shell num="04" title={lang === "vi" ? "Great Inflation vs cú sốc hậu-COVID" : "Great Inflation vs the post-COVID surge"} hypotheses={["H3"]} lang={lang}>
      <Part label={lab("question", lang)} color="Q"><p>{lang === "vi"
        ? "Cú sốc lạm phát 2021–22 có mang các bộ khuếch đại cấu trúc — wage indexation, quyền công đoàn, de-anchoring kỳ vọng — khiến lạm phát 1970s dai dẳng không?"
        : "Does the 2021–22 inflation surge carry the structural amplifiers — wage indexation, union power, expectation de-anchoring — that made 1970s inflation persist?"}</p></Part>
      <Part label={lab("history", lang)} color="history"><p>{lang === "vi"
        ? "CPI headline đỉnh 14.8% tháng 3 năm 1980. Nhiều sóng: embargo 1973–74, wage-oil 1978–80. Fed thời Burns accommodate; kỳ vọng de-anchor. Kỳ vọng Michigan 5 năm đạt hai chữ số. Giải quyết đòi hỏi 19% funds rate của Volcker và hai cuộc suy thoái."
        : "Headline CPI peaked at 14.8% in March 1980. Multiple waves: 1973–74 embargo-driven, 1978–80 wage-oil-driven. Burns-era Fed accommodated; expectations de-anchored. The 5-year Michigan expectation reached double digits. Resolution required Volcker's 19% funds rate and two recessions."}</p></Part>
      <Part label={lab("now", lang)} color="now"><p>{lang === "vi"
        ? "CPI headline đỉnh 9.1% YoY tháng 6 năm 2022. Ban đầu framed 'transitory'. Supply-driven (năng lượng, xe cũ, quán tính shelter) hơn demand-driven. Fed tăng 525bp trong 18 tháng. Headline hạ ~3% giữa-2023; core dính hơn (~4%) nhưng hạ."
        : "Headline CPI peaked 9.1% YoY in June 2022. Initially framed as \"transitory.\" Supply-driven (energy, used cars, shelter inertia) more than demand-driven. Fed hiked 525bp in 18 months. Headline fell to ~3% by mid-2023; core stickier (~4%) but falling."}</p></Part>
      <Part label={lab("same", lang)} color="same"><ul>
        <li>{lang === "vi" ? "Quy mô tương đương sóng 1973–74 (dù thấp hơn 1979–80)." : "Comparable magnitude to the 1973–74 wave (though below 1979–80)."}</li>
        <li>{lang === "vi" ? "Fed ban đầu chậm." : "Federal Reserve initially behind the curve."}</li>
        <li>{lang === "vi" ? "Năng lượng là nguồn đóng góp chính trong cả hai." : "Energy was a major contributor in both."}</li>
      </ul></Part>
      <Part label={lab("diff", lang)} color="diff"><ul>
        <li><strong>{lang === "vi" ? "Không wage indexation." : "No wage indexation."}</strong> {lang === "vi" ? "Hợp đồng COLA ~60% 1970s; <10% hôm nay." : "COLA contracts ~60% in 1970s; <10% today."} <Cite id="C001" lang={lang} /></li>
        <li><strong>{lang === "vi" ? "Quyền công đoàn sụp." : "Union power collapsed."}</strong> {lang === "vi" ? "Unionization khu vực tư ~6% vs ~25%+ 1970s." : "Private-sector unionization ~6% vs ~25%+ in 1970s."} <Cite id="C002" lang={lang} /></li>
        <li><strong>{lang === "vi" ? "Kỳ vọng neo." : "Expectations anchored."}</strong> {lang === "vi" ? "Michigan 5 năm ở ~3% suốt 2021–22." : "5-year Michigan stayed ~3% throughout 2021–22."}</li>
        <li><strong>{lang === "vi" ? "Fed độc lập." : "Independent Fed."}</strong> {lang === "vi" ? "Không accommodate chính trị kiểu Burns." : "No Burns-style political accommodation."}</li>
        <li><strong>{lang === "vi" ? "Kênh giảm phát hàng hóa." : "Goods deflation channel."}</strong> {lang === "vi" ? "Trung Quốc + chuỗi cung ứng toàn cầu hấp thụ cầu; không tồn tại 1970s." : "China + global supply chains absorb demand; didn't exist in 1970s."}</li>
      </ul></Part>
      <Part label={lab("data", lang)} color="data">
        <ChartBlock lang={lang} props={{
          title: { vi: "CPI headline vs core (YoY %)", en: "Headline vs core CPI (YoY %)" },
          series: [
            { name: { vi: "Headline CPI YoY", en: "Headline CPI YoY" }, data: filterRange(yoyPct(cpi?.observations || []), "1965-01-01") },
            { name: { vi: "Core CPI YoY", en: "Core CPI YoY" }, data: filterRange(yoyPct(coreCpi?.observations || []), "1965-01-01") },
          ],
          shading: [{ from: "1973-01-01", to: "1982-12-31", label: { vi: "Great Inflation", en: "Great Inflation" } }, { from: "2021-01-01", to: "2024-12-31", label: { vi: "Hậu-COVID", en: "Post-COVID" } }],
          zeroLine: true, yFormat: "pct", yLabel: { vi: "% YoY", en: "% YoY" },
          source: cpi?.source, sourceUrl: cpi?.source_url, updated: cpi?.updated,
        }}/>
        <ChartBlock lang={lang} props={{
          title: { vi: "Kỳ vọng lạm phát (Michigan 1 năm, %)", en: "Inflation expectations (Michigan 1-year, %)" },
          subtitle: { vi: "Kỳ vọng briefly tăng 2022 nhưng không de-anchor — phân kỳ chính với 1970s.", en: "Expectations briefly spiked in 2022 but never de-anchored — a key divergence from the 1970s." },
          series: [{ name: { vi: "Kỳ vọng 1 năm", en: "1-yr expectation" }, data: filterRange(exp?.observations || [], "1978-01-01") }],
          yFormat: "pct", yLabel: "%",
          source: exp?.source, sourceUrl: exp?.source_url, updated: exp?.updated,
        }}/>
        <ChartBlock lang={lang} props={{
          title: { vi: "PCE vs Core PCE (YoY %)", en: "PCE vs Core PCE (YoY %)" },
          series: [
            { name: { vi: "Headline PCE YoY", en: "Headline PCE YoY" }, data: filterRange(yoyPct(pce?.observations || []), "1965-01-01") },
            { name: { vi: "Core PCE YoY", en: "Core PCE YoY" }, data: filterRange(yoyPct(corePce?.observations || []), "1965-01-01") },
          ],
          zeroLine: true, yFormat: "pct", yLabel: { vi: "% YoY", en: "% YoY" },
          source: pce?.source, sourceUrl: pce?.source_url, updated: pce?.updated,
        }}/>
      </Part>
      <Part label={lab("rebuttal", lang)} color="rebuttal"><p>{lang === "vi"
        ? "Bộ khuếch đại cấu trúc vắng không đảm bảo chúng không thể trở lại. Quán tính shelter, hạn chế di trú, nghỉ hưu giữ tiền lương dính; sóng thứ hai cú sốc hàng hóa có thể kiểm tra uy tín Fed. 1970s có nhiều sóng — sóng đầu cũng không trông dai dẳng."
        : "The structural amplifiers being absent does not guarantee they cannot return. Shelter inertia, immigration restriction, retirements keep wages sticky; a second wave of commodity shocks could test Fed credibility. The 1970s had multiple waves — the first didn't look persistent either."}</p></Part>
      <Part label={lab("concl", lang)} color="concl"><p>{lang === "vi"
        ? "Quy mô vần ở headline. Nhưng cơ chế dai dễn yếu hơn đáng kể. Kết quả đến nay: lạm phát hạ không suy thoái — phân kỳ khỏi 1979–82. "
        : "Magnitude rhymes at headline. But persistence mechanisms are materially weaker. Outcome so far: inflation fell without recession — diverges from 1979–82. "}<VerdictPill id="inflation" lang={lang} /></p></Part>
      <Part label={lab("inv", lang)} color="inv"><p>{lang === "vi"
        ? "Nếu uy tín Fed giữ, lợi suất thực dương và vai hedge trái phiếu có thể trở lại. Nếu sóng thứ hai đến, kịch bản Stagflation tăng lực và hàng hóa/vàng/TIPS outperform."
        : "If the Fed's credibility holds, real yields stay positive and the bond-hedge role can return. If a second wave arrives, the Stagflation scenario gains traction and commodities/gold/TIPS outperform."}</p></Part>
      <Part label={lab("conf", lang)} color="conf"><p><span className="confidence High">{lang === "vi" ? "Cao" : "High"}</span> {lang === "vi" ? "về phân kỳ cấu trúc;" : "on the structural divergence;"} <span className="confidence Medium">{lang === "vi" ? "Trung bình" : "Medium"}</span> {lang === "vi" ? "về sóng thứ hai." : "on a second wave."}</p></Part>
    </Shell>
  );
}
