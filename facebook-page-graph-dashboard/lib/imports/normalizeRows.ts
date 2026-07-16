/**
 * Normalize rows từ raw cells → typed records.
 *
 * Hỗ trợ:
 * - Number parsing (comma/dot thousand separator)
 * - Date parsing (ISO, MM/DD/YYYY, DD/MM/YYYY, Vietnamese)
 * - URL canonicalization
 * - Message snippet trimming
 */
import type { ColumnMapping } from "./columnDetection";

export interface NormalizedRow {
  postId: string | null;
  permalinkUrl: string | null;
  externalContentId: string | null;
  createdTime: string | null; // ISO string
  messageSnippet: string | null;
  reach: number | null;
  impressions: number | null;
  engagedUsers: number | null;
  clicks: number | null;
  reactions: number | null;
  comments: number | null;
  shares: number | null;
  videoViews: number | null;
  watchTime: number | null;
  rawRowJson: string;
}

/**
 * Parse number từ string — strip thousand separator (comma hoặc dot).
 * Trả null nếu không parse được.
 *
 * Rules:
 * - "1,234" → 1234 (comma = thousand)
 * - "1.234" → 1234 (dot = thousand) BUT ONLY if integer part ≤ 3 digits
 * - "1234.567" → 1234.567 (dot = decimal, because integer part > 3 digits)
 * - "1,234.56" → 1234.56 (US: comma=thousand, dot=decimal)
 * - "1.234,56" → 1234.56 (EU: dot=thousand, comma=decimal)
 * - "2246375.241" → 2246375.241 (decimal, not thousand separator!)
 */
export function parseNumber(raw: string): number | null {
  if (raw == null) return null;
  const s = String(raw).trim();
  if (!s) return null;

  let cleaned = s.replace(/[^0-9.,\-]/g, "");
  if (!cleaned || cleaned === "-" || cleaned === ".") return null;

  const lastComma = cleaned.lastIndexOf(",");
  const lastDot = cleaned.lastIndexOf(".");
  if (lastComma > -1 && lastDot > -1) {
    if (lastComma > lastDot) {
      // EU/VI format: 1.234,56
      cleaned = cleaned.replace(/\./g, "").replace(",", ".");
    } else {
      // US format: 1,234.56
      cleaned = cleaned.replace(/,/g, "");
    }
  } else if (lastComma > -1) {
    // Chỉ có comma → có thể là thousand separator (1,234) hoặc decimal (1,5)
    const parts = cleaned.split(",");
    if (parts.length === 2 && parts[1].length <= 2) {
      cleaned = cleaned.replace(",", ".");
    } else {
      cleaned = cleaned.replace(/,/g, "");
    }
  } else if (lastDot > -1) {
    // Chỉ có dot → heuristic:
    // - Nếu integer part (trước dot) CÓ 1-3 digits → dot = thousand separator
    //   vd: "1.234" → 1234, "12.345" → 12345
    // - Nếu integer part CÓ 4+ digits → dot = decimal point
    //   vd: "1234.5" → 1234.5, "2246375.241" → 2246375.241
    const parts = cleaned.split(".");
    if (parts.length > 2) {
      // Nhiều dot → thousand separator (1.234.567)
      cleaned = cleaned.replace(/\./g, "");
    } else if (parts.length === 2) {
      const intPart = parts[0];
      const decPart = parts[1];
      if (intPart.length <= 3 && decPart.length === 3) {
        // "X.YYY" where X is 1-3 digits → thousand separator
        cleaned = cleaned.replace(/\./g, "");
      }
      // Otherwise keep as decimal: "1234.56", "2246375.241", "1.5", "1.24"
    }
  }

  const n = Number(cleaned);
  return Number.isFinite(n) ? n : null;
}

/**
 * Parse date từ string → ISO date string (date-only, no timezone shift).
 *
 * Trả về YYYY-MM-DD (date-only), KHÔNG dùng toISOString() để tránh
 * timezone shift (local midnight → UTC previous day).
 *
 * VD hỗ trợ:
 * - "2026-07-07" → "2026-07-07"
 * - "2026-07-07T10:30:00Z" → "2026-07-07"
 * - "07/07/2026" → "2026-07-07" (heuristic: nếu first > 12 → DD/MM)
 * - "7/7/2026" → "2026-07-07"
 * - "07-07-2026" → "2026-07-07"
 * - "7 tháng 7, 2026" → "2026-07-07"
 */
