"use client";
import { useLang } from "../../components/LangProvider.jsx";
import { sourceStats } from "../../lib/data_loader.mjs";

export default function SourcesPage() {
  const { lang } = useLang();
  const stats = sourceStats();
  const primaryCount = stats.series_list.filter((s) => !s.derived && s.n > 0).length;
  return (
    <div>
      <section className="hero" style={{padding: "40px 0 24px"}}>
        <div className="container">
          <span className="eyebrow">{lang === "vi" ? "Registry nguồn" : "Source registry"}</span>
          <h1 style={{fontSize: 32}}>{lang === "vi" ? "Mỗi nhận định có trích dẫn. Mỗi biểu đồ có nguồn." : "Every claim has a citation. Every chart has a source."}</h1>
          <p className="sub" style={{fontSize: 16}}>
            {lang === "vi"
              ? `${primaryCount} series nguồn sơ cấp lấy ${stats.fetched_at?.slice(0,10)} từ ${Object.keys(stats.providers).filter(p => p !== "None").length} provider. Theo brief §19: không link chết, không trộn nguồn/đơn vị, không trộn nominal/real, không trộn spot/futures.`
              : `${primaryCount} primary-source series fetched on ${stats.fetched_at?.slice(0,10)} from ${Object.keys(stats.providers).filter(p => p !== "None").length} providers. Per brief §19: no dead links, no source/unit mixing, no nominal/real confusion, no spot/futures confusion.`}
          </p>
        </div>
      </section>

      <section className="section" style={{paddingTop: 24}}>
        <div className="container">
          <div className="grid-4" style={{marginBottom: 24}}>
            <div className="stat"><div className="label">{lang === "vi" ? "Tổng series" : "Total series"}</div><div className="value">{stats.total_series}</div></div>
            <div className="stat"><div className="label">{lang === "vi" ? "Nguồn sơ cấp" : "Primary source"}</div><div className="value" style={{color: "var(--success)"}}>{primaryCount}</div></div>
            <div className="stat"><div className="label">{lang === "vi" ? "Thiếu" : "Insufficient"}</div><div className="value" style={{color: stats.insufficient > 0 ? "var(--danger)" : "var(--success)"}}>{stats.insufficient}</div></div>
            <div className="stat"><div className="label">{lang === "vi" ? "Provider" : "Providers"}</div><div className="value">{Object.keys(stats.providers).filter(p => p !== "None").length}</div></div>
          </div>

          <div className="card">
            <h2 style={{marginTop: 0}}>{lang === "vi" ? "Phân tích provider" : "Provider breakdown"}</h2>
            <table>
              <thead><tr><th>{lang === "vi" ? "Provider" : "Provider"}</th><th className="num">{lang === "vi" ? "Series" : "Series"}</th><th>{lang === "vi" ? "Loại" : "Type"}</th></tr></thead>
              <tbody>
                {Object.entries(stats.providers).filter(([k]) => k !== "None").map(([p, n]) => (
                  <tr key={p}>
                    <td><strong>{p}</strong></td>
                    <td className="num">{n}</td>
                    <td>{p === "FRED" ? (lang === "vi" ? "Sơ cấp (ngân hàng trung ương / cơ quan thống kê)" : "Primary (central bank / statistical agency)") : p.includes("World Bank") ? (lang === "vi" ? "Sơ cấp (tổ chức quốc tế)" : "Primary (intl. institution)") : p === "Shiller" ? (lang === "vi" ? "Sơ cấp (học thuật, Yale)" : "Primary (academic, Yale)") : (lang === "vi" ? "Sơ cấp" : "Primary")}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h2 style={{marginTop: 32}}>{lang === "vi" ? "Registry series đầy đủ" : "Full series registry"}</h2>
          <div className="card">
            <table style={{fontSize: 12}}>
              <thead><tr><th>{lang === "vi" ? "Khóa" : "Key"}</th><th>{lang === "vi" ? "Nhãn" : "Label"}</th><th>{lang === "vi" ? "Provider" : "Provider"}</th><th className="num">{lang === "vi" ? "Số obs" : "Obs"}</th><th>{lang === "vi" ? "Nguồn" : "Source"}</th><th>{lang === "vi" ? "Trạng thái" : "Status"}</th></tr></thead>
              <tbody>
                {stats.series_list.map((s) => (
                  <tr key={s.key}>
                    <td><code>{s.key}</code></td>
                    <td>{s.label}</td>
                    <td>{s.provider || "—"}</td>
                    <td className="num">{s.n || (s.derived ? (lang === "vi" ? "tính toán" : "derived") : 0)}</td>
                    <td style={{fontSize: 11}}>{s.source_url ? <a href={s.source_url} target="_blank" rel="noopener">{s.source}</a> : (s.source || (s.derived ? (lang === "vi" ? "tính lúc render" : "computed at render") : "—"))}</td>
                    <td>{s.derived ? <span className="pill insufficient">{lang === "vi" ? "tính" : "derived"}</span> : s.insufficient_primary_data ? <span className="pill weak">{lang === "vi" ? "thiếu" : "insufficient"}</span> : <span className="pill strong">OK</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <h2 style={{marginTop: 32}}>{lang === "vi" ? "Từ điển dữ liệu (đơn vị & phương pháp)" : "Data dictionary (units & methods)"}</h2>
          <div className="card">
            <ul style={{fontSize: 14, lineHeight: 1.7}}>
              {(lang === "vi" ? [
                ["YoY %", "phần trăm thay đổi năm-trước-năm-nay của series cấp index (CPI, PCE, M2). Công thức: (value_t / value_(t-12m) − 1) × 100."],
                ["Giá thực", "series nominal deflated bởi CPI Mỹ, rebase năm tham chiếu (2024 trừ khi ghi chú). real_t = nominal_t / CPI_t × CPI_base."],
                ["Lãi suất chính sách thực", "Fed Funds effective − core CPI YoY. Proxy cho stance chính sách trừ lạm phát."],
                ["Term premium", "ACM 10-year term premium (Adrian-Crump-Moench, NY Fed) — component lợi suất không giải thích bởi kỳ vọng lãi suất."],
                ["Tương quan stock-bond", "rolling 36 tháng tương quan **lợi nhuận** S&P 500 và **lợi nhuận trái phiếu** (proxy: -duration × Δy + carry, duration ≈ 8 năm cho 10Y Treasury). KHÔNG phải tương quan với yield change — yield tăng → giá trái phiếu giảm."],
                ["CAPE", "Shiller cyclically-adjusted P/E — giá S&P 500 thực chia cho trung bình trailing 10 năm earnings thực."],
                ["Daily → monthly", "giá trị có sẵn cuối mỗi tháng, trừ khi ghi chú khác."],
                ["Dữ liệu dự trữ / sản xuất", "nơi FRED thiếu series (ví dụ mua vàng ngân hàng trung ương, grade quặng), nguồn được nêu rõ trong chương thay vì biểu đồ."],
              ] : [
                ["YoY %", "year-over-year percent change of an index-level series (CPI, PCE, M2). Formula: (value_t / value_{(t-12m)} − 1) × 100."],
                ["Real value", "nominal series deflated by US CPI, rebased to a reference year (2024 unless noted). real_t = nominal_t / CPI_t × CPI_base."],
                ["Real policy rate", "Fed Funds effective − core CPI YoY. A proxy for the stance of policy net of inflation."],
                ["Term premium", "ACM 10-year term premium (Adrian-Crump-Moench, NY Fed) — the yield component not explained by rate expectations."],
                ["Stock-bond correlation", "36-month rolling correlation of monthly S&P 500 **returns** and **bond returns** (proxy: -duration × Δy + carry, duration ≈ 8y for 10Y Treasury). NOT yield-change correlation — yield up → bond price DOWN."],
                ["CAPE", "Shiller cyclically-adjusted P/E — real S&P 500 price divided by 10-year trailing average real earnings."],
                ["Daily → monthly", "last available value of each month, except where noted otherwise."],
                ["Reserve / production data", "where FRED lacks a series (e.g. central-bank gold buying, ore grades), the source is named explicitly in the chapter rather than charted."],
              ]).map(([k, v]) => <li key={k}><strong>{k}</strong>: {v}</li>)}
            </ul>
          </div>
        </div>
      </section>
    </div>
  );
}
