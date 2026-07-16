// @ts-nocheck — one-time analysis script, already executed
/**
 * Build Balanced Peer Set v3.1 — merge all candidates from 2 search passes,
 * dedupe by entity + ecosystem, classify, score, and generate 7 output files.
 *
 * Core principles:
 * - Build Core Set from scratch (NOT keep-7 + add)
 * - Max 1 candidate per ecosystem
 * - Max 50% stock in Core Set
 * - At least 1 gold, 1 RE
 * - No groups/institutional/editorial in Direct Core
 * - Pure corporate → institutional_reference
 */
import { writeFileSync, mkdirSync } from "fs";
import { join } from "path";

const now = "2026-07-10";
const outDir = join(process.cwd(), "data", "benchmark");
const verifyDir = join(outDir, "manual-verification-v3-1");
mkdirSync(verifyDir, { recursive: true });

// ─── Types ──────────────────────────────────────────────
interface Cand {
  id: string;
  name: string;
  url: string;
  platform: string;
  objectType: string;
  operatingModel: string;
  classification: string; // independent_creator | broker_creator | corporate_affiliated | institutional | news_editorial | community_group | course_funnel | sales_advertising
  ecosystemId: string;
  ecosystemName: string;
  isIndependentCreator: boolean;
  category: string;
  scaleBand: string;
  followerCount: number | null;
  active: string;
  verified: string; // high | medium | low
  vertical: string; // stock | gold | re | macro
  topicOverlap: number;
  audienceOverlap: number;
  formatSimilarity: number;
  operatingModelSimilarity: number;
  postingFrequency: number;
  publicDataAvailability: number;
  scaleComparability: number;
  contentConsistency: number;
  commercialNoiseRisk: number;
  identityConfidence: number;
  notes: string;
  sampleValidated: boolean;
  observedPostCount: number;
  videoShare: number | null;
}

function fit(c: Partial<Cand>): number {
  return (
    (c.topicOverlap ?? 3) * 0.20 +
    (c.audienceOverlap ?? 3) * 0.15 +
    (c.formatSimilarity ?? 3) * 0.10 +
    (c.operatingModelSimilarity ?? 3) * 0.20 +
    (c.postingFrequency ?? 3) * 0.10 +
    (c.publicDataAvailability ?? 3) * 0.10 +
    (c.scaleComparability ?? 3) * 0.05 +
    (c.contentConsistency ?? 3) * 0.05 +
    (c.identityConfidence ?? 3) * 0.05 -
    (c.commercialNoiseRisk ?? 2) * 0.05
  );
}

function scale(followers: number | null): string {
  if (!followers) return "unknown";
  if (followers < 10000) return "micro";
  if (followers < 100000) return "small";
  if (followers < 500000) return "medium";
  return "large";
}

function esc(s: unknown): string {
  if (s == null) return "";
  const str = String(s);
  if (str.includes(",") || str.includes('"') || str.includes("\n")) return `"${str.replace(/"/g, '""')}"`;
  return str;
}

// ─── Helper to create candidates ────────────────────────
let counter = 0;
function mk(p: Partial<Cand> & { name: string; url: string }): Cand {
  counter++;
  const c: Cand = {
    id: `V31-${String(counter).padStart(3, "0")}`,
    platform: "facebook",
    objectType: "facebook_page",
    operatingModel: "other",
    classification: "independent_creator",
    ecosystemId: `ECO-${counter}`,
    ecosystemName: "",
    isIndependentCreator: true,
    category: "other",
    scaleBand: "unknown",
    followerCount: null,
    active: "active",
    verified: "medium",
    vertical: "macro",
    topicOverlap: 3,
    audienceOverlap: 3,
    formatSimilarity: 3,
    operatingModelSimilarity: 3,
    postingFrequency: 3,
    publicDataAvailability: 3,
    scaleComparability: 3,
    contentConsistency: 3,
    commercialNoiseRisk: 2,
    identityConfidence: 3,
    notes: "",
    sampleValidated: false,
    observedPostCount: 0,
    videoShare: null,
    ...p,
  };
  c.scaleBand = scale(c.followerCount);
  return c;
}

