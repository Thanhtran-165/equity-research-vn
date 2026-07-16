/**
 * Content Classification — topic and format detection from post text + DOM signals.
 *
 * Used by the automated collector to auto-classify collected posts.
 */

export interface ClassificationResult {
  topicTag: string;
  contentType: string;
  commercialSignal: boolean;
}

const TOPIC_KEYWORDS: Record<string, string[]> = {
  chung_khoan: [
    "chứng khoán", "cổ phiếu", "vn-index", "vnindex", "hose", "hnx",
    "bluechip", "phái sinh", "ticker", "mã cổ phiếu", "đầu tư chứng khoán",
    "vn30", "khối ngoại", "dòng tiền chứng khoán", "margin",
  ],
  vang_usd: [
    "vàng", "xauusd", "sjc", "doji", "usd", "tỷ giá", "dxy", "dollar",
    "hàng hóa", "dầu thô", "crude oil", "vàng thế giới", "giá vàng",
    "xagusd", "bạc", "silver",
  ],
  lai_suat: [
    "lãi suất", "ngân hàng", "nhnn", "sbv", "trái phiếu", "tín dụng",
    "cho vay", "repo", "refinancing", "oma", "deposit",
  ],
  bat_dong_san: [
    "bất động sản", "bđs", "căn hộ", "nhà đất", "đất nền", "dự án",
    "vinhomes", "masterise", "novaland", "tín dụng bất động sản",
  ],
  vi_mo: [
    "vĩ mô", "tăng trưởng", "lạm phát", "gdp", "ngân sách",
    "kinh tế vĩ mô", "fiscal", "monetary", "chính sách kinh tế",
  ],
  dia_chinh_tri: [
    "trump", "địa chính trị", "thương chiến", "mỹ trung", "putin",
    "ukraine", "israel", "iran", "tariff", "biểu thuế", "fed",
  ],
};

const COMMERCIAL_KEYWORDS = [
  "khóa học", "khoá học", "đăng ký", "đăng kí", "zalo", "hotline",
  "nhắn tin", "inbox", "liên hệ", "room vip", "room tín hiệu",
  "tư vấn đầu tư", "mở tài khoản", "chuyên viên tư vấn", "ib",
];

function countKeywordMatches(text: string, keywords: string[]): number {
  const lower = text.toLowerCase();
  let count = 0;
  for (const kw of keywords) {
    if (lower.includes(kw.toLowerCase())) count++;
  }
  return count;
}

/**
 * Classify a post by topic and format from its text content and optional DOM signals.
 */
export function classifyContent(
  text: string | null,
  domSignals?: { hasVideo?: boolean; hasPhoto?: boolean; hasLink?: boolean },
): ClassificationResult {
  const textLower = (text || "").toLowerCase();

  // Topic detection — pick the category with most keyword matches
  let bestTopic = "khac";
  let bestScore = 0;
  for (const [topic, keywords] of Object.entries(TOPIC_KEYWORDS)) {
    const score = countKeywordMatches(textLower, keywords);
    if (score > bestScore) {
      bestScore = score;
      bestTopic = topic;
    }
  }

  // Format detection
  let contentType = "text";
  if (domSignals?.hasVideo) {
    contentType = "video";
  } else if (domSignals?.hasPhoto) {
    contentType = "image";
  } else if (domSignals?.hasLink) {
    contentType = "link";
  }

  // Commercial signal detection
  const commercialSignal = countKeywordMatches(textLower, COMMERCIAL_KEYWORDS) > 0;

  return { topicTag: bestTopic, contentType, commercialSignal };
}

/**
 * Parse Vietnamese follower count text to number.
 * Handles formats like "23K", "188N", "1,2 Tr", "29K", "217N người theo dõi"
 */
export function parseFollowerCount(text: string): number | null {
  if (!text) return null;
  const lower = text.toLowerCase().trim();

  // Match patterns: "23k", "188n", "1,2 tr", "217k", "1.2tr", "1,234,567"
  const kMatch = lower.match(/([\d.,]+)\s*k/i);
  const nMatch = lower.match(/([\d.,]+)\s*n/i); // Vietnamese "nghìn" = thousand
  const trMatch = lower.match(/([\d.,]+)\s*tr/i); // Vietnamese "triệu" = million
  const rawMatch = lower.match(/([\d.]+)\s*người theo dõi/i);

  if (trMatch) {
    const num = parseFloat(trMatch[1].replace(",", "."));
    return Math.round(num * 1_000_000);
  }
  if (kMatch) {
    const num = parseFloat(kMatch[1].replace(",", "."));
    return Math.round(num * 1_000);
  }
  if (nMatch) {
    const num = parseFloat(nMatch[1].replace(",", "."));
    return Math.round(num * 1_000);
  }
  if (rawMatch) {
    const num = parseInt(rawMatch[1].replace(/[.,]/g, ""));
    if (Number.isFinite(num)) return num;
  }

  // Try plain number
  const plainNum = parseInt(lower.replace(/[^0-9]/g, ""));
  return Number.isFinite(plainNum) && plainNum > 0 ? plainNum : null;
}

/**
 * Parse Vietnamese metric count text to number.
 * Handles "106", "1,2 N", "12 N", "3,4 Tr", "1.234"
 */
export function parseMetricCount(text: string | null): number | null {
  if (!text || !text.trim()) return null;
  const lower = text.toLowerCase().trim();

  // Check for "N" (nghìn/thousand)
  const nMatch = lower.match(/([\d.,]+)\s*n\b/i);
  if (nMatch) {
    const num = parseFloat(nMatch[1].replace(",", "."));
    return Math.round(num * 1_000);
  }

  // Check for "Tr" (triệu/million)
  const trMatch = lower.match(/([\d.,]+)\s*tr\b/i);
  if (trMatch) {
    const num = parseFloat(trMatch[1].replace(",", "."));
    return Math.round(num * 1_000_000);
  }

  // Check for "K" (thousand)
  const kMatch = lower.match(/([\d.,]+)\s*k\b/i);
  if (kMatch) {
    const num = parseFloat(kMatch[1].replace(",", "."));
    return Math.round(num * 1_000);
  }

  // Plain number (strip non-numeric except dot and comma)
  const cleaned = lower.replace(/[^0-9.,]/g, "");
  if (!cleaned) return null;

  // Handle comma as thousand separator
  if (cleaned.includes(",") && !cleaned.includes(".")) {
    const parts = cleaned.split(",");
    if (parts.length === 2 && parts[1].length <= 2) {
      return parseFloat(cleaned.replace(",", ".")); // decimal
    }
    return parseInt(cleaned.replace(/,/g, ""));
  }

  const num = parseFloat(cleaned);
  return Number.isFinite(num) ? Math.round(num) : null;
}
