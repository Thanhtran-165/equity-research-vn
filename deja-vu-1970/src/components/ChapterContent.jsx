// src/components/ChapterContent.jsx
// Bilingual chapter bodies. Each chapter has full Vietnamese + English content.
// Use useLang() to pick the right language at render time.

import { getSeries } from "../lib/data_loader.mjs";
import { Chart } from "./Chart.mjs";
import { filterRange, yoyPct, deflate, toMonthly, drawdown, rebase } from "../lib/transforms.mjs";
import { useLang } from "./LangProvider.jsx";

function Part({ label, color, children }) {
  const cmap = { Q: "var(--chart-line-2)", history: "var(--chart-line-3)", now: "var(--chart-line-2)", same: "var(--success)", diff: "var(--danger)", data: "var(--accent)", rebuttal: "var(--danger)", concl: "var(--chart-line)", inv: "var(--chart-line-3)", conf: "var(--fg-muted)" };
  return (
    <section style={{margin: "24px 0", borderTop: "2px solid var(--border)", paddingTop: 16}}>
      <h3 style={{color: cmap[color] || "var(--fg)", marginBottom: 8, fontSize: 18}}>{label}</h3>
      <div>{children}</div>
    </section>
  );
}

function ChartBlock({ props, lang }) {
  return <div dangerouslySetInnerHTML={{ __html: Chart({ ...props, lang }) }} />;
}

function Shell({ num, title, hypotheses, lang, children }) {
  const t = (k) => k; // chapter-specific strings handled inline
  return (
    <div className="container-narrow" style={{paddingTop: 24, paddingBottom: 40}}>
      <div style={{marginBottom: 8}}>
        <a href="/chapters" style={{fontSize: 13}}>{lang === "vi" ? "← Tất cả chương" : "← All chapters"}</a>
      </div>
      <span className="eyebrow">{lang === "vi" ? "Chương" : "Chapter"} {num}</span>
      <h1 style={{fontSize: 30, marginTop: 4}}>{title}</h1>
      {hypotheses?.length > 0 && (
        <div style={{fontSize: 13, color: "var(--fg-muted)", marginBottom: 16}}>
          {lang === "vi" ? "Kiểm định" : "Tests"}: {hypotheses.join(" · ")}
        </div>
      )}
      {children}
    </div>
  );
}

// Helper: build chart series for common patterns
function buildReal(key, cpiObs, baseYear = 2024) {
  const s = getSeries(key);
  if (!s) return [];
  return deflate(s.observations, cpiObs || [], baseYear);
}