// ─── ALL CANDIDATES (merged from 2 passes) ──────────────
// STOCK CREATORS
const stockCands: Cand[] = [
  mk({ name: "Ichimoku Quốc Cường", url: "https://facebook.com/ichimoku.quoccuong/", objectType: "facebook_page", operatingModel: "stock_creator", classification: "independent_creator", ecosystemId: "ICHIMOKU", ecosystemName: "Ichimoku/ITP", followerCount: 188535, vertical: "stock", topicOverlap: 5, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 5, postingFrequency: 5, publicDataAvailability: 4, scaleComparability: 2, contentConsistency: 4, identityConfidence: 4, verified: "high", videoShare: 80, notes: "~188K likes; ITP co-founder; daily VNIndex livestreams" }),
  mk({ name: "Ichimoku Trịnh Phát", url: "https://facebook.com/IchimokuTrinhPhat.ITP/", objectType: "facebook_page", operatingModel: "stock_creator", classification: "corporate_affiliated", ecosystemId: "ICHIMOKU", ecosystemName: "Ichimoku/ITP", isIndependentCreator: false, vertical: "stock", topicOverlap: 5, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 3, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "Same ITP ecosystem as Quốc Cường" }),
  mk({ name: "CLB ICHIMOKU", url: "https://facebook.com/CLB.ICHIMOKU/", objectType: "facebook_page", operatingModel: "stock_creator", classification: "corporate_affiliated", ecosystemId: "ICHIMOKU", ecosystemName: "Ichimoku/ITP", isIndependentCreator: false, vertical: "stock", topicOverlap: 5, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 3, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 3, identityConfidence: 3, verified: "medium", notes: "Community page for ITP ecosystem" }),
  mk({ name: "Kolia Phan", url: "https://facebook.com/koliaphan/", objectType: "facebook_page", operatingModel: "stock_creator", classification: "independent_creator", ecosystemId: "KOLIA", ecosystemName: "Kolia Phan", followerCount: 43939, vertical: "stock", topicOverlap: 5, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 5, publicDataAvailability: 4, scaleComparability: 3, contentConsistency: 4, identityConfidence: 4, verified: "high", notes: "Forbes VN Top 6 Finance KOL 2024; multi-asset (stocks, gold, silver); daily commentary" }),
  mk({ name: "Chứng Khoán 5 Phút", url: "https://facebook.com/TuyenDauTu/", objectType: "facebook_page", operatingModel: "stock_creator", classification: "independent_creator", ecosystemId: "CK5P", ecosystemName: "Chứng Khoán 5 Phút", followerCount: 23628, vertical: "stock", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "Multi-platform video; YouTube 18.7K subs" }),
  mk({ name: "SmartF", url: "https://facebook.com/smartf.page/", objectType: "facebook_page", operatingModel: "stock_creator", classification: "independent_creator", ecosystemId: "SMARTF", ecosystemName: "SmartF", followerCount: 91870, vertical: "stock", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 3, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "In-depth securities analysis; ~92K likes; strong video" }),
  mk({ name: "AzFin Viet Nam (Dang Tran Phuc)", url: "https://facebook.com/AzFinVietNam/", objectType: "facebook_page", operatingModel: "stock_creator", classification: "independent_creator", ecosystemId: "AZFIN", ecosystemName: "AzFin", vertical: "stock", topicOverlap: 5, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 3, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "Value investing; YouTube 102K subs; stock valuation" }),
  mk({ name: "Cu Thong Thai", url: "https://facebook.com/CuThongThai.VNInvestor/", objectType: "facebook_page", operatingModel: "stock_creator", classification: "independent_creator", ecosystemId: "CTT", ecosystemName: "Cú Thông Thái", vertical: "stock", topicOverlap: 5, audienceOverlap: 4, formatSimilarity: 3, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "F0 investing tutorials; published author; multi-platform" }),
  mk({ name: "Lynch Phan", url: "https://facebook.com/lynchphan/", objectType: "facebook_page", operatingModel: "stock_creator", classification: "independent_creator", ecosystemId: "LYNCH", ecosystemName: "Lynch Phan / Take Profit", vertical: "stock", topicOverlap: 5, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 3, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "Take Profit Holdings; Stock Show; fundamental analysis courses" }),
  mk({ name: "LCTV Investment (Ngo Minh Duc)", url: "https://facebook.com/lctv.vn/", objectType: "facebook_page", operatingModel: "stock_creator", classification: "independent_creator", ecosystemId: "LCTV", ecosystemName: "LCTV", vertical: "stock", topicOverlap: 5, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 3, identityConfidence: 3, verified: "medium", notes: "CEO Ngo Minh Duc; TA livestreams; multi-platform" }),
  mk({ name: "TCDC News", url: "https://facebook.com/tcdcnews/", objectType: "facebook_page", operatingModel: "stock_creator", classification: "independent_creator", ecosystemId: "TCDC", ecosystemName: "TCDC News", vertical: "stock", topicOverlap: 5, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 5, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "Daily market analysis videos; VN-Index; foreign flow tracking" }),
  mk({ name: "Sơn Chứng Khoán", url: "https://facebook.com/927906937079284", objectType: "facebook_page", operatingModel: "stock_creator", classification: "independent_creator", ecosystemId: "SONCK", ecosystemName: "Sơn CK", vertical: "stock", topicOverlap: 5, audienceOverlap: 4, formatSimilarity: 3, operatingModelSimilarity: 4, postingFrequency: 3, publicDataAvailability: 4, scaleComparability: 4, identityConfidence: 2, verified: "low", notes: "Stock commentator; persona-style" }),
  mk({ name: "The Reviewer", url: "https://facebook.com/100090652970156/", objectType: "facebook_page", operatingModel: "stock_creator", classification: "independent_creator", ecosystemId: "REVIEWER", ecosystemName: "The Reviewer", vertical: "stock", topicOverlap: 5, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 3, publicDataAvailability: 3, scaleComparability: 4, identityConfidence: 2, verified: "low", notes: "In-depth stock analysis videos (NAF, F88, HPDE)" }),
  mk({ name: "Finguru Viet Nam", url: "https://facebook.com/finguruvietnam/", objectType: "facebook_page", operatingModel: "stock_creator", classification: "independent_creator", ecosystemId: "FINGURU", ecosystemName: "Finguru", vertical: "stock", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 3, operatingModelSimilarity: 3, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 3, identityConfidence: 3, verified: "medium", notes: "Data-driven foreign flow analysis; weekly reports" }),
  mk({ name: "Thong To Chung Khoan", url: "https://facebook.com/Thongtochungkhoan/", objectType: "facebook_page", operatingModel: "stock_creator", classification: "independent_creator", ecosystemId: "TTCK", ecosystemName: "Thông Tô CK", vertical: "stock", topicOverlap: 5, audienceOverlap: 4, formatSimilarity: 3, operatingModelSimilarity: 3, postingFrequency: 5, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 3, identityConfidence: 3, verified: "medium", notes: "Stock market intelligence; KQKD; manipulation alerts" }),
];