export function parseDate(raw: string): string | null {
  if (raw == null) return null;
  const s = String(raw).trim();
  if (!s) return null;

  // ISO direct: 2026-07-07 or 2026-07-07T10:30:00Z
  if (/^\d{4}-\d{2}-\d{2}/.test(s)) {
    const datePart = s.slice(0, 10);
    const d = new Date(datePart + "T00:00:00Z");
    if (isNaN(d.getTime())) return null;
    return datePart;
  }

  // Vietnamese: "7 tháng 7, 2026"
  const viMatch = s.match(/(\d{1,2})\s*tháng\s*(\d{1,2}),?\s*(\d{4})/);
  if (viMatch) {
    const [, d, m, y] = viMatch;
    const day = String(d).padStart(2, "0");
    const month = String(m).padStart(2, "0");
    const iso = `${y}-${month}-${day}`;
    const check = new Date(iso + "T00:00:00Z");
    if (isNaN(check.getTime())) return null;
    return iso;
  }

  // MM/DD/YYYY or DD/MM/YYYY (no timezone conversion!)
  const slashMatch = s.match(/^(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})/);
  if (slashMatch) {
    let [, a, b, y] = slashMatch;
    let month = Number(a);
    let day = Number(b);
    if (Number(a) > 12) {
      day = Number(a);
      month = Number(b);
    }
    const iso = `${y}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
    const check = new Date(iso + "T00:00:00Z");
    if (isNaN(check.getTime())) return null;
    return iso;
  }

  // YYYY/MM/DD
  const ymdMatch = s.match(/^(\d{4})[\/\-](\d{1,2})[\/\-](\d{1,2})/);
  if (ymdMatch) {
    const [, y, m, d] = ymdMatch;
    const iso = `${y}-${String(m).padStart(2, "0")}-${String(d).padStart(2, "0")}`;
    const check = new Date(iso + "T00:00:00Z");
    if (isNaN(check.getTime())) return null;
    return iso;
  }

  // Date.parse fallback (returns ISO string)
  const d = new Date(s);
  if (isNaN(d.getTime())) return null;
  // Extract date part only, no timezone shift
  return d.toISOString().slice(0, 10);
}

/**
 * Canonicalize URL — strip tracking params, normalize host.
 */
export function canonicalizeUrl(raw: string): string | null {
  if (raw == null) return null;
  let s = String(raw).trim();
  if (!s) return null;
  if (!/^https?:\/\//i.test(s)) {
    s = "https://" + s;
  }
  try {
    const u = new URL(s);
    // Facebook permalink thường có dạng /<page>/posts/<id> hoặc /<page>/videos/<id>
    // Strip query params tracking
    return u.origin + u.pathname;
  } catch {
    return s;
  }
}

/**
 * Trim message snippet — lấy tối đa 200 ký tự + normalize whitespace.
 */
export function normalizeMessageSnippet(raw: string): string | null {
  if (raw == null) return null;
  const s = String(raw).trim();
  if (!s) return null;
  return s.replace(/\s+/g, " ").slice(0, 500);
}

/**
 * Convert raw cells → NormalizedRow.
 */
export function normalizeRow(
  cells: string[],
  mapping: ColumnMapping,
): NormalizedRow {
  const get = (field: string): string | null => {
    const idx = mapping[field];
    if (idx == null) return null;
    return cells[idx] ?? null;
  };

  return {
    postId: get("postId")?.trim() || null,
    permalinkUrl: canonicalizeUrl(get("permalinkUrl") ?? "") ?? null,
    externalContentId: get("externalContentId")?.trim() || null,
    createdTime: parseDate(get("createdTime") ?? ""),
    messageSnippet: normalizeMessageSnippet(get("messageSnippet") ?? ""),
    reach: parseNumber(get("reach") ?? ""),
    impressions: parseNumber(get("impressions") ?? ""),
    engagedUsers: parseNumber(get("engagedUsers") ?? ""),
    clicks: parseNumber(get("clicks") ?? ""),
    reactions: parseNumber(get("reactions") ?? ""),
    comments: parseNumber(get("comments") ?? ""),
    shares: parseNumber(get("shares") ?? ""),
    videoViews: parseNumber(get("videoViews") ?? ""),
    watchTime: parseNumber(get("watchTime") ?? "") != null ? parseNumber(get("watchTime") ?? "") : null,
    rawRowJson: JSON.stringify(cells),
  };
}

export function normalizeRows(cells: string[][], mapping: ColumnMapping): NormalizedRow[] {
  return cells.map((row) => normalizeRow(row, mapping));
}