// ============== CHAPTER 1 ==============
export function Chapter01() {
  const { lang } = useLang();
  const cpi = getSeries("cpi");
  const vi = {
    title: "Cách đọc nghiên cứu này",
    intro: "Đây là nghiên cứu về vần điệu cấu trúc, không phải dự báo. Tiền đề là thập niên 2020 gợi nhớ giai đoạn 1970–1980 theo những cách đáng xem — nhưng gợi nhớ không giống lặp lại. Đọc phần còn lại của site tốt phụ thuộc vào việc hiểu các điểm đo những gì và không đo những gì.",
  };
  const en = {
    title: "How to read this research",
    intro: "This is a study of structural rhyme, not a forecast. The premise is that the 2020s evoke the 1970–1980 period in ways worth examining — but evoking is not the same as repeating. Reading the rest of this site well depends on understanding what the scores measure and what they don't.",
  };
  const cur = lang === "vi" ? vi : en;
  return (
    <Shell num="01" title={cur.title} lang={lang}>
      <p style={{fontSize: 17}}>{cur.intro}</p>

      <Part label={lang === "vi" ? "Déjà vu là gì — và không là gì" : "What déjà vu is — and isn't"} color="Q">
        <p>{lang === "vi"
          ? "Điểm Déjà Vu Similarity 16 chiều trả lời một câu hỏi duy nhất: 'cấu trúc hôm nay giống cấu trúc 1965–1985 đến mức nào?' Điểm cao nghĩa là tương đồng mạnh; điểm thấp nghĩa là cấu trúc hôm nay phân kỳ (thường theo hướng tồi hơn, không phải tốt hơn — nợ cao, ví dụ)."
          : "The 16-dimension Déjà Vu Similarity Score answers a single question: \"how much does today's structural setup resemble that of 1965–1985?\" A high score means strong resemblance; a low score means today's setup diverges (often in ways that are worse, not better — high debt, e.g.)."}
        </p>
      </Part>

      <Part label={lang === "vi" ? "Bốn lớp chấm điểm (P / S / M / O)" : "The four-layer scoring (P / S / M / O)"} color="data">
        <table>
          <thead><tr><th>{lang === "vi" ? "Lớp" : "Layer"}</th><th>{lang === "vi" ? "Câu hỏi" : "Question"}</th><th className="num">{lang === "vi" ? "Trọng số" : "Weight"}</th></tr></thead>
          <tbody>
            <tr><td><strong>{lang === "vi" ? "Hiện tượng" : "Phenomenon"}</strong></td><td>{lang === "vi" ? "Hai giai đoạn có cùng dấu hiệu bề mặt?" : "Do both periods show the same surface signs?"}</td><td className="num">20%</td></tr>
            <tr><td><strong>{lang === "vi" ? "Cấu trúc" : "Structure"}</strong></td><td>{lang === "vi" ? "Nền tảng kinh tế có giống?" : "Is the underlying economic platform similar?"}</td><td className="num">30%</td></tr>
            <tr><td><strong>{lang === "vi" ? "Cơ chế" : "Mechanism"}</strong></td><td>{lang === "vi" ? "Cùng kênh truyền dẫn?" : "Do the same transmission channels operate?"}</td><td className="num">30%</td></tr>
            <tr><td><strong>{lang === "vi" ? "Kết quả" : "Outcome"}</strong></td><td>{lang === "vi" ? "Cùng kết quả vĩ mô & thị trường?" : "Could the same macro and market results occur?"}</td><td className="num">20%</td></tr>
          </tbody>
        </table>
        <p>{lang === "vi"
          ? "Cấu trúc và cơ chế có trọng số gấp đôi hiện tượng. Lý do: tương đồng bề mặt là thứ dễ giả mạo nhất. Tiêu đề về 'khủng hoảng dầu' hay 'lạm phát' có thể đúng ở lớp hiện tượng trong khi cơ chế bên dưới đã thay đổi căn bản."
          : "Structure and mechanism carry double the weight of phenomenon. The reason: surface resemblance is the easiest thing to fake. Headlines about \"oil crisis\" or \"inflation\" can be true at the phenomenon layer while the underlying mechanism has fundamentally changed."}</p>
      </Part>

      <Part label={lang === "vi" ? "Độ tin cậy quan trọng" : "Confidence matters"} color="conf">
        <p>{lang === "vi"
          ? "Mỗi nhận định quan trọng được gắn nhãn Cao, Trung bình, hoặc Thấp. Xử lý nhận định Thấp như suy đoán có cơ sở, không phải sự thật thiết lập. Các kịch bản trong Chương 17 cố ý bỏ số xác suất — chúng tôi liệt kê điều gì sẽ xác nhận hay bác bỏ mỗi kịch bản, không phải khả năng chúng xảy ra."
          : "Every major claim is tagged High, Medium, or Low. Treat Low-confidence claims as informed speculation, not established fact. The scenarios in Chapter 17 deliberately omit probability numbers — we list what would confirm or refute each, not how likely they are."}</p>
      </Part>

      <Part label={lang === "vi" ? "Dấu hiệu dừng" : "The stop signs"} color="rebuttal">
        <p>{lang === "vi" ? "Ba điều nghiên cứu này rõ ràng không làm:" : "Three things this study explicitly does not do:"}</p>
        <ul>
          <li>{lang === "vi" ? "Không nhận định nhân quả. Event-time overlay cho thấy điều gì xảy quanh sự kiện; không chứng minh một điều gây ra điều khác." : "No causal claims. Event-time overlays show what happened around events; they don't prove one caused another."}</li>
          <li>{lang === "vi" ? "Không lời khuyên mua/bán. 'Độ nhạy tài sản' nghĩa là 'kịch bản sẽ đẩy giá theo hướng nào', không phải 'làm gì về nó'." : "No buy/sell calls. \"Asset sensitivity\" means \"which way a scenario would push a price,\" not \"what to do about it.\""}</li>
          <li>{lang === "vi" ? "Không dự báo chắc chắn. 1970s mất 15 năm để diễn ra và đầy đảo chiều; setup hôm nay cũng vậy." : "No certain forecasts. The 1970s took 15 years to play out and were full of reversals; today's setup will too."}</li>
        </ul>
      </Part>

      <Part label={lang === "vi" ? "Cách điều hướng" : "How to navigate"} color="concl">
        <ul>
          <li><a href="/">{lang === "vi" ? "Tổng quan" : "Overview"}</a> {lang === "vi" ? "cho tóm tắt điều hành và bốn chế độ." : "for the executive summary and four regimes."}</li>
          <li><a href="/scorecard">{lang === "vi" ? "Bảng điểm" : "Scorecard"}</a> {lang === "vi" ? "cho phân tích 16 chiều và 6 kịch bản." : "for the 16-dimension breakdown and 6 scenarios."}</li>
          <li><a href="/commodities">{lang === "vi" ? "Hàng hóa" : "Commodities"}</a> {lang === "vi" ? "cho phân tích sâu 13 hàng hóa." : "for the 13-commodity deep-dive."}</li>
          <li><a href="/timeline">{lang === "vi" ? "Timeline" : "Timeline"}</a> {lang === "vi" ? "cho niên ký song song." : "for the parallel chronology."}</li>
          <li><a href="/sources">{lang === "vi" ? "Nguồn" : "Sources"}</a> {lang === "vi" ? "cho từ điển dữ liệu và registry trích dẫn đầy đủ." : "for the data dictionary and full citation registry."}</li>
          <li><a href="/about">{lang === "vi" ? "Phương pháp" : "Method"}</a> {lang === "vi" ? "cho những gì chúng tôi làm, không làm và giới hạn." : "for what we do, what we don't, and the limitations."}</li>
        </ul>
      </Part>
    </Shell>
  );
}

// Reusable Part + ChartBlock exports for other chapter files
export { Part, ChartBlock, Shell, buildReal };