// GOLD / COMMODITY CREATORS
const goldCands: Cand[] = [
  mk({ name: "Ngân Talk", url: "https://facebook.com/ngantalk/", objectType: "facebook_page", operatingModel: "gold_creator", classification: "independent_creator", ecosystemId: "NGANTALK", ecosystemName: "Ngân Talk", followerCount: 217635, vertical: "gold", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 5, scaleComparability: 2, contentConsistency: 5, identityConfidence: 4, verified: "high", notes: "~218K likes; gold/silver commentator; Monthly Gold Compass; no signals/courses" }),
  mk({ name: "Huỳnh Trung Khánh", url: "unverified", objectType: "facebook_profile", operatingModel: "gold_creator", classification: "institutional", isIndependentCreator: false, ecosystemId: "VGTA", ecosystemName: "VGTA/WGC", vertical: "gold", topicOverlap: 4, audienceOverlap: 3, formatSimilarity: 2, operatingModelSimilarity: 2, postingFrequency: 2, publicDataAvailability: 2, scaleComparability: 2, identityConfidence: 2, verified: "low", notes: "VGTA Vice Chairman; WGC advisor; URL unverified" }),
  mk({ name: "Trần Duy Phương (DFF)", url: "https://facebook.com/tranduyphuong7979/", objectType: "facebook_profile", operatingModel: "gold_creator", classification: "independent_creator", ecosystemId: "DFF", ecosystemName: "DFF/Trần Duy Phương", followerCount: 40296, vertical: "gold", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 3, contentConsistency: 4, identityConfidence: 4, verified: "high", notes: "~40K likes; gold analyst; SJC vs world; VTC News regular" }),
  mk({ name: "King Traders (Hoang Vy Master)", url: "https://facebook.com/thitruongphaisinh/", objectType: "facebook_page", operatingModel: "commodity_creator", classification: "independent_creator", ecosystemId: "KINGTRADER", ecosystemName: "King Traders", vertical: "gold", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 3, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "Gold/XAUUSD trading strategies; Fed rate videos" }),
  mk({ name: "Hua Cuong (Shane Hua)", url: "https://facebook.com/ShaneHua.Investor/", objectType: "facebook_profile", operatingModel: "commodity_creator", classification: "independent_creator", ecosystemId: "SHANE", ecosystemName: "Shane Hua / Elliott Wave", followerCount: 16900, vertical: "gold", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 3, scaleComparability: 4, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "First VN CEWA-M analyst; daily XAUUSD TA; ~17K" }),
  mk({ name: "Master Bollinger Bands", url: "https://facebook.com/masterbollingerbands/", objectType: "facebook_page", operatingModel: "commodity_creator", classification: "independent_creator", ecosystemId: "MBB", ecosystemName: "Master Bollinger Bands", vertical: "gold", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "Regular vàng-bạc-DXY analysis videos" }),
  mk({ name: "Kolia Phan (gold)", url: "https://facebook.com/koliaphan/", objectType: "facebook_page", operatingModel: "gold_creator", classification: "independent_creator", ecosystemId: "KOLIA", ecosystemName: "Kolia Phan", followerCount: 43939, vertical: "gold", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 5, publicDataAvailability: 4, scaleComparability: 3, contentConsistency: 4, identityConfidence: 4, verified: "high", notes: "Also strong gold content; Forbes Top 6; multi-asset" }),
  mk({ name: "Ngô Văn Dương", url: "https://facebook.com/NgoVanDuong04/", objectType: "facebook_page", operatingModel: "gold_creator", classification: "independent_creator", ecosystemId: "NVD", ecosystemName: "Ngô Văn Dương", vertical: "gold", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 5, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "Daily XAUUSD TA videos; breakout patterns" }),
  mk({ name: "Phan Hiếu Kỳ (PHK Academy)", url: "https://facebook.com/phanhieuky102/", objectType: "facebook_page", operatingModel: "gold_creator", classification: "course_funnel", isIndependentCreator: false, ecosystemId: "PHK", ecosystemName: "PHK Academy", vertical: "gold", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 3, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 4, commercialNoiseRisk: 3, identityConfidence: 3, verified: "medium", notes: "Gold TA educator; ebook; daily buy/sell strategy; PHK Academy funnel" }),
  mk({ name: "Hùng BigMan", url: "https://facebook.com/hungbigman/", objectType: "facebook_page", operatingModel: "macro_creator", classification: "independent_creator", ecosystemId: "BIGMAN", ecosystemName: "Hùng BigMan", followerCount: 80324, vertical: "gold", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 3, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "~80K likes; multi-asset (gold, RE, BTC, stocks)" }),
];

