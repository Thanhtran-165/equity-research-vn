/**
 * Topic detection - dựa trên keyword (rule-based, MVP).
 * Mở rộng list KEYWORDS khi cần.
 */

export type Topic = "vi_mo" | "chung_khoan" | "lai_suat" | "bds" | "vang" | "khac";

export const TOPIC_LABEL_VI: Record<Topic, string> = {
  vi_mo: "Vĩ mô",
  chung_khoan: "Chứng khoán",
  lai_suat: "Lãi suất",
  bds: "BĐS",
  vang: "Vàng",
  khac: "Khác",
};

// keyword viết thường, không dấu + có dấu để khớp cả hai kiểu.
const KEYWORDS: Record<Exclude<Topic, "khac">, string[]> = {
  vi_mo: [
    "cpi", "gdp", "fed", "tỷ giá", "ty gia", "usd", "lạm phát", "lam phat",
    "tăng trưởng", "tang truong", "chính sách tiền tệ", "chinh sach tien te",
    "vĩ mô", "vi mo", "fomc", "ppi", "nhịp đập vĩ mô",
  ],
  chung_khoan: [
    "vnindex", "vn-index", "cổ phiếu", "co phieu", "thị trường", "thi truong",
    "định giá", "dinh gia", "margin", "thanh khoản", "thanh khoan",
    "chứng khoán", "chung khoan", "hsx", "hnx", "upcom", "room",
  ],
  lai_suat: [
    "lãi suất", "lai suat", "yield", "trái phiếu", "trai phieu", "sbv",
    "liên ngân hàng", "lien ngan hang", "omo", "tín phiếu", "tin phieu",
    "nhnn", "ngân hàng nhà nước",
  ],
  bds: [
    "bất động sản", "bat dong san", "bđs", "căn hộ", "can ho", "chung cư",
    "chung cu", "nhà đất", "nha dat", "đất nền", "dat nen", "vinhomes",
    "nghệ an", "masterise", "novaland", "sungroup",
  ],
  vang: [
    "vàng", "vang", "sjc", "paxg", "gold", "xauusd", "xau/usd",
    "doji", "phú quý", "bac ao",
  ],
};

const TOPIC_ORDER: Exclude<Topic, "khac">[] = [
  "vi_mo",
  "chung_khoan",
  "lai_suat",
  "bds",
  "vang",
];

/**
 * Đếm số keyword match mỗi topic, trả về topic có nhiều match nhất.
 */
export function detectTopic(message?: string | null): Topic {
  if (!message) return "khac";
  const lower = message.toLowerCase();
  const score: Record<string, number> = {};
  for (const t of TOPIC_ORDER) {
    let count = 0;
    for (const kw of KEYWORDS[t]) {
      if (lower.includes(kw)) count++;
    }
    if (count > 0) score[t] = count;
  }
  const entries = Object.entries(score);
  if (entries.length === 0) return "khac";
  entries.sort((a, b) => b[1] - a[1]);
  return entries[0][0] as Topic;
}
