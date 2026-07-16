/**
 * Moderation rule-based (MVP, không cần AI external).
 * Bao gồm:
 * - detectKeywordFlag(message)
 * - detectSentiment(message)
 * - calculateRiskLevel(message)
 * - suggestAction(comment)
 * - suggestReply(comment)
 * - moderateComment(message) - wrapper tiện dùng
 */

export type KeywordFlag = "spam" | "attack" | "common_question" | "none";
export type Sentiment = "positive" | "negative" | "neutral";
export type RiskLevel = "low" | "medium" | "high";
export type SuggestedAction = "hide_or_review" | "manual_review" | "suggest_reply" | "none";

export interface ModerationResult {
  keywordFlag: KeywordFlag;
  sentiment: Sentiment;
  riskLevel: RiskLevel;
  suggestedAction: SuggestedAction;
  suggestedReply: string | null;
}

// ---------- Keyword groups ----------

// Spam / mời chào
const SPAM_KEYWORDS = [
  "inbox em",
  "inbox anh",
  "ib em",
  "kiếm tiền nhanh",
  "kiem tien nhanh",
  "cam kết lợi nhuận",
  "cam ket loi nhuan",
  "nhóm vip",
  "nhom vip",
  "bảo hiểm lỗ",
  "bao hiem lo",
  "link đăng ký",
  "link dang ky",
  "zalo",
  "kéo nhóm",
  "keo nhom",
  "hợp tác đầu tư",
  "die coin",
  "sân bay",
];

// Công kích / chửi tục: list placeholder, KHÔNG dùng từ phản cảm thực sự trong code.
const ATTACK_KEYWORDS = [
  "lừa đảo",
  "lua dao",
  "scam",
  "ngu",
  "ngốc",
  "xàm",
  "rác",
  "nhảm nhí",
  "ảo tưởng",
  "ao tuong",
];

// Câu hỏi phổ biến
const COMMON_QUESTION_KEYWORDS: { keywords: string[]; reply: string }[] = [
  {
    keywords: ["nguồn đâu", "nguon dau", "nguồn data", "lấy ở đâu", "lay o dau"],
    reply:
      "Mình sẽ bổ sung nguồn dữ liệu hoặc giải thích thêm ở phần bình luận sau nhé.",
  },
  {
    keywords: [
      "có khuyến nghị mua không",
      "co khuyen nghiem mua khong",
      "khuyến nghị mua",
      "nên mua không",
      "nen mua khong",
    ],
    reply:
      "Nội dung chỉ nhằm mục đích phân tích và thảo luận, không phải khuyến nghị đầu tư cá nhân.",
  },
  {
    keywords: ["mua mã nào", "mua ma nao", "chọn mã nào", "chon ma nao"],
    reply:
      "Nội dung chỉ nhằm mục đích phân tích và thảo luận, không phải khuyến nghị đầu tư cá nhân.",
  },
  {
    keywords: ["bán chưa", "ban chua", "nên bán", "nen ban", "chốt lời", "cat loi"],
    reply:
      "Quyết định mua/bán phụ thuộc kế hoạch cá nhân. Bài viết chỉ phân tích dữ liệu, không khuyến nghị điểm vào/ra cụ thể.",
  },
  {
    keywords: ["room vip", "nhóm vip", "nhom vip", "vip group"],
    reply:
      "Hiện mình ưu tiên chia sẻ phân tích công khai trên Page, chưa dùng bình luận để mời chào nhóm đầu tư.",
  },
  {
    keywords: ["học ở đâu", "hoc o dau", "khóa học", "khoa hoc", "tài liệu", "tai lieu"],
    reply:
      "Mình đang tổng hợp tài liệu học phân tích cơ bản, bạn có thể nhắn tin cho Page để được hướng dẫn cập nhật.",
  },
];

const POSITIVE_KEYWORDS = ["hay", "cảm ơn", "cam on", "hữu ích", "huu ich", "tuyệt", "tuyet", "like", "cảm ơn ad", "👍"];
const NEGATIVE_KEYWORDS = ["tệ", "te", "sai", "nhàm", "nham", "chán", "chan", "không hợp", "khong hop"];

// ---------- helpers ----------

function includesAny(text: string, keywords: string[]): string | null {
  for (const k of keywords) {
    if (text.includes(k)) return k;
  }
  return null;
}

function normalize(s: string): string {
  return s.toLowerCase();
}

// ---------- public API ----------

export function detectKeywordFlag(message?: string | null): KeywordFlag {
  if (!message) return "none";
  const t = normalize(message);
  if (includesAny(t, SPAM_KEYWORDS)) return "spam";
  if (includesAny(t, ATTACK_KEYWORDS)) return "attack";
  for (const q of COMMON_QUESTION_KEYWORDS) {
    if (q.keywords.some((k) => t.includes(k))) return "common_question";
  }
  return "none";
}

export function detectSentiment(message?: string | null): Sentiment {
  if (!message) return "neutral";
  const t = normalize(message);
  let neg = 0;
  let pos = 0;
  for (const k of NEGATIVE_KEYWORDS) if (t.includes(k)) neg++;
  for (const k of POSITIVE_KEYWORDS) if (t.includes(k)) pos++;
  if (neg > pos) return "negative";
  if (pos > neg) return "positive";
  return "neutral";
}

export function calculateRiskLevel(
  message?: string | null,
  flag?: KeywordFlag,
  sentiment?: Sentiment,
): RiskLevel {
  const f = flag ?? detectKeywordFlag(message);
  const s = sentiment ?? detectSentiment(message);

  if (f === "spam") return "high";
  if (f === "attack") return "high";
  if (f === "common_question") return "low";
  if (s === "negative") return "medium";
  return "low";
}

export function suggestAction(
  message?: string | null,
  flag?: KeywordFlag,
  risk?: RiskLevel,
): SuggestedAction {
  const f = flag ?? detectKeywordFlag(message);
  const r = risk ?? calculateRiskLevel(message, f);
  if (f === "spam") return "hide_or_review";
  if (f === "attack") return "manual_review";
  if (f === "common_question") return "suggest_reply";
  if (r === "medium") return "manual_review";
  return "none";
}

export function suggestReply(message?: string | null, flag?: KeywordFlag): string | null {
  if (!message) return null;
  const t = normalize(message);
  const f = flag ?? detectKeywordFlag(message);
  if (f === "common_question") {
    for (const q of COMMON_QUESTION_KEYWORDS) {
      if (q.keywords.some((k) => t.includes(k))) return q.reply;
    }
  }
  if (f === "spam") {
    return "Cảm ơn bạn đã quan tâm. Hiện Page không nhận quảng cáo hoặc mời chào trong bình luận.";
  }
  return null;
}

export function moderateComment(message?: string | null): ModerationResult {
  const keywordFlag = detectKeywordFlag(message);
  const sentiment = detectSentiment(message);
  const riskLevel = calculateRiskLevel(message, keywordFlag, sentiment);
  const suggestedAction = suggestAction(message, keywordFlag, riskLevel);
  const suggestedReply = suggestReply(message, keywordFlag);
  return { keywordFlag, sentiment, riskLevel, suggestedAction, suggestedReply };
}