// REAL ESTATE CREATORS
const reCands: Cand[] = [
  mk({ name: "Trần Khánh Quang", url: "https://facebook.com/quang1505/", objectType: "facebook_page", operatingModel: "real_estate_creator", classification: "independent_creator", ecosystemId: "TKQ", ecosystemName: "Trần Khánh Quang / Việt An Hoa", followerCount: 18268, vertical: "re", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 4, identityConfidence: 4, verified: "high", notes: "CEO Việt An Hoa; RE cycle analysis; cash-flow rotation; ~18K likes" }),
  mk({ name: "Phạm Văn Nam", url: "https://facebook.com/phamvannamb/", objectType: "facebook_page", operatingModel: "real_estate_creator", classification: "independent_creator", ecosystemId: "PVN", ecosystemName: "Phạm Văn Nam", followerCount: 85965, vertical: "re", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 3, contentConsistency: 4, identityConfidence: 4, verified: "high", notes: "~86K likes; 15+ yrs; 7 books; apartment/land analysis; multi-platform" }),
  mk({ name: "Lê Quốc Kiên", url: "https://facebook.com/lequockienbds/", objectType: "facebook_page", operatingModel: "real_estate_creator", classification: "independent_creator", ecosystemId: "LQK", ecosystemName: "Lê Quốc Kiên", vertical: "re", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "Independent RE consultant; press analyst; housing credit; price/income ratios" }),
  mk({ name: "Trần Văn Định", url: "https://facebook.com/mrtranvandinh/", objectType: "facebook_page", operatingModel: "real_estate_creator", classification: "independent_creator", ecosystemId: "TVD", ecosystemName: "Trần Văn Định", followerCount: 137141, vertical: "re", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 2, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "~137K likes; RE educator; 2025-2027 forecasts; hotspot analysis" }),
  mk({ name: "Trần Minh BDS", url: "https://facebook.com/tranminhbds/", objectType: "facebook_page", operatingModel: "real_estate_broker", classification: "broker_creator", ecosystemId: "TM", ecosystemName: "Trần Minh BDS", vertical: "re", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "Broker/influencer; author; market analysis videos; multi-platform" }),
  mk({ name: "Hoàng Quốc Dũng", url: "https://facebook.com/hoangquocdungvtv/", objectType: "facebook_page", operatingModel: "real_estate_creator", classification: "independent_creator", ecosystemId: "HQD", ecosystemName: "Hoàng Quốc Dũng / Review BĐS", followerCount: 28179, vertical: "re", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "~28K likes; admin Review BĐS group; project reviews; how-to videos" }),
  mk({ name: "NewsRealVN", url: "https://facebook.com/NewsRealVN", objectType: "facebook_page", operatingModel: "real_estate_creator", classification: "independent_creator", ecosystemId: "NEWSREAL", ecosystemName: "NewsRealVN", vertical: "re", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 3, publicDataAvailability: 3, scaleComparability: 4, contentConsistency: 4, identityConfidence: 2, verified: "low", notes: "Deep RE-cycle analysis; interest-rate/cash-flow framing" }),
  mk({ name: "Realtique Vietnam", url: "https://facebook.com/RealtiqueVietnam/", objectType: "facebook_page", operatingModel: "real_estate_creator", classification: "independent_creator", ecosystemId: "REALTIQUE", ecosystemName: "Realtique VN", vertical: "re", topicOverlap: 4, audienceOverlap: 3, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 3, publicDataAvailability: 3, scaleComparability: 4, contentConsistency: 3, identityConfidence: 3, verified: "medium", notes: "RE content creator; bullish VN RE theses; 30-yr history; multi-platform" }),
  mk({ name: "Nhà Tốt TV", url: "https://facebook.com/NhaTotTV/", objectType: "facebook_page", operatingModel: "real_estate_creator", classification: "independent_creator", ecosystemId: "NHA TOT", ecosystemName: "Nhà Tốt TV", vertical: "re", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "RE investment videos; Vinhomes/Masterise/CapitaLand; TikTok 25K" }),
  mk({ name: "Nguyễn Văn Hanh BĐS", url: "https://facebook.com/datrungvietnam/", objectType: "facebook_page", operatingModel: "real_estate_broker", classification: "broker_creator", ecosystemId: "NVH", ecosystemName: "Nguyễn Văn Hanh", vertical: "re", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "Land-use-fee analysis; Vinhomes; gold-vs-RE strategy" }),
];

