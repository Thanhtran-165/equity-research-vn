"use client";
import { useLang } from "../../components/LangProvider.jsx";
import { CLAIMS, SOURCES } from "../../data/claims.mjs";

export default function ClaimsPage() {
  const { lang } = useLang();
  const vi = lang === "vi";

  // Group claims by chapter
  const byChapter = {};
  for (const c of CLAIMS) (byChapter[c.chapter] ||= []).push(c);
  const chapters = Object.keys(byChapter).sort();

  return (
    <div>
      <section className="hero" style={{padding: "40px 0 24px"}}>
        <div className="container">
          <span className="eyebrow">{vi ? "Claim Registry" : "Claim Registry"}</span>
          <h1 style={{fontSize: 32}}>{vi ? "Mỗi nhận định định tính có trích dẫn" : "Every qualitative claim has a citation"}</h1>
          <p className="sub" style={{fontSize: 16}}>
            {vi
              ? `${CLAIMS.length} nhận định trong văn bản chương không được biểu đồ hỗ trợ trực tiếp, mỗi nhận định có nguồn sơ cấp. Sửa P1: registry series chứng minh nguồn biểu đồ, registry này chứng minh nguồn claim định tính và định lượng.`
              : `${CLAIMS.length} claims in chapter prose that aren't directly backed by a charted series, each with a primary source. P1 fix: the series registry proves chart sources; this registry proves qualitative and quantitative claim sources.`}
          </p>
        </div>
      </section>

      <section className="section" style={{paddingTop: 24}}>
        <div className="container">
          <div className="grid-4" style={{marginBottom: 24}}>
            <div className="stat"><div className="label">{vi ? "Tổng claim" : "Total claims"}</div><div className="value">{CLAIMS.length}</div></div>
            <div className="stat"><div className="label">{vi ? "Nguồn sơ cấp" : "Primary sources"}</div><div className="value" style={{color: "var(--success)"}}>{SOURCES.filter(s => s.source_type === "primary").length}</div></div>
            <div className="stat"><div className="label">{vi ? "Nguồn thứ cấp" : "Secondary sources"}</div><div className="value">{SOURCES.filter(s => s.source_type === "secondary").length}</div></div>
            <div className="stat"><div className="label">{vi ? "Confidence High" : "High confidence"}</div><div className="value" style={{color: "var(--success)"}}>{CLAIMS.filter(c => c.confidence === "High").length}</div></div>
          </div>

          <h2>{vi ? "Claim theo chương" : "Claims by chapter"}</h2>
          {chapters.map((ch) => (
            <div key={ch} className="card" style={{marginBottom: 16}}>
              <h3 style={{marginTop: 0}}>{vi ? "Chương" : "Chapter"} {ch}</h3>
              {byChapter[ch].map((c) => {
                const src = SOURCES.find((s) => s.id === c.source_id);
                return (
                  <div key={c.id} style={{borderBottom: "1px solid var(--grid)", padding: "10px 0"}}>
                    <div style={{display: "flex", gap: 8, alignItems: "baseline", flexWrap: "wrap"}}>
                      <code style={{fontSize: 11, color: "var(--fg-muted)"}}>{c.id}</code>
                      <span className={`confidence ${c.confidence}`}>{c.confidence}</span>
                      <span style={{fontSize: 11, color: "var(--fg-muted)"}}>{c.as_of_date}</span>
                    </div>
                    <div style={{fontSize: 14, margin: "4px 0"}}>{c.claim}</div>
                    {c.supporting_quote && (
                      <div style={{fontSize: 12, color: "var(--fg-muted)", fontStyle: "italic", margin: "4px 0", paddingLeft: 12, borderLeft: "2px solid var(--border)"}}>
                        "{c.supporting_quote}"
                      </div>
                    )}
                    {src && (
                      <div style={{fontSize: 12, marginTop: 4}}>
                        <strong>{vi ? "Nguồn" : "Source"}:</strong>{" "}
                        <a href={src.url} target="_blank" rel="noopener">{src.title}</a>
                        {" "}
                        <span style={{color: "var(--fg-muted)"}}>— {src.organization} ({src.source_type})</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ))}

          <h2 style={{marginTop: 32}}>{vi ? "Đầy đủ nguồn" : "Full source list"}</h2>
          <div className="card">
            <table style={{fontSize: 12}}>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>{vi ? "Tiêu đề" : "Title"}</th>
                  <th>{vi ? "Tổ chức" : "Organization"}</th>
                  <th>{vi ? "Loại" : "Type"}</th>
                </tr>
              </thead>
              <tbody>
                {SOURCES.map((s) => (
                  <tr key={s.id}>
                    <td><code>{s.id}</code></td>
                    <td><a href={s.url} target="_blank" rel="noopener">{s.title}</a></td>
                    <td>{s.organization}</td>
                    <td><span className={`pill ${s.source_type === "primary" ? "strong" : "medium"}`}>{s.source_type}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </div>
  );
}
