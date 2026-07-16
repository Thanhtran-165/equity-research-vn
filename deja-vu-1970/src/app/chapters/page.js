"use client";
import { useLang } from "../../components/LangProvider.jsx";
import { CHAPTERS } from "../../data/chapters.mjs";

export default function ChaptersIndex() {
  const { lang } = useLang();
  const pick = (obj) => (obj && typeof obj === "object" ? (obj[lang] || obj.vi || obj.en) : obj);
  const sections = {};
  for (const c of CHAPTERS) {
    const sec = pick(c.section);
    (sections[sec] ||= []).push(c);
  }
  const sectionOrderVi = ["Mở đầu", "Vĩ mô", "Công nghệ", "Hàng hóa", "Tài chính", "Phản biện", "Chế độ", "Kết luận"];
  const sectionOrderEn = ["Front", "Macro", "Tech", "Commodities", "Financial", "Rebuttal", "Regime", "Conclusion"];
  const order = lang === "vi" ? sectionOrderVi : sectionOrderEn;
  return (
    <div>
      <section className="hero" style={{padding: "40px 0 24px"}}>
        <div className="container">
          <span className="eyebrow">{lang === "vi" ? "Nghiên cứu đầy đủ" : "Full study"}</span>
          <h1 style={{fontSize: 32}}>{lang === "vi" ? "Mười tám chương" : "Eighteen chapters"}</h1>
          <p className="sub" style={{fontSize: 16}}>
            {lang === "vi"
              ? "Mỗi chương theo template 10 phần: câu hỏi → lịch sử → hiện tại → giống → khác → dữ liệu → phản biện → kết luận → ý nghĩa đầu tư → độ tin cậy."
              : "Each chapter follows a 10-part template: question → history → present → similarities → differences → data → rebuttal → conclusion → investment relevance → confidence."}
          </p>
        </div>
      </section>
      <section className="section" style={{paddingTop: 24}}>
        <div className="container">
          {order.map((sec) => sections[sec] && (
            <div key={sec} style={{marginBottom: 28}}>
              <h2 style={{fontSize: 16, textTransform: "uppercase", letterSpacing: "0.08em", color: "var(--accent)", marginBottom: 12}}>{sec}</h2>
              <div className="grid-2">
                {sections[sec].map((c) => (
                  <a key={c.slug} href={c.redirect || `/chapters/${c.slug}`} className="card" style={{textDecoration: "none", color: "inherit"}}>
                    <div style={{fontSize: 12, color: "var(--fg-muted)"}}>{lang === "vi" ? "Chương" : "Chapter"} {c.slug}</div>
                    <div style={{fontSize: 17, fontWeight: 600, marginTop: 2}}>{pick(c.title)}</div>
                    {c.hypotheses?.length > 0 && (<div style={{fontSize: 12, color: "var(--fg-muted)", marginTop: 4}}>{c.hypotheses.join(" · ")}</div>)}
                  </a>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