// MACRO / MULTI-ASSET CREATORS
const macroCands: Cand[] = [
  mk({ name: "Chau Xuan Nguyen", url: "https://facebook.com/tamnhinkinhtevimo", objectType: "facebook_page", operatingModel: "macro_creator", classification: "independent_creator", ecosystemId: "CXN", ecosystemName: "Châu Xuân Nguyễn", followerCount: 22014, vertical: "macro", topicOverlap: 5, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 5, identityConfidence: 4, verified: "high", notes: "~22K likes; 'rare independent economic voice'; GDP/fiscal/monetary critique" }),
  mk({ name: "Hieu.TV", url: "https://facebook.com/hieuhiinvest", objectType: "facebook_page", operatingModel: "macro_creator", classification: "independent_creator", ecosystemId: "HIEUTV", ecosystemName: "Hieu.TV", followerCount: 9249, vertical: "macro", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "Financial freedom; multi-asset (stocks, gold); podcast; 9.2K likes" }),
  mk({ name: "Fandi Finance & Invest", url: "https://facebook.com/Fandi.FinanceandInvest/", objectType: "facebook_page", operatingModel: "macro_creator", classification: "independent_creator", ecosystemId: "FANDI", ecosystemName: "Fandi Finance", vertical: "macro", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 4, identityConfidence: 3, verified: "medium", notes: "Weekly gold rush decoding; multi-asset positioning" }),
  mk({ name: "FinPeace (Nguyễn Tuấn Anh)", url: "https://facebook.com/tuananhfinpeace/", objectType: "facebook_page", operatingModel: "macro_creator", classification: "independent_creator", ecosystemId: "FINPEACE", ecosystemName: "FinPeace", vertical: "macro", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 3, operatingModelSimilarity: 4, postingFrequency: 3, publicDataAvailability: 3, scaleComparability: 4, contentConsistency: 3, identityConfidence: 2, verified: "low", notes: "Multi-asset investor (gold + stocks); wealth education" }),
  mk({ name: "AnFin", url: "https://facebook.com/anfin.vn/", objectType: "facebook_page", operatingModel: "commodity_creator", classification: "corporate_affiliated", isIndependentCreator: false, ecosystemId: "ANFIN", ecosystemName: "AnFin", followerCount: 70000, vertical: "gold", topicOverlap: 4, audienceOverlap: 3, formatSimilarity: 3, operatingModelSimilarity: 2, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 3, commercialNoiseRisk: 3, identityConfidence: 3, verified: "medium", notes: "~70K likes; MXV-licensed derivatives app; WTI/gold analysis; corporate" }),
  mk({ name: "TraderViet", url: "https://facebook.com/TraderVietcom/", objectType: "facebook_page", operatingModel: "commodity_creator", classification: "community_group", isIndependentCreator: false, ecosystemId: "TV", ecosystemName: "TraderViet", followerCount: 112726, vertical: "gold", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 3, postingFrequency: 5, publicDataAvailability: 4, scaleComparability: 3, contentConsistency: 4, identityConfidence: 3, verified: "high", notes: "~113K likes; trading community; XAUUSD/forex TA; forum" }),
  mk({ name: "Săn Leader", url: "https://facebook.com/sanleader.vn", objectType: "facebook_page", operatingModel: "macro_creator", classification: "independent_creator", ecosystemId: "SANLEADER", ecosystemName: "Săn Leader", vertical: "macro", topicOverlap: 4, audienceOverlap: 4, formatSimilarity: 4, operatingModelSimilarity: 4, postingFrequency: 4, publicDataAvailability: 4, scaleComparability: 4, contentConsistency: 3, identityConfidence: 3, verified: "medium", notes: "Stocks/forex/gold/macro educator; DXY/USD; free content" }),
];

