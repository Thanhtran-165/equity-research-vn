"use client";
import { useLang } from "../../components/LangProvider.jsx";
import { TIMELINE } from "../../data/timeline.mjs";

export default function TimelinePage() {
  const { lang } = useLang();
  const pick = (obj) => (obj && typeof obj === "object" ? (obj[lang] || obj.vi || obj.en) : obj);
  return (
    <div>
      <section className="hero" style={{padding: "40px 0 24px"}}>
        <div className="container">
          <span className="eyebrow">{lang === "vi" ? "Chương 2 · Timeline" : "Chapter 2 · Timeline"}</span>
          <h1 style={{fontSize: 32}}>{lang === "vi" ? "Timeline song song: 1965–1985 vs 2020–hiện tại" : "Parallel timeline: 1965–1985 vs 2020–present"}</h1>
          <p className="sub" style={{fontSize: 16}}>
            {lang === "vi"
              ? "Tám lớp cạnh nhau. Đọc chéo để thấy gì vần; đọc dọc mỗi cột để thấy mỗi giai đoạn như câu chuyện riêng. Không phải mọi event lịch sử map sang event hiện tại — bất đối xứng đó là điểm."
              : "Eight layers side by side. Read across to see what rhymes; read down each column to see each period as its own coherent story. Not every historical event maps to a current one — that asymmetry is the point."}
          </p>
        </div>
      </section>
      <section className="section" style={{paddingTop: 24}}>
        <div className="container">
          {TIMELINE.layers.map((layer) => (
            <div key={layer.id} className="card" style={{marginBottom: 24}}>
              <h2 style={{marginTop: 0, display: "flex", alignItems: "center", gap: 10, fontSize: 20}}>
                <span style={{display: "inline-block", width: 12, height: 12, borderRadius: 3, background: layer.color}} />
                {pick(layer.label)}
              </h2>
              <div className="grid-2" style={{marginTop: 16}}>
                <div>
                  <h3 style={{marginTop: 0, color: "var(--fg-muted)", fontSize: 14, textTransform: "uppercase", letterSpacing: "0.06em"}}>1965–1985</h3>
                  {layer.historical.map((e, i) => (
                    <div key={i} style={{display: "flex", gap: 12, padding: "6px 0", borderBottom: "1px solid var(--grid)"}}>
                      <div style={{minWidth: 70, fontWeight: 600, fontSize: 13, color: "var(--accent)"}}>{e.date}</div>
                      <div style={{fontSize: 14}}>{pick(e.text)}</div>
                    </div>
                  ))}
                </div>
                <div>
                  <h3 style={{marginTop: 0, color: "var(--fg-muted)", fontSize: 14, textTransform: "uppercase", letterSpacing: "0.06em"}}>{lang === "vi" ? "2020–hiện tại" : "2020–present"}</h3>
                  {layer.current.map((e, i) => (
                    <div key={i} style={{display: "flex", gap: 12, padding: "6px 0", borderBottom: "1px solid var(--grid)"}}>
                      <div style={{minWidth: 70, fontWeight: 600, fontSize: 13, color: "var(--chart-line-2)"}}>{e.date}</div>
                      <div style={{fontSize: 14}}>{pick(e.text)}</div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ))}
          <p style={{fontSize: 13, color: "var(--fg-muted)", marginTop: 24}}>
            {lang === "vi"
              ? "Timeline biên soạn từ nguồn thể chế sơ cấp (Federal Reserve, BIS, IEA, OPEC, BOJ, lưu trữ Nhà Trắng) và báo chí đương thời. Độ chính xác ngày thay đổi theo event."
              : "Timeline compiled from primary institutional sources (Federal Reserve, BIS, IEA, OPEC, BOJ, White House archives) and contemporaneous reporting. Date precision varies by event."}
          </p>
        </div>
      </section>
    </div>
  );
}
