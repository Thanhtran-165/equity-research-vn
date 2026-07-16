"use client";
import { useLang } from "../../components/LangProvider.jsx";

export default function AboutPage() {
  const { lang } = useLang();
  const vi = lang === "vi";
  return (
    <div>
      <section className="hero" style={{padding: "40px 0 24px"}}>
        <div className="container">
          <span className="eyebrow">{vi ? "Phương pháp" : "Methodology"}</span>
          <h1 style={{fontSize: 32}}>{vi ? "Cách đọc nghiên cứu này — và cách không đọc" : "How to read this research — and how not to"}</h1>
          <p className="sub" style={{fontSize: 16}}>
            {vi ? "Phép so sánh lịch sử là công cụ tư duy, không phải mô hình dự báo. Khung dưới giải thích điểm đo gì, điểm không đo, và giới hạn ở đâu."
                : "Historical analogy is a thinking tool, not a forecasting model. The framework below explains what the scores mean, what they don't mean, and where the limits are."}
          </p>
        </div>
      </section>
      <section className="section" style={{paddingTop: 24}}>
        <div className="container-narrow">
          <h2>{vi ? "Ý tưởng trung tâm" : "The central idea"}</h2>
          <blockquote style={{borderLeft: "4px solid var(--accent)", margin: "16px 0", padding: "8px 16px", color: "var(--fg-muted)"}}>
            {vi ? "Lịch sử không nhất thiết lặp lại, nhưng cấu trúc nền kinh tế, cú sốc địa chính trị, phản ứng chính sách, chu kỳ công nghệ, thị trường hàng hóa và hành vi tài sản có thể gieo vần với nhau."
                : "History does not necessarily repeat, but the structures of the economy, geopolitical shocks, policy reactions, technology cycles, commodity markets, and asset behaviors can rhyme with one another."}
          </blockquote>

          <h2>{vi ? "Điểm déjà vu đo gì" : "What déjà vu scoring measures"}</h2>
          <p>{vi ? "Mỗi 16 chiều chấm trên bốn lớp — Hiện tượng, Cấu trúc, Cơ chế, Kết quả — mỗi cái 0 đến 5:"
                  : "Each of the 16 dimensions is scored on four layers — Phenomenon, Structure, Mechanism, Outcome — each 0 to 5:"}</p>
          <table>
            <thead><tr><th>{vi ? "Lớp" : "Layer"}</th><th>{vi ? "Câu hỏi" : "What it asks"}</th><th className="num">{vi ? "Trọng số" : "Weight"}</th></tr></thead>
            <tbody>
              <tr><td><strong>{vi ? "Hiện tượng" : "Phenomenon"}</strong></td><td>{vi ? "Hai giai đoạn có cùng dấu hiệu bề mặt?" : "Do the two periods show the same surface signs?"}</td><td className="num">0.20</td></tr>
              <tr><td><strong>{vi ? "Cấu trúc" : "Structure"}</strong></td><td>{vi ? "Nền tảng kinh tế bên dưới có giống?" : "Is the underlying economic platform similar?"}</td><td className="num">0.30</td></tr>
              <tr><td><strong>{vi ? "Cơ chế" : "Mechanism"}</strong></td><td>{vi ? "Cùng kênh truyền dẫn hoạt động?" : "Do the same transmission channels operate?"}</td><td className="num">0.30</td></tr>
              <tr><td><strong>{vi ? "Kết quả" : "Outcome"}</strong></td><td>{vi ? "Cùng kết quả kinh tế & thị trường có thể xảy ra?" : "Could the same economic and asset results occur?"}</td><td className="num">0.20</td></tr>
            </tbody>
          </table>
          <p style={{fontSize: 14, color: "var(--fg-muted)"}}>
            {vi ? "Cấu trúc và cơ chế mang nhiều trọng số hơn hiện tượng vì tương đồng bề mặt là dạng analogy yếu nhất — đó là nơi tiêu đề gây hiểu lầm nhiều nhất."
                : "Structure and mechanism carry more weight than phenomenon because surface resemblance is the weakest form of analogy — that's where headlines mislead most often."}
          </p>

          <h2>{vi ? "Mức độ tin cậy nhận định" : "Claim confidence levels"}</h2>
          <ul>
            <li><span className="confidence High">High</span> {vi ? "— dữ liệu nhất quán, nguồn sơ cấp, cơ chế rõ." : "— consistent data, primary source, clear mechanism."}</li>
            <li><span className="confidence Medium">Medium</span> {vi ? "— dữ liệu tốt nhưng cơ chế tranh cãi." : "— good data but mechanism debated."}</li>
            <li><span className="confidence Low">Low</span> {vi ? "— dữ liệu mỏng, quy mô khó đo, narrative mạnh hơn bằng chứng." : "— data thin, scale hard to measure, narrative stronger than evidence."}</li>
          </ul>

          <h2>{vi ? "Nghiên cứu này KHÔNG phải là gì" : "What this research is not"}</h2>
          <ul>
            <li><strong>{vi ? "Không phải dự báo." : "Not a forecast."}</strong> {vi ? "Không lời mua/bán. Không dự báo date-stamped. Không xác suất trên kịch bản (theo §3.5)." : "No buy/sell calls. No date-stamped predictions. No probabilities on scenarios (per §3.5)."}</li>
            <li><strong>{vi ? "Không phải nhân quả." : "Not causal."}</strong> {vi ? "Event-time overlay (§12) không chứng minh một event gây ra event khác." : "Event-time overlays (§12) do not prove that one event caused another."}</li>
            <li><strong>{vi ? "Không phải đầy đủ." : "Not exhaustive."}</strong> {vi ? "Một số series (mua vàng ngân hàng trung ương tấn, grade quặng, capex semi) thiếu series sơ cấp hàng tháng sạch — chúng được bàn định tính trong chương thay vì biểu đồ." : "Some series (central-bank gold buying tonnage, ore grades, semiconductor capex) lack a clean monthly primary source — those are discussed qualitatively in chapters rather than charted."}</li>
            <li><strong>{vi ? "Không phải phân tích chính trị." : "Not political analysis."}</strong> {vi ? "Event địa chính trị được mô tả dựa trên dữ kiện; mọi diễn giải được gắn mức độ tin cậy." : "Geopolitical events are described based on facts; all interpretations are labeled with a confidence level."}</li>
          </ul>

          <h2>{vi ? "Giới hạn đã biết" : "Known limitations"}</h2>
          <ul>
            <li>{vi ? "FRED đã bỏ một số series legacy (LBMA gold, silver); vàng/bạc đây đến từ World Bank Pink Sheet (nominal US$ hàng tháng)." : "FRED has discontinued some legacy series (LBMA gold, silver); gold/silver here come from the World Bank Pink Sheet (monthly nominal US$)."}</li>
            <li>{vi ? "'Market concentration' và 'stock-bond correlation' được tính từ series underlying, không lấy trực tiếp." : "\"Market concentration\" and \"stock-bond correlation\" are computed from underlying series, not fetched directly."}</li>
            <li>{vi ? "Dữ liệu nguồn cung critical-minerals (lithium, rare earths) phần lớn narrative — không có series sơ cấp hàng tháng sạch." : "Critical-minerals supply data (lithium, rare earths) is largely narrative — no clean monthly primary series exists."}</li>
            <li>{vi ? "BOJ policy rate được proxy bởi call/interbank rate (FRED IRSTCI01JPM156N), không phải series policy-rate chính thức." : "BOJ policy rate is proxied by the call/interbank rate (FRED IRSTCI01JPM156N), not a published policy-rate series."}</li>
            <li>{vi ? "Series dầu POILBREUSDM (Brent IMF) chỉ có giá trị thực từ ~1990; biểu đồ dầu lịch sử dùng WTISPLC (1946–nay) làm backbone, có ghi chú splice." : "The POILBREUSDM (IMF Brent) series only has usable values from ~1990; historical oil charts use WTISPLC (1946–present) as backbone, with splice documented."}</li>
            <li>{vi ? "Tương quan stock-bond dùng bond-return proxy (-D×Δy + carry), KHÔNG phải yield change — tránh đảo dấu." : "Stock-bond correlation uses bond-return proxy (-D×Δy + carry), NOT yield change — to avoid sign inversion."}</li>
            <li>{vi ? "So sánh lịch sử là point-in-time tại ngày fetch; cho giám sát trực tiếp xem watchlist." : "Historical comparisons are point-in-time as of fetch date; for live monitoring see the watchlist."}</li>
          </ul>

          <h2>{vi ? "Phiên bản & changelog" : "Versioning & changelog"}</h2>
          <ul>
            <li><strong>v1.0</strong> ({new Date().toISOString().slice(0,10)}) — {vi ? "phát hành đầu tiên. 50 series, 16 chiều, 13 hàng hóa, 6 kịch bản." : "initial release. 50 series, 16 dimensions, 13 commodities, 6 scenarios."}</li>
          </ul>
        </div>
      </section>
    </div>
  );
}