// ─── Merge + dedupe by URL and name ─────────────────────
const all = [...stockCands, ...goldCands, ...reCands, ...macroCands];
const seenUrl = new Set<string>();
const seenName = new Set<string>();
const deduped: Cand[] = [];
for (const c of all) {
  const urlKey = c.url.toLowerCase().replace(/\/+$/, "");
  const nameKey = c.name.toLowerCase().replace(/\s+/g, " ").trim();
  if (c.url !== "unverified" && seenUrl.has(urlKey)) continue;
  if (seenName.has(nameKey)) continue;
  if (c.url !== "unverified") seenUrl.add(urlKey);
  seenName.add(nameKey);
  deduped.push(c);
}

// Score all
const scored = deduped.map(c => ({ ...c, fitScore: parseFloat(fit(c).toFixed(2)) }));

// ─── Ecosystem dedup: max 1 per ecosystem in Core ───────
const ecosystemBest = new Map<string, typeof scored[0]>();
for (const c of scored) {
  if (c.objectType === "facebook_group" || c.classification === "institutional" || c.classification === "news_editorial" || c.classification === "corporate_affiliated" || c.classification === "course_funnel") continue;
  const existing = ecosystemBest.get(c.ecosystemId);
  if (!existing || c.fitScore > existing.fitScore) {
    ecosystemBest.set(c.ecosystemId, c);
  }
}

// ─── Build Core Set from scratch ────────────────────────
// Target: 3-4 stock, 2 gold, 2 RE, 1-2 macro, max 1 scale ref
const eligible = Array.from(ecosystemBest.values()).sort((a, b) => b.fitScore - a.fitScore);

interface CorePick {
  cand: typeof scored[0];
  vertical: string;
  reason: string;
}

const corePicks: CorePick[] = [];
const usedEcosystems = new Set<string>();
const maxByVertical: Record<string, number> = { stock: 4, gold: 2, re: 2, macro: 2 };
const currentByVertical: Record<string, number> = { stock: 0, gold: 0, re: 0, macro: 0 };

// First pass: fill quotas by vertical priority
for (const c of eligible) {
  if (corePicks.length >= 10) break;
  if (usedEcosystems.has(c.ecosystemId)) continue;
  const v = c.vertical;
  if (currentByVertical[v] >= maxByVertical[v]) continue;

  // Core requirements check
  if (c.fitScore < 3.5) continue;
  if (c.operatingModelSimilarity < 3) continue;
  if (c.topicOverlap < 3) continue;
  if (c.publicDataAvailability < 3) continue;
  if (c.verified === "low" && c.fitScore < 3.8) continue; // stricter for low-confidence

  corePicks.push({ cand: c, vertical: v, reason: `fit=${c.fitScore}; ${v}; ${c.ecosystemName}` });
  usedEcosystems.add(c.ecosystemId);
  currentByVertical[v]++;
}

// ─── 12 Replacement shortlist (4 stock, 3 gold, 3 RE, 2 macro) ────
const shortlistTargets: Record<string, number> = { stock: 4, gold: 3, re: 3, macro: 2 };
const shortlistCurrent: Record<string, number> = { stock: 0, gold: 0, re: 0, macro: 0 };
const replacementShortlist: typeof scored[] = [];
const slUsedEco = new Set<string>();

for (const c of eligible.sort((a, b) => b.fitScore - a.fitScore)) {
  const v = c.vertical;
  if (shortlistCurrent[v] >= shortlistTargets[v]) continue;
  if (slUsedEco.has(c.ecosystemId) && shortlistCurrent[v] > 0) {
    // Allow 2nd from same ecosystem in shortlist if quota not met
  }
  replacementShortlist.push(c);
  shortlistCurrent[v]++;
  slUsedEco.add(c.ecosystemId);
  if (replacementShortlist.length >= 12) break;
}

// ─── Generate all 7 files ───────────────────────────────

// 1. expanded-targeted-candidates-v3-1.csv
const csv1Headers = ["candidateId","name","canonicalUrl","platform","objectType","operatingModel","classification","ecosystemId","ecosystemName","isIndependentCreator","category","scaleBand","followerCount","activeStatus","verified","vertical","topicOverlapScore","audienceOverlapScore","formatSimilarityScore","operatingModelSimilarityScore","postingFrequencyScore","publicDataAvailabilityScore","scaleComparabilityScore","contentConsistencyScore","commercialNoiseRiskScore","identityConfidenceScore","totalFitScoreV3","observedPostCount","videoShare","lastVerifiedAt","notes"];
const csv1Lines = [csv1Headers.join(",")];
for (const c of scored) {
  csv1Lines.push([c.id,c.name,c.url,c.platform,c.objectType,c.operatingModel,c.classification,c.ecosystemId,c.ecosystemName,c.isIndependentCreator,c.category,c.scaleBand,c.followerCount ?? "",c.active,c.verified,c.vertical,c.topicOverlap,c.audienceOverlap,c.formatSimilarity,c.operatingModelSimilarity,c.postingFrequency,c.publicDataAvailability,c.scaleComparability,c.contentConsistency,c.commercialNoiseRisk,c.identityConfidence,c.fitScore,c.observedPostCount,c.videoShare ?? "",now,c.notes].map(esc).join(","));
}
writeFileSync(join(outDir, "expanded-targeted-candidates-v3-1.csv"), csv1Lines.join("\n") + "\n");

// 2. verification-checklist.csv
const csv2Headers = ["candidateId","name","proposedVertical","canonicalUrl","urlVerified","objectType","active","latestPostDate","followersVisible","followersCount","reactionsVisible","commentsVisible","sharesVisible","videoViewsVisible","samplePostsChecked","dominantTopics","dominantFormats","brokerageActivity","commercialNoise","verificationDecision","notes"];
const csv2Lines = [csv2Headers.join(",")];
const needVerify = scored.filter(c => c.verified !== "high" && c.objectType !== "facebook_group").slice(0, 30);
for (const c of needVerify) {
  csv2Lines.push([c.id,c.name,c.vertical,c.url,c.verified === "high" ? "yes" : "unverified",c.objectType,"","","","","","","","","","","","","","","uncertain",c.notes].map(esc).join(","));
}
writeFileSync(join(verifyDir, "verification-checklist.csv"), csv2Lines.join("\n") + "\n");

// 3. verification-guide.md
writeFileSync(join(verifyDir, "verification-guide.md"), `# Manual Verification Guide v3.1

## Mục tiêu
Xác minh thủ công các ứng viên quan trọng mà search engine không index đầy đủ.

## Quy trình từng ứng viên

1. Mở canonical URL trong verification-checklist.csv
2. Kiểm tra:
   - URL đúng page/profile không?
   - Page đang hoạt động? Bài gần nhất cách bao lâu?
   - Follower count có nhìn thấy không?
   - Reactions/Comments/Shares có nhìn thấy không?
   - 8-10 bài gần đây thuộc chủ đề gì?
   - Tỷ lệ video bao nhiêu?
   - Có hoạt động brokerage/room/course không?

3. Điền verificationDecision:
   - approve_direct_candidate: đủ chuẩn Core
   - approve_extended: tốt cho Extended
   - topic_reference: chỉ tham chiếu
   - reject: không phù hợp
   - uncertain: cần thêm thông tin

## Quy tắc
- Blank = chưa kiểm tra
- Không bịa follower count
- Không tự động approve chỉ vì tên chứa "chứng khoán"
`);

// 4. candidate-links.md
const linksLines = ["# Candidate Links — Manual Verification v3.1", "", "## Direct links để user kiểm tra nhanh", ""];
for (const c of scored.filter(c => c.objectType !== "facebook_group" && c.url !== "unverified").slice(0, 30)) {
  linksLines.push(`### ${c.name} (${c.vertical}, fit=${c.fitScore})`);
  linksLines.push(`- URL: ${c.url}`);
  linksLines.push(`- Type: ${c.objectType} | Model: ${c.operatingModel} | Ecosystem: ${c.ecosystemName}`);
  linksLines.push(`- Verified: ${c.verified} | Scale: ${c.scaleBand}${c.followerCount ? ` (${c.followerCount.toLocaleString()})` : ""}`);
  linksLines.push("");
}
writeFileSync(join(verifyDir, "candidate-links.md"), linksLines.join("\n") + "\n");

// 5. replacement-shortlist-v3-1.csv
const csv5Headers = ["rank","name","canonicalUrl","objectType","operatingModel","classification","ecosystem","vertical","totalFitScoreV3","verificationConfidence","followerCount","scaleBand","identityStatus","why_include","why_exclude","recommendedRole","notes"];
const csv5Lines = [csv5Headers.join(",")];
replacementShortlist.forEach((c, i) => {
  csv5Lines.push([i+1,c.name,c.url,c.objectType,c.operatingModel,c.classification,c.ecosystemName,c.vertical,c.fitScore,c.verified,c.followerCount ?? "",c.scaleBand,c.identityConfidence >= 4 ? "verified" : c.identityConfidence >= 3 ? "likely" : "unverified",`fit=${c.fitScore}; topic=${c.topicOverlap}; opModel=${c.operatingModelSimilarity}`,c.scaleComparability <= 2 ? "scale mismatch" : c.verified === "low" ? "URL unverified" : "","direct_core_candidate",c.notes].map(esc).join(","));
});
writeFileSync(join(outDir, "replacement-shortlist-v3-1.csv"), csv5Lines.join("\n") + "\n");

// 6. public-benchmark-peer-set-v3-1-proposed.csv
const csv6Headers = ["name","canonicalUrl","objectType","operatingModel","classification","ecosystemId","scaleBand","benchmarkRole","vertical","collectionFrequency","recommendedPostsPerCollection","fitScore","verificationConfidence","videoShare","notes"];
const csv6Lines = [csv6Headers.join(",")];
// Core picks
for (const p of corePicks) {
  csv6Lines.push([p.cand.name,p.cand.url,p.cand.objectType,p.cand.operatingModel,p.cand.classification,p.cand.ecosystemId,p.cand.scaleBand,"direct_core_peer",p.vertical,"weekly",4,p.cand.fitScore,p.cand.verified,p.cand.videoShare ?? "","PROPOSED v3.1 Core — "+p.reason+" — "+p.cand.notes].map(esc).join(","));
}
// Extended (next tier independent creators not in core)
const extended = eligible.filter(c => !usedEcosystems.has(c.ecosystemId) && c.fitScore >= 3.3).slice(0, 10);
for (const c of extended) {
  csv6Lines.push([c.name,c.url,c.objectType,c.operatingModel,c.classification,c.ecosystemId,c.scaleBand,"extended_creator_peer",c.vertical,"biweekly",3,c.fitScore,c.verified,c.videoShare ?? "","PROPOSED v3.1 Extended — "+c.notes].map(esc).join(","));
}
// Institutional/topic references (corporate, news, groups)
const refs = scored.filter(c => c.classification === "institutional" || c.classification === "news_editorial" || c.classification === "corporate_affiliated" || c.objectType === "facebook_group").slice(0, 15);
for (const c of refs) {
  csv6Lines.push([c.name,c.url,c.objectType,c.operatingModel,c.classification,c.ecosystemId,c.scaleBand,"topic_reference",c.vertical,"monthly",0,c.fitScore,c.verified,c.videoShare ?? "","PROPOSED v3.1 Topic Ref — "+c.notes].map(esc).join(","));
}
// Existing 7 peers (all downgraded per audit)
const existingDowngrades = [
  { name: "Người Quan Sát", url: "https://facebook.com/nguoiquansat.thongtintaichinh/", role: "topic_reference", reason: "Media outlet 563K; 12.5× scale; editorial" },
  { name: "VTV Index", url: "https://facebook.com/VTVIndex/", role: "topic_reference", reason: "VTV institutional media" },
  { name: "DFFVN", url: "https://facebook.com/dffvn.official/", role: "pending_verification", reason: "May be independent creator — needs 8-post check" },
  { name: "Kafi.vn", url: "https://facebook.com/Kafi.vn/", role: "institutional_reference", reason: "Corporate securities brand" },
  { name: "Thời Báo Ngân Hàng", url: "https://facebook.com/thoibaonganhang.vn/", role: "institutional_reference", reason: "Editorial/news outlet" },
  { name: "Chứng khoán Nhất Việt - VFS", url: "https://facebook.com/ChungkhoanVFS/", role: "institutional_reference", reason: "Corporate securities company" },
  { name: "Thuận Phái Sinh VN", url: "https://facebook.com/thuanphaisinhvn/", role: "extended_creator_peer", reason: "Text-first; may not match 87% video format" },
];
for (const e of existingDowngrades) {
  csv6Lines.push([e.name,e.url,"facebook_page","unknown","unknown","","unknown",e.role,"stock","none",0,0,"low","","EXISTING AUDIT DOWNGRADE — "+e.reason].map(esc).join(","));
}
writeFileSync(join(outDir, "public-benchmark-peer-set-v3-1-proposed.csv"), csv6Lines.join("\n") + "\n");

// ─── Summary ────────────────────────────────────────────
console.log("=== Balanced Peer Set v3.1 Summary ===");
console.log("Total candidates (deduped):", scored.length);
console.log("\nCore picks:", corePicks.length);
for (const p of corePicks) console.log(`  ${p.vertical}: ${p.cand.name} (fit=${p.cand.fitScore}, eco=${p.cand.ecosystemName})`);
console.log("\nVertical balance:", JSON.stringify(currentByVertical));
console.log("\nReplacement shortlist:", replacementShortlist.length);
console.log("Files written to data/benchmark/:");
console.log("  expanded-targeted-candidates-v3-1.csv");
console.log("  manual-verification-v3-1/verification-checklist.csv");
console.log("  manual-verification-v3-1/verification-guide.md");
console.log("  manual-verification-v3-1/candidate-links.md");
console.log("  replacement-shortlist-v3-1.csv");
console.log("  public-benchmark-peer-set-v3-1-proposed.csv");
